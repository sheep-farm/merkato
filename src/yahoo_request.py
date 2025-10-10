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
            max_workers: Maximum number of parallel threads (default: 15)
        """
        super().__init__()
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.lock = Lock()

    def _is_valid_response(self, data):
        """
        Validate if the response contains valid stock data.

        Args:
            data: Response data from yahooquery

        Returns:
            bool: True if valid, False otherwise
        """
        # Check if data is an error response
        if isinstance(data, str):
            return False

        # Check if data is a dict with error message
        if isinstance(data, dict):
            # Yahoo returns error messages in specific keys
            if 'error' in data or 'Error Message' in str(data):
                return False

            # Check for "No data found" type responses
            if data.get('regularMarketPrice') is None:
                return False

            # Check if symbol exists (has a proper name or price)
            if 'longName' not in data and 'shortName' not in data:
                return False

        return True

    def _fetch_batch(self, symbols_batch):
        """
        Fetch a batch of symbols.

        Args:
            symbols_batch: List of symbols to fetch

        Returns:
            Tuple (results_dict, errors_list)
        """
        batch_results = {}
        batch_errors = []

        try:
            ticker = Ticker(symbols_batch)

            for symbol in symbols_batch:
                if isinstance(ticker.price, dict) and symbol in ticker.price:
                    data = ticker.price[symbol]

                    # Validate if response is valid
                    if not self._is_valid_response(data):
                        batch_errors.append(symbol)
                        continue

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
            # On request error, mark all symbols as errors
            batch_errors.extend(symbols_batch)
            print(f"Error fetching batch {symbols_batch}: {e}", file=sys.stderr)

        return (batch_results, batch_errors)

    def _split_into_batches(self, symbols):
        """
        Split symbol list into batches.

        Args:
            symbols: List of symbols

        Returns:
            List of batches (each batch is a list of symbols)
        """
        batches = []
        for i in range(0, len(symbols), self.batch_size):
            batches.append(symbols[i:i + self.batch_size])
        return batches

    def fetch(self, symbols):
        """
        Fetch information for multiple symbols concurrently.

        Args:
            symbols: List of symbols to fetch

        Returns:
            Tuple (results_dict, errors_list)
        """
        if not symbols:
            return {}, ['EMPTY ERROR']

        # Split symbols into batches
        batches = self._split_into_batches(symbols)

        results = {}
        errors = []

        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_batch = {
                executor.submit(self._fetch_batch, batch): batch
                for batch in batches
            }

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_results, batch_errors = future.result()

                # Merge results (thread-safe)
                with self.lock:
                    results.update(batch_results)
                    errors.extend(batch_errors)

        return (results, errors)

    def set_batch_size(self, size):
        """
        Configure batch size.

        Args:
            size: Number of symbols per request
        """
        self.batch_size = max(1, size)

    def set_max_workers(self, workers):
        """
        Configure maximum number of threads.

        Args:
            workers: Maximum number of parallel threads
        """
        self.max_workers = max(1, workers)
