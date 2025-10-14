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
import html
import locale

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject, Gio

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
        'empty-state-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.remove_is_enabled = False
        self.current_sort = 'alphabetical'

        self.stock_list_store = Gio.ListStore.new(Stock)
        self._list_stock.bind_model(self.stock_list_store, self._create_stock_row)

        self._list_stock.connect('row-selected', self._on_row_selected)
        self.stock_list_store.connect("items-changed", self._on_items_changed)

        self._update_state()

    # ============== Métodos de ordenação ==============

    def sort_alphabetical(self):
        """Ordena alfabeticamente por nome."""
        self.current_sort = 'alphabetical'
        self._apply_sort()

    def sort_by_gains(self):
        """Ordena por maiores ganhos."""
        self.current_sort = 'gains'
        self._apply_sort()

    def sort_by_losses(self):
        """Ordena por maiores perdas."""
        self.current_sort = 'losses'
        self._apply_sort()

    def _apply_sort(self):
        """Aplica a ordenação atual."""
        stocks = self.get_all_stocks()

        if self.current_sort == 'alphabetical':
            stocks.sort(key=lambda s: s.long_name.lower())
        elif self.current_sort == 'gains':
            stocks.sort(
                key=lambda s: float(s.change_pct) if s.change_pct is not None else -float('inf'),
                reverse=True
            )
        elif self.current_sort == 'losses':
            stocks.sort(
                key=lambda s: float(s.change_pct) if s.change_pct is not None else float('inf')
            )

        self.stock_list_store.remove_all()
        for stock in stocks:
            self.stock_list_store.append(stock)

    # ============== Manipulação de stocks ==============

    def append(self, stock_item: Stock):
        """Adiciona um stock à lista."""
        if stock_item:
            self.stock_list_store.append(stock_item)

    def update(self, updated_stock: Stock) -> bool:
        """
        Atualiza um stock existente.

        Args:
            updated_stock: Stock com dados atualizados

        Returns:
            True se atualizado com sucesso
        """
        for i in range(self.stock_list_store.get_n_items()):
            stock = self.stock_list_store.get_item(i)
            if stock.symbol == updated_stock.symbol:
                stock.long_name = updated_stock.long_name
                stock.price = updated_stock.price
                stock.change = updated_stock.change
                stock.change_pct = updated_stock.change_pct
                stock.market_state = updated_stock.market_state
                stock.currency = updated_stock.currency
                stock.currency_symbol = updated_stock.currency_symbol

                self.stock_list_store.items_changed(i, 1, 1)

                if self.current_sort != 'alphabetical':
                    self._apply_sort()

                return True

        return False

    def remove_stock_by_symbol(self, symbol: str) -> bool:
        """
        Remove um stock pelo símbolo.

        Args:
            symbol: Símbolo do stock

        Returns:
            True se removido com sucesso
        """
        for i in range(self.stock_list_store.get_n_items()):
            stock = self.stock_list_store.get_item(i)
            if stock.symbol == symbol:
                self.stock_list_store.remove(i)
                return True
        return False

    def clear_all(self):
        """Remove todos os stocks."""
        self.stock_list_store.remove_all()

    def get_all_stocks(self) -> list:
        """Retorna lista com todos os stocks."""
        return [
            self.stock_list_store.get_item(i)
            for i in range(self.stock_list_store.get_n_items())
        ]

    def get_selected_stock(self) -> Stock:
        """Retorna o stock selecionado."""
        selected_row = self._list_stock.get_selected_row()
        return selected_row.stock_item if selected_row else None

    def is_empty(self) -> bool:
        """Verifica se a lista está vazia."""
        return self.stock_list_store.get_n_items() == 0

    # ============== Modo de remoção ==============

    def set_remove_enabled(self, enabled: bool):
        """
        Habilita/desabilita o modo de remoção.

        Args:
            enabled: True para habilitar
        """
        self.remove_is_enabled = enabled

        for i in range(self.stock_list_store.get_n_items()):
            row = self._list_stock.get_row_at_index(i)
            if row and hasattr(row, 'remove_button'):
                if enabled:
                    row.remove_button.add_css_class("enabled")
                else:
                    row.remove_button.remove_css_class("enabled")

    # ============== Criação de linhas ==============

    def _create_stock_row(self, stock_item: Stock) -> Gtk.ListBoxRow:
        """
        Cria uma linha para exibir um stock.

        Args:
            stock_item: Stock a ser exibido

        Returns:
            Widget da linha
        """
        if not stock_item:
            return None

        row = Adw.ActionRow()
        row.set_activatable(True)
        row.set_cursor_from_name("pointer")
        row.stock_item = stock_item

        # Título e subtítulo
        if stock_item.long_name:
            row.set_title(html.escape(stock_item.long_name))
        if stock_item.symbol:
            row.set_subtitle(stock_item.symbol)

        # Box de informações (preço e variação)
        suffix_box = self._create_price_box(stock_item)
        row.add_suffix(suffix_box)

        # Botão de remoção
        remove_button = self._create_remove_button(stock_item)
        row.remove_button = remove_button
        row.add_suffix(remove_button)

        # Estilo baseado no estado do mercado
        self._apply_market_state_style(row, stock_item)

        # Ação ao clicar (abre no Yahoo Finance)
        url = f"https://finance.yahoo.com/quote/{stock_item.symbol}/"
        row.connect("activated", lambda r: Gio.AppInfo.launch_default_for_uri(url, None))

        return row

    def _create_price_box(self, stock_item: Stock) -> Gtk.Box:
        """Cria o box com preço e variação."""
        suffix_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        suffix_box.set_halign(Gtk.Align.END)
        suffix_box.set_valign(Gtk.Align.CENTER)
        suffix_box.set_spacing(2)

        # Label de preço
        price_label = Gtk.Label()
        price_label.set_halign(Gtk.Align.END)
        price_label.add_css_class("numeric")

        currency_symbol = '' if stock_item.symbol.startswith("^") else stock_item.currency
        price_fmt = locale.format_string("%.2f", stock_item.price, grouping=True, monetary=True)
        price_label.set_label(f"{price_fmt} {currency_symbol}")

        # Label de variação
        change_label = Gtk.Label()
        change_label.set_halign(Gtk.Align.END)
        change_label.add_css_class("caption")

        change_fmt = locale.format_string("%.2f", stock_item.change, grouping=True, monetary=True)
        change_pct_fmt = locale.format_string("%.2f", stock_item.change_pct * 100, grouping=True, monetary=True)

        if stock_item.change >= 0:
            change_label.set_label(f"+{change_fmt} ({change_pct_fmt}%)")
            change_label.add_css_class("success")
        else:
            change_label.set_label(f"{change_fmt} ({change_pct_fmt}%)")
            change_label.add_css_class("error")

        suffix_box.append(price_label)
        suffix_box.append(change_label)

        return suffix_box

    def _create_remove_button(self, stock_item: Stock) -> Gtk.Button:
        """Cria o botão de remoção."""
        remove_button = Gtk.Button()
        remove_button.set_icon_name("user-trash-symbolic")
        remove_button.set_valign(Gtk.Align.CENTER)
        remove_button.add_css_class("flat")
        remove_button.add_css_class("circular")
        remove_button.add_css_class("remove-button")
        remove_button.set_tooltip_text(_("Remove from watchlist"))
        remove_button.connect("clicked", self._on_remove_button_clicked, stock_item)

        if self.remove_is_enabled:
            remove_button.add_css_class("enabled")

        return remove_button

    def _apply_market_state_style(self, row: Gtk.Widget, stock_item: Stock):
        """Aplica estilo baseado no estado do mercado."""
        if stock_item.market_state == "REGULAR":
            row.remove_css_class("market-closed")
            row.add_css_class("market-opened")
        else:
            row.remove_css_class("market-opened")
            row.add_css_class("market-closed")

    # ============== Callbacks ==============

    def _on_row_selected(self, listbox, row):
        """Callback quando uma linha é selecionada."""
        if row:
            self.emit('stock-selected', row.stock_item)

    def _on_remove_button_clicked(self, button, stock_item):
        """Callback quando o botão de remoção é clicado."""
        self.emit('stock-remove-requested', stock_item)

    def _on_items_changed(self, list_store, position, removed, added):
        """Callback quando itens são modificados na lista."""
        self._update_state()

    def _update_state(self):
        """Atualiza o estado de visibilidade (vazio/com conteúdo)."""
        is_empty = self.is_empty()
        has_items = not is_empty

        self._list_scroll.set_visible(has_items)
        self._empty_watchlist_state.set_visible(is_empty)

        self.emit('empty-state-changed', is_empty)
