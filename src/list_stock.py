# list_stock.py
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

import gi
import sys
import html
import locale

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject, Gio, Gdk

from .stock import Stock

@Gtk.Template(resource_path='/com/github/sheepfarm/merkato/list_stock.ui')
class MerkatoListStock(Gtk.Box):
    __gtype_name__ = 'MerkatoListStock'

    _list_stock = Gtk.Template.Child()
    _empty_watchlist_state = Gtk.Template.Child()
    _list_scroll = Gtk.Template.Child()

    __gsignals__ = {
        'stock-selected': (GObject.SignalFlags.RUN_FIRST, None, (Stock,)),
        'stock-remove-requested': (GObject.SignalFlags.RUN_FIRST, None, (Stock,)),
        'empty-state-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool,))
    }

    def __init__ (self, **kwargs):
        super().__init__(**kwargs)
        self.remove_is_enabled = False

        self.stock_list_store = Gio.ListStore.new(Stock)
        self._list_stock.connect('row-selected', self._on_row_selected)

        self._list_stock.bind_model(self.stock_list_store, self._create_stock_row)

        # Connect signals to update visibility
        self.stock_list_store.connect("items-changed", self._on_items_changed)
        self.updtate_state()


    def _on_items_changed (self, list_store, position, removed, added):
        self.updtate_state()


    def _create_stock_row (self, stock_item: Stock) -> Gtk.ListBoxRow:
        if stock_item:
            # Create ActionRow
            row = Adw.ActionRow()
            row.set_activatable(True)
            row.set_cursor_from_name("pointer")

            if stock_item.long_name:
                row.set_title(html.escape(stock_item.long_name))
            if stock_item.symbol:
                row.set_subtitle(stock_item.symbol)

            # Box with price and change
            suffix_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            suffix_box.set_halign(Gtk.Align.END)
            suffix_box.set_valign(Gtk.Align.CENTER)
            suffix_box.set_spacing(2)

            # Price label
            price_label = Gtk.Label()
            price_label.set_halign(Gtk.Align.END)
            price_label.add_css_class("numeric")

            currency_symbol = ''
            if not stock_item.symbol.startswith("^"):
                currency_symbol = stock_item.currency;

            price_fmt = locale.format_string("%.2f", stock_item.price, grouping=True, monetary=True)

            price_label.set_label(f"{price_fmt} {currency_symbol}")

            # Change label
            change_label = Gtk.Label()
            change_label.set_halign(Gtk.Align.END)
            change_label.add_css_class("caption")

            change_fmt = locale.format_string("%.2f", stock_item.change, grouping=True, monetary=True)
            change_pct_fmt = locale.format_string("%.2f", stock_item.change_pct * 100, grouping=True, monetary=True)

            if stock_item.change >= 0:
               change_label.set_label(f"+{change_fmt} ({change_pct_fmt}%)")
            else:
               change_label.set_label(f"{change_fmt} ({change_pct_fmt}%)")

            suffix_box.append(price_label)
            suffix_box.append(change_label)

            row.add_suffix(suffix_box)

            # Remove button
            remove_button = Gtk.Button()
            remove_button.set_icon_name("user-trash-symbolic")
            remove_button.set_valign(Gtk.Align.CENTER)
            remove_button.add_css_class("flat")
            remove_button.add_css_class("circular")
            remove_button.add_css_class("remove-button")
            remove_button.set_tooltip_text("Remove from watchlist")
            remove_button.connect("clicked", self._on_remove_button_clicked, stock_item)

            # Apply enabled state
            if self.remove_is_enabled:
                remove_button.add_css_class("enabled")

            # Store button reference for later updates
            row.remove_button = remove_button

            row.add_suffix(remove_button)

            # Store Stock reference in row
            row.stock_item = stock_item

            if stock_item.market_state == "REGULAR":
                row.remove_css_class("market-closed")
                row.add_css_class("market-opened")
            else:
                row.remove_css_class("market-opened")
                row.add_css_class("market-closed")

            if stock_item.change >= 0:
                change_label.remove_css_class("error")
                change_label.add_css_class("success")
            else:
                change_label.remove_css_class("success")
                change_label.add_css_class("error")

            url = f"https://finance.yahoo.com/quote/{stock_item.symbol}/"
            row.connect("activated", lambda r: Gio.AppInfo.launch_default_for_uri(url, None))

            return row
        else:
            return None


    def _on_remove_button_clicked(self, button, stock_item):
        """Handle remove button click"""
        print(f"Remove button clicked for: {stock_item.symbol} - {stock_item.long_name}")
        self.emit('stock-remove-requested', stock_item)


    def _on_row_selected (self, listbox, row):
        if row:
            self.emit('stock-selected', row.stock_item)


    def append (self, stock_item: Stock):
        if stock_item:
            self.stock_list_store.append(stock_item)


    def remove(self, stock_item: Stock) -> bool:
        if stock_item:
            return remove_stock_by_symbol(stock_item.symbol)


    def remove_by_index (self, index: int):
        if 0 <= index < self.stock_list_store.get_n_items():
            self.stock_list_store.remove(index)


    def remove_stock_by_symbol (self, symbol: str) -> bool:
        for i in range(self.stock_list_store.get_n_items()):
            stock = self.stock_list_store.get_item(i)
            if stock.symbol == symbol:
                self.stock_list_store.remove(i)
                return True
        return False


    def update (self, _stock) -> bool:

        for i in range(self.stock_list_store.get_n_items()):
            stock = self.stock_list_store.get_item(i)
            if stock.symbol == _stock.symbol:
                stock.long_name = _stock.long_name
                stock.price = _stock.price
                stock.change = _stock.change
                stock.market_state = _stock.market_state
                stock.currency = _stock.currency
                stock.currency_symbol = _stock.currency_symbol
                self.stock_list_store.items_changed(i, 1, 1)
                return True
        return False


    def clear_all (self):
        self.stock_list_store.remove_all()


    def get_all_stocks (self):
        return [self.stock_list_store.get_item(i) for i in range(self.stock_list_store.get_n_items())]


    def updtate_state (self):
        is_empty = self.stock_list_store.get_n_items() == 0
        has_items = not is_empty

        self._list_scroll.set_visible(has_items)
        self._empty_watchlist_state.set_visible(is_empty)

        # Emit signal with empty state
        self.emit('empty-state-changed', is_empty)


    def get_selected_stock(self) -> Stock:
        return self._list_stock.get_selected_row().stock_item


    def set_remove_enabled(self, enabled: bool):
        """Enable or disable remove buttons for all rows"""
        self.remove_is_enabled = enabled

        # Update all existing rows
        for i in range(self.stock_list_store.get_n_items()):
            row = self._list_stock.get_row_at_index(i)
            if row and hasattr(row, 'remove_button'):
                if enabled:
                    row.remove_button.add_css_class("enabled")
                else:
                    row.remove_button.remove_css_class("enabled")

    def is_empty(self) -> bool:
        return self.stock_list_store.get_n_items() == 0
