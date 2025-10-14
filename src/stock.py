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

from gi.repository import GObject


class Stock(GObject.Object):
    """
    Modelo de dados para representar um stock/ação.
    Contém informações de preço, variação e estado do mercado.
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
        currency_symbol: str = ''
    ):
        """
        Inicializa um Stock.

        Args:
            symbol: Símbolo do ticker (ex: 'AAPL', 'PETR4.SA')
            long_name: Nome completo da empresa
            price: Preço atual
            change: Variação absoluta
            change_pct: Variação percentual (0.05 = 5%)
            market_state: Estado do mercado ('REGULAR', 'CLOSED', etc)
            currency: Código da moeda (ex: 'USD', 'BRL')
            currency_symbol: Símbolo da moeda (ex: '$', 'R$')
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

    # ============== Propriedades ==============

    @GObject.Property(type=str)
    def symbol(self) -> str:
        """Símbolo do ticker."""
        return self._symbol

    @symbol.setter
    def symbol(self, value: str):
        self._symbol = value

    @GObject.Property(type=str)
    def long_name(self) -> str:
        """Nome completo da empresa."""
        return self._long_name

    @long_name.setter
    def long_name(self, value: str):
        self._long_name = value

    @GObject.Property(type=float)
    def price(self) -> float:
        """Preço atual."""
        return self._price

    @price.setter
    def price(self, value: float):
        self._price = value

    @GObject.Property(type=float)
    def change(self) -> float:
        """Variação absoluta do preço."""
        return self._change

    @change.setter
    def change(self, value: float):
        self._change = value

    @GObject.Property(type=float)
    def change_pct(self) -> float:
        """Variação percentual (0.05 = 5%)."""
        return self._change_pct

    @change_pct.setter
    def change_pct(self, value: float):
        self._change_pct = value

    @GObject.Property(type=str)
    def market_state(self) -> str:
        """Estado do mercado."""
        return self._market_state

    @market_state.setter
    def market_state(self, value: str):
        self._market_state = value

    @GObject.Property(type=str)
    def currency(self) -> str:
        """Código da moeda."""
        return self._currency

    @currency.setter
    def currency(self, value: str):
        self._currency = value

    @GObject.Property(type=str)
    def currency_symbol(self) -> str:
        """Símbolo da moeda."""
        return self._currency_symbol

    @currency_symbol.setter
    def currency_symbol(self, value: str):
        self._currency_symbol = value

    # ============== Métodos de conversão ==============

    def to_dict(self):
        """
        Converte o Stock para dicionário.

        Returns:
            Dicionário com todos os dados do stock
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
        }

    @classmethod
    def from_dict(cls, data):
        """
        Cria um Stock a partir de um dicionário.

        Args:
            data: Dicionário com dados do stock

        Returns:
            Instância de Stock
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
        )

    # ============== Métodos auxiliares ==============

    def is_gaining(self) -> bool:
        """
        Verifica se o stock está em alta.

        Returns:
            True se a variação é positiva
        """
        return self.change > 0

    def is_losing(self) -> bool:
        """
        Verifica se o stock está em queda.

        Returns:
            True se a variação é negativa
        """
        return self.change < 0

    def is_market_open(self) -> bool:
        """
        Verifica se o mercado está aberto.

        Returns:
            True se o mercado está em horário regular
        """
        return self.market_state == "REGULAR"

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
            f"change_pct={self.change_pct})"
        )
