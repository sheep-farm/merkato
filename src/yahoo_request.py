# yahoo_request.py
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
import sys
from gi.repository import GObject, Gio
from yahooquery import Ticker
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from .stock import Stock

class YahooRequest (GObject.Object):
    __gtype_name__ = 'YahooRequest'

    def __init__(self, batch_size=1, max_workers=15):
        """
        Initialize YahooRequest with concurrency support.

        Args:
            batch_size: Number of symbols per request (default: 1)
            max_workers: Maximum number of parallel threads (default: 10)
        """
        super().__init__()
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.lock = Lock()

    def _fetch_batch(self, symbols_batch):
        """
        Busca um lote de símbolos.

        Args:
            symbols_batch: Lista de símbolos a serem buscados

        Returns:
            Tupla (results_dict, errors_list)
        """
        batch_results = {}
        batch_errors = []

        try:
            ticker = Ticker(symbols_batch)

            for symbol in symbols_batch:
                if isinstance(ticker.price, dict) and symbol in ticker.price:
                    data = ticker.price[symbol]

                    stock_item = Stock(symbol)

                    if 'longName' in data:
                        stock_item.long_name = data['longName']
                    if 'regularMarketPrice' in data:
                        stock_item.price = data['regularMarketPrice']
                    if 'regularMarketChange' in data:
                        stock_item.change = data['regularMarketChange']
                    if 'regularMarketChangePercent' in data:
                        stock_item.change_pct = data['regularMarketChangePercent']
                    if 'currency' in data:
                        stock_item.currency = data['currency']
                    if 'currencySymbol' in data:
                        stock_item.currency_symbol = data['currencySymbol']
                    if 'marketState' in data:
                        stock_item.market_state = data['marketState']

                    batch_results[symbol] = stock_item
                else:
                    batch_errors.append(symbol)

        except Exception as e:
            # Em caso de erro na requisição, marca todos os símbolos como erro
            batch_errors.extend(symbols_batch)
            print(f"Erro ao buscar batch {symbols_batch}: {e}", file=sys.stderr)

        return (batch_results, batch_errors)

    def _split_into_batches(self, symbols):
        """
        Divide a lista de símbolos em lotes.

        Args:
            symbols: Lista de símbolos

        Returns:
            Lista de lotes (cada lote é uma lista de símbolos)
        """
        batches = []
        for i in range(0, len(symbols), self.batch_size):
            batches.append(symbols[i:i + self.batch_size])
        return batches

    def fetch(self, symbols):
        """
        Busca informações de múltiplos símbolos de forma concorrente.

        Args:
            symbols: Lista de símbolos a serem buscados

        Returns:
            Tupla (results_dict, errors_list)
        """
        if not symbols:
            return {}, ['EMPTY ERROR']

        # Divide símbolos em lotes
        batches = self._split_into_batches(symbols)

        results = {}
        errors = []

        # Processa lotes em paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submete todas as tarefas
            future_to_batch = {
                executor.submit(self._fetch_batch, batch): batch
                for batch in batches
            }

            # Coleta resultados conforme completam
            for future in as_completed(future_to_batch):
                batch_results, batch_errors = future.result()

                # Merge dos resultados (thread-safe)
                with self.lock:
                    results.update(batch_results)
                    errors.extend(batch_errors)


        return (results, errors)

    def set_batch_size(self, size):
        """
        Configura o tamanho do lote.

        Args:
            size: Número de símbolos por requisição
        """
        self.batch_size = max(1, size)

    def set_max_workers(self, workers):
        """
        Configura o número máximo de threads.

        Args:
            workers: Número máximo de threads paralelas
        """
        self.max_workers = max(1, workers)
