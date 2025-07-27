import asyncio
import logging
from typing import Optional, Dict, List, Any, Tuple
from decimal import ROUND_DOWN, ROUND_UP

from src.domain.entities.order import Order, OrderValidationResult, OrderExecutionResult
from src.domain.factories.order_factory import OrderFactory
from src.domain.services.utils.decimal_rounding_service import DecimalRoundingService
from src.domain.services.orders.balance_service import BalanceService
from src.infrastructure.repositories.orders_repository import OrdersRepository
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from src.domain.repositories.i_statistics_repository import IStatisticsRepository
from src.domain.entities.statistics import Statistics, StatisticCategory, StatisticType

logger = logging.getLogger(__name__)


class OrderPlacementService:
    """
    Сервис для размещения ордеров на бирже.
    Соблюдает принцип единственной ответственности (SRP).
    Отвечает ТОЛЬКО за размещение ордеров на бирже.
    """
    
    def __init__(
        self,
        balance_service: BalanceService,
        orders_repo: OrdersRepository,
        order_factory: OrderFactory,
        exchange_connector: CcxtExchangeConnector,
        statistics_repo: Optional[IStatisticsRepository] = None
    ):
        self.balance_service = balance_service
        self.orders_repo = orders_repo
        self.order_factory = order_factory
        self.exchange_connector = exchange_connector
        self.statistics_repo = statistics_repo
        
        # Retry parameters
        self.max_retries = 3
        self.retry_delay = 1.0
        self.retry_backoff = 2.0
        
        self._stats = {
            'orders_placed': 0,
            'orders_failed': 0,
            'retry_attempts': 0
        }
    
    async def place_buy_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: int,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        Размещение BUY ордера на бирже
        
        Args:
            symbol: Торговая пара (BTCUSDT)
            amount: Количество для покупки
            price: Цена покупки
            deal_id: ID связанной сделки
            order_type: Тип ордера (LIMIT, MARKET)
            client_order_id: Клиентский ID ордера
            
        Returns:
            OrderExecutionResult с информацией о результате
        """
        try:
            # Корректируем количество согласно правилам биржи
            amount = self.order_factory.adjust_amount_precision(symbol, amount, round_up=True)
            
            # Корректируем цену согласно precision с биржи
            market_info = await self.exchange_connector.get_symbol_info(symbol)
            price_precision = market_info.precision.get('price')
            if price_precision:
                price = float(DecimalRoundingService.round_by_tick_size(
                    price, str(price_precision), rounding_mode=ROUND_DOWN
                ))
            
            logger.info(f"🛒 Placing BUY order: {amount} {symbol} @ {price}")
            
            # Создание ордера через фабрику
            order = self.order_factory.create_buy_order(
                symbol=symbol,
                amount=amount,
                price=price,
                deal_id=deal_id,
                order_type=order_type,
                client_order_id=client_order_id
            )
            
            # Сохранение в репозиторий
            self.orders_repo.save(order)
            
            # Размещение на бирже
            execution_result = await self._execute_order_on_exchange(order)
            
            # Обновление статистики
            await self._update_placement_statistics(execution_result.success, Order.SIDE_BUY)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ Error placing BUY order: {e}")
            await self._update_placement_statistics(False, Order.SIDE_BUY)
            return OrderExecutionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def place_sell_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: int,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        Размещение SELL ордера на бирже
        """
        try:
            # Корректируем количество согласно правилам биржи (округляем вниз)
            amount = self.order_factory.adjust_amount_precision(symbol, amount)
            
            # Корректируем цену согласно precision с биржи
            market_info = await self.exchange_connector.get_symbol_info(symbol)
            price_precision = market_info.precision.get('price')
            if price_precision:
                price = float(DecimalRoundingService.round_by_tick_size(
                    price, str(price_precision), rounding_mode=ROUND_UP
                ))
            
            logger.info(f"🏷️ Placing SELL order: {amount} {symbol} @ {price}")
            
            # Создание ордера через фабрику
            order = self.order_factory.create_sell_order(
                symbol=symbol,
                amount=amount,
                price=price,
                deal_id=deal_id,
                order_type=order_type,
                client_order_id=client_order_id
            )
            
            # Сохранение в репозиторий
            self.orders_repo.save(order)
            
            # Размещение на бирже
            execution_result = await self._execute_order_on_exchange(order)
            
            # Обновление статистики
            await self._update_placement_statistics(execution_result.success, Order.SIDE_SELL)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ Error placing SELL order: {e}")
            await self._update_placement_statistics(False, Order.SIDE_SELL)
            return OrderExecutionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def place_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        deal_id: int,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        Размещение маркет-ордера (для стоп-лосса и экстренных продаж)
        """
        try:
            logger.info(f"🚨 Placing MARKET {side} order: {amount} {symbol}")
            
            # Корректируем количество
            amount = self.order_factory.adjust_amount_precision(symbol, amount)
            
            # Создание маркет-ордера
            if side.upper() == Order.SIDE_BUY:
                order = self.order_factory.create_buy_order(
                    symbol=symbol,
                    amount=amount,
                    price=0,  # Для маркет-ордера цена не важна
                    deal_id=deal_id,
                    order_type=Order.TYPE_MARKET,
                    client_order_id=client_order_id
                )
            else:
                order = self.order_factory.create_sell_order(
                    symbol=symbol,
                    amount=amount,
                    price=0,  # Для маркет-ордера цена не важна
                    deal_id=deal_id,
                    order_type=Order.TYPE_MARKET,
                    client_order_id=client_order_id
                )
            
            # Сохранение в репозиторий
            self.orders_repo.save(order)
            
            # Размещение на бирже
            execution_result = await self._execute_order_on_exchange(order)
            
            # Обновление статистики
            await self._update_placement_statistics(execution_result.success, side.upper())
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ Error placing MARKET order: {e}")
            await self._update_placement_statistics(False, side.upper())
            return OrderExecutionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def place_existing_order(self, order: Order) -> OrderExecutionResult:
        """
        Размещение на бирже уже существующего локального ордера (в статусе PENDING)
        """
        if not order.is_pending():
            return OrderExecutionResult(
                success=False, 
                error_message=f"Order {order.order_id} is not in PENDING state."
            )
        
        logger.info(f"📤 Placing existing order {order.order_id} ({order.side} {order.amount} {order.symbol})")
        
        try:
            execution_result = await self._execute_order_on_exchange(order)
            
            # Обновление статистики
            await self._update_placement_statistics(execution_result.success, order.side)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ Error placing existing order {order.order_id}: {e}")
            await self._update_placement_statistics(False, order.side)
            return OrderExecutionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def _execute_order_on_exchange(self, order: Order) -> OrderExecutionResult:
        """
        Реальное размещение ордера на бирже с retry механизмом
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📤 Executing order on exchange (attempt {attempt + 1}/{self.max_retries})")
                
                # Вызов API биржи
                exchange_response = await self.exchange_connector.create_order(
                    symbol=order.symbol,
                    side=order.side.lower(),
                    order_type=order.order_type.lower(),
                    amount=order.amount,
                    price=order.price if order.order_type == Order.TYPE_LIMIT else None
                )
                
                # Обновляем ордер данными с биржи
                order.mark_as_placed_on_exchange(
                    exchange_id=exchange_response['id'],
                    exchange_timestamp=exchange_response.get('timestamp')
                )
                
                # Дополнительный запрос для получения полных данных об исполнении
                if hasattr(self.exchange_connector, 'fetch_order'):
                    full_order_data = await self.exchange_connector.fetch_order(
                        order.exchange_id,
                        order.symbol
                    )
                    order.update_from_ccxt_response(full_order_data)
                
                # Сохраняем обновленный ордер
                self.orders_repo.save(order)
                
                logger.info(f"✅ Order placed successfully: {order.exchange_id}")
                self._stats['orders_placed'] += 1
                
                return OrderExecutionResult(
                    success=True,
                    order=order,
                    exchange_response=exchange_response
                )
                
            except Exception as e:
                last_error = e
                order.retries += 1
                self._stats['retry_attempts'] += 1
                logger.warning(f"⚠️ Order placement failed (attempt {attempt + 1}): {e}")
                
                # Exponential backoff для retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (self.retry_backoff ** attempt))
        
        # Все попытки неудачны
        order.mark_as_failed(f"Failed after {self.max_retries} attempts: {last_error}")
        self.orders_repo.save(order)
        self._stats['orders_failed'] += 1
        
        return OrderExecutionResult(
            success=False,
            order=order,
            error_message=f"Failed after {self.max_retries} attempts: {last_error}"
        )
    
    async def _update_placement_statistics(self, success: bool, side: str) -> None:
        """Обновление статистики размещения ордеров"""
        if not self.statistics_repo:
            return
        
        try:
            # Общая статистика размещения
            await self.statistics_repo.increment_counter(
                f"orders_placed_total",
                StatisticCategory.ORDERS,
                tags={"side": side.lower(), "success": str(success).lower()}
            )
            
            # Статистика по результату
            if success:
                await self.statistics_repo.increment_counter(
                    f"orders_placed_success",
                    StatisticCategory.ORDERS,
                    tags={"side": side.lower()}
                )
            else:
                await self.statistics_repo.increment_counter(
                    f"orders_placed_failed",
                    StatisticCategory.ORDERS,
                    tags={"side": side.lower()}
                )
                
        except Exception as e:
            logger.error(f"Error updating placement statistics: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики сервиса"""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Сброс статистики"""
        self._stats = {
            'orders_placed': 0,
            'orders_failed': 0,
            'retry_attempts': 0
        }