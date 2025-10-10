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
        'stock-selected': (GObject.SignalFlags.RUN_FIRST, None, (Stock,))
    }


    def __init__ (self, **kwargs):
        super().__init__(**kwargs)
        self.setup_css()

        self.stock_list_store = Gio.ListStore.new(Stock)
        self._list_stock.connect('row-selected', self._on_row_selected)

        self._list_stock.bind_model(self.stock_list_store, self._create_stock_row)

        # Conectar sinais para atualizar visibilidade
        self.stock_list_store.connect("items-changed", self._on_items_changed)
        self.updtate_state()

    def setup_css(self):
        """Configura estilos CSS customizados"""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
              .market-closed {
                background: repeating-linear-gradient(
                    45deg,
                    rgba(255, 193, 7, 0.04),
                    rgba(255, 193, 7, 0.04) 12px,
                    rgba(255, 193, 7, 0.08) 12px,
                    rgba(255, 193, 7, 0.08) 24px
                );
            }

            /*
            .market-closed {
                background: repeating-linear-gradient(
                    45deg,
                    rgba(0, 0, 0, 0.015),
                    rgba(0, 0, 0, 0.015) 10px,
                    rgba(0, 0, 0, 0.03) 10px,
                    rgba(0, 0, 0, 0.03) 20px
                );
            }
            */
            /* Opcional: adiciona borda sutil */

            .market-closed {
                //border-left: 3px solid rgba(255, 193, 7, 0.3);
            }

        """)

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _on_items_changed (self, list_store, position, removed, added):
        self.updtate_state()


    def _create_stock_row (self, stock_item: Stock) -> Gtk.ListBoxRow:
        if stock_item:
            # Criar ActionRow
            row = Adw.ActionRow()
            row.set_activatable(True)
            row.connect("activated", self._on_row_activated, f"https://finance.yahoo.com/quote/{stock_item.symbol}/")

            row.set_title(html.escape(stock_item.long_name))
            row.set_subtitle(stock_item.symbol)
            # Box com preço e variação
            suffix_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            suffix_box.set_halign(Gtk.Align.END)
            suffix_box.set_valign(Gtk.Align.CENTER)
            suffix_box.set_spacing(2)

            # Label de preço
            price_label = Gtk.Label()
            price_label.set_halign(Gtk.Align.END)
            price_label.add_css_class("numeric")

            currency_symbol = ''
            if not stock_item.symbol.startswith("^"):
                currency_symbol = stock_item.currency_symbol;

            price_label.set_label(f"{currency_symbol} {stock_item.price:.2f}")

            # Label de variação
            change_label = Gtk.Label()
            change_label.set_halign(Gtk.Align.END)
            change_label.add_css_class("caption")
            change = stock_item.change
            change_pct = stock_item.change_pct * 100

            if change >= 0:
               change_label.set_label(f"+{change:.2f} ({change_pct:.2f}%)")
            else:
               change_label.set_label(f"{change:.2f} ({change_pct:.2f}%)")

            suffix_box.append(price_label)
            suffix_box.append(change_label)

            row.add_suffix(suffix_box)

            # Armazenar referência ao Stock no row
            row.stock_item = stock_item

            if stock_item.market_state == 'CLOSED':
                row.remove_css_class("market-opened")
                row.add_css_class("market-closed")
            else:
                row.remove_css_class("market-closed")
                row.add_css_class("market-opened")

            if stock_item.change >= 0:
                change_label.remove_css_class("error")
                change_label.add_css_class("success")
            else:
                change_label.remove_css_class("success")
                change_label.add_css_class("error")

            return row
        else:
            return None


    def _on_row_activated(self, row, url):
        launcher = Gtk.UriLauncher.new(url)
        launcher.launch(None, None, None, None)


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


    def update (self, symbol: str, price: float, change: float) -> bool:

        for i in range(self.stock_list_store.get_n_items()):
            stock = self.stock_list_store.get_item(i)
            if stock.symbol == symbol:
                stock.price = price
                stock.change = change
                self.stock_list_store.items_changed(i, 1, 1)
                return True
        return False


    def clear_all (self):
        self.stock_list_store.remove_all()


    def get_all_stocks (self):
        return [self.stock_list_store.get_item(i) for i in range(self.stock_list_store.get_n_items())]


    def updtate_state (self):
        has_items = self._list_stock.get_row_at_index(0) is not None
        self._list_scroll.set_visible(has_items)


    def get_selected_stock(self) -> Stock:
        return self._list_stock.get_selected_row().stock_item

