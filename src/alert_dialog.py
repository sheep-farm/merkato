# alert_dialog.py
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
from .alert import Alert
from .stock import Stock


@Gtk.Template(resource_path='/com/github/sheepfarm/merkato/alert_dialog.ui')
class AlertDialog(Adw.Dialog):
    __gtype_name__ = 'AlertDialog'

    # Template children
    cancel_button = Gtk.Template.Child()
    create_button = Gtk.Template.Child()
    symbol_entry = Gtk.Template.Child()
    stock_name_row = Gtk.Template.Child()
    alert_type_row = Gtk.Template.Child()
    target_price_entry = Gtk.Template.Child()
    currency_label = Gtk.Template.Child()
    current_price_row = Gtk.Template.Child()

    __gsignals__ = {
        'alert-created': (GObject.SignalFlags.RUN_FIRST, None, (Alert,)),
    }

    def __init__(self, stock: Stock = None, **kwargs):
        super().__init__(**kwargs)

        self.stock = stock
        self.created_alert = None

        # Connect signals
        self.cancel_button.connect('clicked', self.on_cancel_clicked)
        self.create_button.connect('clicked', self.on_create_clicked)
        self.symbol_entry.connect('changed', self.on_symbol_changed)
        self.target_price_entry.connect('changed', self.on_price_changed)

        # Configure alert type (default: above)
        self.alert_type_row.set_selected(0)

        # If a stock was provided, fill in the data
        if stock:
            self.set_stock(stock)
        else:
            self.symbol_entry.set_editable(True)

        self.validate_form()

    def set_stock(self, stock: Stock):
        """
        Set the stock for which to create the alert.

        Args:
            stock: Stock object
        """
        self.stock = stock
        self.symbol_entry.set_text(stock.symbol)
        self.symbol_entry.set_editable(False)
        self.stock_name_row.set_subtitle(stock.long_name)

        # Update current price
        price_str = f"{stock.currency_symbol}{stock.price:.2f}"
        self.current_price_row.set_subtitle(price_str)

        # Update currency symbol
        self.currency_label.set_label(stock.currency_symbol)

        self.validate_form()

    def on_symbol_changed(self, entry):
        """Callback when the symbol is changed."""
        # TODO: Fetch stock information when user types
        # For now, just validate the form
        self.validate_form()

    def on_price_changed(self, entry):
        """Callback when the target price is changed."""
        self.validate_form()

    def validate_form(self) -> bool:
        """
        Validate the form and enable/disable the Create button.

        Returns:
            True if the form is valid
        """
        symbol = self.symbol_entry.get_text().strip()
        price_text = self.target_price_entry.get_text().strip()

        # Validate symbol
        has_symbol = len(symbol) > 0

        # Validate price
        has_valid_price = False
        try:
            if price_text:
                price = float(price_text)
                has_valid_price = price > 0
        except ValueError:
            pass

        is_valid = has_symbol and has_valid_price
        self.create_button.set_sensitive(is_valid)

        return is_valid

    def on_cancel_clicked(self, button):
        """Callback for Cancel button."""
        self.close()

    def on_create_clicked(self, button):
        """Callback for Create button."""
        if not self.validate_form():
            return

        # Collect form data
        symbol = self.symbol_entry.get_text().strip().upper()
        target_price = float(self.target_price_entry.get_text().strip())

        # Alert type (0 = above, 1 = below)
        alert_type = 'above' if self.alert_type_row.get_selected() == 0 else 'below'

        # Create the alert
        alert = Alert(
            symbol=symbol,
            alert_type=alert_type,
            target_price=target_price,
            enabled=True,
        )

        print(f"Alert created: {alert}")
        self.created_alert = alert
        self.emit('alert-created', alert)
        self.close()

    def get_created_alert(self) -> Alert:
        """
        Return the created alert (or None if cancelled).

        Returns:
            Alert object or None
        """
        return self.created_alert
