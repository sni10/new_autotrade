# my_trading_app/domain/entities/order.py
import time

class Order:
    """
    Базовая сущность "Ордер" (покупка/продажа).
    """

    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CANCELED = "CANCELED"

    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"

    TYPE_LIMIT = "LIMIT"
    TYPE_MARKET = "MARKET"

    def __init__(
        self,
        order_id: int,
        side: str,
        order_type: str,
        price: float = 0.0,
        amount: float = 0.0,
        status: str = STATUS_OPEN,
        created_at: int = None,
        closed_at: int = None,
        deal_id: int = None,           # <-- Связь с Deal
    ):
        self.order_id = order_id
        self.side = side
        self.order_type = order_type
        self.price = price
        self.amount = amount
        self.status = status
        self.created_at = created_at or int(time.time() * 1000)
        self.closed_at = closed_at
        self.deal_id = deal_id

    def is_open(self) -> bool:
        return self.status == self.STATUS_OPEN

    def is_closed(self) -> bool:
        return self.status == self.STATUS_CLOSED

    def close(self):
        """Простейший метод закрытия."""
        self.status = self.STATUS_CLOSED
        self.closed_at = int(time.time() * 1000)

    def cancel(self):
        """Простейший метод отмены."""
        self.status = self.STATUS_CANCELED
        self.closed_at = int(time.time() * 1000)

    def __repr__(self):
        return (f"<Order(id={self.order_id}, deal_id={self.deal_id}, side={self.side}, "
                f"type={self.order_type}, status={self.status}, price={self.price}, amount={self.amount})>")
