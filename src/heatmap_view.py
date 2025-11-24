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
    """Rectangle representing a single stock tile."""
    def __init__(self, x, y, width, height, stock=None):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.stock = stock


class SectorRect:
    """Rectangle representing a sector block (group of stocks)."""
    def __init__(self, x, y, width, height, name):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.name = name or "Other"


class HeatmapView(Gtk.DrawingArea):
    """
    Yahoo-style heatmap using a squarified treemap with 2 levels:
    - Sector blocks
    - Stock tiles inside each sector
    """

    __gtype_name__ = "HeatmapView"

    __gsignals__ = {
        "stock-selected": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self):
        super().__init__()

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.stocks = []
        self.rectangles = []        # list[Rectangle] stocks
        self.sector_rectangles = [] # list[SectorRect]
        self.hovered_rect = None

        self._last_width = 0
        self._last_height = 0

        # Drawing
        self.set_draw_func(self._on_draw)

        # Motion / hover
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        motion.connect("leave", self._on_leave)
        self.add_controller(motion)

        # Click
        click = Gtk.GestureClick()
        click.connect("pressed", self._on_click)
        self.add_controller(click)

        # Tooltip
        self.set_has_tooltip(True)
        self.connect("query-tooltip", self._on_query_tooltip)

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def set_stocks(self, stocks):
        """
        Set list of stock objects to display.

        Each stock is expected to have at least:
        - symbol: str
        - change_pct: float (fraction, e.g. 0.0123 = 1.23%)
        - price: float

        Optional (improves layout / tooltip):
        - change: float (absolute dollar change)
        - sector: str
        - industry: str
        - long_name: str
        - market_cap: float
        - volume: float
        """
        self.stocks = list(stocks) if stocks else []
        # Invalida cache para forçar recálculo
        self._last_width = 0
        self._last_height = 0
        self._calculate_layout()
        self.queue_draw()

    # ------------------------------------------------------------------ #
    # Weight / grouping / treemap utilities                              #
    # ------------------------------------------------------------------ #
    def _compute_stock_weight(self, stock):
        """
        Compute weight used for area of the tile.

        Priority:
        1) market_cap, if present and positive
        2) volume * price, if both present and positive
        3) price * (abs(change_pct) + 0.2)
        4) fallback 1.0
        """
        try:
            mc = getattr(stock, "market_cap", None)
            if mc is not None and mc > 0:
                return float(mc)
        except Exception:
            pass

        try:
            vol = getattr(stock, "volume", None)
            price = getattr(stock, "price", None)
            if vol is not None and price is not None and vol > 0 and price > 0:
                return float(vol) * float(price)
        except Exception:
            pass

        try:
            price = float(getattr(stock, "price", 1.0) or 1.0)
            cp = float(getattr(stock, "change_pct", 0.0) or 0.0)
            return price * (abs(cp) + 0.2)
        except Exception:
            return 1.0

    def _group_by_sector(self):
        """Return dict sector_name -> list[stock]."""
        groups = {}
        for s in self.stocks:
            sec = getattr(s, "sector", None) or "Other"
            groups.setdefault(sec, []).append(s)
        return groups

    def _squarified_treemap(self, items, x, y, w, h, horizontal_first=True):
        """
        Squarified treemap implementation.

        items: list of (area, payload)
        Returns: list of (x, y, width, height, payload)
        """
        items = [(float(a), p) for a, p in items if a > 0]
        if not items or w <= 0 or h <= 0:
            return []

        items.sort(key=lambda t: t[0], reverse=True)

        def worst_aspect(row_areas, side_len):
            if not row_areas or side_len <= 0:
                return float("inf")
            row_area = sum(row_areas)
            if row_area <= 0:
                return float("inf")
            max_a = max(row_areas)
            min_a = min(row_areas)
            s2 = side_len * side_len
            return max(
                s2 * max_a / (row_area * row_area),
                (row_area * row_area) / (s2 * min_a),
            )

        def layout_row(row_items, x, y, w, h, horizontal):
            row_area = sum(a for a, _ in row_items)
            if row_area <= 0 or w <= 0 or h <= 0:
                return [], x, y, w, h

            out = []
            if horizontal:
                row_height = row_area / w
                cx = x
                for a, payload in row_items:
                    rw = a / row_height if row_height > 0 else 0
                    out.append((cx, y, rw, row_height, payload))
                    cx += rw
                y += row_height
                h -= row_height
            else:
                row_width = row_area / h
                cy = y
                for a, payload in row_items:
                    rh = a / row_width if row_width > 0 else 0
                    out.append((x, cy, row_width, rh, payload))
                    cy += rh
                x += row_width
                w -= row_width

            return out, x, y, w, h

        rects = []
        row_items = []
        row_areas = []
        horizontal = horizontal_first
        remaining = list(items)

        while remaining:
            a, payload = remaining.pop(0)
            if not row_items:
                row_items.append((a, payload))
                row_areas.append(a)
                continue

            side_len = h if horizontal else w
            current = worst_aspect(row_areas, side_len)
            new = worst_aspect(row_areas + [a], side_len)

            if new <= current:
                row_items.append((a, payload))
                row_areas.append(a)
            else:
                new_rects, x, y, w, h = layout_row(row_items, x, y, w, h, horizontal)
                rects.extend(new_rects)
                horizontal = not horizontal
                row_items = [(a, payload)]
                row_areas = [a]

        if row_items:
            new_rects, x, y, w, h = layout_row(row_items, x, y, w, h, horizontal)
            rects.extend(new_rects)

        # filter degenerate rectangles
        cleaned = []
        for rx, ry, rw, rh, payload in rects:
            if rw <= 0 or rh <= 0:
                continue
            cleaned.append((rx, ry, rw, rh, payload))
        return cleaned

    # ------------------------------------------------------------------ #
    # Layout                                                             #
    # ------------------------------------------------------------------ #
    def _calculate_layout(self, width=None, height=None):
        """Calculate simple grid layout with equal-sized squares."""
        if width is None:
            width = self.get_width()
        if height is None:
            height = self.get_height()

        if width <= 0 or height <= 0:
            self.rectangles = []
            self.sector_rectangles = []
            return

        if (
            width == self._last_width
            and height == self._last_height
            and self.rectangles
        ):
            return

        self._last_width = width
        self._last_height = height
        self.rectangles = []
        self.sector_rectangles = []

        if not self.stocks:
            return

        # Calculate grid dimensions
        n = len(self.stocks)
        if n == 0:
            return

        # Find optimal grid layout (closest to square)
        cols = math.ceil(math.sqrt(n * width / height))
        rows = math.ceil(n / cols)

        # Calculate cell size with small gap
        gap = 2
        cell_width = (width - (cols + 1) * gap) / cols
        cell_height = (height - (rows + 1) * gap) / rows

        # Create rectangles
        for i, stock in enumerate(self.stocks):
            col = i % cols
            row = i // cols

            x = gap + col * (cell_width + gap)
            y = gap + row * (cell_height + gap)

            self.rectangles.append(Rectangle(x, y, cell_width, cell_height, stock))

    # ------------------------------------------------------------------ #
    # Colors                                                             #
    # ------------------------------------------------------------------ #
    def _get_color_for_stock(self, stock, is_hover=False):
        """
        Cores vibrantes e saturadas: verde para positivo, vermelho para negativo.
        change_pct is assumed to be a fraction.
        """
        cp = float(getattr(stock, "change_pct", 0.0) or 0.0)
        abs_cp = abs(cp)

        max_ref = 0.08  # 8% saturates the color
        t = min(abs_cp / max_ref, 1.0)

        if cp >= 0:
            # Verde vibrante: do verde médio ao verde intenso
            base = (0.15, 0.60, 0.20)  # verde médio
            high = (0.05, 0.95, 0.25)  # verde muito saturado
        else:
            # Vermelho vibrante: do vermelho médio ao vermelho intenso
            base = (0.70, 0.15, 0.15)  # vermelho médio
            high = (0.95, 0.05, 0.05)  # vermelho muito saturado

        r = base[0] + (high[0] - base[0]) * t
        g = base[1] + (high[1] - base[1]) * t
        b = base[2] + (high[2] - base[2]) * t

        if is_hover:
            # Hover: adiciona brilho
            r = min(1.0, r + 0.15)
            g = min(1.0, g + 0.15)
            b = min(1.0, b + 0.15)

        return r, g, b

    # ------------------------------------------------------------------ #
    # Drawing                                                            #
    # ------------------------------------------------------------------ #
    def _on_draw(self, area, cr, width, height):
        self._calculate_layout(width, height)

        # Background (matches Adwaita dark reasonably)
        cr.set_source_rgb(0.08, 0.08, 0.10)
        cr.paint()

        if not self.rectangles:
            cr.set_source_rgb(0.7, 0.7, 0.7)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(16)
            text = "No stocks in this category"
            ext = cr.text_extents(text)
            x = (width - ext.width) / 2
            y = (height + ext.height) / 2
            cr.move_to(x, y)
            cr.show_text(text)
            return

        # 1) stock tiles (fill)
        for rect in self.rectangles:
            stock = rect.stock
            if not stock:
                continue
            is_hover = rect is self.hovered_rect
            r, g, b = self._get_color_for_stock(stock, is_hover)
            cr.set_source_rgb(r, g, b)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

        # 2) thin borders for tiles
        cr.set_line_width(1.0)
        cr.set_source_rgb(0.12, 0.12, 0.14)
        for rect in self.rectangles:
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.stroke()

        # 3) text inside tiles
        for rect in self.rectangles:
            self._draw_stock_text(cr, rect)

    def _draw_sectors(self, cr):
        """Draw sector border and label."""
        for srect in self.sector_rectangles:
            # Border
            cr.set_line_width(2.0)
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.15)
            cr.rectangle(srect.x, srect.y, srect.width, srect.height)
            cr.stroke()

            if srect.width < 40 or srect.height < 16:
                continue

            name = srect.name
            if len(name) > 24:
                name = name[:21] + "..."

            # Text style
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            font_size = min(12.0, srect.height * 0.20)
            cr.set_font_size(font_size)

            ext = cr.text_extents(name)
            tx = srect.x + 4
            ty = srect.y + ext.height + 2

            # Background behind text
            pad_x = 3
            pad_y = 1
            bg_w = ext.width + pad_x * 2
            bg_h = ext.height + pad_y * 2
            cr.set_source_rgba(0.02, 0.02, 0.02, 0.75)
            cr.rectangle(tx - pad_x, srect.y + 1, bg_w, bg_h)
            cr.fill()

            # Text
            cr.set_source_rgb(0.92, 0.92, 0.94)
            cr.move_to(tx, ty)
            cr.show_text(name)

    def _draw_stock_text(self, cr, rect: Rectangle):
        """Draw symbol, change% and optionally price inside a tile."""
        stock = rect.stock
        if not stock:
            return

        if rect.width < 48 or rect.height < 26:
            return

        symbol = getattr(stock, "symbol", "?")
        cp = float(getattr(stock, "change_pct", 0.0) or 0.0)
        cp_percent = cp * 100.0
        change_text = f"{cp_percent:+.1f}%"

        cr.set_source_rgb(1.0, 1.0, 1.0)

        # Symbol
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        sym_size = min(18.0, rect.height * 0.45, max(10.0, rect.width * 0.28))
        cr.set_font_size(sym_size)

        ext_sym = cr.text_extents(symbol)
        sym_x = rect.x + (rect.width - ext_sym.width) / 2
        sym_y = rect.y + rect.height * 0.45
        cr.move_to(sym_x, sym_y)
        cr.show_text(symbol)

        # Change %
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ch_size = min(14.0, rect.height * 0.30, max(9.0, rect.width * 0.24))
        cr.set_font_size(ch_size)

        ext_ch = cr.text_extents(change_text)
        ch_x = rect.x + (rect.width - ext_ch.width) / 2
        ch_y = sym_y + ext_ch.height + 2
        cr.move_to(ch_x, ch_y)
        cr.show_text(change_text)

        # Price (only if enough room)
        if rect.width > 90 and rect.height > 55:
            price = getattr(stock, "price", None)
            if price is not None:
                price_text = f"${price:.2f}"
                cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                cr.set_font_size(14.0)
                ext_p = cr.text_extents(price_text)
                px = rect.x + (rect.width - ext_p.width) / 2
                py = rect.y + rect.height - 6
                cr.move_to(px, py)
                cr.show_text(price_text)

    # ------------------------------------------------------------------ #
    # Hit-testing / events                                               #
    # ------------------------------------------------------------------ #
    def _find_rect_at(self, x, y):
        for rect in self.rectangles:
            if rect.x <= x <= rect.x + rect.width and rect.y <= y <= rect.y + rect.height:
                return rect
        return None

    def _on_motion(self, controller, x, y):
        rect = self._find_rect_at(x, y)
        if rect is not self.hovered_rect:
            self.hovered_rect = rect
            self.queue_draw()

            # Gtk4 + Adwaita (Wayland/X11) safe cursor usage:
            if rect is not None:
                try:
                    cursor = Gdk.Cursor.new_from_name("pointer")
                except TypeError:
                    # If API signature differs, just don't use a custom cursor
                    cursor = None
                self.set_cursor(cursor)
            else:
                self.set_cursor(None)

    def _on_leave(self, controller):
        if self.hovered_rect is not None:
            self.hovered_rect = None
            self.queue_draw()
        self.set_cursor(None)

    def _on_click(self, gesture, n_press, x, y):
        rect = self._find_rect_at(x, y)
        if rect and rect.stock:
            self.emit("stock-selected", rect.stock)

    def _on_query_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        rect = self._find_rect_at(x, y)
        if not rect or not rect.stock:
            return False

        stock = rect.stock
        symbol = getattr(stock, "symbol", "?")
        long_name = getattr(stock, "long_name", "") or ""
        price = getattr(stock, "price", None)
        cp = float(getattr(stock, "change_pct", 0.0) or 0.0)
        cp_percent = cp * 100.0
        change_abs = getattr(stock, "change", None)
        sector = getattr(stock, "sector", None)
        industry = getattr(stock, "industry", None)

        text = f"<b>{symbol}</b>"
        if long_name:
            text += f" - {long_name}"
        text += "\n\n"

        if price is not None:
            text += f"<b>Price:</b> ${price:.2f}\n"

        text += f"<b>Change:</b> {cp_percent:+.2f}%\n"
        if change_abs is not None:
            text += f"<b>Change $:</b> ${change_abs:+.2f}\n"

        if sector:
            text += f"<b>Sector:</b> {sector}\n"
        if industry:
            text += f"<b>Industry:</b> {industry}"

        tooltip.set_markup(text)
        return True
