import gi
import sys
from gi.repository import GObject, Gio
from yahooquery import Ticker

from .stock import Stock

class YahooRequest (GObject.Object):
    __gtype_name__ = 'YahooRequest'

    def __init__(self):
        super().__init__()


    def fetch (self, symbols):

        if not symbols:
            return {}, ['EMPTY ERROR']

        ticker = Ticker(symbols)

        results = {}
        errors = []

        for symbol in symbols:
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

                results[symbol] = stock_item
            else:
                errors.append(symbol)

        return (results, errors)

