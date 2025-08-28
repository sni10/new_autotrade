# tests/mocks/mock_exchange_connector.py
import asyncio
import time
from typing import Dict, List, Any, Tuple
from domain.entities.order import ExchangeInfo, Order
from domain.entities.ticker import Ticker
import ccxt

class MockCcxtExchangeConnector:
    def __init__(self, market_info: Dict[str, Any]):
        self._orders: Dict[str, Order] = {}
        self._balances: Dict[str, float] = {"USDT": 10000.0, "THE": 5000.0}
        self._next_order_id = 1000
        self.market_info = market_info

    def _normalize_symbol(self, symbol: str) -> str:
        if not symbol or '/' in symbol: return symbol
        if symbol.endswith('USDT'): return f"{symbol[:-4]}/USDT"
        return symbol

    async def create_order(self, symbol: str, side: str, order_type: str, amount: float, price: float = None, params: Dict[str, Any] = None) -> Order:
        normalized_symbol = self._normalize_symbol(symbol)
        order_id = str(self._next_order_id)
        self._next_order_id += 1
        order = Order(order_id=int(order_id), exchange_id=order_id, symbol=normalized_symbol, side=side.upper(), order_type=order_type.upper(), amount=amount, price=price, status=Order.STATUS_OPEN)
        self._orders[order_id] = order
        return order

    async def cancel_order(self, order_id: str, symbol: str) -> Order:
        if order_id in self._orders:
            self._orders[order_id].status = Order.STATUS_CANCELED
            self._orders[order_id].closed_at = int(time.time() * 1000)
            return self._orders[order_id]
        raise ccxt.OrderNotFound(f"Order {order_id} not found")

    async def fetch_order(self, order_id: str, symbol: str) -> Order:
        if order_id in self._orders:
            return self._orders[order_id]
        raise ccxt.OrderNotFound(f"Order {order_id} not found")

    async def get_symbol_info(self, symbol: str) -> ExchangeInfo:
        normalized_symbol = self._normalize_symbol(symbol)
        info = self.market_info[normalized_symbol].copy()
        info.pop('last_price', None)
        return ExchangeInfo(**info)

    async def fetch_ticker(self, symbol: str) -> Ticker:
        normalized_symbol = self._normalize_symbol(symbol)
        price = self.market_info[normalized_symbol].get("last_price", 50000.0)
        return Ticker(data={"last": price, "symbol": normalized_symbol})

    async def check_sufficient_balance(self, symbol: str, side: str, amount: float, price: float = None) -> Tuple[bool, str, float]:
        normalized_symbol = self._normalize_symbol(symbol)
        base, quote = normalized_symbol.split('/')
        if side.lower() == "buy":
            required = amount * price
            available = self._balances.get(quote, 0)
            return available >= required, quote, available
        else:
            available = self._balances.get(base, 0)
            return available >= amount, base, available

    def set_market_price(self, symbol: str, price: float):
        normalized_symbol = self._normalize_symbol(symbol)
        if normalized_symbol in self.market_info:
            self.market_info[normalized_symbol]['last_price'] = price

    def fill_order(self, order_id: str, fill_price: float = None):
        if order_id in self._orders:
            order = self._orders[order_id]
            order.status = Order.STATUS_FILLED
            order.filled_amount = order.amount
            order.remaining_amount = 0.0
            order.average_price = fill_price if fill_price else order.price
            order.closed_at = int(time.time() * 1000)
            order.last_update = order.closed_at
