# infrastructure/connectors/exchange_connector.py
import json

import ccxt
import asyncio

class CcxtExchangeConnector:
    """
    Простейшая обёртка над ccxt (REST) для торговли.
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
        exchange_class = getattr(ccxt, self.exchange_name)
        client = exchange_class({
            'apiKey': self.config.get('apiKey'),
            'secret': self.config.get('secret'),
            'enableRateLimit': True,
        })

        if self.use_sandbox:
            if hasattr(client, 'set_sandbox_mode'):
                client.set_sandbox_mode(True)
            else:
                print(f"Sandbox mode not supported for {self.exchange_name}")

        return client

    async def create_order(self, symbol, side, order_type, amount, price=None):
        """
        Оформление ордера (buy/sell) через REST.
        """
        # ccxt - обычно синхронный, но можно обернуть в asyncio.to_thread
        def place():
            if order_type == 'limit':
                return self.client.create_order(symbol, 'limit', side, amount, price)
            else:
                return self.client.create_order(symbol, 'market', side, amount)

        return await asyncio.to_thread(place)

    async def cancel_order(self, order_id, symbol):
        def cancel():
            return self.client.cancel_order(order_id, symbol)

        return await asyncio.to_thread(cancel)

    # Доп. методы: fetch_balance, fetch_orders и т.д.
