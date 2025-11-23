# heatmap_view.py
#
# Copyright 2025 Flávio de Vasconcellos Corrêa
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk, Gdk, GObject
import cairo
import math


class Rectangle:
    """Representa um retângulo no treemap."""
    def __init__(self, x, y, width, height, stock=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.stock = stock


class HeatmapView(Gtk.DrawingArea):
    """
    Widget de heatmap usando Cairo.
    Um treemap com áreas proporcionais ao peso (derivado de change_pct).
    Verde = ganhos, Vermelho = perdas.
    Estilo mais próximo do treemap do Yahoo Finance.
    """

    __gtype_name__ = 'HeatmapView'

    __gsignals__ = {
        'stock-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self):
        super().__init__()

        self.stocks = []
        self.rectangles = []
        self.hovered_rect = None

        # Para evitar re-layout desnecessário
        self._last_width = 0
        self._last_height = 0

        # Configurar eventos
        self.set_draw_func(self._on_draw)

        motion_controller = Gtk.EventControllerMotion()
        motion_controller.connect('motion', self._on_motion)
        motion_controller.connect('leave', self._on_leave)
        self.add_controller(motion_controller)

        click_controller = Gtk.GestureClick()
        click_controller.connect('pressed', self._on_click)
        self.add_controller(click_controller)

        self.set_has_tooltip(True)
        self.connect('query-tooltip', self._on_query_tooltip)

    # ---------------------------------------------------------------------
    # API pública
    # ---------------------------------------------------------------------
    def set_stocks(self, stocks):
        """
        Define a lista de stocks a ser exibida.

        Args:
            stocks: Lista de objetos Stock
                    Espera-se que tenham: symbol, change_pct, price,
                    opcionalmente sector, industry, long_name.
        """
        self.stocks = list(stocks)
        self._calculate_layout()
        self.queue_draw()

    # ---------------------------------------------------------------------
    # Layout - Treemap Squarified
    # ---------------------------------------------------------------------
    def _calculate_layout(self, width=None, height=None):
        """
        Calcula o layout dos retângulos usando algoritmo de
        treemap squarified (Bruls et al., 2000).
        """
        if not self.stocks:
            self.rectangles = []
            return

        # Descobre tamanho disponível
        if width is None or height is None:
            width = self.get_width()
            height = self.get_height()

        if width <= 0 or height <= 0:
            width = 800
            height = 600

        # Guarda para saber se precisa recalcular depois
        self._last_width = width
        self._last_height = height

        padding = 8
        inner_x = padding
        inner_y = padding
        inner_width = max(1, width - 2 * padding)
        inner_height = max(1, height - 2 * padding)

        # ---------------------------------------------
        # 1. Calcula pesos positivos a partir de change_pct
        # ---------------------------------------------
        # Normaliza para que todos os pesos sejam positivos
        min_change = min(s.change_pct for s in self.stocks)
        offset = abs(min_change) + 0.5 if min_change < 0 else 0.5

        weights = []
        for s in self.stocks:
            w = s.change_pct + offset
            # Evita peso zero ou negativo por segurança numérica
            w = max(w, 0.01)
            weights.append((w, s))

        total_weight = sum(w for w, _ in weights)
        if total_weight <= 0:
            total_weight = len(weights)

        total_area = float(inner_width * inner_height)
        # Área correspondente a cada peso
        norm_weights = [(w / total_weight) * total_area for (w, s) in weights]

        # Ordena por área decrescente (melhora a "squarificação")
        items = list(zip(norm_weights, [s for (_, s) in weights]))
        items.sort(key=lambda t: t[0], reverse=True)

        # ---------------------------------------------
        # 2. Squarified treemap
        # ---------------------------------------------
        rectangles = []

        def worst_aspect_ratio(row, row_area, side_len):
            """Calcula o pior aspect ratio da linha atual."""
            if not row:
                return float('inf')
            max_area = max(row)
            min_area = min(row)
            # Fórmula clássica de squarified
            return max(
                (side_len ** 2) * max_area / (row_area ** 2),
                (row_area ** 2) / ((side_len ** 2) * min_area)
            )

        def layout_row(row_items, x, y, w, h, horizontal=True):
            """
            Distribui uma "linha" de itens dentro da área atual.
            row_items: lista de (area, stock).
            horizontal: se True, coloca retângulos lado a lado na horizontal;
                        caso contrário, empilha na vertical.
            """
            row_area = sum(a for a, _ in row_items)
            if row_area <= 0:
                return [], x, y, w, h

            rects = []

            if horizontal:
                # Altura fixa, largura variável
                row_height = row_area / w
                curr_x = x
                for a, stk in row_items:
                    rect_width = a / row_height if row_height > 0 else 0
                    rects.append(
                        Rectangle(curr_x, y, rect_width, row_height, stk)
                    )
                    curr_x += rect_width
                # Atualiza área remanescente
                y += row_height
                h -= row_height
            else:
                # Largura fixa, altura variável
                row_width = row_area / h
                curr_y = y
                for a, stk in row_items:
                    rect_height = a / row_width if row_width > 0 else 0
                    rects.append(
                        Rectangle(x, curr_y, row_width, rect_height, stk)
                    )
                    curr_y += rect_height
                # Atualiza área remanescente
                x += row_width
                w -= row_width

            return rects, x, y, w, h

        # Algoritmo principal
        x, y = inner_x, inner_y
        w, h = inner_width, inner_height
        row = []
        row_areas = []
        horizontal = True  # alterna direção a cada linha

        for area, stock in items:
            if area <= 0:
                continue

            # Tenta adicionar o item à linha atual
            new_row = row_areas + [area]
            side_len = h if horizontal else w
            if side_len <= 0:
                break

            if not row_areas:
                row_areas.append(area)
                row.append((area, stock))
                continue

            prev_worst = worst_aspect_ratio(row_areas, sum(row_areas), side_len)
            new_worst = worst_aspect_ratio(new_row, sum(new_row), side_len)

            if new_worst <= prev_worst:
                # Ainda melhora / mantém, coloca junto
                row_areas.append(area)
                row.append((area, stock))
            else:
                # Layout da linha atual e começa uma nova
                new_rects, x, y, w, h = layout_row(row, x, y, w, h, horizontal)
                rectangles.extend(new_rects)
                horizontal = not horizontal
                row = [(area, stock)]
                row_areas = [area]

        # Última linha
        if row:
            new_rects, x, y, w, h = layout_row(row, x, y, w, h, horizontal)
            rectangles.extend(new_rects)

        self.rectangles = rectangles

    # ---------------------------------------------------------------------
    # Cores e desenho
    # ---------------------------------------------------------------------
    def _get_color_for_stock(self, stock, is_hover=False):
        """
        Retorna cor RGB baseada na mudança percentual.
        Verde para ganhos, vermelho para perdas.
        Intensidade contínua, estilo heatmap.

        Args:
            stock: Objeto Stock
            is_hover: Se está em hover

        Returns:
            Tupla (r, g, b) com valores 0-1
        """
        change = stock.change_pct
        abs_change = abs(change)

        # Saturação limitada (±8% vira "cheio")
        max_ref = 8.0
        t = min(abs_change / max_ref, 1.0)

        # Verde para alta, vermelho para queda
        if change >= 0:
            # Base verde mais escura
            base_r, base_g, base_b = (0.25, 0.45, 0.25)
            dark_r, dark_g, dark_b = (0.0, 0.39, 0.0)
        else:
            # Base vermelha mais escura
            base_r, base_g, base_b = (0.45, 0.20, 0.20)
            dark_r, dark_g, dark_b = (0.55, 0.0, 0.0)


        r = base_r + (dark_r - base_r) * t
        g = base_g + (dark_g - base_g) * t
        b = base_b + (dark_b - base_b) * t

        if is_hover:
            # Ilumina um pouco no hover
            r = min(1.0, r + 0.15)
            g = min(1.0, g + 0.15)
            b = min(1.0, b + 0.15)

        return (r, g, b)

    def _on_draw(self, area, cr, width, height):
        """Callback de desenho do Cairo."""
        # Recalcula layout se o tamanho mudou
        if width != self._last_width or height != self._last_height:
            self._calculate_layout(width, height)

        # Background
        cr.set_source_rgb(0.12, 0.12, 0.12)
        cr.paint()

        if not self.rectangles:
            # Mensagem quando vazio
            cr.set_source_rgb(0.7, 0.7, 0.7)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(18)

            text = "No stocks in this category"
            extents = cr.text_extents(text)
            x = (width - extents.width) / 2
            y = (height + extents.height) / 2

            cr.move_to(x, y)
            cr.show_text(text)
            return

        # Desenha cada retângulo
        for rect in self.rectangles:
            if not rect.stock:
                continue

            # Cor baseada em performance
            is_hover = (rect == self.hovered_rect)
            r, g, b = self._get_color_for_stock(rect.stock, is_hover)

            # Retângulo preenchido
            cr.set_source_rgb(r, g, b)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

            # Borda sutil
            cr.set_source_rgb(0.2, 0.2, 0.2)
            cr.set_line_width(1)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()

            # Texto
            self._draw_text(cr, rect)

    def _draw_text(self, cr, rect):
        """Desenha texto dentro do retângulo."""
        min_width = 50
        min_height = 30

        if rect.width < min_width or rect.height < min_height:
            return

        stock = rect.stock
        cr.set_source_rgb(1, 1, 1)

        # Símbolo (bold)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        font_size = min(rect.width / 4, rect.height / 3, 20)
        cr.set_font_size(font_size)

        symbol = stock.symbol
        extents = cr.text_extents(symbol)
        text_x = rect.x + (rect.width - extents.width) / 2
        text_y = rect.y + rect.height / 2 - 4

        cr.move_to(text_x, text_y)
        cr.show_text(symbol)

        # Mudança % (bold)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        font_size = min(rect.width / 5, rect.height / 4, 16)
        cr.set_font_size(font_size)

        change = stock.change_pct * 100
        change_text = f"{change:+.1f}%"
        extents = cr.text_extents(change_text)
        text_x = rect.x + (rect.width - extents.width) / 2
        text_y = rect.y + rect.height / 2 + extents.height + 2

        cr.move_to(text_x, text_y)
        cr.show_text(change_text)

        # Preço (pequeno, se houver espaço)
        if rect.width > 100 and rect.height > 70:
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(11)

            price_text = f"${stock.price:.2f}"
            extents = cr.text_extents(price_text)
            text_x = rect.x + (rect.width - extents.width) / 2
            text_y = rect.y + rect.height - 6

            cr.move_to(text_x, text_y)
            cr.show_text(price_text)

    # ---------------------------------------------------------------------
    # Hit-testing / eventos
    # ---------------------------------------------------------------------
    def _find_rect_at(self, x, y):
        """Encontra retângulo na posição x, y."""
        for rect in self.rectangles:
            if (rect.x <= x <= rect.x + rect.width and
                rect.y <= y <= rect.y + rect.height):
                return rect
        return None

    def _on_motion(self, controller, x, y):
        """Callback de movimento do mouse."""
        rect = self._find_rect_at(x, y)

        if rect != self.hovered_rect:
            self.hovered_rect = rect
            self.queue_draw()

            if rect:
                # Dependendo da versão do GTK, pode precisar do display:
                # display = self.get_display()
                # self.set_cursor(Gdk.Cursor.new_from_name(display, "pointer"))
                self.set_cursor(Gdk.Cursor.new_from_name("pointer", None))
            else:
                self.set_cursor(None)

    def _on_leave(self, controller):
        """Callback quando mouse sai."""
        if self.hovered_rect:
            self.hovered_rect = None
            self.queue_draw()
        self.set_cursor(None)

    def _on_click(self, gesture, n_press, x, y):
        """Callback de clique."""
        rect = self._find_rect_at(x, y)

        if rect and rect.stock:
            self.emit('stock-selected', rect.stock)

    def _on_query_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        """Callback para tooltip."""
        rect = self._find_rect_at(x, y)

        if rect and rect.stock:
            stock = rect.stock

            # Tooltip detalhado
            text = f"<b>{stock.symbol}</b> - {getattr(stock, 'long_name', '')}\n\n"
            text += f"<b>Price:</b> ${stock.price:.2f}\n"
            text += f"<b>Change:</b> {stock.change_pct * 100:+.2f}%\n"
            text += f"<b>Change $:</b> ${stock.change:+.2f}\n"

            if hasattr(stock, 'sector') and stock.sector:
                text += f"<b>Sector:</b> {stock.sector}\n"

            if hasattr(stock, 'industry') and stock.industry:
                text += f"<b>Industry:</b> {stock.industry}"

            tooltip.set_markup(text)
            return True

        return False
