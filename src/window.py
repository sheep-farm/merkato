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
from .category_model import CategoryModel
from .heatmap_view import HeatmapView


@Gtk.Template(resource_path='/com/github/sheepfarm/merkato/window.ui')
class MerkatoWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'MerkatoWindow'

    # Template children
    split_view = Gtk.Template.Child()
    sidebar_toggle = Gtk.Template.Child()
    category_list = Gtk.Template.Child()
    view_stack = Gtk.Template.Child()
    search_stock_entry = Gtk.Template.Child()
    list_stock = Gtk.Template.Child()
    heatmap_view = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    last_updated_label = Gtk.Template.Child()
    trash_view_mode = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gio.Settings.new('com.ekonomikas.merkato')

        # Restore window size
        width = self.settings.get_int('window-width')
        height = self.settings.get_int('window-height')
        is_maximized = self.settings.get_boolean('window-maximized')
        
        if width > 0 and height > 0:
            self.set_default_size(width, height)
        if is_maximized:
            self.maximize()

        # Inicializa o controller
        self.controller = StockController(update_interval=60)
        
        # Inicializa o modelo de categorias
        self.category_model = CategoryModel()
        
        # Popula a sidebar de categorias
        self._populate_category_sidebar()

        # Conecta sinais do controller
        self._connect_controller_signals()

        # Cria ações
        self._create_actions()

        # Conecta sinais da UI
        self._connect_ui_signals()
        
        # Conecta sinais de categoria
        self._connect_category_signals()
        
        # Conecta sinais do heatmap
        self._connect_heatmap_signals()

        # Carrega watchlist e inicia
        self._initialize()

    def _populate_category_sidebar(self):
        """Popula a sidebar com as categorias."""
        self.category_rows = {}
        
        for category_key, info in self.category_model.CATEGORIES.items():
            row = Adw.ActionRow()
            row.set_title(info.get('label', category_key))
            row.set_activatable(True)
            row.category_key = category_key
            
            # Ícone
            icon = Gtk.Image.new_from_icon_name(info.get('icon', 'folder-symbolic'))
            icon.set_pixel_size(16)
            row.add_prefix(icon)
            
            # Badge contador
            count_label = Gtk.Label(label="0")
            count_label.add_css_class("dim-label")
            count_label.add_css_class("caption")
            row.add_suffix(count_label)
            row.count_label = count_label
            
            self.category_list.append(row)
            self.category_rows[category_key] = row
        
        # Seleciona "All" por padrão
        if "All" in self.category_rows:
            self.category_list.select_row(self.category_rows["All"])

    def _update_category_counts(self):
        """Atualiza os contadores nas categorias."""
        for category_key, row in self.category_rows.items():
            count = self.category_model.get_category_count(category_key)
            row.count_label.set_label(str(count))

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
        self.sidebar_toggle.connect('toggled', self.on_sidebar_toggle)

        self.view_stack.connect('notify::visible-child-name', self.on_view_changed)
    
    def _connect_category_signals(self):
        """Conecta os sinais de categoria."""
        self.category_list.connect('row-activated', self.on_category_selected)
        self.category_model.connect('counts-updated', self.on_category_counts_updated)
    
    def _connect_heatmap_signals(self):
        """Conecta os sinais do heatmap."""
        self.heatmap_view.connect('stock-selected', self.on_heatmap_stock_selected)

    def _initialize(self):
        """Inicializa a aplicação."""
        self.load_watchlist()
        self.on_refresh_action()
        self.controller.start_auto_update()
        self.trash_view_mode.set_visible(not self.list_stock.is_empty())

    # ============== Callbacks de Categoria ==============
    
    def on_category_selected(self, listbox, row):
        """Callback quando uma categoria é selecionada."""
        if row and hasattr(row, 'category_key'):
            category_key = row.category_key
            self._filter_stocks_by_category(category_key)
    
    def on_category_counts_updated(self, model):
        """Callback quando as contagens são atualizadas."""
        self._update_category_counts()
    
    def on_view_changed(self, stack, param):
        """Callback quando a view muda entre List e Heatmap."""
        visible_child = stack.get_visible_child_name()

        # Mostra lixeira apenas na view List
        is_list_view = (visible_child == "list")
        self.trash_view_mode.set_visible(is_list_view and not self.list_stock.is_empty())

        # Se estava ativo e mudou para heatmap, desativa
        if not is_list_view and self.trash_view_mode.get_active():
            self.trash_view_mode.set_active(False)

    def on_sidebar_toggle(self, toggle_button):
        """Callback para toggle da sidebar."""
        self.split_view.set_show_sidebar(toggle_button.get_active())
    
    def _filter_stocks_by_category(self, category_key):
        """Filtra a lista de stocks pela categoria."""
        filtered_stocks = self.category_model.get_stocks_by_category(category_key)
        
        # Atualiza lista
        self.list_stock.clear_all()
        for stock in filtered_stocks:
            self.list_stock.append(stock)
        self.list_stock._apply_sort()
        
        # Atualiza heatmap COM A ORDEM DA LISTA
        sorted_stocks = self.list_stock.get_all_stocks()
        self.heatmap_view.set_stocks(sorted_stocks)
    
    # ============== Callbacks do Heatmap ==============
    
    def on_heatmap_stock_selected(self, heatmap, stock):
        """Callback quando um stock é selecionado no heatmap."""
        url = f"https://finance.yahoo.com/quote/{stock.symbol}/"
        Gio.AppInfo.launch_default_for_uri(url, None)

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
            self.category_model.update_stock(stock)
            self.list_stock.update(stock)

        # Atualiza heatmap com ordem da lista
        sorted_stocks = self.list_stock.get_all_stocks()
        self.heatmap_view.set_stocks(sorted_stocks)

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
        self.category_model.add_stock(stock)
        
        # Atualiza views se stock pertence à categoria atual
        selected_row = self.category_list.get_selected_row()
        if selected_row and hasattr(selected_row, 'category_key'):
            current_category = selected_row.category_key
            filtered = self.category_model.get_stocks_by_category(current_category)
            if stock in filtered:
                self.list_stock.append(stock)
                # Atualiza heatmap com ordem da lista
                sorted_stocks = self.list_stock.get_all_stocks()
                self.heatmap_view.set_stocks(sorted_stocks)

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
        
        # Atualiza heatmap com nova ordem
        sorted_stocks = self.list_stock.get_all_stocks()
        self.heatmap_view.set_stocks(sorted_stocks)

    def on_empty_state_changed(self, widget, is_empty):
        """Callback quando o estado vazio da lista muda."""
        visible_child = self.view_stack.get_visible_child_name()
        is_list_view = (visible_child == "list")
        self.trash_view_mode.set_visible(is_list_view and not is_empty)

        if is_empty and self.trash_view_mode.get_active():
            self.trash_view_mode.set_active(False)

    def on_close_request(self, window):
        """Save window state before closing"""
        self.settings.set_int('window-width', self.get_width())
        self.settings.set_int('window-height', self.get_height())
        self.settings.set_boolean('window-maximized', self.is_maximized())
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
            self.category_model.remove_stock(stock_item.symbol)
            
            # Atualiza heatmap
            sorted_stocks = self.list_stock.get_all_stocks()
            self.heatmap_view.set_stocks(sorted_stocks)
            
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
        self.last_updated_label.set_label(_(f"{datetime.now().strftime('%H:%M:%S')}"))

    def load_watchlist(self):
        """Carrega a watchlist do controller."""
        stocks_data, sort_order = self.controller.load_watchlist()

        if stocks_data:
            for stock_data in stocks_data:
                stock_item = Stock.from_dict(stock_data)
                self.category_model.add_stock(stock_item)
                self.list_stock.append(stock_item)

        if sort_order:
            self.sort_action.set_state(GLib.Variant("s", sort_order))
            self.list_stock.current_sort = sort_order
            self.list_stock._apply_sort()
        
        # Atualiza contadores e heatmap inicial
        self._update_category_counts()
        sorted_stocks = self.list_stock.get_all_stocks()
        self.heatmap_view.set_stocks(sorted_stocks)

    def save_watchlist(self) -> bool:
        """Salva a watchlist através do controller."""
        all_stocks = self.category_model.get_stocks_by_category("All")
        is_success = self.controller.save_watchlist(all_stocks)

        if not is_success:
            print(_("WARNING: Failed to save watchlist"))

        return is_success
