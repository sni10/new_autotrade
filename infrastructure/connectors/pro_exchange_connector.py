# infrastructure/connectors/market_data_connector.py
import json

import ccxt.pro as ccxtpro


class CcxtProMarketDataConnector:
    """
    Обёртка над ccxt.pro для подписки на WebSocket потоки.
    """

    def __init__(self, exchange_name="binance", use_sandbox=False):
        self.exchange_name = exchange_name
        self.use_sandbox = use_sandbox
        self.config = None
        self._load_config()
        self.client = self._init_exchange_client()

    def _load_config(self):
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        self.config = config[self.exchange_name]['sandbox' if self.use_sandbox else 'production']

    def _init_exchange_client(self):
        exchange_class = getattr(ccxtpro, self.exchange_name)
        client = exchange_class({
            # 'apiKey': self.config.get('apiKey'),
            # 'secret': self.config.get('secret'),
            'enableRateLimit': True,
            'newUpdates': True,
        })
        if self.use_sandbox:
            if hasattr(client, 'set_sandbox_mode'):
                client.set_sandbox_mode(True)
            else:
                print(f"Sandbox mode not supported for {self.exchange_name}")

        return client

    async def subscribe(self, symbol: str):
        """
        Можно отдельно подписаться на конкретные каналы (trades, ticker).
        Или же просто ничего не делать: ccxt.pro сам подписывается на watch_*.
        """
        pass

    async def get_next_trades_update(self, symbol: str, limit: int = 100):
        """
        Возвращаем следующее обновление, например trades или order_book.
        Можно сделать разные методы (get_next_trades, get_next_ticker).
        """
        # Пример: только trades
        trades = await self.client.watch_trades(symbol)
        return trades  # Это массив последних сделок


    async def get_next_order_book_update(self, symbol: str, limit: int = 1):
        """
        Возвращаем следующее обновление, например trades или order_book.
        Можно сделать разные методы (get_next_trades, get_next_ticker).
        """
        # Пример: только orders
        orders = await self.client.watch_order_book(symbol, limit=limit)
        return orders  # Это массив последних сделок
