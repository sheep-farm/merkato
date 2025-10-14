# stock_controller.py
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

import threading
from datetime import datetime
from gi.repository import GObject, GLib
from typing import List, Callable, Optional

from .yahoo_request import YahooRequest
from .watchlist_manager import WatchlistManager
from .stock import Stock


class StockController(GObject.Object):
    """
    Controller que gerencia a lógica de negócio relacionada a stocks.
    Responsável por: busca, atualização, persistência e auto-atualização.
    """
    __gtype_name__ = 'StockController'

    __gsignals__ = {
        'search-started': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'search-completed': (GObject.SignalFlags.RUN_FIRST, None, (object, object)),
        'search-error': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'refresh-started': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'refresh-completed': (GObject.SignalFlags.RUN_FIRST, None, (object, object)),
        'refresh-error': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'stock-added': (GObject.SignalFlags.RUN_FIRST, None, (Stock,)),
        'stock-removed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'watchlist-loaded': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, update_interval: int = 60):
        super().__init__()
        self.update_interval = update_interval
        self.timeout_id = None
        self.is_paused = False
        self.is_searching = False
        self.is_refreshing = False

        self._symbols = []
        self._symbols_lock = threading.Lock()

        self.watchlist_manager = WatchlistManager()
        self.yahoo_request = YahooRequest()

    # ============== Propriedades ==============

    @property
    def symbols(self) -> List[str]:
        """Retorna cópia da lista de símbolos."""
        with self._symbols_lock:
            return self._symbols.copy()

    def has_symbol(self, symbol: str) -> bool:
        """Verifica se um símbolo já está na watchlist."""
        with self._symbols_lock:
            return symbol in self._symbols

    # ============== Busca de Stocks ==============

    def search_stocks(self, symbols_input: str):
        """
        Busca stocks por símbolos.

        Args:
            symbols_input: String com símbolos separados por vírgula
        """
        if self.is_searching:
            return

        symbols_input = symbols_input.strip().upper()
        symbols = [s.strip() for s in symbols_input.split(',') if s.strip()]

        # Filtra símbolos que já existem
        with self._symbols_lock:
            symbols = [s for s in symbols if s not in self._symbols]

        if not symbols:
            return

        self.is_searching = True
        self.emit('search-started')

        thread = threading.Thread(
            target=self._do_search,
            args=(symbols,),
            daemon=True
        )
        thread.start()

    def _do_search(self, symbols: List[str]):
        """Executa a busca em thread separada."""
        try:
            results, errors = self.yahoo_request.fetch(symbols)
            GLib.idle_add(self._on_search_completed, results, errors)
        except Exception as e:
            print(f"Search error: {e}")
            GLib.idle_add(self._on_search_error, str(e))
        finally:
            GLib.idle_add(self._clear_search_flag)

    def _on_search_completed(self, results: dict, errors: list):
        """Callback quando a busca é completada."""
        for symbol, stock in results.items():
            with self._symbols_lock:
                if stock.symbol not in self._symbols:
                    self._symbols.append(stock.symbol)
            self.emit('stock-added', stock)

        self.save_watchlist()
        self.emit('search-completed', results, errors)
        return False

    def _on_search_error(self, error_msg: str):
        """Callback quando ocorre erro na busca."""
        self.emit('search-error', error_msg)
        return False

    def _clear_search_flag(self):
        """Limpa flag de busca em andamento."""
        self.is_searching = False
        return False

    # ============== Atualização de Stocks ==============

    def refresh_stocks(self) -> bool:
        """
        Atualiza todos os stocks da watchlist.

        Returns:
            True para manter o timeout ativo
        """
        if self.is_refreshing:
            return True

        self.is_refreshing = True
        self.emit('refresh-started')

        symbols_copy = self.symbols

        thread = threading.Thread(
            target=self._do_refresh,
            args=(symbols_copy,),
            daemon=True
        )
        thread.start()

        return True

    def _do_refresh(self, symbols: List[str]):
        """Executa o refresh em thread separada."""
        try:
            results, errors = self.yahoo_request.fetch(symbols)
            GLib.idle_add(self._on_refresh_completed, results, errors)
        except Exception as e:
            print(f"Refresh error: {e}")
            GLib.idle_add(self._on_refresh_error, str(e))
        finally:
            GLib.idle_add(self._clear_refresh_flag)

    def _on_refresh_completed(self, results: dict, errors: list):
        """Callback quando o refresh é completado."""
        self.save_watchlist()
        self.emit('refresh-completed', results, errors)
        return False

    def _on_refresh_error(self, error_msg: str):
        """Callback quando ocorre erro no refresh."""
        self.emit('refresh-error', error_msg)
        return False

    def _clear_refresh_flag(self):
        """Limpa flag de refresh em andamento."""
        self.is_refreshing = False
        return False

    # ============== Gerenciamento de Watchlist ==============

    def remove_stock(self, symbol: str) -> bool:
        """
        Remove um stock da watchlist.

        Args:
            symbol: Símbolo do stock a remover

        Returns:
            True se removido com sucesso
        """
        with self._symbols_lock:
            if symbol in self._symbols:
                self._symbols.remove(symbol)
                self.save_watchlist()
                self.emit('stock-removed', symbol)
                return True
        return False

    def load_watchlist(self) -> tuple:
        """
        Carrega a watchlist salva.

        Returns:
            Tuple (stocks_data: list, sort_order: str)
        """
        stocks_data = self.watchlist_manager.load()

        if stocks_data:
            with self._symbols_lock:
                self._symbols = [stock['symbol'] for stock in stocks_data]

        sort_order = self.watchlist_manager.load_sort_order()

        self.emit('watchlist-loaded', stocks_data)

        return (stocks_data, sort_order)

    def save_watchlist(self, stocks: Optional[List[Stock]] = None) -> bool:
        """
        Salva a watchlist atual.

        Args:
            stocks: Lista de objetos Stock (opcional)

        Returns:
            True se salvo com sucesso
        """
        if stocks is None:
            return True

        return self.watchlist_manager.save(stocks)

    def save_sort_order(self, sort_order: str) -> bool:
        """
        Salva a ordem de classificação.

        Args:
            sort_order: Tipo de ordenação

        Returns:
            True se salvo com sucesso
        """
        return self.watchlist_manager.save_sort_order(sort_order)

    # ============== Auto-atualização ==============

    def start_auto_update(self):
        """Inicia a atualização automática."""
        if self.timeout_id is None:
            self.is_paused = False
            self.timeout_id = GLib.timeout_add_seconds(
                self.update_interval,
                self.refresh_stocks
            )

    def pause_auto_update(self):
        """Pausa a atualização automática."""
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
            self.is_paused = True

    def restart_auto_update(self):
        """Reinicia a atualização automática."""
        self.pause_auto_update()
        self.start_auto_update()

    def stop_auto_update(self):
        """Para a atualização automática."""
        self.pause_auto_update()
        self.is_paused = False

    # ============== Configuração ==============

    def set_update_interval(self, interval: int):
        """
        Define o intervalo de atualização automática.

        Args:
            interval: Intervalo em segundos
        """
        self.update_interval = max(10, interval)
        if self.timeout_id is not None:
            self.restart_auto_update()

    def configure_yahoo_request(self, batch_size: int = None, max_workers: int = None):
        """
        Configura parâmetros do YahooRequest.

        Args:
            batch_size: Tamanho do lote de requisições
            max_workers: Número máximo de threads
        """
        if batch_size is not None:
            self.yahoo_request.set_batch_size(batch_size)
        if max_workers is not None:
            self.yahoo_request.set_max_workers(max_workers)
