# my_trading_app/domain/entities/deal.py
import time
from .order import Order

class Deal:
    """
    Базовая сущность "Сделка".
    Содержит ссылки на buy_order и sell_order, статусы и т.д.
    """

    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CANCELED = "CANCELED"

    def __init__(
        self,
        deal_id: int,
        currency_pair_id: str,
        status: str = STATUS_OPEN,
        buy_order: Order = None,
        sell_order: Order = None,
        created_at: int = None,
        closed_at: int = None,
    ):
        self.deal_id = deal_id
        self.currency_pair_id = currency_pair_id
        self.status = status
        self.buy_order = buy_order
        self.sell_order = sell_order
        self.created_at = created_at or int(time.time() * 1000)
        self.closed_at = closed_at

        # Если buy_order или sell_order есть — установим им deal_id
        self._sync_order_deal_id()

    def _sync_order_deal_id(self):
        """Вспомогательный метод, чтобы прописать deal_id в ордера."""
        if self.buy_order:
            self.buy_order.deal_id = self.deal_id
        if self.sell_order:
            self.sell_order.deal_id = self.deal_id

    def attach_orders(self, buy_order: Order, sell_order: Order):
        """
        Если нужно задним числом «подвесить» ордера к сделке.
        """
        self.buy_order = buy_order
        self.sell_order = sell_order
        self._sync_order_deal_id()

    def open(self):
        """Простейший метод: пометить сделку как открытую."""
        self.status = self.STATUS_OPEN

    def close(self):
        """Простейший метод: пометить сделку как закрытую."""
        self.status = self.STATUS_CLOSED
        self.closed_at = int(time.time() * 1000)

    def cancel(self):
        """Простейший метод: пометить сделку как отменённую."""
        self.status = self.STATUS_CANCELED
        self.closed_at = int(time.time() * 1000)

    def is_open(self) -> bool:
        return self.status == self.STATUS_OPEN

    def is_closed(self) -> bool:
        return self.status == self.STATUS_CLOSED

    def __repr__(self):
        return f"<Deal(id={self.deal_id}, status={self.status}, pair={self.currency_pair_id})>"
