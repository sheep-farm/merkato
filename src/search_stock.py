# search_stock.py
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

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, GObject


@Gtk.Template(resource_path='/com/github/sheepfarm/merkato/search_stock.ui')
class MerkatoSearchStock(Gtk.Box):
    """
    Widget de busca de stocks.
    Contém um campo de entrada e botão de busca.
    """
    __gtype_name__ = 'MerkatoSearchStock'

    __gsignals__ = {
        'activate': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    _entry: Gtk.Entry = Gtk.Template.Child()
    _button: Gtk.Button = Gtk.Template.Child()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_signals()
        self._update_button_state()


    def _setup_signals(self):
        """Configura os sinais do widget."""
        self._entry.connect('activate', self._on_activate)
        self._entry.connect('changed', self._on_changed)
        self._entry.connect('changed', self._on_text_changed)
        self._button.connect('clicked', self._on_activate)

    # ============== Callbacks ==============

    def _on_activate(self, widget):
        """Callback quando o usuário ativa a busca."""
        text = self._entry.get_text()
        if text.strip():
            self.emit('activate', text)


    def _on_changed(self, widget):
        """Callback quando o texto muda."""
        self.emit('changed', self._entry.get_text())


    def _on_text_changed(self, widget):
        """Callback para atualizar estado do botão."""
        self._update_button_state()

    # ============== Métodos públicos ==============

    def get_text(self) -> str:
        """
        Retorna o texto atual do campo de entrada.

        Returns:
            Texto do campo
        """
        return self._entry.get_text()


    def set_text(self, text: str):
        """
        Define o texto do campo de entrada.

        Args:
            text: Texto a ser definido
        """
        self._entry.set_text(text)


    def clear_entry(self):
        """Limpa o campo de entrada."""
        self.set_text('')


    def freeze(self, frozen: bool = True):
        """
        Congela/descongela o widget (desabilita interação).

        Args:
            frozen: True para congelar, False para descongelar
        """
        self._entry.set_sensitive(not frozen)

        if not frozen:
            self._update_button_state()
        else:
            self._button.set_sensitive(False)


    def focus_entry(self):
        """Coloca o foco no campo de entrada."""
        self._entry.grab_focus()


    def select_all(self):
        """Seleciona todo o texto do campo."""
        self._entry.select_region(0, -1)

    # ============== Métodos privados ==============

    def _update_button_state(self):
        """Atualiza o estado do botão baseado no texto."""
        has_text = len(self._entry.get_text()) > 0
        self._button.set_sensitive(has_text)


    def _is_frozen(self) -> bool:
        """
        Verifica se o widget está congelado.

        Returns:
            True se está congelado
        """
        return not self._entry.get_sensitive()
