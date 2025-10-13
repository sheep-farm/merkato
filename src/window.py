# window.py
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

import threading

from datetime import datetime
from gi.repository import Adw
from gi.repository import Gtk, Gio, GLib

from .search_stock  import MerkatoSearchStock
from .list_stock    import MerkatoListStock
from .yahoo_request import YahooRequest
from .watchlist_manager import WatchlistManager
from .stock import Stock

@Gtk.Template(resource_path='/com/github/sheepfarm/merkato/window.ui')
class MerkatoWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'MerkatoWindow'


    search_stock_entry = Gtk.Template.Child()
    list_stock = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    last_updated_label = Gtk.Template.Child()
    trash_view_mode = Gtk.Template.Child()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.symbols_cache = []
        self.timeout_id = None
        self.is_paused = False
        self.update_interval = 90

        self.create_action('refresh', self.on_refresh_action)
        self.search_stock_entry.connect('activate', self.on_search_clicked)
        self.search_stock_entry.connect('changed', self.on_search_changed)
        self.connect('close-request', self._on_close_request)
        self.list_stock.connect('empty-state-changed', self.on_empty_state_changed)

        # Connect trash mode toggle
        self.trash_view_mode.connect('toggled', self.on_trash_mode_toggled)

        # Connect remove signal from list_stock
        self.list_stock.connect('stock-remove-requested', self.on_stock_remove_requested)

        self.watchlist_manager = WatchlistManager()
        self.load_watchlist()

        self.on_refresh_action()

        self.start_auto_update()

        self.trash_view_mode.set_visible(not self.list_stock.is_empty())


    def on_empty_state_changed(self, widget, is_empty):
        self.trash_view_mode.set_visible(not is_empty)


    def _on_close_request(self, window):
        self.save_watchlist()


    def create_action(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)


    def on_search_changed(self, widget, text: str):
        if text:
            self.pause_auto_update()
        else:
            self.restart_auto_update()


    ############################################################################
    # TRASH MODE
    ############################################################################
    def on_trash_mode_toggled(self, toggle_button):
        """Handle trash mode toggle"""
        is_active = toggle_button.get_active()
        self.list_stock.set_remove_enabled(is_active)
        self.search_stock_entry.set_visible(not is_active)

        if is_active:
            self.pause_auto_update()
        else:
            self.restart_auto_update()


    def on_stock_remove_requested(self, widget, stock_item):
        """Handle stock removal request"""
        print(f"Removing stock: {stock_item.symbol} - {stock_item.long_name}")

        # Remove from list
        success = self.list_stock.remove_stock_by_symbol(stock_item.symbol)

        if success:
            # Remove from cache
            if stock_item.symbol in self.symbols_cache:
                self.symbols_cache.remove(stock_item.symbol)

            # Save watchlist
            self.save_watchlist()

            print(f"Successfully removed {stock_item.symbol}")
        else:
            print(f"Failed to remove {stock_item.symbol}")

        self.trash_view_mode.set_active(not self.list_stock.is_empty())


    ############################################################################
    # REFRESH POR INTERVALO DE TEMPO
    ############################################################################
    def start_auto_update(self):
        if self.timeout_id is None:
            self.is_paused = False
            self.timeout_id = GLib.timeout_add_seconds(
                self.update_interval,
                self.on_refresh_action
            )


    def pause_auto_update(self):
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
            self.is_paused = True
            self.spinner.set_spinning(False)


    def stop_auto_update(self):
        self.pause_auto_update()
        self.is_paused = False
        self.spinner.set_spinning(False)


    def restart_auto_update(self):
        self.pause_auto_update()
        self.start_auto_update()


    ############################################################################
    # REFRESH THREAD
    ############################################################################
    def on_refresh_action(self, action = None, param = None):
        self.spinner.set_spinning(True)
        self.search_stock_entry.freeze(True)

        # Execute search in separate thread
        thread = threading.Thread(
            target=self._do_refresh,
            args=(self.symbols_cache,),
            daemon=True
        )
        thread.start()


    def _do_refresh(self, symbols):
        try:
            yr = YahooRequest()
            (results, errors) = yr.fetch(symbols)

            # Use GLib.idle_add to update UI in main thread
            GLib.idle_add(self._refresh_results, results, errors)
        except Exception as e:
            print(f"Search error: {e}")
            GLib.idle_add(self._on_search_error, str(e))


    def _refresh_results(self, results, errors):
        for symbol, stock in results.items():
            self.list_stock.update(stock)

        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)

        self.last_updated_label.set_label(
            _(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        )

        return False  # Remove idle callback


    ############################################################################
    # SEARCH THREAD
    ############################################################################
    def on_search_clicked (self, widget, symbol_input=None):
        if symbol_input is None:
            symbol_input = self.search_ticker_entry.get_text()
        symbol_input = symbol_input.strip().upper()
        symbols = [symbol.strip() for symbol in symbol_input.split(',') if symbol.strip()]
        symbols  = [item for item in symbols if item not in self.symbols_cache]

        # Avoid multiple simultaneous searches
        if hasattr(self, 'is_searching') and self.is_searching:
            return

        self.spinner.set_spinning(True)
        self.search_stock_entry.freeze(True)

        # Execute search in separate thread
        thread = threading.Thread(
            target=self._do_search,
            args=(symbols,),
            daemon=True
        )
        thread.start()


    def _do_search(self, symbols):
        try:
            yr = YahooRequest()
            (results, errors) = yr.fetch(symbols)

            # Use GLib.idle_add to update UI in main thread
            GLib.idle_add(self._update_results, results, errors)

        except Exception as e:
            print(f"Search error: {e}")
            GLib.idle_add(self._on_search_error, str(e))


    def _update_results(self, results, errors):
        # self.list_stock.clear_all()
        for symbol, stock in results.items():
            self.list_stock.append(stock)
            self.symbols_cache.append(stock.symbol)

        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)
        self.search_stock_entry.clear_entry()

        self.last_updated_label.set_label(
            f"{datetime.now().strftime('%H:%M:%S')}"
        )

        return False  # Remove idle callback


    def _on_search_error(self, error_msg):
        """Handle search errors"""
        print(f"Error: {error_msg}")
        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)

        return False

    ###########################################################################
    # PERSISTENCE
    ###########################################################################
    def load_watchlist(self):
        saved_stocks_data = self.watchlist_manager.load()

        if saved_stocks_data:
            # Convert dictionaries to StockItem and add to list
            for stock_data in saved_stocks_data:
                stock_item = Stock.from_dict(stock_data)
                self.list_stock.append(stock_item)
                self.symbols_cache.append(stock_item.symbol)
            self.last_updated_label.set_label('cached')


    def save_watchlist(self) -> bool:
        is_success = self.watchlist_manager.save(self.list_stock.get_all_stocks())

        if not is_success:
            print(_("WARNING: Failed to save watchlist"))

        return is_success
