# stock.py (MODIFIED to include sector/industry)
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

from gi.repository import GObject


class Stock(GObject.Object):
    """
    Data model to represent a stock.
    Contains information about price, change, market state, and category.
    """
    __gtype_name__ = 'Stock'

    def __init__(
        self,
        symbol: str = '',
        long_name: str = '',
        price: float = 0.0,
        change: float = 0.0,
        change_pct: float = 0.0,
        market_state: str = '',
        currency: str = '',
        currency_symbol: str = '',
        # NEW FIELDS FOR CATEGORIZATION
        quote_type: str = '',
        sector: str = '',
        industry: str = ''
    ):
        """
        Initializes a Stock.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'PETR4.SA')
            long_name: Company full name
            price: Current price
            change: Absolute change
            change_pct: Percentage change (0.05 = 5%)
            market_state: Market state ('REGULAR', 'CLOSED', etc)
            currency: Currency code (e.g., 'USD', 'BRL')
            currency_symbol: Currency symbol (e.g., '$', 'R$')
            quote_type: Type (EQUITY, CRYPTOCURRENCY, ETF, etc)
            sector: Sector (Technology, Healthcare, etc)
            industry: Specific industry
        """
        super().__init__()
        self._symbol = symbol
        self._long_name = long_name
        self._price = price
        self._change = change
        self._change_pct = change_pct
        self._market_state = market_state
        self._currency = currency
        self._currency_symbol = currency_symbol
        self._quote_type = quote_type
        self._sector = sector
        self._industry = industry

    # ============== Existing Properties ==============

    @GObject.Property(type=str)
    def symbol(self) -> str:
        """Ticker symbol."""
        return self._symbol

    @symbol.setter
    def symbol(self, value: str):
        self._symbol = value

    @GObject.Property(type=str)
    def long_name(self) -> str:
        """Company full name."""
        return self._long_name

    @long_name.setter
    def long_name(self, value: str):
        self._long_name = value

    @GObject.Property(type=float)
    def price(self) -> float:
        """Current price."""
        return self._price

    @price.setter
    def price(self, value: float):
        self._price = value

    @GObject.Property(type=float)
    def change(self) -> float:
        """Absolute price change."""
        return self._change

    @change.setter
    def change(self, value: float):
        self._change = value

    @GObject.Property(type=float)
    def change_pct(self) -> float:
        """Percentage change (0.05 = 5%)."""
        return self._change_pct

    @change_pct.setter
    def change_pct(self, value: float):
        self._change_pct = value

    @GObject.Property(type=str)
    def market_state(self) -> str:
        """Market state."""
        return self._market_state

    @market_state.setter
    def market_state(self, value: str):
        self._market_state = value

    @GObject.Property(type=str)
    def currency(self) -> str:
        """Currency code."""
        return self._currency

    @currency.setter
    def currency(self, value: str):
        self._currency = value

    @GObject.Property(type=str)
    def currency_symbol(self) -> str:
        """Currency symbol."""
        return self._currency_symbol

    @currency_symbol.setter
    def currency_symbol(self, value: str):
        self._currency_symbol = value

    # ============== NEW Properties for Categorization ==============

    @GObject.Property(type=str)
    def quote_type(self) -> str:
        """Quote type (EQUITY, CRYPTOCURRENCY, ETF, etc)."""
        return self._quote_type

    @quote_type.setter
    def quote_type(self, value: str):
        self._quote_type = value

    @GObject.Property(type=str)
    def sector(self) -> str:
        """Company sector."""
        return self._sector

    @sector.setter
    def sector(self, value: str):
        self._sector = value

    @GObject.Property(type=str)
    def industry(self) -> str:
        """Specific industry."""
        return self._industry

    @industry.setter
    def industry(self, value: str):
        self._industry = value

    # ============== Conversion Methods ==============

    def to_dict(self):
        """
        Converts the Stock to a dictionary.

        Returns:
            Dictionary with all stock data
        """
        return {
            'symbol': self.symbol,
            'long_name': self.long_name,
            'price': self.price,
            'change': self.change,
            'change_pct': self.change_pct,
            'market_state': self.market_state,
            'currency': self.currency,
            'currency_symbol': self.currency_symbol,
            'quote_type': self.quote_type,
            'sector': self.sector,
            'industry': self.industry,
        }

    @classmethod
    def from_dict(cls, data):
        """
        Creates a Stock from a dictionary.

        Args:
            data: Dictionary with stock data

        Returns:
            Stock instance
        """
        return cls(
            symbol=data.get('symbol', ''),
            long_name=data.get('long_name', ''),
            price=data.get('price', 0.0),
            change=data.get('change', 0.0),
            change_pct=data.get('change_pct', 0.0),
            market_state=data.get('market_state', ''),
            currency=data.get('currency', ''),
            currency_symbol=data.get('currency_symbol', ''),
            quote_type=data.get('quote_type', ''),
            sector=data.get('sector', ''),
            industry=data.get('industry', ''),
        )

    # ============== Helper Methods ==============

    def is_gaining(self) -> bool:
        """
        Checks if the stock is gaining.

        Returns:
            True if change is positive
        """
        return self.change > 0

    def is_losing(self) -> bool:
        """
        Checks if the stock is losing.

        Returns:
            True if change is negative
        """
        return self.change < 0

    def is_market_open(self) -> bool:
        """
        Checks if the market is open.

        Returns:
            True if market is in regular hours
        """
        return self.market_state == "REGULAR"

    def is_cryptocurrency(self) -> bool:
        """
        Verifica se é uma criptomoeda.

        Returns:
            True se quote_type é CRYPTOCURRENCY
        """
        return self.quote_type == "CRYPTOCURRENCY"

    def get_formatted_change_pct(self) -> str:
        """
        Retorna a variação percentual formatada.

        Returns:
            String no formato '+5.23%' ou '-2.45%'
        """
        pct = self.change_pct * 100
        sign = '+' if pct >= 0 else ''
        return f"{sign}{pct:.2f}%"

    def __str__(self) -> str:
        """Representação em string do Stock."""
        return f"{self.symbol} ({self.long_name}): {self.price} {self.currency}"

    def __repr__(self) -> str:
        """Representação técnica do Stock."""
        return (
            f"Stock(symbol='{self.symbol}', "
            f"long_name='{self.long_name}', "
            f"price={self.price}, "
            f"change={self.change}, "
            f"sector='{self.sector}')"
        )