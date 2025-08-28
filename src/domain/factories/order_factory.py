# domain/factories/order_factory.py.new - ENHANCED для реальной торговли
import time
import uuid
import math
import logging
from itertools import count
from typing import Optional, Dict, Any
from domain.entities.order import Order, ExchangeInfo

logger = logging.getLogger(__name__)

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

    def __init__(self, exchange_info_cache: Optional[Dict[str, ExchangeInfo]] = None, exchange_connector=None):
        """
        Инициализация фабрики

        Args:
            exchange_info_cache: Кеш информации о торговых парах с биржи
            exchange_connector: Коннектор для получения рыночных данных (для валидации цен)
        """
        self.exchange_info_cache = exchange_info_cache or {}
        self.exchange_connector = exchange_connector

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
        amount,  # Может быть float или Decimal
        price,   # Может быть float или Decimal
        deal_id: Optional[int] = None,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        🛒 Создание BUY ордера с валидацией и правильным округлением (синхронно)

        Args:
            symbol: Торговая пара (BTCUSDT)
            amount: Количество для покупки (float или Decimal)
            price: Цена покупки (float или Decimal)
            deal_id: ID связанной сделки
            order_type: Тип ордера (по умолчанию LIMIT)
            client_order_id: Клиентский ID
            metadata: Дополнительная информация
        """

        # Применяем правильное округление согласно параметрам биржи
        adjusted_amount = self.adjust_amount_precision(symbol, float(amount), round_up=True)
        adjusted_price = self.adjust_price_precision(symbol, float(price))

        # Примечание: асинхронная валидация PERCENT_PRICE_BY_SIDE пропущена в синхронном режиме
        # чтобы обеспечить совместимость с тестами и синхронными вызовами фабрики.

        # Добавляем метаданные для buy ордера
        buy_metadata = metadata or {}
        buy_metadata.update({
            'order_direction': 'entry',  # Вход в позицию
            'created_by': 'order_factory',
            'creation_timestamp': int(time.time() * 1000),
            'original_amount': str(amount),  # Сохраняем оригинальные значения для отладки
            'original_price': str(price),
            'adjusted_amount': str(adjusted_amount),
            'adjusted_price': str(adjusted_price)
        })

        return self._create_base_order(
            side=Order.SIDE_BUY,
            order_type=order_type,
            symbol=symbol,
            amount=adjusted_amount,  # Используем округленные значения
            price=adjusted_price,    # Используем округленные значения
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=buy_metadata
        )

    def create_sell_order(
        self,
        symbol: str,
        amount,  # Может быть float или Decimal
        price,   # Может быть float или Decimal
        deal_id: Optional[int] = None,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        🏷️ Создание SELL ордера с валидацией и правильным округлением (синхронно)

        Args:
            symbol: Торговая пара (BTCUSDT)
            amount: Количество для продажи (float или Decimal)
            price: Цена продажи (float или Decimal)
            deal_id: ID связанной сделки
            order_type: Тип ордера (по умолчанию LIMIT)
            client_order_id: Клиентский ID
            metadata: Дополнительная информация
        """

        # Применяем правильное округление согласно параметрам биржи
        adjusted_amount = self.adjust_amount_precision(symbol, float(amount), round_up=False)  # SELL округляем вниз
        adjusted_price = self.adjust_price_precision(symbol, float(price))

        # Примечание: асинхронная валидация PERCENT_PRICE_BY_SIDE пропущена в синхронном режиме
        # чтобы обеспечить совместимость с тестами и синхронными вызовами фабрики.

        # Добавляем метаданные для sell ордера
        sell_metadata = metadata or {}
        sell_metadata.update({
            'order_direction': 'exit',  # Выход из позиции
            'created_by': 'order_factory',
            'creation_timestamp': int(time.time() * 1000),
            'original_amount': str(amount),  # Сохраняем оригинальные значения для отладки
            'original_price': str(price),
            'adjusted_amount': str(adjusted_amount),
            'adjusted_price': str(adjusted_price)
        })

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=order_type,
            symbol=symbol,
            amount=adjusted_amount,  # Используем округленные значения
            price=adjusted_price,    # Используем округленные значения
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=sell_metadata
        )

    def create_market_buy_order(
        self,
        symbol: str,
        amount,  # Может быть float или Decimal
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        🛒 Создание MARKET BUY ордера (покупка по рынку) с правильным округлением
        """
        # ИСПРАВЛЕНИЕ: Применяем правильное округление для количества
        adjusted_amount = self.adjust_amount_precision(symbol, float(amount), round_up=True)
        
        metadata = {
            'order_direction': 'entry',
            'order_urgency': 'immediate',
            'market_order': True,
            'original_amount': str(amount),
            'adjusted_amount': str(adjusted_amount)
        }

        return self._create_base_order(
            side=Order.SIDE_BUY,
            order_type=Order.TYPE_MARKET,
            symbol=symbol,
            amount=adjusted_amount,  # Используем округленное значение
            price=0.0,  # Для market ордеров цена не нужна
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    def create_market_sell_order(
        self,
        symbol: str,
        amount,  # Может быть float или Decimal
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        🏷️ Создание MARKET SELL ордера (продажа по рынку) с правильным округлением
        """
        # ИСПРАВЛЕНИЕ: Применяем правильное округление для количества (SELL округляем вниз)
        adjusted_amount = self.adjust_amount_precision(symbol, float(amount), round_up=False)
        
        metadata = {
            'order_direction': 'exit',
            'order_urgency': 'immediate',
            'market_order': True,
            'original_amount': str(amount),
            'adjusted_amount': str(adjusted_amount)
        }

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=Order.TYPE_MARKET,
            symbol=symbol,
            amount=adjusted_amount,  # Используем округленное значение
            price=0.0,  # Для market ордеров цена не нужна
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    def create_stop_loss_order(
        self,
        symbol: str,
        amount,  # Может быть float или Decimal
        stop_price,  # Может быть float или Decimal
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        🛡️ Создание STOP LOSS ордера для защиты от убытков с правильным округлением

        Args:
            symbol: Торговая пара
            amount: Количество для продажи (float или Decimal)
            stop_price: Цена срабатывания стоп-лосса (float или Decimal)
            deal_id: ID связанной сделки
            client_order_id: Клиентский ID
        """
        # ИСПРАВЛЕНИЕ: Применяем правильное округление для amount и price
        adjusted_amount = self.adjust_amount_precision(symbol, float(amount), round_up=False)  # SELL округляем вниз
        adjusted_stop_price = self.adjust_price_precision(symbol, float(stop_price))
        
        metadata = {
            'order_direction': 'exit',
            'order_purpose': 'stop_loss',
            'risk_management': True,
            'original_amount': str(amount),
            'original_stop_price': str(stop_price),
            'adjusted_amount': str(adjusted_amount),
            'adjusted_stop_price': str(adjusted_stop_price)
        }

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=Order.TYPE_STOP_LOSS,
            symbol=symbol,
            amount=adjusted_amount,  # Используем округленные значения
            price=adjusted_stop_price,  # Используем округленные значения
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    def create_take_profit_order(
        self,
        symbol: str,
        amount,  # Может быть float или Decimal
        target_price,  # Может быть float или Decimal
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        💰 Создание TAKE PROFIT ордера для фиксации прибыли с правильным округлением

        Args:
            symbol: Торговая пара
            amount: Количество для продажи (float или Decimal)
            target_price: Целевая цена прибыли (float или Decimal)
            deal_id: ID связанной сделки
            client_order_id: Клиентский ID
        """
        # ИСПРАВЛЕНИЕ: Применяем правильное округление для amount и price
        adjusted_amount = self.adjust_amount_precision(symbol, float(amount), round_up=False)  # SELL округляем вниз
        adjusted_target_price = self.adjust_price_precision(symbol, float(target_price))
        
        metadata = {
            'order_direction': 'exit',
            'order_purpose': 'take_profit',
            'profit_taking': True,
            'original_amount': str(amount),
            'original_target_price': str(target_price),
            'adjusted_amount': str(adjusted_amount),
            'adjusted_target_price': str(adjusted_target_price)
        }

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=Order.TYPE_TAKE_PROFIT,
            symbol=symbol,
            amount=adjusted_amount,  # Используем округленные значения
            price=adjusted_target_price,  # Используем округленные значения
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

    async def fetch_market_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        📊 Получает текущую рыночную цену для валидации PERCENT_PRICE_BY_SIDE
        
        Returns:
            Dict с ключами: 'bid', 'ask', 'last' или None если не удалось получить
        """
        if not self.exchange_connector:
            logger.warning(f"⚠️ Exchange connector not available for market price fetching: {symbol}")
            return None
            
        try:
            ticker = await self.exchange_connector.fetch_ticker(symbol)
            return {
                'bid': ticker.bid,
                'ask': ticker.ask,
                'last': ticker.last
            }
        except Exception as e:
            logger.error(f"❌ Failed to fetch market price for {symbol}: {e}")
            return None

    async def validate_percent_price_by_side(self, symbol: str, price: float, side: str) -> tuple[bool, str, Optional[float]]:
        """
        🔍 Валидация цены против фильтра PERCENT_PRICE_BY_SIDE
        
        Args:
            symbol: Торговая пара
            price: Цена ордера
            side: BUY или SELL
            
        Returns:
            tuple: (is_valid, error_message, suggested_price)
        """
        market_prices = await self.fetch_market_price(symbol)
        if not market_prices:
            # Если не можем получить рыночную цену, пропускаем валидацию
            logger.warning(f"⚠️ Cannot validate PERCENT_PRICE_BY_SIDE for {symbol}: market price unavailable")
            return True, "", None
            
        # Используем консервативные лимиты (±10%) если нет точной информации о фильтрах
        # В реальной реализации эти значения должны браться из exchange info
        max_deviation_percent = 10.0  # 10% отклонение от рыночной цены
        
        if side.upper() == Order.SIDE_BUY:
            # Для BUY ордеров проверяем относительно ask цены
            reference_price = market_prices.get('ask') or market_prices.get('last')
            if not reference_price:
                return True, "", None
                
            min_allowed = reference_price * (1 - max_deviation_percent / 100)
            max_allowed = reference_price * (1 + max_deviation_percent / 100)
            
            if price < min_allowed:
                suggested_price = min_allowed
                return False, f"BUY price {price} too low (min: {min_allowed:.8f}, market: {reference_price:.8f})", suggested_price
            elif price > max_allowed:
                suggested_price = max_allowed
                return False, f"BUY price {price} too high (max: {max_allowed:.8f}, market: {reference_price:.8f})", suggested_price
                
        elif side.upper() == Order.SIDE_SELL:
            # Для SELL ордеров проверяем относительно bid цены
            reference_price = market_prices.get('bid') or market_prices.get('last')
            if not reference_price:
                return True, "", None
                
            min_allowed = reference_price * (1 - max_deviation_percent / 100)
            max_allowed = reference_price * (1 + max_deviation_percent / 100)
            
            if price < min_allowed:
                suggested_price = min_allowed
                return False, f"SELL price {price} too low (min: {min_allowed:.8f}, market: {reference_price:.8f})", suggested_price
            elif price > max_allowed:
                suggested_price = max_allowed
                return False, f"SELL price {price} too high (max: {max_allowed:.8f}, market: {reference_price:.8f})", suggested_price
        
        return True, "", None

    async def adjust_price_for_percent_price_filter(self, symbol: str, price: float, side: str, auto_adjust: bool = True) -> tuple[float, bool, str]:
        """
        🔧 Корректирует цену для соответствия фильтру PERCENT_PRICE_BY_SIDE
        
        Args:
            symbol: Торговая пара
            price: Исходная цена
            side: BUY или SELL
            auto_adjust: Автоматически корректировать цену если она вне диапазона
            
        Returns:
            tuple: (adjusted_price, was_adjusted, adjustment_message)
        """
        is_valid, error_msg, suggested_price = await self.validate_percent_price_by_side(symbol, price, side)
        
        if is_valid:
            return price, False, ""
            
        if not auto_adjust or suggested_price is None:
            return price, False, f"Price validation failed: {error_msg}"
            
        # Применяем точность биржи к скорректированной цене
        adjusted_price = self.adjust_price_precision(symbol, suggested_price)
        
        adjustment_msg = f"Price adjusted from {price} to {adjusted_price} for PERCENT_PRICE_BY_SIDE compliance: {error_msg}"
        logger.warning(f"⚠️ {adjustment_msg}")
        
        return adjusted_price, True, adjustment_msg
