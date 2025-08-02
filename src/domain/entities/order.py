# domain/entities/order.py.new - ENHANCED для реальной торговли
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

class Order:
    """
    🚀 РАСШИРЕННАЯ сущность "Ордер" для реальной торговли на бирже
    Добавлены критически важные поля для работы с биржевым API
    """

    # Статусы ордера
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CANCELED = "CANCELED"
    STATUS_FAILED = "FAILED"
    STATUS_PENDING = "PENDING"
    STATUS_FILLED = "FILLED"          # 🆕 Полностью исполнен
    STATUS_PARTIALLY_FILLED = "PARTIALLY_FILLED"  # 🆕 Частично исполнен
    STATUS_NOT_FOUND_ON_EXCHANGE = "NOT_FOUND_ON_EXCHANGE" # 🆕 Ордер не найден на бирже

    # Стороны ордера
    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"

    # Типы ордера
    TYPE_LIMIT = "LIMIT"
    TYPE_MARKET = "MARKET"
    TYPE_STOP_LOSS = "STOP_LOSS"      # 🆕 Стоп-лосс
    TYPE_TAKE_PROFIT = "TAKE_PROFIT"  # 🆕 Тейк-профит

    def __init__(
        self,
        order_id: int,
        side: str,
        order_type: str,
        price: float = 0.0,
        amount: float = 0.0,
        status: str = STATUS_PENDING,
        created_at: int = None,
        closed_at: int = None,
        deal_id: int = None,
        # 🆕 КРИТИЧЕСКИЕ ПОЛЯ ДЛЯ БИРЖИ:
        exchange_id: Optional[str] = None,      # ID ордера на бирже
        symbol: Optional[str] = None,           # Торговая пара (BTCUSDT)
        filled_amount: float = 0.0,             # Исполненный объем
        remaining_amount: float = 0.0,          # Оставшийся объем
        average_price: float = 0.0,             # Средняя цена исполнения
        fees: float = 0.0,                      # Комиссии
        fee_currency: str = "USDT",             # Валюта комиссии
        # 🆕 ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ:
        time_in_force: str = "GTC",             # Good Till Cancelled
        client_order_id: Optional[str] = None,  # Клиентский ID
        exchange_timestamp: Optional[int] = None, # Время на бирже
        last_update: Optional[int] = None,      # Последнее обновление
        error_message: Optional[str] = None,    # Сообщение об ошибке
        retries: int = 0,                       # Количество попыток
        # 🆕 МЕТАДАННЫЕ:
        metadata: Optional[Dict[str, Any]] = None,
        # --- Поля из ccxt unified API для полноты ---
        last_trade_timestamp: Optional[int] = None,
        cost: float = 0.0,
        trades: Optional[List[Dict[str, Any]]] = None,
        stop_price: Optional[float] = None,
        post_only: bool = False,
        exchange_raw_data: Optional[Dict[str, Any]] = None # Полный ответ от биржи
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

        # 🆕 Биржевые поля
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.filled_amount = filled_amount
        self.remaining_amount = remaining_amount or amount
        self.average_price = average_price
        self.fees = fees
        self.fee_currency = fee_currency

        # 🆕 Дополнительные поля
        self.time_in_force = time_in_force
        self.client_order_id = client_order_id
        self.exchange_timestamp = exchange_timestamp
        self.last_update = last_update or self.created_at
        self.error_message = error_message
        self.retries = retries
        
        # --- Новые поля из ccxt ---
        self.last_trade_timestamp = last_trade_timestamp
        self.cost = cost
        self.trades = trades or []
        self.stop_price = stop_price
        self.post_only = post_only
        
        self.metadata = metadata or {}
        self.exchange_raw_data = exchange_raw_data

    # 🆕 РАСШИРЕННЫЕ МЕТОДЫ ПРОВЕРКИ СТАТУСА
    def is_open(self) -> bool:
        """Ордер открыт и ожидает исполнения"""
        return self.status == self.STATUS_OPEN

    def is_closed(self) -> bool:
        """Ордер закрыт (исполнен или отменен)"""
        return self.status in [self.STATUS_CLOSED, self.STATUS_FILLED, self.STATUS_CANCELED, self.STATUS_NOT_FOUND_ON_EXCHANGE]

    def is_filled(self) -> bool:
        """Ордер полностью исполнен"""
        return self.status == self.STATUS_FILLED

    def is_partially_filled(self) -> bool:
        """Ордер частично исполнен"""
        return self.status == self.STATUS_PARTIALLY_FILLED

    def is_pending(self) -> bool:
        """Ордер ожидает размещения на бирже"""
        return self.status == self.STATUS_PENDING

    def is_failed(self) -> bool:
        """Ордер не смог быть размещен"""
        return self.status == self.STATUS_FAILED

    # 🆕 МЕТОДЫ РАБОТЫ С ИСПОЛНЕНИЕМ
    def get_fill_percentage(self) -> float:
        """Возвращает процент исполнения ордера (0.0 - 1.0)"""
        if self.amount == 0:
            return 0.0
        # Приводим оба значения к float для корректного деления
        filled = float(self.filled_amount)
        total = float(self.amount)
        return min(filled / total, 1.0)

    def get_remaining_amount(self) -> float:
        """Возвращает оставшийся объем для исполнения"""
        # Приводим оба значения к float для корректного вычитания
        total = float(self.amount)
        filled = float(self.filled_amount)
        return max(total - filled, 0.0)

    def is_fully_filled(self) -> bool:
        """Проверяет, полностью ли исполнен ордер"""
        # Приводим оба значения к float для корректного сравнения
        filled = float(self.filled_amount)
        total = float(self.amount)
        return filled >= total

    # 🆕 МЕТОДЫ ОБНОВЛЕНИЯ СТАТУСА
    def update_from_order(self, other_order: 'Order') -> None:
        """Обновляет ордер данными из другого Order объекта"""
        self.exchange_id = other_order.exchange_id
        self.status = other_order.status
        self.filled_amount = other_order.filled_amount
        self.remaining_amount = other_order.remaining_amount
        self.average_price = other_order.average_price
        self.fees = other_order.fees
        self.fee_currency = other_order.fee_currency
        self.cost = other_order.cost
        self.last_trade_timestamp = other_order.last_trade_timestamp
        self.trades = other_order.trades
        self.closed_at = other_order.closed_at
        self.last_update = other_order.last_update
        self.exchange_timestamp = other_order.exchange_timestamp
        self.exchange_raw_data = other_order.exchange_raw_data

    def update_from_exchange(self, exchange_data: Dict[str, Any]) -> None:
        """Обновляет ордер данными с биржи, безопасно обрабатывая None."""
        self.exchange_id = exchange_data.get('id', self.exchange_id)
        self.exchange_raw_data = exchange_data # Сохраняем полный ответ от биржи

        # Безопасное обновление числовых полей
        filled = exchange_data.get('filled')
        if filled is not None:
            self.filled_amount = float(filled)

        remaining = exchange_data.get('remaining')
        if remaining is not None:
            self.remaining_amount = float(remaining)

        average = exchange_data.get('average')
        if average is not None:
            self.average_price = float(average)

        if 'fee' in exchange_data and exchange_data['fee'] is not None:
            fee_cost = exchange_data['fee'].get('cost')
            if fee_cost is not None:
                self.fees = float(fee_cost)
        
        # Обновляем новые поля
        self.cost = exchange_data.get('cost', self.cost)
        self.last_trade_timestamp = exchange_data.get('lastTradeTimestamp', self.last_trade_timestamp)
        self.trades = exchange_data.get('trades', self.trades)

        # Обновляем статус на основе данных биржи
        exchange_status = exchange_data.get('status', '').lower()
        if exchange_status == 'closed':
            self.status = self.STATUS_FILLED
        elif exchange_status == 'canceled':
            self.status = self.STATUS_CANCELED
        elif exchange_status == 'open':
            if self.filled_amount > 0:
                self.status = self.STATUS_PARTIALLY_FILLED
            else:
                self.status = self.STATUS_OPEN

        self.last_update = int(time.time() * 1000)
        self.exchange_timestamp = exchange_data.get('timestamp', self.exchange_timestamp)

    def mark_as_placed(self, exchange_id: str, exchange_timestamp: int = None) -> None:
        """Помечает ордер как размещенный на бирже"""
        self.exchange_id = exchange_id
        self.status = self.STATUS_OPEN
        self.exchange_timestamp = exchange_timestamp or int(time.time() * 1000)
        self.last_update = int(time.time() * 1000)

    def mark_as_failed(self, error_message: str) -> None:
        """Помечает ордер как неудачный"""
        self.status = self.STATUS_FAILED
        self.error_message = error_message
        self.closed_at = int(time.time() * 1000)
        self.last_update = self.closed_at

    # 🆕 МЕТОДЫ ДЛЯ ЗАКРЫТИЯ
    def close(self, filled_amount: float = None, average_price: float = None):
        """Закрывает ордер как исполненный"""
        if filled_amount is not None:
            self.filled_amount = filled_amount
        if average_price is not None:
            self.average_price = average_price

        self.status = self.STATUS_FILLED if self.is_fully_filled() else self.STATUS_PARTIALLY_FILLED
        self.closed_at = int(time.time() * 1000)
        self.last_update = self.closed_at

    def cancel(self, reason: str = None):
        """Отменяет ордер"""
        self.status = self.STATUS_CANCELED
        self.closed_at = int(time.time() * 1000)
        self.last_update = self.closed_at
        if reason:
            self.error_message = f"Canceled: {reason}"

    # 🆕 МЕТОДЫ ДЛЯ РАСЧЕТОВ
    def calculate_total_cost(self) -> float:
        """Рассчитывает общую стоимость ордера (без комиссий)"""
        price = self.average_price if self.average_price > 0 else self.price
        # Приводим оба значения к float для корректного умножения
        filled = float(self.filled_amount)
        price_float = float(price)
        return filled * price_float

    def calculate_total_cost_with_fees(self) -> float:
        """Рассчитывает общую стоимость с учетом комиссий"""
        return self.calculate_total_cost() + self.fees

    # 🆕 МЕТОДЫ ДЛЯ ВАЛИДАЦИИ
    def validate_for_exchange(self) -> tuple[bool, str]:
        """Валидирует ордер перед отправкой на биржу"""
        if not self.symbol:
            return False, "Symbol is required"
        if self.amount <= 0:
            return False, "Amount must be positive"
        if self.side not in [self.SIDE_BUY, self.SIDE_SELL]:
            return False, "Invalid side"
        if self.order_type == self.TYPE_LIMIT and self.price <= 0:
            return False, "Price must be positive for limit orders"
        return True, "Valid"

    # 🆕 СЕРИАЛИЗАЦИЯ
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует ордер в словарь для сохранения"""
        return {
            'order_id': self.order_id,
            'side': self.side,
            'order_type': self.order_type,
            'price': self.price,
            'amount': self.amount,
            'status': self.status,
            'created_at': self.created_at,
            'closed_at': self.closed_at,
            'deal_id': self.deal_id,
            'exchange_id': self.exchange_id,
            'symbol': self.symbol,
            'filled_amount': self.filled_amount,
            'remaining_amount': self.remaining_amount,
            'average_price': self.average_price,
            'fees': self.fees,
            'fee_currency': self.fee_currency,
            'time_in_force': self.time_in_force,
            'client_order_id': self.client_order_id,
            'exchange_timestamp': self.exchange_timestamp,
            'last_update': self.last_update,
            'error_message': self.error_message,
            'retries': self.retries,
            'metadata': self.metadata,
            'cost': self.cost,
            'last_trade_timestamp': self.last_trade_timestamp,
            'trades': self.trades,
            'stop_price': self.stop_price,
            'post_only': self.post_only,
            'exchange_raw_data': self.exchange_raw_data
        }

    @staticmethod
    def _extract_fees_value(data: Dict[str, Any]) -> float:
        """Безопасно извлекает значение fees из данных биржи"""
        # Сначала проверяем прямое поле 'fees'
        fees_value = data.get('fees')
        if fees_value is not None:
            # Если fees является списком, берем первый элемент или сумму
            if isinstance(fees_value, list):
                if len(fees_value) > 0:
                    # Если элементы списка - словари с 'cost', извлекаем cost
                    if isinstance(fees_value[0], dict) and 'cost' in fees_value[0]:
                        return float(fees_value[0]['cost']) if fees_value[0]['cost'] is not None else 0.0
                    # Если элементы списка - числа, берем первый
                    elif isinstance(fees_value[0], (int, float)):
                        return float(fees_value[0])
                return 0.0
            # Если fees - число, возвращаем его
            elif isinstance(fees_value, (int, float)):
                return float(fees_value)
            # Если fees - словарь с 'cost'
            elif isinstance(fees_value, dict) and 'cost' in fees_value:
                return float(fees_value['cost']) if fees_value['cost'] is not None else 0.0
        
        # Если прямого поля 'fees' нет, проверяем поле 'fee'
        fee_data = data.get('fee', {})
        if isinstance(fee_data, dict) and 'cost' in fee_data:
            cost = fee_data.get('cost')
            return float(cost) if cost is not None else 0.0
        
        # По умолчанию возвращаем 0.0
        return 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """
        Создает ордер из словаря, адаптируя ключи от ccxt.
        """
        # Явная адаптация ключевых полей ccxt к полям нашего конструктора
        adapted_data = {
            'order_id': data.get('order_id') or data.get('id'),
            'exchange_id': data.get('exchange_id') or data.get('id'),
            'order_type': data.get('order_type') or data.get('type'),
            'side': data.get('side'),
            'symbol': data.get('symbol'),
            'status': data.get('status'),
            'price': data.get('price'),
            'amount': data.get('amount'),
            'cost': data.get('cost'),
            'average_price': data.get('average_price') or data.get('average'),
            'filled_amount': data.get('filled_amount') or data.get('filled'),
            'remaining_amount': data.get('remaining_amount') or data.get('remaining'),
            'created_at': data.get('created_at'),
            'closed_at': data.get('closed_at'),
            'exchange_timestamp': data.get('exchange_timestamp') or data.get('timestamp'),
            'last_trade_timestamp': data.get('last_trade_timestamp') or data.get('lastTradeTimestamp'),
            'deal_id': data.get('deal_id'),
            'fees': cls._extract_fees_value(data),
            'fee_currency': data.get('fee_currency') if data.get('fee_currency') is not None else data.get('fee', {}).get('currency'),
            'trades': data.get('trades'),
            'exchange_raw_data': data.get('exchange_raw_data') or data.get('info'),
            'client_order_id': data.get('client_order_id') or data.get('clientOrderId'),
            'time_in_force': data.get('time_in_force') or data.get('timeInForce'),
            'stop_price': data.get('stop_price') or data.get('stopPrice'),
            'post_only': data.get('post_only') or data.get('postOnly', False),
            'retries': data.get('retries', 0),
            'metadata': data.get('metadata'),
            'error_message': data.get('error_message'),
        }

        # Убираем None значения, чтобы не перезаписывать значения по умолчанию в __init__
        final_data = {k: v for k, v in adapted_data.items() if v is not None}

        # Убедимся, что обязательные поля присутствуют
        if 'order_id' not in final_data:
            raise ValueError("'order_id' or 'id' is required to create an Order from dict")
        if 'side' not in final_data:
            raise ValueError("'side' is required to create an Order from dict")
        if 'order_type' not in final_data:
            raise ValueError("'order_type' or 'type' is required to create an Order from dict")

        return cls(**final_data)

    def __repr__(self):
        fill_pct = self.get_fill_percentage() * 100
        return (f"<Order(id={self.order_id}, exchange_id={self.exchange_id}, "
                f"deal_id={self.deal_id}, side={self.side}, type={self.order_type}, "
                f"status={self.status}, price={self.price}, amount={self.amount}, "
                f"filled={self.filled_amount} ({fill_pct:.1f}%), fees={self.fees})>")

    def __str__(self):
        """Человеко-читаемое представление"""
        return (f"{self.side} {self.amount} {self.symbol} at {self.price} "
                f"[{self.status}] filled: {self.filled_amount}")


# 🆕 ДОПОЛНИТЕЛЬНЫЕ КЛАССЫ ДЛЯ РАБОТЫ С ОРДЕРАМИ

@dataclass
class OrderValidationResult:
    """Результат валидации ордера"""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass
class OrderExecutionResult:
    """Результат исполнения ордера"""
    success: bool
    order: Optional[Order] = None
    error_message: Optional[str] = None
    exchange_response: Optional[Dict[str, Any]] = None

@dataclass
class ExchangeInfo:
    """Информация о торговой паре с биржи"""
    symbol: str
    min_qty: float
    max_qty: float
    step_size: float
    min_price: float
    max_price: float
    tick_size: float
    min_notional: float
    fees: Dict[str, float]  # maker/taker fees
    precision: Dict[str, float] # ❗️ ДОБАВЛЕНО: полная информация о точности
