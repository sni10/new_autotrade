import logging
from typing import Dict, List, Optional, Tuple, Any

from src.domain.entities.order import Order, OrderValidationResult
from src.domain.services.orders.balance_service import BalanceService
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from src.domain.repositories.i_statistics_repository import IStatisticsRepository
from src.domain.entities.statistics import Statistics, StatisticCategory, StatisticType

logger = logging.getLogger(__name__)


class OrderValidationService:
    """
    Сервис для валидации параметров ордеров.
    Соблюдает принцип единственной ответственности (SRP).
    Отвечает ТОЛЬКО за валидацию ордеров перед размещением.
    """
    
    def __init__(
        self,
        balance_service: BalanceService,
        exchange_connector: CcxtExchangeConnector,
        statistics_repo: Optional[IStatisticsRepository] = None
    ):
        self.exchange_connector = exchange_connector
        self.statistics_repo = statistics_repo
        
        self._stats = {
            'validations_performed': 0,
            'validations_passed': 0,
            'validations_failed': 0,
            'warnings_issued': 0
        }
    
    async def validate_order_params(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        order_type: str
    ) -> OrderValidationResult:
        """
        Полная валидация параметров ордера
        
        Args:
            symbol: Торговая пара
            side: Сторона ордера (BUY/SELL)
            amount: Количество
            price: Цена (для лимитных ордеров)
            order_type: Тип ордера (LIMIT/MARKET)
            
        Returns:
            OrderValidationResult с результатом валидации
        """
        try:
            self._stats['validations_performed'] += 1
            
            errors = []
            warnings = []
            
            # 1. Базовая валидация параметров
            basic_errors = self._validate_basic_params(symbol, side, amount, price, order_type)
            errors.extend(basic_errors)
            
            # 2. Валидация через биржевую информацию
            if self.exchange_connector:
                exchange_errors, exchange_warnings = await self._validate_against_exchange_info(
                    symbol, side, amount, price, order_type
                )
                errors.extend(exchange_errors)
                warnings.extend(exchange_warnings)
            else:
                warnings.append("No exchange connector available for detailed validation")
            
            # Результат валидации
            is_valid = len(errors) == 0
            
            if is_valid:
                self._stats['validations_passed'] += 1
            else:
                self._stats['validations_failed'] += 1
                
            if warnings:
                self._stats['warnings_issued'] += len(warnings)
            
            # Обновляем статистику
            await self._update_validation_statistics(is_valid, symbol, side, order_type)
            
            return OrderValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"❌ Error validating order params: {e}")
            self._stats['validations_failed'] += 1
            
            return OrderValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[]
            )
    
    def _validate_basic_params(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        order_type: str
    ) -> List[str]:
        """Базовая валидация параметров"""
        errors = []
        
        # Проверка обязательных полей
        if not symbol:
            errors.append("Symbol is required")
        if not symbol.replace('/', '').replace('-', '').isalnum():
            errors.append("Invalid symbol format")
            
        if not side:
            errors.append("Side is required")
        elif side not in [Order.SIDE_BUY, Order.SIDE_SELL]:
            errors.append("Side must be BUY or SELL")
        
        # Проверка числовых значений
        if amount <= 0:
            errors.append("Amount must be positive")
        elif amount > 1e10:  # Защита от слишком больших значений
            errors.append("Amount is too large")
            
        if order_type == Order.TYPE_LIMIT:
            if price <= 0:
                errors.append("Price must be positive for limit orders")
            elif price > 1e10:  # Защита от слишком больших значений
                errors.append("Price is too large")
                
        if not order_type:
            errors.append("Order type is required")
        elif order_type not in [Order.TYPE_LIMIT, Order.TYPE_MARKET]:
            errors.append("Order type must be LIMIT or MARKET")
        
        return errors
    
    async def _validate_against_exchange_info(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        order_type: str
    ) -> Tuple[List[str], List[str]]:
        """Валидация против информации с биржи"""
        errors = []
        warnings = []
        
        try:
            symbol_info = await self.exchange_connector.get_symbol_info(symbol)
            
            # Валидация количества
            if hasattr(symbol_info, 'min_qty') and amount < symbol_info.min_qty:
                errors.append(f"Amount {amount} below minimum {symbol_info.min_qty}")
                
            if hasattr(symbol_info, 'max_qty') and amount > symbol_info.max_qty:
                errors.append(f"Amount {amount} above maximum {symbol_info.max_qty}")
            
            # Валидация цены для лимитных ордеров
            if order_type == Order.TYPE_LIMIT:
                if hasattr(symbol_info, 'min_price') and price < symbol_info.min_price:
                    errors.append(f"Price {price} below minimum {symbol_info.min_price}")
                    
                if hasattr(symbol_info, 'max_price') and price > symbol_info.max_price:
                    errors.append(f"Price {price} above maximum {symbol_info.max_price}")
                
                # Проверка минимальной стоимости ордера
                notional_value = amount * price
                if hasattr(symbol_info, 'min_notional') and notional_value < symbol_info.min_notional:
                    errors.append(f"Order value {notional_value} below minimum {symbol_info.min_notional}")
                
                # Предупреждения
                if (hasattr(symbol_info, 'min_notional') and 
                    notional_value < symbol_info.min_notional * 1.1):
                    warnings.append("Order value close to minimum notional")
                    
            # Валидация шагов цены и количества
            await self._validate_precision_steps(symbol_info, amount, price, order_type, errors, warnings)
            
        except Exception as e:
            warnings.append(f"Could not validate against exchange info: {e}")
        
        return errors, warnings
    
    async def _validate_precision_steps(
        self,
        symbol_info: Any,
        amount: float,
        price: float,
        order_type: str,
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Валидация шагов точности"""
        try:
            # Проверка шага количества
            if hasattr(symbol_info, 'amount_precision'):
                amount_precision = symbol_info.amount_precision
                if amount_precision and amount_precision > 0:
                    step = 1 / (10 ** amount_precision)
                    if abs(amount % step) > 1e-10:  # Учитываем погрешность float
                        warnings.append(f"Amount precision may not match exchange requirements (step: {step})")
            
            # Проверка шага цены для лимитных ордеров
            if order_type == Order.TYPE_LIMIT and hasattr(symbol_info, 'price_precision'):
                price_precision = symbol_info.price_precision
                if price_precision and price_precision > 0:
                    step = 1 / (10 ** price_precision)
                    if abs(price % step) > 1e-10:  # Учитываем погрешность float
                        warnings.append(f"Price precision may not match exchange requirements (step: {step})")
                        
        except Exception as e:
            warnings.append(f"Could not validate precision steps: {e}")
    
    async def validate_order_object(self, order: Order) -> OrderValidationResult:
        """
        Валидация объекта ордера
        
        Args:
            order: Ордер для валидации
            
        Returns:
            OrderValidationResult
        """
        try:
            return await self.validate_order_params(
                symbol=order.symbol,
                side=order.side,
                amount=order.amount,
                price=order.price,
                order_type=order.order_type
            )
            
        except Exception as e:
            logger.error(f"❌ Error validating order object: {e}")
            return OrderValidationResult(
                is_valid=False,
                errors=[f"Order object validation error: {str(e)}"],
                warnings=[]
            )
    
    async def validate_multiple_orders(self, orders: List[Order]) -> Dict[int, OrderValidationResult]:
        """
        Валидация нескольких ордеров
        
        Args:
            orders: Список ордеров для валидации
            
        Returns:
            Словарь {order_id: ValidationResult}
        """
        results = {}
        
        try:
            for order in orders:
                validation_result = await self.validate_order_object(order)
                results[order.order_id] = validation_result
                
        except Exception as e:
            logger.error(f"❌ Error validating multiple orders: {e}")
            
        return results
    
    async def check_duplicate_orders(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        active_orders: List[Order],
        tolerance_percent: float = 0.1
    ) -> Tuple[bool, Optional[Order]]:
        """
        Проверка на дублирующиеся ордера
        
        Args:
            symbol: Торговая пара
            side: Сторона ордера
            amount: Количество
            price: Цена
            active_orders: Список активных ордеров
            tolerance_percent: Допустимое отклонение в процентах
            
        Returns:
            (is_duplicate, duplicate_order)
        """
        try:
            tolerance = tolerance_percent / 100
            
            for order in active_orders:
                if (order.symbol == symbol and 
                    order.side == side and
                    order.is_open()):
                    
                    # Проверяем близость количества
                    amount_diff = abs(order.amount - amount) / order.amount
                    
                    # Проверяем близость цены
                    price_diff = abs(order.price - price) / order.price if order.price > 0 else 0
                    
                    if amount_diff <= tolerance and price_diff <= tolerance:
                        return True, order
            
            return False, None
            
        except Exception as e:
            logger.error(f"❌ Error checking duplicate orders: {e}")
            return False, None
    
    async def _update_validation_statistics(
        self,
        is_valid: bool,
        symbol: str,
        side: str,
        order_type: str
    ) -> None:
        """Обновление статистики валидации"""
        if not self.statistics_repo:
            return
        
        try:
            # Общая статистика валидации
            await self.statistics_repo.increment_counter(
                "order_validations_total",
                StatisticCategory.ORDERS,
                tags={
                    "symbol": symbol,
                    "side": side.lower(),
                    "order_type": order_type.lower(),
                    "result": "valid" if is_valid else "invalid"
                }
            )
            
            # Статистика успешности
            if is_valid:
                await self.statistics_repo.increment_counter(
                    "order_validations_passed",
                    StatisticCategory.ORDERS,
                    tags={"symbol": symbol}
                )
            else:
                await self.statistics_repo.increment_counter(
                    "order_validations_failed",
                    StatisticCategory.ORDERS,
                    tags={"symbol": symbol}
                )
                
        except Exception as e:
            logger.error(f"Error updating validation statistics: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики сервиса"""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Сброс статистики"""
        self._stats = {
            'validations_performed': 0,
            'validations_passed': 0,
            'validations_failed': 0,
            'warnings_issued': 0
        }