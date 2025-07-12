# infrastructure/repositories/orders_repository.py.new - ENHANCED для реальной торговли
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from domain.entities.order import Order
import json
import logging

logger = logging.getLogger(__name__)

class OrdersRepository(ABC):
    """
    🚀 РАСШИРЕННЫЙ интерфейс репозитория для ордеров с поддержкой биржевых операций
    """

    @abstractmethod
    def save(self, order: Order) -> None:
        """Сохранить ордер"""
        pass

    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Получить ордер по локальному ID"""
        pass

    @abstractmethod
    def get_by_exchange_id(self, exchange_id: str) -> Optional[Order]:
        """🆕 Получить ордер по ID биржи"""
        pass

    @abstractmethod
    def get_all_by_deal(self, deal_id: int) -> List[Order]:
        """Получить все ордера сделки"""
        pass

    @abstractmethod
    def get_all(self) -> List[Order]:
        """Получить все ордера"""
        pass

    @abstractmethod
    def get_open_orders(self) -> List[Order]:
        """🆕 Получить только открытые ордера"""
        pass

    @abstractmethod
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """🆕 Получить ордера по торговой паре"""
        pass

    @abstractmethod
    def get_orders_by_status(self, status: str) -> List[Order]:
        """🆕 Получить ордера по статусу"""
        pass

    @abstractmethod
    def get_pending_orders(self) -> List[Order]:
        """🆕 Получить ордера в ожидании размещения"""
        pass

    @abstractmethod
    def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """🆕 Получить ордера за период"""
        pass

    @abstractmethod
    def bulk_update_status(self, order_ids: List[int], status: str) -> int:
        """🆕 Массовое обновление статуса"""
        pass

    @abstractmethod
    def delete_old_orders(self, older_than_days: int) -> int:
        """🆕 Удаление старых ордеров"""
        pass


class InMemoryOrdersRepository(OrdersRepository):
    """
    🚀 РАСШИРЕННАЯ InMemory реализация с поддержкой всех новых методов
    Подходит для MVP, но в production нужна БД
    """

    def __init__(self, max_orders: int = 10000):
        self._storage: Dict[int, Order] = {}
        self._exchange_id_index: Dict[str, int] = {}  # exchange_id -> order_id
        self._symbol_index: Dict[str, List[int]] = {}  # symbol -> [order_ids]
        self._deal_index: Dict[int, List[int]] = {}    # deal_id -> [order_ids]
        self._status_index: Dict[str, List[int]] = {}  # status -> [order_ids]
        self.max_orders = max_orders

        # Статистика
        self.stats = {
            'total_saves': 0,
            'total_queries': 0,
            'index_rebuilds': 0
        }

    def save(self, order: Order) -> None:
        """Сохранить ордер с обновлением индексов"""
        try:
            # Проверяем лимит
            if len(self._storage) >= self.max_orders and order.order_id not in self._storage:
                self._cleanup_old_orders()

            # Удаляем старые индексы если ордер уже существует
            if order.order_id in self._storage:
                self._remove_from_indexes(self._storage[order.order_id])

            # Сохраняем ордер
            self._storage[order.order_id] = order

            # Обновляем индексы
            self._add_to_indexes(order)

            self.stats['total_saves'] += 1
            logger.debug(f"💾 Order {order.order_id} saved successfully")

        except Exception as e:
            logger.error(f"❌ Error saving order {order.order_id}: {e}")
            raise

    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Получить ордер по локальному ID"""
        self.stats['total_queries'] += 1
        return self._storage.get(order_id)

    def get_by_exchange_id(self, exchange_id: str) -> Optional[Order]:
        """🆕 Получить ордер по ID биржи"""
        self.stats['total_queries'] += 1
        order_id = self._exchange_id_index.get(exchange_id)
        if order_id:
            return self._storage.get(order_id)
        return None

    def get_all_by_deal(self, deal_id: int) -> List[Order]:
        """Получить все ордера сделки"""
        self.stats['total_queries'] += 1
        order_ids = self._deal_index.get(deal_id, [])
        return [self._storage[oid] for oid in order_ids if oid in self._storage]

    def get_all(self) -> List[Order]:
        """Получить все ордера"""
        self.stats['total_queries'] += 1
        return list(self._storage.values())

    def get_open_orders(self) -> List[Order]:
        """🆕 Получить только открытые ордера"""
        self.stats['total_queries'] += 1
        open_statuses = [Order.STATUS_OPEN, Order.STATUS_PARTIALLY_FILLED]
        orders = []
        for status in open_statuses:
            order_ids = self._status_index.get(status, [])
            orders.extend([self._storage[oid] for oid in order_ids if oid in self._storage])
        return orders

    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """🆕 Получить ордера по торговой паре"""
        self.stats['total_queries'] += 1
        order_ids = self._symbol_index.get(symbol, [])
        return [self._storage[oid] for oid in order_ids if oid in self._storage]

    def get_orders_by_status(self, status: str) -> List[Order]:
        """🆕 Получить ордера по статусу"""
        self.stats['total_queries'] += 1
        order_ids = self._status_index.get(status, [])
        return [self._storage[oid] for oid in order_ids if oid in self._storage]

    def get_pending_orders(self) -> List[Order]:
        """🆕 Получить ордера в ожидании размещения"""
        return self.get_orders_by_status(Order.STATUS_PENDING)

    def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """🆕 Получить ордера за период"""
        self.stats['total_queries'] += 1
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)

        orders = []
        for order in self._storage.values():
            if start_timestamp <= order.created_at <= end_timestamp:
                orders.append(order)

        return sorted(orders, key=lambda x: x.created_at, reverse=True)

    def bulk_update_status(self, order_ids: List[int], status: str) -> int:
        """🆕 Массовое обновление статуса"""
        updated_count = 0

        for order_id in order_ids:
            if order_id in self._storage:
                order = self._storage[order_id]
                old_status = order.status

                # Обновляем статус
                order.status = status
                order.last_update = int(datetime.now().timestamp() * 1000)

                # Обновляем индексы
                self._update_status_index(order, old_status, status)
                updated_count += 1

        logger.info(f"📊 Bulk updated {updated_count} orders to status {status}")
        return updated_count

    def delete_old_orders(self, older_than_days: int) -> int:
        """🆕 Удаление старых ордеров"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        cutoff_timestamp = int(cutoff_date.timestamp() * 1000)

        to_delete = []
        for order_id, order in self._storage.items():
            # Удаляем только закрытые старые ордера
            if (order.closed_at and order.closed_at < cutoff_timestamp) or \
               (not order.closed_at and order.created_at < cutoff_timestamp and order.is_closed()):
                to_delete.append(order_id)

        deleted_count = 0
        for order_id in to_delete:
            order = self._storage[order_id]
            self._remove_from_indexes(order)
            del self._storage[order_id]
            deleted_count += 1

        logger.info(f"🗑️ Deleted {deleted_count} old orders (older than {older_than_days} days)")
        return deleted_count

    # 🔧 МЕТОДЫ УПРАВЛЕНИЯ ИНДЕКСАМИ

    def _add_to_indexes(self, order: Order):
        """Добавляет ордер во все индексы"""
        # Exchange ID index
        if order.exchange_id:
            self._exchange_id_index[order.exchange_id] = order.order_id

        # Symbol index
        if order.symbol:
            if order.symbol not in self._symbol_index:
                self._symbol_index[order.symbol] = []
            if order.order_id not in self._symbol_index[order.symbol]:
                self._symbol_index[order.symbol].append(order.order_id)

        # Deal index
        if order.deal_id:
            if order.deal_id not in self._deal_index:
                self._deal_index[order.deal_id] = []
            if order.order_id not in self._deal_index[order.deal_id]:
                self._deal_index[order.deal_id].append(order.order_id)

        # Status index
        if order.status not in self._status_index:
            self._status_index[order.status] = []
        if order.order_id not in self._status_index[order.status]:
            self._status_index[order.status].append(order.order_id)

    def _remove_from_indexes(self, order: Order):
        """Удаляет ордер из всех индексов"""
        # Exchange ID index
        if order.exchange_id and order.exchange_id in self._exchange_id_index:
            del self._exchange_id_index[order.exchange_id]

        # Symbol index
        if order.symbol and order.symbol in self._symbol_index:
            if order.order_id in self._symbol_index[order.symbol]:
                self._symbol_index[order.symbol].remove(order.order_id)
            if not self._symbol_index[order.symbol]:
                del self._symbol_index[order.symbol]

        # Deal index
        if order.deal_id and order.deal_id in self._deal_index:
            if order.order_id in self._deal_index[order.deal_id]:
                self._deal_index[order.deal_id].remove(order.order_id)
            if not self._deal_index[order.deal_id]:
                del self._deal_index[order.deal_id]

        # Status index
        if order.status in self._status_index:
            if order.order_id in self._status_index[order.status]:
                self._status_index[order.status].remove(order.order_id)
            if not self._status_index[order.status]:
                del self._status_index[order.status]

    def _update_status_index(self, order: Order, old_status: str, new_status: str):
        """Обновляет индекс статусов при изменении статуса"""
        # Удаляем из старого статуса
        if old_status in self._status_index and order.order_id in self._status_index[old_status]:
            self._status_index[old_status].remove(order.order_id)
            if not self._status_index[old_status]:
                del self._status_index[old_status]

        # Добавляем в новый статус
        if new_status not in self._status_index:
            self._status_index[new_status] = []
        if order.order_id not in self._status_index[new_status]:
            self._status_index[new_status].append(order.order_id)

    def _cleanup_old_orders(self):
        """Очистка старых ордеров при достижении лимита"""
        if len(self._storage) < self.max_orders:
            return

        # Удаляем 10% самых старых закрытых ордеров
        closed_orders = []
        for order in self._storage.values():
            if order.is_closed():
                closed_orders.append((order.order_id, order.closed_at or order.created_at))

        # Сортируем по времени закрытия
        closed_orders.sort(key=lambda x: x[1])

        # Удаляем самые старые
        to_delete_count = max(1, len(closed_orders) // 10)
        for i in range(min(to_delete_count, len(closed_orders))):
            order_id = closed_orders[i][0]
            order = self._storage[order_id]
            self._remove_from_indexes(order)
            del self._storage[order_id]

        logger.info(f"🧹 Cleaned up {to_delete_count} old orders")

    def rebuild_indexes(self):
        """🔧 Перестроение всех индексов"""
        logger.info("🔧 Rebuilding orders indexes...")

        # Очищаем индексы
        self._exchange_id_index.clear()
        self._symbol_index.clear()
        self._deal_index.clear()
        self._status_index.clear()

        # Перестраиваем
        for order in self._storage.values():
            self._add_to_indexes(order)

        self.stats['index_rebuilds'] += 1
        logger.info("✅ Orders indexes rebuilt successfully")

    # 📊 СТАТИСТИКА И МОНИТОРИНГ

    def get_statistics(self) -> Dict[str, Any]:
        """📊 Получение статистики репозитория"""
        total_orders = len(self._storage)

        # Группировка по статусам
        status_counts = {}
        for status, order_ids in self._status_index.items():
            status_counts[status] = len(order_ids)

        # Группировка по символам
        symbol_counts = {}
        for symbol, order_ids in self._symbol_index.items():
            symbol_counts[symbol] = len(order_ids)

        return {
            'total_orders': total_orders,
            'max_orders': self.max_orders,
            'usage_percent': (total_orders / self.max_orders) * 100,
            'status_distribution': status_counts,
            'symbol_distribution': symbol_counts,
            'total_deals': len(self._deal_index),
            'orders_with_exchange_id': len(self._exchange_id_index),
            'performance_stats': self.stats.copy()
        }

    def export_to_json(self, file_path: str = None) -> str:
        """💾 Экспорт всех ордеров в JSON"""
        orders_data = []
        for order in self._storage.values():
            orders_data.append(order.to_dict())

        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_orders': len(orders_data),
            'orders': orders_data,
            'statistics': self.get_statistics()
        }

        json_data = json.dumps(export_data, indent=2, default=str)

        if file_path:
            with open(file_path, 'w') as f:
                f.write(json_data)
            logger.info(f"📁 Orders exported to {file_path}")

        return json_data

    def import_from_json(self, json_data: str = None, file_path: str = None) -> int:
        """📥 Импорт ордеров из JSON"""
        try:
            if file_path:
                with open(file_path, 'r') as f:
                    json_data = f.read()

            if not json_data:
                raise ValueError("No JSON data provided")

            data = json.loads(json_data)
            orders_data = data.get('orders', [])

            imported_count = 0
            for order_dict in orders_data:
                try:
                    order = Order.from_dict(order_dict)
                    self.save(order)
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Failed to import order: {e}")

            logger.info(f"📥 Imported {imported_count} orders")
            return imported_count

        except Exception as e:
            logger.error(f"❌ Error importing orders: {e}")
            return 0

    # 🔍 РАСШИРЕННЫЕ ПОИСКОВЫЕ МЕТОДЫ

    def search_orders(
        self,
        symbol: str = None,
        status: str = None,
        deal_id: int = None,
        exchange_id: str = None,
        side: str = None,
        order_type: str = None,
        min_amount: float = None,
        max_amount: float = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = None
    ) -> List[Order]:
        """🔍 Комплексный поиск ордеров по множественным критериям"""
        self.stats['total_queries'] += 1

        # Начинаем со всех ордеров
        candidates = list(self._storage.values())

        # Применяем фильтры
        if symbol:
            candidates = [o for o in candidates if o.symbol == symbol]
        if status:
            candidates = [o for o in candidates if o.status == status]
        if deal_id:
            candidates = [o for o in candidates if o.deal_id == deal_id]
        if exchange_id:
            candidates = [o for o in candidates if o.exchange_id == exchange_id]
        if side:
            candidates = [o for o in candidates if o.side == side]
        if order_type:
            candidates = [o for o in candidates if o.order_type == order_type]
        if min_amount:
            candidates = [o for o in candidates if o.amount >= min_amount]
        if max_amount:
            candidates = [o for o in candidates if o.amount <= max_amount]

        # Фильтр по дате
        if date_from:
            from_timestamp = int(date_from.timestamp() * 1000)
            candidates = [o for o in candidates if o.created_at >= from_timestamp]
        if date_to:
            to_timestamp = int(date_to.timestamp() * 1000)
            candidates = [o for o in candidates if o.created_at <= to_timestamp]

        # Сортируем по времени создания (новые первые)
        candidates.sort(key=lambda x: x.created_at, reverse=True)

        # Применяем лимит
        if limit:
            candidates = candidates[:limit]

        return candidates

    def get_orders_with_errors(self) -> List[Order]:
        """⚠️ Получить ордера с ошибками"""
        orders_with_errors = []
        for order in self._storage.values():
            if order.error_message or order.status == Order.STATUS_FAILED:
                orders_with_errors.append(order)
        return orders_with_errors

    def get_orders_requiring_sync(self) -> List[Order]:
        """🔄 Получить ордера требующие синхронизации с биржей"""
        sync_required = []
        current_time = int(datetime.now().timestamp() * 1000)

        for order in self._storage.values():
            # Ордера открытые более 5 минут без обновлений
            if (order.is_open() and
                order.exchange_id and
                current_time - order.last_update > 5 * 60 * 1000):
                sync_required.append(order)

        return sync_required
