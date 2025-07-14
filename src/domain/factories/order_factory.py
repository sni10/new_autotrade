# domain/factories/order_factory.py.new - ENHANCED для реальной торговли
import time
import uuid
import math
from itertools import count
from typing import Optional, Dict, Any
from domain.entities.order import Order, ExchangeInfo

# 🔧 Генератор уникальных ID на основе счетчика + timestamp
_id_gen = count(int(time.time()*1e6))

def _next_id():
    """🔧 Генерация следующего уникального ID"""
    return next(_id_gen)

def _generate_client_order_id(prefix: str = "auto") -> str:
    """🆕 Генерация уникального клиентского ID"""
    timestamp = int(time.time() * 1000)
    short_uuid = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{short_uuid}"

class OrderFactory:
    """
    🚀 РАСШИРЕННАЯ фабрика для создания ордеров с валидацией и поддержкой биржевых параметров
    """

    def __init__(self, exchange_info_cache: Optional[Dict[str, ExchangeInfo]] = None):
        """
        Инициализация фабрики

        Args:
            exchange_info_cache: Кеш информации о торговых парах с биржи
        """
        self.exchange_info_cache = exchange_info_cache or {}

    def _create_base_order(
        self,
        side: str,
        order_type: str,
        symbol: str,
        amount: float,
        price: float = 0.0,
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
        time_in_force: str = "GTC",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        🆕 Базовый метод создания ордера с полной валидацией

        Args:
            side: BUY или SELL
            order_type: LIMIT, MARKET, STOP_LOSS, etc.
            symbol: Торговая пара (например, BTCUSDT)
            amount: Количество для торговли
            price: Цена (для лимитных ордеров)
            deal_id: ID связанной сделки
            client_order_id: Клиентский ID (генерируется автоматически если None)
            time_in_force: Время жизни ордера
            metadata: Дополнительная информация
        """

        # Генерируем ID если не предоставлен
        if client_order_id is None:
            client_order_id = _generate_client_order_id(f"{side.lower()}_{symbol.lower()}")

        # Создаем ордер с расширенными параметрами
        order = Order(
            order_id=_next_id(),
            side=side,
            order_type=order_type,
            price=price,
            amount=amount,
            status=Order.STATUS_PENDING,  # Начинаем с PENDING
            deal_id=deal_id,
            symbol=symbol,
            remaining_amount=amount,  # Изначально весь объем остается
            client_order_id=client_order_id,
            time_in_force=time_in_force,
            metadata=metadata or {}
        )

        return order

    def create_buy_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: Optional[int] = None,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        🛒 Создание BUY ордера с валидацией

        Args:
            symbol: Торговая пара (BTCUSDT)
            amount: Количество для покупки
            price: Цена покупки
            deal_id: ID связанной сделки
            order_type: Тип ордера (по умолчанию LIMIT)
            client_order_id: Клиентский ID
            metadata: Дополнительная информация
        """

        # Добавляем метаданные для buy ордера
        buy_metadata = metadata or {}
        buy_metadata.update({
            'order_direction': 'entry',  # Вход в позицию
            'created_by': 'order_factory',
            'creation_timestamp': int(time.time() * 1000)
        })

        return self._create_base_order(
            side=Order.SIDE_BUY,
            order_type=order_type,
            symbol=symbol,
            amount=amount,
            price=price,
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=buy_metadata
        )

    def create_sell_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: Optional[int] = None,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        🏷️ Создание SELL ордера с валидацией

        Args:
            symbol: Торговая пара (BTCUSDT)
            amount: Количество для продажи
            price: Цена продажи
            deal_id: ID связанной сделки
            order_type: Тип ордера (по умолчанию LIMIT)
            client_order_id: Клиентский ID
            metadata: Дополнительная информация
        """

        # Добавляем метаданные для sell ордера
        sell_metadata = metadata or {}
        sell_metadata.update({
            'order_direction': 'exit',  # Выход из позиции
            'created_by': 'order_factory',
            'creation_timestamp': int(time.time() * 1000)
        })

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=order_type,
            symbol=symbol,
            amount=amount,
            price=price,
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=sell_metadata
        )

    def create_market_buy_order(
        self,
        symbol: str,
        amount: float,
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        🛒 Создание MARKET BUY ордера (покупка по рынку)
        """
        metadata = {
            'order_direction': 'entry',
            'order_urgency': 'immediate',
            'market_order': True
        }

        return self._create_base_order(
            side=Order.SIDE_BUY,
            order_type=Order.TYPE_MARKET,
            symbol=symbol,
            amount=amount,
            price=0.0,  # Для market ордеров цена не нужна
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    def create_market_sell_order(
        self,
        symbol: str,
        amount: float,
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        🏷️ Создание MARKET SELL ордера (продажа по рынку)
        """
        metadata = {
            'order_direction': 'exit',
            'order_urgency': 'immediate',
            'market_order': True
        }

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=Order.TYPE_MARKET,
            symbol=symbol,
            amount=amount,
            price=0.0,  # Для market ордеров цена не нужна
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    def create_stop_loss_order(
        self,
        symbol: str,
        amount: float,
        stop_price: float,
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        🛡️ Создание STOP LOSS ордера для защиты от убытков

        Args:
            symbol: Торговая пара
            amount: Количество для продажи
            stop_price: Цена срабатывания стоп-лосса
            deal_id: ID связанной сделки
            client_order_id: Клиентский ID
        """
        metadata = {
            'order_direction': 'exit',
            'order_purpose': 'stop_loss',
            'risk_management': True,
            'stop_price': stop_price
        }

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=Order.TYPE_STOP_LOSS,
            symbol=symbol,
            amount=amount,
            price=stop_price,
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    def create_take_profit_order(
        self,
        symbol: str,
        amount: float,
        target_price: float,
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        💰 Создание TAKE PROFIT ордера для фиксации прибыли

        Args:
            symbol: Торговая пара
            amount: Количество для продажи
            target_price: Целевая цена прибыли
            deal_id: ID связанной сделки
            client_order_id: Клиентский ID
        """
        metadata = {
            'order_direction': 'exit',
            'order_purpose': 'take_profit',
            'profit_taking': True,
            'target_price': target_price
        }

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=Order.TYPE_TAKE_PROFIT,
            symbol=symbol,
            amount=amount,
            price=target_price,
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    # 🆕 МЕТОДЫ ВАЛИДАЦИИ

    def validate_order_params(
        self,
        symbol: str,
        amount: float,
        price: float = None,
        side: str = None
    ) -> tuple[bool, list[str]]:
        """
        🔍 Валидация параметров ордера перед созданием

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []

        # Проверяем основные параметры
        if not symbol:
            errors.append("Symbol is required")
        if amount <= 0:
            errors.append("Amount must be positive")
        if price is not None and price <= 0:
            errors.append("Price must be positive")
        if side and side not in [Order.SIDE_BUY, Order.SIDE_SELL]:
            errors.append("Side must be BUY or SELL")

        # Проверяем против exchange info если доступно
        if symbol in self.exchange_info_cache:
            exchange_info = self.exchange_info_cache[symbol]

            if amount < exchange_info.min_qty:
                errors.append(f"Amount {amount} below minimum {exchange_info.min_qty}")
            if amount > exchange_info.max_qty:
                errors.append(f"Amount {amount} above maximum {exchange_info.max_qty}")

            if price is not None:
                if price < exchange_info.min_price:
                    errors.append(f"Price {price} below minimum {exchange_info.min_price}")
                if price > exchange_info.max_price:
                    errors.append(f"Price {price} above maximum {exchange_info.max_price}")

                # Проверяем минимальную стоимость ордера
                notional_value = amount * price
                if notional_value < exchange_info.min_notional:
                    errors.append(f"Order value {notional_value} below minimum {exchange_info.min_notional}")

        return len(errors) == 0, errors

    def adjust_amount_precision(self, symbol: str, amount: float, round_up: bool = False) -> float:
        """🔧 Корректирует количество согласно ``step_size`` биржи.

        Если ``round_up`` установлено в ``True``, то количество округляется
        вверх до ближайшего допустимого шага. Это полезно при создании BUY
        ордеров, чтобы избежать ситуации, когда биржа округляет значение в
        меньшую сторону и фактически покупается меньшее количество.
        """
        if symbol not in self.exchange_info_cache:
            return amount

        exchange_info = self.exchange_info_cache[symbol]
        step_size = exchange_info.step_size

        if step_size > 0:
            precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
            steps = amount / step_size
            steps = math.ceil(steps) if round_up else math.floor(steps)
            adjusted = round(steps * step_size, precision)
            adjusted = min(max(adjusted, exchange_info.min_qty), exchange_info.max_qty)
            return adjusted

        return amount

    def adjust_price_precision(self, symbol: str, price: float) -> float:
        """
        🔧 Корректирует цену согласно tick_size биржи
        """
        if symbol not in self.exchange_info_cache:
            return price

        exchange_info = self.exchange_info_cache[symbol]
        tick_size = exchange_info.tick_size

        if tick_size > 0:
            # Округляем до ближайшего tick_size
            precision = len(str(tick_size).split('.')[-1]) if '.' in str(tick_size) else 0
            adjusted = round(price // tick_size * tick_size, precision)
            return max(adjusted, exchange_info.min_price)

        return price

    def update_exchange_info(self, symbol: str, exchange_info: ExchangeInfo) -> None:
        """
        🔄 Обновляет информацию о торговой паре
        """
        self.exchange_info_cache[symbol] = exchange_info

    def get_exchange_info(self, symbol: str) -> Optional[ExchangeInfo]:
        """
        📊 Возвращает информацию о торговой паре
        """
        return self.exchange_info_cache.get(symbol)
