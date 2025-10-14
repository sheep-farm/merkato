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

from datetime import datetime
from gi.repository import Adw, Gtk, Gio, GLib

from .search_stock import MerkatoSearchStock
from .list_stock import MerkatoListStock
from .stock_controller import StockController
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

        # Inicializa o controller
        self.controller = StockController(update_interval=60)

        # Conecta sinais do controller
        self._connect_controller_signals()

        # Cria ações
        self._create_actions()

        # Conecta sinais da UI
        self._connect_ui_signals()

        # Carrega watchlist e inicia
        self._initialize()

    def _create_actions(self):
        """Cria as ações da janela."""
        self.refresh_action = self._create_action('refresh', self.on_refresh_action)

        sort_action = Gio.SimpleAction.new_stateful(
            "sort",
            GLib.VariantType.new("s"),
            GLib.Variant("s", "alphabetical")
        )
        sort_action.connect("activate", self.on_sort_action)
        self.add_action(sort_action)
        self.sort_action = sort_action

    def _create_action(self, name, callback):
        """Helper para criar ações."""
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        return action

    def _connect_controller_signals(self):
        """Conecta os sinais do controller."""
        self.controller.connect('search-started', self.on_search_started)
        self.controller.connect('search-completed', self.on_search_completed)
        self.controller.connect('search-error', self.on_search_error)

        self.controller.connect('refresh-started', self.on_refresh_started)
        self.controller.connect('refresh-completed', self.on_refresh_completed)
        self.controller.connect('refresh-error', self.on_refresh_error)

        self.controller.connect('watchlist-loaded', self.on_watchlist_loaded)
        self.controller.connect('stock-added', self.on_stock_added)

    def _connect_ui_signals(self):
        """Conecta os sinais dos widgets da UI."""
        self.search_stock_entry.connect('activate', self.on_search_clicked)
        self.search_stock_entry.connect('changed', self.on_search_changed)
        self.connect('close-request', self.on_close_request)

        self.list_stock.connect('empty-state-changed', self.on_empty_state_changed)
        self.list_stock.connect('stock-remove-requested', self.on_stock_remove_requested)

        self.trash_view_mode.connect('toggled', self.on_trash_mode_toggled)

    def _initialize(self):
        """Inicializa a aplicação."""
        self.load_watchlist()
        self.on_refresh_action()
        self.controller.start_auto_update()
        self.trash_view_mode.set_visible(not self.list_stock.is_empty())

    # ============== Callbacks do Controller ==============

    def on_search_started(self, controller):
        """Callback quando a busca inicia."""
        self.spinner.set_spinning(True)
        self.search_stock_entry.freeze(True)

    def on_search_completed(self, controller, results, errors):
        """Callback quando a busca é completada."""
        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)
        self.search_stock_entry.clear_entry()
        self.update_timestamp()

    def on_search_error(self, controller, error_msg):
        """Callback quando ocorre erro na busca."""
        print(f"Search Error: {error_msg}")
        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)

    def on_refresh_started(self, controller):
        """Callback quando o refresh inicia."""
        self.refresh_action.set_enabled(False)
        self.sort_action.set_enabled(False)
        self.spinner.set_spinning(True)
        self.search_stock_entry.freeze(True)
        self.trash_view_mode.set_sensitive(False)

    def on_refresh_completed(self, controller, results, errors):
        """Callback quando o refresh é completado."""
        for symbol, stock in results.items():
            self.list_stock.update(stock)

        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)
        self.trash_view_mode.set_sensitive(True)
        self.refresh_action.set_enabled(True)
        self.sort_action.set_enabled(True)
        self.update_timestamp()

    def on_refresh_error(self, controller, error_msg):
        """Callback quando ocorre erro no refresh."""
        print(f"Refresh Error: {error_msg}")
        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)
        self.trash_view_mode.set_sensitive(True)
        self.refresh_action.set_enabled(True)
        self.sort_action.set_enabled(True)

    def on_watchlist_loaded(self, controller, stocks_data):
        """Callback quando a watchlist é carregada."""
        if stocks_data:
            self.last_updated_label.set_label(_('cached'))

    def on_stock_added(self, controller, stock):
        """Callback quando um stock é adicionado."""
        self.list_stock.append(stock)

    # ============== Callbacks da UI ==============

    def on_sort_action(self, action, parameter):
        """Callback para ação de ordenação."""
        sort_type = parameter.get_string()
        action.set_state(parameter)

        if sort_type == "alphabetical":
            self.list_stock.sort_alphabetical()
        elif sort_type == "gains":
            self.list_stock.sort_by_gains()
        elif sort_type == "losses":
            self.list_stock.sort_by_losses()

        self.controller.save_sort_order(sort_type)

    def on_empty_state_changed(self, widget, is_empty):
        """Callback quando o estado vazio da lista muda."""
        self.trash_view_mode.set_visible(not is_empty)

        if is_empty and self.trash_view_mode.get_active():
            self.trash_view_mode.set_active(False)

    def on_close_request(self, window):
        """Callback quando a janela vai ser fechada."""
        self.save_watchlist()
        self.controller.stop_auto_update()

    def on_search_changed(self, widget, text: str):
        """Callback quando o texto de busca muda."""
        if text:
            self.controller.pause_auto_update()
        else:
            self.controller.restart_auto_update()

    def on_trash_mode_toggled(self, toggle_button):
        """Callback quando o modo de remoção é alternado."""
        is_active = toggle_button.get_active()
        self.list_stock.set_remove_enabled(is_active)
        self.search_stock_entry.set_visible(not is_active)
        self.refresh_action.set_enabled(not is_active)
        self.sort_action.set_enabled(not is_active)

        if is_active:
            self.controller.pause_auto_update()
        else:
            self.controller.restart_auto_update()

    def on_stock_remove_requested(self, widget, stock_item):
        """Callback quando um stock é solicitado para remoção."""
        print(f"Removing stock: {stock_item.symbol} - {stock_item.long_name}")

        success = self.list_stock.remove_stock_by_symbol(stock_item.symbol)

        if success:
            self.controller.remove_stock(stock_item.symbol)
            print(f"Successfully removed {stock_item.symbol}")
        else:
            print(f"Failed to remove {stock_item.symbol}")

    def on_refresh_action(self, action=None, param=None):
        """Callback para ação de refresh."""
        self.controller.refresh_stocks()
        return True

    def on_search_clicked(self, widget, symbol_input=None):
        """Callback quando a busca é acionada."""
        if symbol_input is None:
            symbol_input = self.search_stock_entry.get_text()

        if symbol_input.strip():
            self.controller.search_stocks(symbol_input)

    # ============== Métodos auxiliares ==============

    def update_timestamp(self):
        """Atualiza o label de última atualização."""
        self.last_updated_label.set_label(
            _(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        )

    def load_watchlist(self):
        """Carrega a watchlist do controller."""
        stocks_data, sort_order = self.controller.load_watchlist()

        if stocks_data:
            for stock_data in stocks_data:
                stock_item = Stock.from_dict(stock_data)
                self.list_stock.append(stock_item)

        if sort_order:
            self.sort_action.set_state(GLib.Variant("s", sort_order))
            self.list_stock.current_sort = sort_order
            self.list_stock._apply_sort()

    def save_watchlist(self) -> bool:
        """Salva a watchlist através do controller."""
        stocks = self.list_stock.get_all_stocks()
        is_success = self.controller.save_watchlist(stocks)

        if not is_success:
            print(_("WARNING: Failed to save watchlist"))

        return is_success
