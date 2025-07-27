# domain/entities/order_ccxt_compliant.py - CCXT COMPLIANT VERSION
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

class Order:
    """
    🚀 CCXT COMPLIANT Order Entity - Полная совместимость с CCXT структурами
    
    Эта версия строго соответствует CCXT Unified API для Order Structure:
    https://docs.ccxt.com/en/latest/manual.html#order-structure
    
    Все поля именованы точно по CCXT стандарту, дополнительные поля проекта добавлены отдельно.
    """

    # CCXT Статусы ордера (точно по стандарту)
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CANCELED = "canceled"
    STATUS_EXPIRED = "expired"
    STATUS_REJECTED = "rejected"
    STATUS_FILLED = STATUS_CLOSED  # Backward compatibility
    
    # ДОПОЛНИТЕЛЬНЫЕ статусы для проекта
    STATUS_PENDING = "pending"                # Ордер создан локально, но не размещен на бирже
    STATUS_PARTIALLY_FILLED = "partial"      # Частично исполнен (для удобства)

    # CCXT Стороны ордера
    SIDE_BUY = "buy"
    SIDE_SELL = "sell"

    # CCXT Типы ордера
    TYPE_LIMIT = "limit"
    TYPE_MARKET = "market"
    TYPE_STOP = "stop"
    TYPE_STOP_LIMIT = "stop_limit"
    TYPE_TAKE_PROFIT = "take_profit"
    TYPE_TAKE_PROFIT_LIMIT = "take_profit_limit"

    # CCXT Time in Force
    TIF_GTC = "GTC"  # Good Till Canceled
    TIF_IOC = "IOC"  # Immediate Or Cancel
    TIF_FOK = "FOK"  # Fill Or Kill
    TIF_PO = "PO"    # Post Only

    def __init__(
        self,
        # CCXT ОБЯЗАТЕЛЬНЫЕ ПОЛЯ (точно по стандарту):
        id: Optional[str] = None,                    # exchange order ID (строка!)
        clientOrderId: Optional[str] = None,         # клиентский ID ордера
        datetime: Optional[str] = None,              # ISO8601 datetime строка
        timestamp: Optional[int] = None,             # Unix timestamp в миллисекундах
        lastTradeTimestamp: Optional[int] = None,    # время последней сделки
        status: str = STATUS_PENDING,                # статус ордера
        symbol: Optional[str] = None,                # торговая пара (BTC/USDT)
        type: str = TYPE_LIMIT,                      # тип ордера
        timeInForce: Optional[str] = TIF_GTC,        # время жизни ордера
        side: str = SIDE_BUY,                        # сторона ордера
        price: Optional[float] = None,               # цена за единицу
        amount: float = 0.0,                         # запрошенное количество
        filled: float = 0.0,                         # исполненное количество
        remaining: Optional[float] = None,           # оставшееся количество
        cost: Optional[float] = None,                # общая стоимость (filled * average)
        average: Optional[float] = None,             # средняя цена исполнения
        trades: Optional[List[Dict[str, Any]]] = None,  # массив сделок
        fee: Optional[Dict[str, Any]] = None,        # структура комиссии
        info: Optional[Dict[str, Any]] = None,       # полный ответ от биржи
        
        # ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ AUTOTRADE:
        deal_id: Optional[int] = None,               # связь со сделкой AutoTrade
        local_order_id: Optional[int] = None,        # внутренний ID для AutoTrade
        created_at: Optional[int] = None,            # время создания в AutoTrade
        last_update: Optional[int] = None,           # последнее обновление
        error_message: Optional[str] = None,         # сообщение об ошибке
        retries: int = 0,                           # количество попыток
        metadata: Optional[Dict[str, Any]] = None    # дополнительная информация проекта
    ):
        # CCXT СТАНДАРТНЫЕ ПОЛЯ
        self.id = id
        self.clientOrderId = clientOrderId
        self.datetime = datetime or self._generate_iso_datetime()
        self.timestamp = timestamp or int(time.time() * 1000)
        self.lastTradeTimestamp = lastTradeTimestamp
        self.status = status
        self.symbol = symbol
        self.type = type
        self.timeInForce = timeInForce
        self.side = side
        self.price = price
        self.amount = amount
        self.filled = filled
        self.remaining = remaining if remaining is not None else amount
        self.cost = cost
        self.average = average
        self.trades = trades or []
        self.fee = fee or {'cost': 0.0, 'currency': None, 'rate': None}
        self.info = info or {}
        
        # ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ AUTOTRADE
        self.deal_id = deal_id
        self.local_order_id = local_order_id
        self.created_at = created_at or self.timestamp
        self.last_update = last_update or self.timestamp
        self.error_message = error_message
        self.retries = retries
        self.metadata = metadata or {}

    def _generate_iso_datetime(self) -> str:
        """Генерирует ISO8601 datetime строку"""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # ===== CCXT COMPATIBILITY METHODS =====

    def update_from_ccxt_response(self, ccxt_response: Dict[str, Any]) -> None:
        """
        Обновляет Order из стандартного CCXT ответа.
        Это основной метод для синхронизации с биржей.
        """
        # Обновляем все CCXT поля
        self.id = ccxt_response.get('id', self.id)
        self.clientOrderId = ccxt_response.get('clientOrderId', self.clientOrderId)
        self.datetime = ccxt_response.get('datetime', self.datetime)
        self.timestamp = ccxt_response.get('timestamp', self.timestamp)
        self.lastTradeTimestamp = ccxt_response.get('lastTradeTimestamp', self.lastTradeTimestamp)
        self.status = ccxt_response.get('status', self.status)
        self.symbol = ccxt_response.get('symbol', self.symbol)
        self.type = ccxt_response.get('type', self.type)
        self.timeInForce = ccxt_response.get('timeInForce', self.timeInForce)
        self.side = ccxt_response.get('side', self.side)
        self.price = ccxt_response.get('price', self.price)
        self.amount = ccxt_response.get('amount', self.amount)
        self.filled = ccxt_response.get('filled', self.filled)
        if self.filled is None:
            self.filled = 0.0
        self.remaining = ccxt_response.get('remaining', self.remaining)
        if self.remaining is None:
            self.remaining = self.amount - self.filled
        self.cost = ccxt_response.get('cost', self.cost)
        self.average = ccxt_response.get('average', self.average)
        self.trades = ccxt_response.get('trades', self.trades)
        self.fee = ccxt_response.get('fee', self.fee)
        self.info = ccxt_response.get('info', self.info)
        
        # Обновляем служебные поля
        self.last_update = int(time.time() * 1000)

    def to_ccxt_dict(self) -> Dict[str, Any]:
        """
        Преобразует Order в CCXT совместимый словарь.
        Возвращает только CCXT поля в правильном формате.
        """
        return {
            'id': self.id,
            'clientOrderId': self.clientOrderId,
            'datetime': self.datetime,
            'timestamp': self.timestamp,
            'lastTradeTimestamp': self.lastTradeTimestamp,
            'status': self.status,
            'symbol': self.symbol,
            'type': self.type,
            'timeInForce': self.timeInForce,
            'side': self.side,
            'price': self.price,
            'amount': self.amount,
            'filled': self.filled,
            'remaining': self.remaining,
            'cost': self.cost,
            'average': self.average,
            'trades': self.trades,
            'fee': self.fee,
            'info': self.info
        }

    @classmethod
    def from_ccxt_response(
        cls, 
        ccxt_response: Dict[str, Any], 
        deal_id: Optional[int] = None,
        local_order_id: Optional[int] = None
    ) -> 'Order':
        """
        Создает Order из CCXT ответа.
        Это предпочтительный способ создания ордеров из биржевых данных.
        """
        order = cls(
            id=ccxt_response.get('id'),
            clientOrderId=ccxt_response.get('clientOrderId'),
            datetime=ccxt_response.get('datetime'),
            timestamp=ccxt_response.get('timestamp'),
            lastTradeTimestamp=ccxt_response.get('lastTradeTimestamp'),
            status=ccxt_response.get('status'),
            symbol=ccxt_response.get('symbol'),
            type=ccxt_response.get('type'),
            timeInForce=ccxt_response.get('timeInForce'),
            side=ccxt_response.get('side'),
            price=ccxt_response.get('price'),
            amount=ccxt_response.get('amount', 0.0),
            filled=ccxt_response.get('filled') or 0.0,
            remaining=ccxt_response.get('remaining') if ccxt_response.get('remaining') is not None else ccxt_response.get('amount', 0.0),
            cost=ccxt_response.get('cost'),
            average=ccxt_response.get('average'),
            trades=ccxt_response.get('trades', []),
            fee=ccxt_response.get('fee', {'cost': 0.0, 'currency': None, 'rate': None}),
            info=ccxt_response.get('info', {}),
            deal_id=deal_id,
            local_order_id=local_order_id
        )
        return order

    # ===== STATUS CHECK METHODS =====

    def is_open(self) -> bool:
        """Ордер открыт и ожидает исполнения"""
        return self.status == self.STATUS_OPEN

    def is_closed(self) -> bool:
        """Ордер закрыт (исполнен полностью)"""
        return self.status == self.STATUS_CLOSED

    def is_canceled(self) -> bool:
        """Ордер отменен"""
        return self.status == self.STATUS_CANCELED

    def is_expired(self) -> bool:
        """Ордер истек"""
        return self.status == self.STATUS_EXPIRED

    def is_rejected(self) -> bool:
        """Ордер отклонен биржей"""
        return self.status == self.STATUS_REJECTED

    def is_pending(self) -> bool:
        """Ордер ожидает размещения на бирже (локальный статус)"""
        return self.status == self.STATUS_PENDING

    def is_partially_filled(self) -> bool:
        """Ордер частично исполнен"""
        return self.filled > 0 and self.filled < self.amount

    def is_fully_filled(self) -> bool:
        """Ордер полностью исполнен"""
        return self.filled >= self.amount

    def is_final_status(self) -> bool:
        """Ордер в финальном статусе (не изменится)"""
        return self.status in [self.STATUS_CLOSED, self.STATUS_CANCELED, self.STATUS_EXPIRED, self.STATUS_REJECTED]

    # ===== CALCULATION METHODS =====

    def get_fill_percentage(self) -> float:
        """Возвращает процент исполнения ордера (0.0 - 1.0)"""
        if self.amount == 0:
            return 0.0
        return min(self.filled / self.amount, 1.0)

    def get_remaining_amount(self) -> float:
        """Возвращает оставшийся объем для исполнения"""
        return max(self.amount - self.filled, 0.0)

    def calculate_total_cost(self) -> float:
        """Рассчитывает общую стоимость ордера"""
        if self.cost is not None:
            return self.cost
        
        # Fallback calculation
        price = self.average if self.average else self.price
        if price:
            return self.filled * price
        return 0.0

    def calculate_total_cost_with_fees(self) -> float:
        """Рассчитывает общую стоимость с учетом комиссий"""
        total_cost = self.calculate_total_cost()
        fee_cost = self.fee.get('cost', 0.0) if self.fee else 0.0
        return total_cost + fee_cost

    def get_effective_price(self) -> Optional[float]:
        """Возвращает эффективную цену (average или price)"""
        return self.average if self.average else self.price

    # ===== VALIDATION METHODS =====

    def validate_ccxt_compliance(self) -> tuple[bool, List[str]]:
        """Валидирует Order на соответствие CCXT стандарту"""
        errors = []
        
        # Обязательные поля для размещения на бирже
        if not self.symbol:
            errors.append("symbol is required")
        if not self.side:
            errors.append("side is required")
        if not self.type:
            errors.append("type is required")
        if self.amount <= 0:
            errors.append("amount must be positive")
        if self.type == self.TYPE_LIMIT and (not self.price or self.price <= 0):
            errors.append("price is required for limit orders")
        
        # Валидация значений
        if self.side not in [self.SIDE_BUY, self.SIDE_SELL]:
            errors.append(f"invalid side: {self.side}")
        if self.type not in [self.TYPE_LIMIT, self.TYPE_MARKET, self.TYPE_STOP, self.TYPE_STOP_LIMIT]:
            errors.append(f"invalid type: {self.type}")
        
        return len(errors) == 0, errors

    def validate_for_exchange_placement(self) -> tuple[bool, str]:
        """Валидирует ордер перед размещением на бирже"""
        is_valid, errors = self.validate_ccxt_compliance()
        if not is_valid:
            return False, "; ".join(errors)
        return True, "Valid"

    # ===== UPDATE METHODS =====

    def mark_as_placed_on_exchange(self, exchange_id: str, exchange_timestamp: Optional[int] = None) -> None:
        """Помечает ордер как размещенный на бирже"""
        self.id = exchange_id
        self.status = self.STATUS_OPEN
        if exchange_timestamp:
            self.timestamp = exchange_timestamp
            self.datetime = datetime.fromtimestamp(exchange_timestamp / 1000, timezone.utc).isoformat().replace('+00:00', 'Z')
        self.last_update = int(time.time() * 1000)

    # Backward compatibility
    def mark_as_placed(self, exchange_id: str, exchange_timestamp: Optional[int] = None) -> None:
        self.mark_as_placed_on_exchange(exchange_id, exchange_timestamp)

    def mark_as_failed(self, error_message: str) -> None:
        """Помечает ордер как отклоненный"""
        self.status = self.STATUS_REJECTED
        self.error_message = error_message
        self.last_update = int(time.time() * 1000)

    # Backward compatibility
    def update_from_exchange(self, data: Dict[str, Any]) -> None:
        self.update_from_ccxt_response(data)

    def update_filled_amount(self, filled: float, average_price: Optional[float] = None) -> None:
        """Обновляет исполненное количество"""
        self.filled = filled
        self.remaining = max(self.amount - filled, 0.0)
        
        if average_price:
            self.average = average_price
            self.cost = filled * average_price
        
        # Обновляем статус
        if self.filled >= self.amount:
            self.status = self.STATUS_CLOSED
        elif self.filled > 0:
            self.status = self.STATUS_PARTIALLY_FILLED
        
        self.last_update = int(time.time() * 1000)

    def cancel_order(self, reason: Optional[str] = None) -> None:
        """Отменяет ордер"""
        self.status = self.STATUS_CANCELED
        if reason:
            self.error_message = f"Canceled: {reason}"
        self.last_update = int(time.time() * 1000)

    # ===== SERIALIZATION METHODS =====

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует ордер в словарь для сохранения (включает все поля)"""
        return {
            # CCXT поля
            'id': self.id,
            'clientOrderId': self.clientOrderId,
            'datetime': self.datetime,
            'timestamp': self.timestamp,
            'lastTradeTimestamp': self.lastTradeTimestamp,
            'status': self.status,
            'symbol': self.symbol,
            'type': self.type,
            'timeInForce': self.timeInForce,
            'side': self.side,
            'price': self.price,
            'amount': self.amount,
            'filled': self.filled,
            'remaining': self.remaining,
            'cost': self.cost,
            'average': self.average,
            'trades': self.trades,
            'fee': self.fee,
            'info': self.info,
            
            # AutoTrade поля
            'deal_id': self.deal_id,
            'local_order_id': self.local_order_id,
            'created_at': self.created_at,
            'last_update': self.last_update,
            'error_message': self.error_message,
            'retries': self.retries,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Создает ордер из словаря"""
        # Отделяем CCXT поля от AutoTrade полей
        ccxt_fields = [
            'id', 'clientOrderId', 'datetime', 'timestamp', 'lastTradeTimestamp',
            'status', 'symbol', 'type', 'timeInForce', 'side', 'price', 'amount',
            'filled', 'remaining', 'cost', 'average', 'trades', 'fee', 'info'
        ]
        
        ccxt_data = {k: v for k, v in data.items() if k in ccxt_fields}
        autotrade_data = {k: v for k, v in data.items() if k not in ccxt_fields}
        
        return cls(**ccxt_data, **autotrade_data)

    # ===== COMPATIBILITY METHODS (для обратной совместимости) =====

    @property
    def order_id(self) -> Optional[int]:
        """Backward compatibility: возвращает local_order_id"""
        return self.local_order_id

    @order_id.setter
    def order_id(self, value: int) -> None:
        """Backward compatibility: устанавливает local_order_id"""
        self.local_order_id = value

    @property
    def exchange_id(self) -> Optional[str]:
        """Backward compatibility: возвращает id (CCXT exchange ID)"""
        return self.id

    @exchange_id.setter
    def exchange_id(self, value: str) -> None:
        """Backward compatibility: устанавливает id (CCXT exchange ID)"""
        self.id = value

    @property
    def order_type(self) -> str:
        """Backward compatibility: возвращает type"""
        return self.type

    @order_type.setter
    def order_type(self, value: str) -> None:
        """Backward compatibility: устанавливает type"""
        self.type = value

    def is_filled(self) -> bool:
        """Backward compatibility: ордер полностью исполнен"""
        return self.is_fully_filled()

    # ===== STRING REPRESENTATIONS =====

    def __repr__(self):
        fill_pct = self.get_fill_percentage() * 100
        return (f"<Order(id={self.id}, local_id={self.local_order_id}, "
                f"deal_id={self.deal_id}, side={self.side}, type={self.type}, "
                f"status={self.status}, price={self.price}, amount={self.amount}, "
                f"filled={self.filled} ({fill_pct:.1f}%), cost={self.cost})>")

    def __str__(self):
        """Человеко-читаемое представление"""
        return (f"{self.side} {self.amount} {self.symbol} at {self.price} "
                f"[{self.status}] filled: {self.filled}")


# ===== ДОПОЛНИТЕЛЬНЫЕ КЛАССЫ =====

@dataclass
class OrderValidationResult:
    """Результат валидации ордера"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


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
    fees: Dict[str, float]
    precision: Dict[str, float]


# ===== UTILITY FUNCTIONS =====

def create_order_from_ccxt(
    ccxt_response: Dict[str, Any], 
    deal_id: Optional[int] = None
) -> Order:
    """
    Utility function для создания Order из CCXT ответа
    """
    return Order.from_ccxt_response(ccxt_response, deal_id=deal_id)


def validate_ccxt_order_structure(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Валидирует структуру данных на соответствие CCXT Order Structure
    """
    required_fields = ['id', 'datetime', 'timestamp', 'status', 'symbol', 'type', 'side', 'amount']
    optional_fields = [
        'clientOrderId', 'lastTradeTimestamp', 'timeInForce', 'price', 
        'filled', 'remaining', 'cost', 'average', 'trades', 'fee', 'info'
    ]
    
    errors = []
    
    # Проверка обязательных полей
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Проверка типов данных
    if 'amount' in data and not isinstance(data['amount'], (int, float)):
        errors.append("amount must be a number")
    
    if 'filled' in data and not isinstance(data['filled'], (int, float)):
        errors.append("filled must be a number")
    
    if 'timestamp' in data and not isinstance(data['timestamp'], int):
        errors.append("timestamp must be an integer")
    
    return len(errors) == 0, errors