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

import sys
from gi.repository import GObject
from yahooquery import Ticker
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from .stock import Stock


class YahooRequest(GObject.Object):
    """
    Classe responsável por fazer requisições à API do Yahoo Finance.
    Suporta requisições paralelas com controle de batch.
    """
    __gtype_name__ = 'YahooRequest'

    # Constantes
    DEFAULT_BATCH_SIZE = 1
    DEFAULT_MAX_WORKERS = 15
    MIN_BATCH_SIZE = 1
    MIN_MAX_WORKERS = 1

    def __init__(self, batch_size=DEFAULT_BATCH_SIZE, max_workers=DEFAULT_MAX_WORKERS):
        """
        Inicializa YahooRequest com suporte a concorrência.

        Args:
            batch_size: Número de símbolos por requisição (padrão: 1)
            max_workers: Número máximo de threads paralelas (padrão: 15)
        """
        super().__init__()
        self.batch_size = max(self.MIN_BATCH_SIZE, batch_size)
        self.max_workers = max(self.MIN_MAX_WORKERS, max_workers)
        self.lock = Lock()

    # ============== Validação ==============

    def _is_valid_response(self, data):
        """
        Valida se a resposta contém dados válidos de stock.

        Args:
            data: Dados de resposta do yahooquery

        Returns:
            True se válido, False caso contrário
        """
        # Verifica se é uma resposta de erro (string)
        if isinstance(data, str):
            return False

        # Verifica se é um dicionário com mensagem de erro
        if isinstance(data, dict):
            # Yahoo retorna mensagens de erro em chaves específicas
            if 'error' in data or 'Error Message' in str(data):
                return False

            # Verifica por respostas tipo "No data found"
            if data.get('regularMarketPrice') is None:
                return False

            # Verifica se o símbolo existe (tem nome ou preço)
            if 'longName' not in data and 'shortName' not in data:
                return False

        return True

    # ============== Requisições ==============

    def fetch(self, symbols):
        """
        Busca informações de múltiplos símbolos concorrentemente.

        Args:
            symbols: Lista de símbolos a buscar

        Returns:
            Tupla (dicionário de resultados, lista de erros)
        """
        if not symbols:
            return ({}, ['EMPTY_LIST'])

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

                # Merge de resultados (thread-safe)
                with self.lock:
                    results.update(batch_results)
                    errors.extend(batch_errors)

        return (results, errors)

    def _fetch_batch(self, symbols_batch):
        """
        Busca um lote de símbolos.

        Args:
            symbols_batch: Lista de símbolos do lote

        Returns:
            Tupla (dicionário de resultados, lista de erros)
        """
        batch_results = {}
        batch_errors = []

        try:
            ticker = Ticker(symbols_batch)

            for symbol in symbols_batch:
                if isinstance(ticker.price, dict) and symbol in ticker.price:
                    data = ticker.price[symbol]

                    # Valida se a resposta é válida
                    if not self._is_valid_response(data):
                        batch_errors.append(symbol)
                        continue

                    # Cria objeto Stock com os dados
                    stock_item = self._create_stock_from_data(symbol, data)
                    batch_results[symbol] = stock_item
                else:
                    batch_errors.append(symbol)

        except Exception as e:
            # Em caso de erro na requisição, marca todos os símbolos como erro
            batch_errors.extend(symbols_batch)
            print(f"Error fetching batch {symbols_batch}: {e}", file=sys.stderr)

        return (batch_results, batch_errors)

    def _create_stock_from_data(self, symbol, data):
        """
        Cria um objeto Stock a partir dos dados da API.

        Args:
            symbol: Símbolo do stock
            data: Dados retornados pela API

        Returns:
            Objeto Stock preenchido
        """
        stock_item = Stock(symbol)

        # Mapeia os campos da API para o objeto Stock
        field_mappings = {
            'longName': 'long_name',
            'regularMarketPrice': 'price',
            'regularMarketChange': 'change',
            'regularMarketChangePercent': 'change_pct',
            'currency': 'currency',
            'currencySymbol': 'currency_symbol',
            'marketState': 'market_state'
        }

        for api_field, stock_field in field_mappings.items():
            if api_field in data:
                setattr(stock_item, stock_field, data[api_field])

        return stock_item

    # ============== Gerenciamento de lotes ==============

    def _split_into_batches(self, symbols):
        """
        Divide lista de símbolos em lotes.

        Args:
            symbols: Lista de símbolos

        Returns:
            Lista de lotes (cada lote é uma lista de símbolos)
        """
        batches = []
        for i in range(0, len(symbols), self.batch_size):
            batches.append(symbols[i:i + self.batch_size])
        return batches

    # ============== Configuração ==============

    def set_batch_size(self, size):
        """
        Configura tamanho do lote.

        Args:
            size: Número de símbolos por requisição
        """
        self.batch_size = max(self.MIN_BATCH_SIZE, size)

    def set_max_workers(self, workers):
        """
        Configura número máximo de threads.

        Args:
            workers: Número máximo de threads paralelas
        """
        self.max_workers = max(self.MIN_MAX_WORKERS, workers)

    # ============== Métodos auxiliares ==============

    def get_batch_size(self):
        """Retorna o tamanho atual do lote."""
        return self.batch_size

    def get_max_workers(self):
        """Retorna o número máximo de workers."""
        return self.max_workers
