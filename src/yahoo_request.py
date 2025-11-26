# yahoo_request.py (MODIFIED to include sector/industry)
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
    Class responsible for making requests to the Yahoo Finance API.
    Supports parallel requests with batch control.
    MODIFIED to also fetch categorization data (sector/industry/quoteType).
    """
    __gtype_name__ = 'YahooRequest'

    # Constantes
    DEFAULT_BATCH_SIZE = 1
    DEFAULT_MAX_WORKERS = 15
    MIN_BATCH_SIZE = 1
    MIN_MAX_WORKERS = 1

    def __init__(self, batch_size=DEFAULT_BATCH_SIZE, max_workers=DEFAULT_MAX_WORKERS):
        """
        Initializes YahooRequest with concurrency support.

        Args:
            batch_size: Number of symbols per request (default: 1)
            max_workers: Maximum number of parallel threads (default: 15)
        """
        super().__init__()
        self.batch_size = max(self.MIN_BATCH_SIZE, batch_size)
        self.max_workers = max(self.MIN_MAX_WORKERS, max_workers)
        self.lock = Lock()

    # ============== Validação ==============

    def _is_valid_response(self, data):
        """
        Validates if the response contains valid stock data.

        Args:
            data: Response data from yahooquery

        Returns:
            True if valid, False otherwise
        """
        # Check if it's an error response (string)
        if isinstance(data, str):
            return False

        # Check if it's a dictionary with an error message
        if isinstance(data, dict):
            # Yahoo returns error messages in specific keys
            if 'error' in data or 'Error Message' in str(data):
                return False

            # Check for "No data found" type responses
            if data.get('regularMarketPrice') is None:
                return False

            # Check if the symbol exists (has name or price)
            if 'longName' not in data and 'shortName' not in data:
                return False

        return True

    # ============== Requisições ==============

    def fetch(self, symbols):
        """
        Fetches information for multiple symbols concurrently.

        Args:
            symbols: List of symbols to fetch

        Returns:
            Tuple (results dictionary, errors list)
        """
        if not symbols:
            return ({}, ['EMPTY_LIST'])

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

    def _fetch_batch(self, symbols_batch):
        """
        Fetches a batch of symbols.

        Args:
            symbols_batch: List of symbols in the batch

        Returns:
            Tuple (results dictionary, errors list)
        """
        batch_results = {}
        batch_errors = []

        try:
            custom_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

            ticker = Ticker(symbols_batch, asynchronous=False)

            # Fetch price (basic data)
            price_data = ticker.price
            # Fetch asset_profile (sector/industry) - may return error for some symbols
            try:
                profile_data = ticker.asset_profile
            except:
                profile_data = {}

            # Fetch quote_type (asset type)
            try:
                quote_type_data = ticker.quote_type
            except:
                quote_type_data = {}

            for symbol in symbols_batch:
                # Validate price data
                if not isinstance(price_data, dict) or symbol not in price_data:
                    batch_errors.append(symbol)
                    continue

                data = price_data[symbol]

                if not self._is_valid_response(data):
                    batch_errors.append(symbol)
                    continue

                # Fetch additional profile data (sector/industry)
                profile = {}
                if isinstance(profile_data, dict) and symbol in profile_data:
                    if isinstance(profile_data[symbol], dict):
                        profile = profile_data[symbol]

                # Fetch quote type
                qtype = {}
                if isinstance(quote_type_data, dict) and symbol in quote_type_data:
                    if isinstance(quote_type_data[symbol], dict):
                        qtype = quote_type_data[symbol]

                # Create Stock object with complete data
                stock_item = self._create_stock_from_data(symbol, data, profile, qtype)
                batch_results[symbol] = stock_item

        except Exception as e:
            # In case of request error, mark all symbols as errors
            batch_errors.extend(symbols_batch)
            print(f"Error fetching batch {symbols_batch}: {e}", file=sys.stderr)

        return (batch_results, batch_errors)

    def _create_stock_from_data(self, symbol, price_data, profile_data, quote_type_data):
        """
        Creates a Stock object from API data.

        Args:
            symbol: Stock symbol
            price_data: Price data from API
            profile_data: Profile data (sector/industry)
            quote_type_data: Quote type data

        Returns:
            Populated Stock object
        """
        stock_item = Stock(symbol)

        # Map basic price fields
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
            if api_field in price_data:
                setattr(stock_item, stock_field, price_data[api_field])

        # Add categorization data from asset_profile
        if profile_data:
            if 'sector' in profile_data:
                stock_item.sector = profile_data['sector']
            if 'industry' in profile_data:
                stock_item.industry = profile_data['industry']

        # Add quote_type
        if quote_type_data and 'quoteType' in quote_type_data:
            stock_item.quote_type = quote_type_data['quoteType']

        return stock_item

    # ============== Batch Management ==============

    def _split_into_batches(self, symbols):
        """
        Splits symbol list into batches.

        Args:
            symbols: List of symbols

        Returns:
            List of batches (each batch is a list of symbols)
        """
        batches = []
        for i in range(0, len(symbols), self.batch_size):
            batches.append(symbols[i:i + self.batch_size])
        return batches

    # ============== Configuração ==============

    def set_batch_size(self, size):
        """
        Configures batch size.

        Args:
            size: Number of symbols per request
        """
        self.batch_size = max(self.MIN_BATCH_SIZE, size)

    def set_max_workers(self, workers):
        """
        Configures maximum number of threads.

        Args:
            workers: Maximum number of parallel threads
        """
        self.max_workers = max(self.MIN_MAX_WORKERS, workers)

    # ============== Helper Methods ==============

    def get_batch_size(self):
        """Returns the current batch size."""
        return self.batch_size

    def get_max_workers(self):
        """Returns the maximum number of workers."""
        return self.max_workers
