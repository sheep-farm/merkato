# watchlist_manager.py
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

import json
import os

from gi.repository import GLib
from datetime import datetime


class WatchlistManager:

    def __init__(self, app_name='merkato'):
        config_dir = os.path.join(GLib.get_user_config_dir(), app_name)
        os.makedirs(config_dir, exist_ok=True)

        self.watchlist_file = os.path.join(config_dir, 'watchlist.json')
        print(f"Watchlist file: {self.watchlist_file}")


    def load(self):
        if not os.path.exists(self.watchlist_file):
            print("No saved watchlist found")
            return []

        try:
            with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            stocks_data = data.get('stocks', [])
            last_updated = data.get('last_updated', 'unknown')

            print(f"Loaded {len(stocks_data)} tickers from watchlist (last updated: {last_updated})")
            return stocks_data

        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in watchlist file: {e}")
            return []
        except Exception as e:
            print(f"ERROR: Failed to load watchlist: {e}")
            return []


    def save(self, stocks):
        if not isinstance(stocks, list):
            print("ERROR: stocks must be a list")
            return False

        try:
            # Converter StockItems para dicionários se necessário
            stocks_data = []
            for stock in stocks:
                if hasattr(stock, 'to_dict'):
                    stocks_data.append(stock.to_dict())
                elif isinstance(stock, dict):
                    stocks_data.append(stock)
                else:
                    print(f"WARNING: Unknown stock type: {type(stock)}")
                    continue

            data = {
                'stocks': stocks_data,
                'last_updated': datetime.now().isoformat(),
                'version': '0.2.0'
            }

            # Salvar com indentação para ser legível
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Saved {len(stocks_data)} tickers to watchlist")
            return True

        except Exception as e:
            print(f"ERROR: Failed to save watchlist: {e}")
            return False

    def save_sort_order(self, sort_order: str) -> bool:
        try:
            config_dir = GLib.get_user_config_dir()
            app_dir = os.path.join(config_dir, 'merkato')
            os.makedirs(app_dir, exist_ok=True)

            sort_file = os.path.join(app_dir, 'sort_order.txt')
            with open(sort_file, 'w') as f:
                f.write(sort_order)
            return True
        except Exception as e:
            print(f"Error saving sort order: {e}")
            return False

    def load_sort_order(self) -> str:
        try:
            config_dir = GLib.get_user_config_dir()
            sort_file = os.path.join(config_dir, 'merkato', 'sort_order.txt')

            if os.path.exists(sort_file):
                with open(sort_file, 'r') as f:
                    return f.read().strip()
            return 'alphabetical'
        except Exception as e:
            print(f"Error loading sort order: {e}")
            return 'alphabetical'

    def clear(self):
        return self.save([])


    def exists(self):
        return os.path.exists(self.watchlist_file)


    def get_count(self):
        return len(self.load())


    def get_file_path(self):
        return self.watchlist_file
