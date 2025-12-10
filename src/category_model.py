# category_model.py
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
from typing import List, Dict

class CategoryModel(GObject.Object):
    """
    Modelo para gerenciar categorização de stocks por setor/tipo.
    """
    __gtype_name__ = 'CategoryModel'

    # Categorias sem ícones
    CATEGORIES = {
        "All": {
            "filter": None,
            "label": _("All Stocks")
        },
        "Cryptocurrency": {
            "filter": {"quoteType": "CRYPTOCURRENCY"},
            "label": _("Cryptocurrency")
        },
        "Technology": {
            "filter": {"sector": "Technology"},
            "label": _("Technology")
        },
        "Healthcare": {
            "filter": {"sector": "Healthcare"},
            "label": _("Healthcare")
        },
        "Energy": {
            "filter": {"sector": "Energy"},
            "label": _("Energy")
        },
        "Financial": {
            "filter": {"sector": "Financial Services"},
            "label": _("Financial Services")
        },
        "Consumer Cyclical": {
            "filter": {"sector": "Consumer Cyclical"},
            "label": _("Consumer Cyclical")
        },
        "Consumer Defensive": {
            "filter": {"sector": "Consumer Defensive"},
            "label": _("Consumer Defensive")
        },
        "Industrial": {
            "filter": {"sector": "Industrials"},
            "label": _("Industrial")
        },
        "Real Estate": {
            "filter": {"sector": "Real Estate"},
            "label": _("Real Estate")
        },
        "Basic Materials": {
            "filter": {"sector": "Basic Materials"},
            "label": _("Basic Materials")
        },
        "Communication": {
            "filter": {"sector": "Communication Services"},
            "label": _("Communication Services")
        },
        "Utilities": {
            "filter": {"sector": "Utilities"},
            "label": _("Utilities")
        },
        "Others": {
            "filter": "special",
            "label": _("Others")
        },
    }

    __gsignals__ = {
        'category-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'counts-updated': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self._stocks = {}  # {symbol: stock_data}
        self._current_category = "All"

    # ============== Propriedades ==============

    @property
    def current_category(self) -> str:
        """Retorna a categoria atual selecionada."""
        return self._current_category

    def set_current_category(self, category: str):
        """Define a categoria atual."""
        if category in self.CATEGORIES:
            self._current_category = category
            self.emit('category-changed', category)

    # ============== Gerenciamento de Stocks ==============

    def add_stock(self, stock):
        """Adiciona um stock ao modelo."""
        self._stocks[stock.symbol] = {
            'symbol': stock.symbol,
            'long_name': stock.long_name,
            'quoteType': getattr(stock, 'quote_type', 'UNKNOWN'),
            'sector': getattr(stock, 'sector', 'Unknown'),
            'industry': getattr(stock, 'industry', 'Unknown'),
            'stock_obj': stock
        }
        self.emit('counts-updated')

    def update_stock(self, stock):
        """Atualiza um stock existente."""
        if stock.symbol in self._stocks:
            self._stocks[stock.symbol].update({
                'long_name': stock.long_name,
                'quoteType': getattr(stock, 'quote_type', 'UNKNOWN'),
                'sector': getattr(stock, 'sector', 'Unknown'),
                'industry': getattr(stock, 'industry', 'Unknown'),
                'stock_obj': stock
            })
            self.emit('counts-updated')

    def remove_stock(self, symbol: str):
        """Remove um stock do modelo."""
        if symbol in self._stocks:
            del self._stocks[symbol]
            self.emit('counts-updated')

    def clear_all(self):
        """Remove todos os stocks."""
        self._stocks.clear()
        self.emit('counts-updated')

    def load_stocks(self, stocks: List):
        """Carrega múltiplos stocks de uma vez."""
        for stock in stocks:
            self.add_stock(stock)

    # ============== Filtragem ==============

    def get_stocks_by_category(self, category: str) -> List:
        """Retorna lista de stocks filtrados por categoria."""
        if category == "All":
            return [data['stock_obj'] for data in self._stocks.values()]

        if category == "Others":
            return self._get_uncategorized_stocks()

        filter_criteria = self.CATEGORIES.get(category, {}).get('filter')
        if not filter_criteria:
            return []

        filtered = []
        for data in self._stocks.values():
            match = True
            for key, value in filter_criteria.items():
                if data.get(key) != value:
                    match = False
                    break
            if match:
                filtered.append(data['stock_obj'])

        return filtered

    def _get_uncategorized_stocks(self) -> List:
        """Retorna stocks que não se encaixam em nenhuma categoria."""
        uncategorized = []

        for data in self._stocks.values():
            belongs = False
            for cat_key, info in self.CATEGORIES.items():
                if cat_key in ["All", "Others"]:
                    continue

                filt = info.get('filter')
                if not filt:
                    continue

                match = True
                for key, val in filt.items():
                    if data.get(key) != val:
                        match = False
                        break

                if match:
                    belongs = True
                    break

            if not belongs:
                uncategorized.append(data['stock_obj'])

        return uncategorized

    def get_category_count(self, category: str) -> int:
        """Retorna quantidade de stocks em uma categoria."""
        return len(self.get_stocks_by_category(category))

    def get_all_category_counts(self) -> Dict[str, int]:
        """Retorna contagem de todas as categorias."""
        return {cat: self.get_category_count(cat) for cat in self.CATEGORIES.keys()}

    def get_stock_category(self, symbol: str) -> str:
        """Retorna a categoria principal de um stock."""
        if symbol not in self._stocks:
            return "Unknown"

        data = self._stocks[symbol]

        if data.get('quoteType') == 'CRYPTOCURRENCY':
            return "Cryptocurrency"

        sector = data.get('sector', 'Unknown')
        for category, info in self.CATEGORIES.items():
            filt = info.get('filter')
            if filt and filt.get('sector') == sector:
                return category

        return "Unknown"

    def has_stocks(self) -> bool:
        """Verifica se há stocks no modelo."""
        return len(self._stocks) > 0

    def get_stock_count(self) -> int:
        """Retorna número total de stocks."""
        return len(self._stocks)

