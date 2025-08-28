# src/domain/entities/deal.py
import time
from .order import Order
from .currency_pair import CurrencyPair

class Deal:
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CANCELED = "CANCELED"

    def __init__(self, deal_id: int = None, currency_pair: CurrencyPair = None, status: str = STATUS_OPEN, buy_order: Order = None, sell_order: Order = None, created_at: int = None, closed_at: int = None, profit: float = 0.0):
        self.deal_id = deal_id
        self.currency_pair = currency_pair
        self.symbol = currency_pair.symbol if currency_pair else None
        self.status = status
        self.buy_order = buy_order
        self.sell_order = sell_order
        self.created_at = created_at or int(time.time() * 1000)
        self.updated_at = self.created_at
        self.closed_at = closed_at
        self.profit = profit
        self._sync_order_deal_id()

    def _sync_order_deal_id(self):
        if self.buy_order: self.buy_order.deal_id = self.deal_id
        if self.sell_order: self.sell_order.deal_id = self.deal_id

    def attach_orders(self, buy_order: Order, sell_order: Order):
        self.buy_order = buy_order
        self.sell_order = sell_order
        self._sync_order_deal_id()

    def close(self):
        self.status = self.STATUS_CLOSED
        self.closed_at = int(time.time() * 1000)
        self.updated_at = self.closed_at

    def is_open(self) -> bool: return self.status == self.STATUS_OPEN
    def is_closed(self) -> bool: return self.status == self.STATUS_CLOSED
    def __repr__(self): return f"<Deal(id={self.deal_id}, status={self.status}, pair={self.symbol})>"
    
    def to_dict(self) -> dict:
        return {
            "deal_id": self.deal_id,
            "symbol": self.symbol,
            "status": self.status,
            "buy_order_id": self.buy_order.order_id if self.buy_order else None,
            "sell_order_id": self.sell_order.order_id if self.sell_order else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
            "profit": self.profit
        }
    
    def update_profit(self, profit: float):
        """Обновить прибыль сделки"""
        self.profit = profit
        self.updated_at = int(time.time() * 1000)
    
    def calculate_profit(self) -> float:
        """Рассчитать прибыль на основе ордеров"""
        if not (self.buy_order and self.sell_order and 
                self.buy_order.is_filled() and self.sell_order.is_filled()):
            return 0.0
        
        buy_cost = self.buy_order.calculate_total_cost_with_fees()
        sell_revenue = self.sell_order.calculate_total_cost()
        calculated_profit = sell_revenue - buy_cost
        
        # Обновляем сохраненную прибыль
        self.update_profit(calculated_profit)
        return calculated_profit
    
    @classmethod
    def from_dict(cls, data: dict, currency_pair: CurrencyPair, orders_map: dict = None):
        deal = cls(
            deal_id=data["deal_id"],
            currency_pair=currency_pair,
            status=data["status"],
            created_at=data["created_at"],
            closed_at=data.get("closed_at"),
            profit=data.get("profit", 0.0)
        )
        
        # Устанавливаем updated_at если есть в данных
        if "updated_at" in data:
            deal.updated_at = data["updated_at"]
        
        if orders_map:
            if data.get("buy_order_id"):
                deal.buy_order = orders_map.get(data["buy_order_id"])
            if data.get("sell_order_id"):
                deal.sell_order = orders_map.get(data["sell_order_id"])
        
        return deal