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
    UM único quadrado onde áreas são proporcionais ao abs(change_percent).
    Verde = ganhos, Vermelho = perdas.
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
    
    def set_stocks(self, stocks):
        """
        Define a lista de stocks a ser exibida.
        
        Args:
            stocks: Lista de objetos Stock
        """
        self.stocks = list(stocks)
        self._calculate_layout()
        self.queue_draw()
    
    def _calculate_layout(self):
        """Calcula o layout do treemap proporcional ao change_percent."""
        if not self.stocks:
            self.rectangles = []
            return
        
        width = self.get_width()
        height = self.get_height()
        
        if width <= 0 or height <= 0:
            width = 800
            height = 600
        
        # Peso = abs(change_pct)
        # Se change_pct == 0, usa valor mínimo
        items = []
        for stock in self.stocks:
            change = abs(stock.change_pct)
            weight = max(change, 0.1)  # Mínimo 0.1 para aparecer
            items.append((stock, weight))
        
        # Treemap com padding
        padding = 8
        self.rectangles = self._squarify(
            items, 
            padding, 
            padding, 
            width - 2*padding, 
            height - 2*padding
        )
    
    def _squarify(self, items, x, y, width, height):
        """
        Implementa algoritmo squarified treemap.
        
        Args:
            items: Lista de (stock, weight)
            x, y: Posição inicial
            width, height: Dimensões disponíveis
        
        Returns:
            Lista de Rectangle
        """
        if not items or width <= 0 or height <= 0:
            return []
        
        # Ordena por peso (maior primeiro)
        items = sorted(items, key=lambda x: x[1], reverse=True)
        
        rectangles = []
        self._squarify_recursive(items, x, y, width, height, rectangles)
        return rectangles
    
    def _squarify_recursive(self, items, x, y, width, height, rectangles):
        """Recursivamente divide o espaço."""
        if not items:
            return
        
        if len(items) == 1:
            stock, weight = items[0]
            rectangles.append(Rectangle(x, y, width, height, stock))
            return
        
        total_weight = sum(w for _, w in items)
        
        # Divide em dois grupos
        mid = len(items) // 2
        group1 = items[:mid]
        group2 = items[mid:]
        
        weight1 = sum(w for _, w in group1)
        weight2 = sum(w for _, w in group2)
        
        ratio1 = weight1 / total_weight
        
        # Decide direção de corte
        if width >= height:
            # Corte vertical
            w1 = width * ratio1
            self._squarify_recursive(group1, x, y, w1, height, rectangles)
            self._squarify_recursive(group2, x + w1, y, width - w1, height, rectangles)
        else:
            # Corte horizontal
            h1 = height * ratio1
            self._squarify_recursive(group1, x, y, width, h1, rectangles)
            self._squarify_recursive(group2, x, y + h1, width, height - h1, rectangles)
    
    def _get_color_for_stock(self, stock, is_hover=False):
        """
        Retorna cor RGB baseada na mudança percentual.
        Verde para ganhos, vermelho para perdas.
        Intensidade proporcional ao valor.
        
        Args:
            stock: Objeto Stock
            is_hover: Se está em hover
        
        Returns:
            Tupla (r, g, b) com valores 0-1
        """
        change = stock.change_pct
        abs_change = abs(change)
        
        if change > 0:
            # VERDE para ganhos
            # Mais ganho = mais escuro
            if abs_change >= 10:
                r, g, b = 0.0, 0.5, 0.0  # Verde muito escuro
            elif abs_change >= 7:
                r, g, b = 0.0, 0.65, 0.0
            elif abs_change >= 5:
                r, g, b = 0.1, 0.7, 0.1
            elif abs_change >= 3:
                r, g, b = 0.2, 0.75, 0.2
            elif abs_change >= 1:
                r, g, b = 0.3, 0.8, 0.3
            else:
                r, g, b = 0.5, 0.85, 0.5  # Verde claro
        else:
            # VERMELHO para perdas
            # Mais perda = mais escuro
            if abs_change >= 10:
                r, g, b = 0.6, 0.0, 0.0  # Vermelho muito escuro
            elif abs_change >= 7:
                r, g, b = 0.7, 0.0, 0.0
            elif abs_change >= 5:
                r, g, b = 0.75, 0.1, 0.1
            elif abs_change >= 3:
                r, g, b = 0.8, 0.2, 0.2
            elif abs_change >= 1:
                r, g, b = 0.85, 0.3, 0.3
            else:
                r, g, b = 0.9, 0.5, 0.5  # Vermelho claro
        
        # Efeito hover
        if is_hover:
            r = min(1.0, r + 0.15)
            g = min(1.0, g + 0.15)
            b = min(1.0, b + 0.15)
        
        return (r, g, b)
    
    def _on_draw(self, area, cr, width, height):
        """Callback de desenho do Cairo."""
        if width != self.get_width() or height != self.get_height():
            self._calculate_layout()
        
        # Background
        cr.set_source_rgb(0.15, 0.15, 0.15)
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
            
            # Desenha retângulo preenchido
            cr.set_source_rgb(r, g, b)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
            
            # Borda branca fina
            cr.set_source_rgb(0.95, 0.95, 0.95)
            cr.set_line_width(2)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()
            
            # Texto (se houver espaço)
            self._draw_text(cr, rect)
    
    def _draw_text(self, cr, rect):
        """Desenha texto dentro do retângulo."""
        min_width = 60
        min_height = 40
        
        if rect.width < min_width or rect.height < min_height:
            return
        
        stock = rect.stock
        cr.set_source_rgb(1, 1, 1)
        
        # Símbolo (bold)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        font_size = min(rect.width / 4, rect.height / 3, 24)
        cr.set_font_size(font_size)
        
        symbol = stock.symbol
        extents = cr.text_extents(symbol)
        text_x = rect.x + (rect.width - extents.width) / 2
        text_y = rect.y + rect.height / 2 - 8
        
        cr.move_to(text_x, text_y)
        cr.show_text(symbol)
        
        # Mudança % (normal)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        font_size = min(rect.width / 5, rect.height / 4, 20)
        cr.set_font_size(font_size)
        
        change = stock.change_pct
        change_text = f"{change:+.1f}%"
        extents = cr.text_extents(change_text)
        text_x = rect.x + (rect.width - extents.width) / 2
        text_y = rect.y + rect.height / 2 + extents.height + 5
        
        cr.move_to(text_x, text_y)
        cr.show_text(change_text)
        
        # Preço (pequeno, se houver muito espaço)
        if rect.width > 100 and rect.height > 80:
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(12)
            
            price_text = f"${stock.price:.2f}"
            extents = cr.text_extents(price_text)
            text_x = rect.x + (rect.width - extents.width) / 2
            text_y = rect.y + rect.height / 2 + extents.height + 25
            
            cr.move_to(text_x, text_y)
            cr.show_text(price_text)
    
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
            text = f"<b>{stock.symbol}</b> - {stock.long_name}\n\n"
            text += f"<b>Price:</b> ${stock.price:.2f}\n"
            text += f"<b>Change:</b> {stock.change_pct:+.2f}%\n"
            text += f"<b>Change $:</b> ${stock.change:+.2f}\n"
            
            if hasattr(stock, 'sector') and stock.sector:
                text += f"<b>Sector:</b> {stock.sector}\n"
            
            if hasattr(stock, 'industry') and stock.industry:
                text += f"<b>Industry:</b> {stock.industry}"
            
            tooltip.set_markup(text)
            return True
        
        return False