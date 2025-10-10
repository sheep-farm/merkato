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

        self.watchlist_manager = WatchlistManager()
        self.load_watchlist()

        self.on_refresh_action()

        self.start_auto_update()


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


    def stop_auto_update(self):
        self.pause_auto_update()
        self.is_paused = False


    def restart_auto_update(self):
        self.pause_auto_update()
        self.start_auto_update()


    ############################################################################
    # REFRESH THREAD
    ############################################################################
    def on_refresh_action(self, action = None, param = None):
        self.spinner.set_spinning(True)
        self.search_stock_entry.freeze(True)

        # Executa a busca em uma thread separada
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

            # Usa GLib.idle_add para atualizar a interface na thread principal
            from gi.repository import GLib
            GLib.idle_add(self._refresh_results, results, errors)

        except Exception as e:
            print(f"Erro na busca: {e}")
            from gi.repository import GLib
            GLib.idle_add(self._on_search_error, str(e))


    def _refresh_results(self, results, errors):
        for symbol, stock in results.items():
            self.list_stock.update(stock.symbol, stock.price, stock.change)

        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)

        self.last_updated_label.set_label(
            _(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        )

        return False  # Remove o idle callback


    ############################################################################
    # SEARCH THREAD
    ############################################################################
    def on_search_clicked (self, widget, symbol_input=None):
        if symbol_input is None:
            symbol_input = self.search_ticker_entry.get_text()
        symbol_input = symbol_input.strip().upper()
        symbols = [symbol.strip() for symbol in symbol_input.split(',') if symbol.strip()]
        symbols  = [item for item in symbols if item not in self.symbols_cache]

        # Evita múltiplas buscas simultâneas
        if hasattr(self, 'is_searching') and self.is_searching:
            return

        self.spinner.set_spinning(True)
        self.search_stock_entry.freeze(True)

        # Executa a busca em uma thread separada
        thread = threading.Thread(
            target=self._do_search,
            args=(symbols,),
            daemon=True
        )
        thread.start()


    def _do_search(self, symbols):
        """Executa a busca em background"""
        try:
            yr = YahooRequest()
            (results, errors) = yr.fetch(symbols)

            # Usa GLib.idle_add para atualizar a interface na thread principal
            from gi.repository import GLib
            GLib.idle_add(self._update_results, results, errors)

        except Exception as e:
            print(f"Erro na busca: {e}")
            from gi.repository import GLib
            GLib.idle_add(self._on_search_error, str(e))


    def _update_results(self, results, errors):
        """Atualiza a interface com os resultados (executa na thread principal)"""
        # self.list_stock.clear_all()
        for symbol, stock in results.items():
            self.list_stock.append(stock)
            self.symbols_cache.append(stock.symbol)

        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)
        self.search_stock_entry.clear_entry()

        self.last_updated_label.set_label(
            f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
        )

        return False  # Remove o idle callback


    def _on_search_error(self, error_msg):
        """Trata erros na busca"""
        print(f"Erro: {error_msg}")
        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)

        return False

    ###########################################################################
    # PERSISTENCE
    ###########################################################################
    def load_watchlist(self):
        saved_stocks_data = self.watchlist_manager.load()

        if saved_stocks_data:
            # Converter dicionários para StockItem e adicionar à lista
            for stock_data in saved_stocks_data:
                stock_item = Stock.from_dict(stock_data)
                self.list_stock.append(stock_item)
                self.symbols_cache.append(stock_item.symbol)
            self.last_updated_label.set_label('Last updated: in cache')


    def save_watchlist(self) -> bool:
        is_success = self.watchlist_manager.save(self.list_stock.get_all_stocks())

        if not is_success:
            print("WARNING: Failed to save watchlist")

        return is_success
        
