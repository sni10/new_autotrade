# tests/mocks/mock_exchange_connector.py
import asyncio
from typing import Dict, List, Any, Tuple
from domain.entities.order import ExchangeInfo, Order

class MockCcxtExchangeConnector:
    """
    Мок-объект для CcxtExchangeConnector, позволяющий симулировать
    поведение биржи в тестах без реальных API вызовов.
    """

    def __init__(self, market_info: Dict[str, Any]):
        self._orders: Dict[str, Dict] = {}
        self._balances: Dict[str, float] = {"USDT": 10000.0, "BTC": 10.0, "ETH": 100.0, "THE": 5000.0}
        self._next_order_id = 1000
        self.market_info = market_info

    async def create_order(self, symbol: str, side: str, order_type: str, amount: float, price: float = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        order_id = str(self._next_order_id)
        self._next_order_id += 1
        
        order_data = {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "amount": amount,
            "price": price,
            "status": "open",
            "filled": 0.0,
            "remaining": amount,
            "average": None,
            "fee": None,
            "timestamp": asyncio.get_event_loop().time()
        }
        self._orders[order_id] = order_data
        return order_data

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        if order_id in self._orders:
            self._orders[order_id]["status"] = "canceled"
            return self._orders[order_id]
        raise ValueError(f"Order {order_id} not found")

    async def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        if order_id in self._orders:
            return self._orders[order_id]
        raise ValueError(f"Order {order_id} not found")

    async def fetch_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        return [o for o in self._orders.values() if o["status"] == "open"]

    async def get_symbol_info(self, symbol: str) -> ExchangeInfo:
        info = self.market_info[symbol].copy() # Копируем, чтобы не изменять оригинал
        info.pop('last_price', None) # Удаляем лишний ключ перед созданием объекта
        return ExchangeInfo(**info)

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        # Возвращаем мок-тикер. Цена может быть изменена в тестах.
        return {"last": self.market_info[symbol].get("last_price", 50000.0)}

    async def check_sufficient_balance(self, symbol: str, side: str, amount: float, price: float = None) -> Tuple[bool, str, float]:
        base, quote = symbol.split('/')
        if side == "buy":
            required = amount * price
            available = self._balances.get(quote, 0)
            return available >= required, quote, available
        else: # sell
            available = self._balances.get(base, 0)
            return available >= amount, base, available

    # --- Вспомогательные методы для тестов ---

    def fill_order(self, order_id: str, fill_price: float = None):
        """Имитирует полное исполнение ордера."""
        if order_id in self._orders:
            order = self._orders[order_id]
            order["status"] = "closed" # ccxt использует 'closed' для исполненных
            order["filled"] = order["amount"]
            order["remaining"] = 0
            order["average"] = fill_price or order["price"]
            # Имитация комиссии
            order["fee"] = {"cost": (order["filled"] * order["average"]) * 0.001, "currency": "USDT"}
        else:
            raise ValueError(f"Order {order_id} not found for filling")

    def set_balance(self, currency: str, amount: float):
        self._balances[currency] = amount

    def set_market_price(self, symbol: str, price: float):
        self.market_info[symbol]["last_price"] = price
