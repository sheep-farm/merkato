# stock.py
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

from gi.repository import GObject, Gio

class Stock(GObject.Object):
    __gtype_name__ = 'Stock'

    def __init__(self, symbol: str = '',
                       long_name: str = '',
                       price: float = 0.0,
                       change: float = 0.0,
                       change_pct: float = 0.0,
                       market_state: str = '',
                       currency: str = '',
                       currency_symbol: str = ''):
        super().__init__()
        self._symbol = symbol
        self._long_name = long_name
        self._price = price
        self._change = change
        self._change_pct = change_pct
        self._market_state = market_state
        self._currency = currency
        self._currency_symbol = currency_symbol


    @GObject.Property(type=str)
    def symbol(self):
        return self._symbol


    @symbol.setter
    def symbol(self, value):
        self._symbol = value


    @GObject.Property(type=str)
    def long_name(self):
        return self._long_name


    @long_name.setter
    def long_name(self, value):
        self._long_name = value


    @GObject.Property(type=float)
    def price(self):
        return self._price


    @price.setter
    def price(self, value):
        self._price = value


    @GObject.Property(type=float)
    def change(self):
        return self._change


    @change.setter
    def change(self, value):
        self._change = value

    @GObject.Property(type=float)
    def change_pct(self):
        return self._change_pct


    @change_pct.setter
    def change_pct(self, value):
        self._change_pct = value


    @GObject.Property(type=str)
    def market_state(self):
        return self._market_state


    @market_state.setter
    def market_state(self, value):
        self._market_state = value

    @GObject.Property(type=str)
    def currency(self):
        return self._currency


    @currency.setter
    def currency(self, value):
        self._currency = value

    @GObject.Property(type=str)
    def currency_symbol(self):
        return self._currency_symbol


    @currency_symbol.setter
    def currency_symbol(self, value):
        self._currency_symbol = value


    def to_dict(self):
        return {
            'symbol': self.symbol,
            'long_name': self.long_name,
            'price': self.price,
            'change': self.change,
            'change_pct': self.change_pct,
            'market_state': self.market_state,
            'currency_symbol': self.currency_symbol,
            'currency': self.currency,
        }


    @classmethod
    def from_dict(cls, data):
        return cls(
            symbol = data.get('symbol', ''),
            long_name = data.get('long_name', ''),
            price = data.get('price', 0.0),
            change = data.get('change', 0.0),
            change_pct = data.get('change_pct', 0.0),
            market_state = data.get('market_state', ''),
            currency = data.get('currency', ''),
            currency_symbol = data.get('currency_symbol', ''),
        )

