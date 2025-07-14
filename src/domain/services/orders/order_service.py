# domain/services/order_service.py.new - РЕАЛЬНАЯ торговля с API
import asyncio
import logging
from typing import Optional, Dict, List, Any, Tuple
from domain.entities.order import Order, OrderValidationResult, OrderExecutionResult
from domain.factories.order_factory import OrderFactory
from infrastructure.repositories.orders_repository import OrdersRepository
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
import ccxt

logger = logging.getLogger(__name__)

class OrderService:
    """
    🚀 ПОЛНОЦЕННЫЙ сервис для реальной торговли на бирже:
    - Создание и размещение ордеров на РЕАЛЬНОЙ бирже
    - Отслеживание статусов ордеров через API
    - Отмена и управление ордерами
    - Проверка балансов и валидация
    - Обработка ошибок и retry механизмы
    """

    def __init__(
        self,
        orders_repo: OrdersRepository,
        order_factory: OrderFactory,
        exchange_connector: CcxtExchangeConnector = None,
        currency_pair_symbol: str = None
    ):
        self.orders_repo = orders_repo
        self.order_factory = order_factory
        self.exchange_connector = exchange_connector
        self.currency_pair_symbol = currency_pair_symbol

        # Retry parameters
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.retry_backoff = 2.0  # exponential backoff multiplier

        # Statistics
        self.stats = {
            'orders_created': 0,
            'orders_executed': 0,
            'orders_failed': 0,
            'orders_cancelled': 0,
            'total_fees': 0.0
        }

    # 🚀 ОСНОВНЫЕ МЕТОДЫ СОЗДАНИЯ И РАЗМЕЩЕНИЯ ОРДЕРОВ

    async def create_and_place_buy_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: int,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        🛒 РЕАЛЬНОЕ создание и размещение BUY ордера на бирже

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
            logger.info(f"🛒 Creating BUY order: {amount} {symbol} @ {price}")

            # 1. Валидация параметров
            validation_result = await self._validate_order_params(
                symbol, Order.SIDE_BUY, amount, price, order_type
            )
            if not validation_result.is_valid:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Validation failed: {', '.join(validation_result.errors)}"
                )

            # 2. Проверка баланса
            balance_check = await self._check_balance_for_order(symbol, Order.SIDE_BUY, amount, price)
            if not balance_check[0]:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Insufficient balance: need {amount * price:.4f} {balance_check[1]}, have {balance_check[2]:.4f}"
                )

            # 3. Создание ордера через фабрику
            order = self.order_factory.create_buy_order(
                symbol=symbol,
                amount=amount,
                price=price,
                deal_id=deal_id,
                order_type=order_type,
                client_order_id=client_order_id
            )

            # 4. Сохранение в репозиторий
            self.orders_repo.save(order)

            # 5. РЕАЛЬНОЕ размещение на бирже
            if self.exchange_connector:
                execution_result = await self._execute_order_on_exchange(order)
                if execution_result.success:
                    self.stats['orders_executed'] += 1
                    logger.info(f"✅ BUY order executed: {order.exchange_id}")
                else:
                    self.stats['orders_failed'] += 1
                    logger.error(f"❌ BUY order failed: {execution_result.error_message}")

                return execution_result
            else:
                # Fallback без коннектора
                order.status = Order.STATUS_PENDING
                self.orders_repo.save(order)
                logger.warning(f"⚠️ BUY order created locally (no exchange connector)")

                return OrderExecutionResult(
                    success=True,
                    order=order,
                    error_message="Created locally - no exchange connector"
                )

        except Exception as e:
            logger.error(f"❌ Error creating BUY order: {e}")
            self.stats['orders_failed'] += 1
            return OrderExecutionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )

    async def create_and_place_sell_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: int,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        🏷️ РЕАЛЬНОЕ создание и размещение SELL ордера на бирже
        """
        try:
            logger.info(f"🏷️ Creating SELL order: {amount} {symbol} @ {price}")

            # 1. Валидация параметров
            validation_result = await self._validate_order_params(
                symbol, Order.SIDE_SELL, amount, price, order_type
            )
            if not validation_result.is_valid:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Validation failed: {', '.join(validation_result.errors)}"
                )

            # 2. Проверка баланса
            balance_check = await self._check_balance_for_order(symbol, Order.SIDE_SELL, amount, price)
            if not balance_check[0]:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Insufficient balance: need {amount:.4f} {balance_check[1]}, have {balance_check[2]:.4f}"
                )

            # 3. Создание ордера через фабрику
            order = self.order_factory.create_sell_order(
                symbol=symbol,
                amount=amount,
                price=price,
                deal_id=deal_id,
                order_type=order_type,
                client_order_id=client_order_id
            )

            # 4. Сохранение в репозиторий
            self.orders_repo.save(order)

            # 5. РЕАЛЬНОЕ размещение на бирже
            if self.exchange_connector:
                execution_result = await self._execute_order_on_exchange(order)
                if execution_result.success:
                    self.stats['orders_executed'] += 1
                    logger.info(f"✅ SELL order executed: {order.exchange_id}")
                else:
                    self.stats['orders_failed'] += 1
                    logger.error(f"❌ SELL order failed: {execution_result.error_message}")

                return execution_result

                return execution_result
            else:
                # Fallback без коннектора
                order.status = Order.STATUS_PENDING
                self.orders_repo.save(order)
                logger.warning(f"⚠️ SELL order created locally (no exchange connector)")

                return OrderExecutionResult(
                    success=True,
                    order=order,
                    error_message="Created locally - no exchange connector"
                )

        except Exception as e:
            logger.error(f"❌ Error creating SELL order: {e}")
            self.stats['orders_failed'] += 1
            return OrderExecutionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )

    # 🔧 ВНУТРЕННИЕ МЕТОДЫ

    async def _execute_order_on_exchange(self, order: Order) -> OrderExecutionResult:
        """
        🚀 РЕАЛЬНОЕ размещение ордера на бирже с retry механизмом
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.info(f"📤 Placing order on exchange (attempt {attempt + 1}/{self.max_retries})")

                # Вызов API биржи
                exchange_response = await self.exchange_connector.create_order(
                    symbol=order.symbol,
                    side=order.side.lower(),
                    order_type=order.order_type.lower(),
                    amount=order.amount,
                    price=order.price if order.order_type == Order.TYPE_LIMIT else None
                )

                # Обновляем ордер данными с биржи
                order.mark_as_placed(
                    exchange_id=exchange_response['id'],
                    exchange_timestamp=exchange_response.get('timestamp')
                )
                # Дополнительный запрос для получения полных данных об исполнении
                full_order_data = await self.exchange_connector.fetch_order(
                    order.exchange_id,
                    order.symbol
                )
                order.update_from_exchange(full_order_data)

                # Сохраняем обновленный ордер
                self.orders_repo.save(order)

                logger.info(f"✅ Order placed successfully: {order.exchange_id}")
                return OrderExecutionResult(
                    success=True,
                    order=order,
                    exchange_response=exchange_response
                )

            except Exception as e:
                last_error = e
                order.retries += 1
                logger.warning(f"⚠️ Order placement failed (attempt {attempt + 1}): {e}")

                # Exponential backoff для retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (self.retry_backoff ** attempt))

        # Все попытки неудачны
        order.mark_as_failed(f"Failed after {self.max_retries} attempts: {last_error}")
        self.orders_repo.save(order)

        return OrderExecutionResult(
            success=False,
            order=order,
            error_message=f"Failed after {self.max_retries} attempts: {last_error}"
        )

    async def _validate_order_params(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        order_type: str
    ) -> OrderValidationResult:
        """
        🔍 Валидация параметров ордера
        """
        errors = []
        warnings = []

        # Основная валидация
        if not symbol:
            errors.append("Symbol is required")
        if amount <= 0:
            errors.append("Amount must be positive")
        if order_type == Order.TYPE_LIMIT and price <= 0:
            errors.append("Price must be positive for limit orders")
        if side not in [Order.SIDE_BUY, Order.SIDE_SELL]:
            errors.append("Side must be BUY or SELL")

        # Валидация через exchange info если доступно
        if self.exchange_connector:
            try:
                symbol_info = await self.exchange_connector.get_symbol_info(symbol)

                if amount < symbol_info.min_qty:
                    errors.append(f"Amount {amount} below minimum {symbol_info.min_qty}")
                if amount > symbol_info.max_qty:
                    errors.append(f"Amount {amount} above maximum {symbol_info.max_qty}")

                if order_type == Order.TYPE_LIMIT:
                    if price < symbol_info.min_price:
                        errors.append(f"Price {price} below minimum {symbol_info.min_price}")
                    if price > symbol_info.max_price:
                        errors.append(f"Price {price} above maximum {symbol_info.max_price}")

                    # Проверяем минимальную стоимость
                    notional_value = amount * price
                    if notional_value < symbol_info.min_notional:
                        errors.append(f"Order value {notional_value} below minimum {symbol_info.min_notional}")

                    # Предупреждения
                    if notional_value < symbol_info.min_notional * 1.1:
                        warnings.append(f"Order value close to minimum notional")

            except Exception as e:
                warnings.append(f"Could not validate against exchange info: {e}")

        return OrderValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def _check_balance_for_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float
    ) -> Tuple[bool, str, float]:
        """
        💰 Проверка баланса для ордера
        """
        if not self.exchange_connector:
            return True, "UNKNOWN", 0.0  # Пропускаем проверку без коннектора

        try:
            return await self.exchange_connector.check_sufficient_balance(
                symbol, side, amount, price
            )
        except Exception as e:
            logger.error(f"❌ Error checking balance: {e}")
            return False, "ERROR", 0.0

    # 📊 МЕТОДЫ ОТСЛЕЖИВАНИЯ И УПРАВЛЕНИЯ ОРДЕРАМИ

    async def get_order_status(self, order: Order) -> Optional[Order]:
        """
        📊 РЕАЛЬНАЯ проверка статуса ордера на бирже
        """
        if not order.exchange_id or not self.exchange_connector:
            return order

        try:
            logger.debug(f"📊 Checking status for order {order.exchange_id}")

            # РЕАЛЬНЫЙ запрос к бирже
            exchange_order = await self.exchange_connector.fetch_order(
                order.exchange_id,
                order.symbol
            )

            # Обновляем локальный ордер данными с биржи
            order.update_from_exchange(exchange_order)

            # Сохраняем обновления
            self.orders_repo.save(order)

            logger.debug(f"📊 Order {order.order_id} status updated: {order.status}")
            return order

        except Exception as e:
            logger.error(f"❌ Error checking order status {order.order_id}: {e}")
            return order

    async def cancel_order(self, order: Order) -> bool:
        """
        ❌ РЕАЛЬНАЯ отмена ордера на бирже
        """
        if not order.is_open():
            logger.warning(f"⚠️ Order {order.order_id} is not open ({order.status})")
            return False

        if not self.exchange_connector or not order.exchange_id:
            # Локальная отмена без биржи
            order.cancel("No exchange connector or exchange_id")
            self.orders_repo.save(order)
            logger.warning(f"⚠️ Order {order.order_id} cancelled locally")
            return True

        try:
            logger.info(f"❌ Cancelling order {order.exchange_id} on exchange")

            # РЕАЛЬНАЯ отмена на бирже
            exchange_response = await self.exchange_connector.cancel_order(
                order.exchange_id,
                order.symbol
            )

            # Обновляем статус
            order.cancel("Cancelled by user")
            if exchange_response:
                order.update_from_exchange(exchange_response)

            self.orders_repo.save(order)
            self.stats['orders_cancelled'] += 1

            logger.info(f"✅ Order {order.order_id} cancelled successfully")
            return True

        except ccxt.OrderNotFound:
            # Ордер не найден на бирже, значит, его уже нет или он исполнен
            logger.warning(f"⚠️ Order {order.order_id} (exchange_id: {order.exchange_id}) not found on exchange. Assuming it's already gone.")
            order.status = Order.STATUS_NOT_FOUND_ON_EXCHANGE # Новый статус
            order.closed_at = int(time.time() * 1000)
            self.orders_repo.save(order)
            return True # Считаем, что цель достигнута: ордера на бирже нет

        except Exception as e:
            logger.error(f"❌ Error cancelling order {order.order_id}: {e}")
            order.status = Order.STATUS_FAILED # Или новый статус FAILED_TO_CANCEL
            order.error_message = str(e)
            self.orders_repo.save(order)
            return False # Отмена не удалась

    async def sync_orders_with_exchange(self) -> List[Order]:
        """
        🔄 Синхронизация всех открытых ордеров с биржей
        """
        if not self.exchange_connector:
            logger.warning("⚠️ No exchange connector for sync")
            return []

        updated_orders = []

        try:
            # Получаем все локальные открытые ордера
            local_orders = self.get_open_orders()

            # Получаем открытые ордера с биржи
            # Используем self.currency_pair_symbol для fetchOpenOrders
            symbol_to_fetch = self.currency_pair_symbol if self.currency_pair_symbol else (local_orders[0].symbol if local_orders else None)
            if not symbol_to_fetch:
                logger.warning("⚠️ No symbol available to fetch open orders. Skipping sync.")
                return []

            exchange_open_orders = await self.exchange_connector.fetch_open_orders(symbol=symbol_to_fetch)
            exchange_open_orders_map = {order['id']: order for order in exchange_open_orders}

            for order in local_orders:
                if order.exchange_id:
                    if order.exchange_id in exchange_open_orders_map:
                        # Ордер есть на бирже и открыт - обновляем статус
                        exchange_data = exchange_open_orders_map[order.exchange_id]
                        order.update_from_exchange(exchange_data)
                        self.orders_repo.save(order)
                        updated_orders.append(order)
                    else:
                        # Ордера нет среди ОТКРЫТЫХ на бирже.
                        # Нужно запросить его полный статус, чтобы понять, что с ним произошло.
                        try:
                            full_exchange_order = await self.exchange_connector.fetch_order(
                                order.exchange_id,
                                order.symbol
                            )
                            order.update_from_exchange(full_exchange_order)
                            self.orders_repo.save(order)
                            updated_orders.append(order)
                            logger.info(f"🔄 Synced order {order.order_id} (exchange_id: {order.exchange_id}) status: {order.status}")
                        except ccxt.OrderNotFound:
                            # Ордер не найден на бирже вообще (ни открытый, ни закрытый)
                            logger.warning(f"⚠️ Order {order.order_id} (exchange_id: {order.exchange_id}) not found on exchange during sync. Marking as NOT_FOUND_ON_EXCHANGE.")
                            order.status = Order.STATUS_NOT_FOUND_ON_EXCHANGE
                            order.closed_at = int(time.time() * 1000)
                            self.orders_repo.save(order)
                            updated_orders.append(order)
                        except Exception as e:
                            logger.error(f"❌ Error fetching status for order {order.order_id} (exchange_id: {order.exchange_id}) during sync: {e}")
                            # Оставляем ордер в текущем состоянии, но логируем ошибку
                else:
                    # Локальный ордер без exchange_id - возможно, не был размещен
                    logger.warning(f"⚠️ Local order {order.order_id} has no exchange_id. Skipping sync for this order.")

            logger.info(f"🔄 Synced {len(updated_orders)} orders with exchange")
            return updated_orders

        except Exception as e:
            logger.error(f"❌ Error syncing orders: {e}")
            return []

    # 📋 МЕТОДЫ ПОЛУЧЕНИЯ ОРДЕРОВ

    def get_orders_by_deal(self, deal_id: int) -> List[Order]:
        """📋 Получает все ордера по ID сделки"""
        return self.orders_repo.get_all_by_deal(deal_id)

    def get_open_orders(self) -> List[Order]:
        """📋 Получает все открытые ордера"""
        all_orders = self.orders_repo.get_all()
        return [order for order in all_orders if order.is_open() or order.is_partially_filled()]

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """📋 Получает ордер по ID"""
        return self.orders_repo.get_by_id(order_id)

    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """📋 Получает все ордера по символу"""
        all_orders = self.orders_repo.get_all()
        return [order for order in all_orders if order.symbol == symbol]

    # 🚨 ЭКСТРЕННЫЕ МЕТОДЫ

    async def emergency_cancel_all_orders(self, symbol: str = None) -> int:
        """
        🚨 Экстренная отмена всех открытых ордеров
        """
        logger.warning("🚨 Emergency cancellation of all orders")

        open_orders = self.get_open_orders()
        if symbol:
            open_orders = [order for order in open_orders if order.symbol == symbol]

        cancelled_count = 0
        for order in open_orders:
            try:
                if await self.cancel_order(order):
                    cancelled_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to cancel order {order.order_id}: {e}")

        logger.warning(f"🚨 Emergency cancelled {cancelled_count}/{len(open_orders)} orders")
        return cancelled_count

    # 📊 СТАТИСТИКА И МОНИТОРИНГ

    def get_statistics(self) -> Dict[str, Any]:
        """📊 Получение статистики работы сервиса"""
        all_orders = self.orders_repo.get_all()

        stats = self.stats.copy()
        stats.update({
            'total_orders': len(all_orders),
            'open_orders': len(self.get_open_orders()),
            'success_rate': (self.stats['orders_executed'] / max(self.stats['orders_created'], 1)) * 100
        })

        return stats

    def reset_statistics(self):
        """🔄 Сброс статистики"""
        self.stats = {
            'orders_created': 0,
            'orders_executed': 0,
            'orders_failed': 0,
            'orders_cancelled': 0,
            'total_fees': 0.0
        }

    def save_order(self, order: Order):
        """Сохранение ордера в репозиторий"""
        self.orders_repo.save(order)
        self.stats['orders_created'] += 1
