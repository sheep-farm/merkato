# category_sidebar.py
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

from gi.repository import Gtk, Adw, GObject


class CategoryRow(Adw.ActionRow):
    """Linha individual para cada categoria."""

    def __init__(self, category_key: str, label: str, icon_name: str, count: int = 0):
        super().__init__()
        self.category_key = category_key

        self.set_title(label)
        self.set_activatable(True)

        # Icon
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(16)
        self.add_prefix(icon)

        # Badge with counter
        self.count_label = Gtk.Label(label=str(count))
        self.count_label.add_css_class("dim-label")
        self.count_label.add_css_class("caption")
        self.add_suffix(self.count_label)

    def update_count(self, count: int):
        """Updates the counter."""
        self.count_label.set_label(str(count))


class CategorySidebar(Gtk.Box):
    """
    Sidebar with list of stock categories.
    """
    __gtype_name__ = 'CategorySidebar'

    __gsignals__ = {
        'category-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }

    def __init__(self, category_model, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)

        self.category_model = category_model
        self.rows = {}

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_margin_top(12)
        header_box.set_margin_bottom(6)
        header_box.set_margin_start(12)
        header_box.set_margin_end(12)

        header_label = Gtk.Label(label=_("Categories"))
        header_label.add_css_class("title-4")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_hexpand(True)
        header_box.append(header_label)

        self.append(header_box)

        # ScrolledWindow for the list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # ListBox with categories
        self.listbox = Gtk.ListBox()
        self.listbox.add_css_class("navigation-sidebar")
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-activated", self._on_row_activated)

        # Adiciona as categorias
        for category_key, data in self.category_model.CATEGORIES.items():
            row = CategoryRow(
                category_key,
                data.get('label', category_key),
                data.get('icon', 'folder-symbolic'),
                self.category_model.get_category_count(category_key)
            )
            self.rows[category_key] = row
            self.listbox.append(row)

        scrolled.set_child(self.listbox)
        self.append(scrolled)

        # Select "All" by default
        if "All" in self.rows:
            self.listbox.select_row(self.rows["All"])

        # Connect to counts update signal
        self.category_model.connect('counts-updated', self._on_counts_updated)

    def _on_row_activated(self, listbox, row):
        """Callback when a category is selected."""
        if row and hasattr(row, 'category_key'):
            self.emit('category-selected', row.category_key)

    def _on_counts_updated(self, model):
        """Callback when counts are updated."""
        self.update_counts()

    def update_counts(self):
        """Updates counters for all categories."""
        counts = self.category_model.get_all_category_counts()
        for category_key, row in self.rows.items():
            count = counts.get(category_key, 0)
            row.update_count(count)

    def select_category(self, category_key: str):
        """
        Seleciona uma categoria programaticamente.

        Args:
            category_key: Chave da categoria
        """
        if category_key in self.rows:
            self.listbox.select_row(self.rows[category_key])
