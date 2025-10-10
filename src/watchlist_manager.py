import json
import os
from gi.repository import GLib
from datetime import datetime


class WatchlistManager:
    """Gerencia a persistência da watchlist de tickers"""

    def __init__(self, app_name='merkato'):
        """
        Inicializa o gerenciador de watchlist

        Args:
            app_name: Nome da aplicação (usado para criar diretório de config)
        """
        config_dir = os.path.join(GLib.get_user_config_dir(), app_name)
        os.makedirs(config_dir, exist_ok=True)

        self.watchlist_file = os.path.join(config_dir, 'watchlist.json')
        print(f"Watchlist file: {self.watchlist_file}")


    def load(self):
        """
        Carrega a watchlist salva do disco

        Returns:
            list: Lista de dicionários com dados dos tickers ou lista vazia se não houver arquivo
        """
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
        """
        Salva a watchlist atual no disco

        Args:
            stocks: Lista de objetos StockItem ou dicionários com dados dos tickers

        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
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
                'version': '2.0'
            }

            # Salvar com indentação para ser legível
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Saved {len(stocks_data)} tickers to watchlist")
            return True

        except Exception as e:
            print(f"ERROR: Failed to save watchlist: {e}")
            return False


    def clear(self):
        """
        Remove todos os tickers da watchlist

        Returns:
            bool: True se limpou com sucesso
        """
        return self.save([])


    def exists(self):
        """
        Verifica se existe um arquivo de watchlist salvo

        Returns:
            bool: True se o arquivo existe
        """
        return os.path.exists(self.watchlist_file)


    def get_count(self):
        """
        Retorna o número de tickers salvos

        Returns:
            int: Quantidade de tickers na watchlist
        """
        return len(self.load())


    def get_file_path(self):
        """
        Retorna o caminho completo do arquivo de watchlist

        Returns:
            str: Caminho absoluto do arquivo
        """
        return self.watchlist_file
