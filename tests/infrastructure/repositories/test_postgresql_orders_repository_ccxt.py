# tests/infrastructure/repositories/test_postgresql_orders_repository_ccxt.py
import pytest
import asyncio
import asyncpg
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.domain.entities.order import Order
from src.infrastructure.repositories.postgresql.postgresql_orders_repository_ccxt import PostgreSQLOrdersRepositoryCCXT


class TestPostgreSQLOrdersRepositoryCCXT:
    """
    🚀 Тесты для CCXT-совместимого PostgreSQL Orders Repository
    """

    @pytest.fixture
    async def mock_pool(self):
        """Мок пула соединений"""
        pool = AsyncMock()
        conn = AsyncMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        return pool, conn

    @pytest.fixture
    def sample_order(self):
        """Образец CCXT-совместимого ордера"""
        return Order(
            id="12345",
            clientOrderId="client_123",
            datetime="2024-01-15T10:30:00.000Z",
            timestamp=1705315800000,
            lastTradeTimestamp=None,
            status=Order.STATUS_OPEN,
            symbol="BTC/USDT",
            type=Order.TYPE_LIMIT,
            timeInForce=Order.TIF_GTC,
            side=Order.SIDE_BUY,
            price=50000.0,
            amount=0.001,
            filled=0.0,
            remaining=0.001,
            cost=None,
            average=None,
            trades=[],
            fee={'cost': 0.0, 'currency': 'USDT', 'rate': None},
            info={},
            deal_id=1,
            local_order_id=1001,
            created_at=1705315800000,
            last_update=1705315800000,
            error_message=None,
            retries=0,
            metadata={}
        )

    @pytest.fixture
    def repository(self, mock_pool):
        """Репозиторий с мок пулом"""
        pool, conn = mock_pool
        return PostgreSQLOrdersRepositoryCCXT(pool), conn

    def test_order_to_db_values_conversion(self, repository, sample_order):
        """Тест конвертации Order в значения для БД"""
        repo, _ = repository
        values = repo._order_to_db_values(sample_order)
        
        # Проверяем, что все значения присутствуют
        assert len(values) == 26  # 26 полей в insert
        assert values[0] == "12345"  # id
        assert values[6] == "BTC/USDT"  # symbol
        assert values[9] == "buy"  # side
        assert str(values[11]) == "50000.0"  # price as Decimal
        assert str(values[12]) == "0.001"  # amount as Decimal
        
    def test_row_to_order_conversion(self, repository):
        """Тест конвертации строки БД в Order"""
        repo, _ = repository
        
        # Мок строки из БД
        mock_row = {
            'id': '12345',
            'client_order_id': 'client_123',
            'datetime': datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            'timestamp': 1705315800000,
            'last_trade_timestamp': None,
            'status': 'open',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'time_in_force': 'GTC',
            'side': 'buy',
            'price': 50000.0,
            'amount': 0.001,
            'filled': 0.0,
            'remaining': 0.001,
            'cost': None,
            'average': None,
            'trades': '[]',
            'fee': '{"cost": 0.0, "currency": "USDT", "rate": null}',
            'info': '{}',
            'deal_id': '1',
            'local_order_id': 1001,
            'created_at': datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            'updated_at': datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            'error_message': None,
            'retries': 0,
            'metadata': '{}'
        }
        
        order = repo._row_to_order(mock_row)
        
        assert order.id == "12345"
        assert order.symbol == "BTC/USDT"
        assert order.side == "buy"
        assert order.price == 50000.0
        assert order.amount == 0.001
        assert order.status == "open"
        assert order.deal_id == 1
        assert order.local_order_id == 1001

    def test_json_fields_round_trip(self, repository, sample_order):
        """Проверяем сериализацию и десериализацию JSONB полей"""
        repo, _ = repository

        values = repo._order_to_db_values(sample_order)
        row = {
            'id': values[0],
            'client_order_id': values[1],
            'datetime': datetime.fromisoformat(sample_order.datetime.replace('Z', '+00:00')),
            'timestamp': values[3],
            'last_trade_timestamp': values[4],
            'status': values[5],
            'symbol': values[6],
            'type': values[7],
            'time_in_force': values[8],
            'side': values[9],
            'price': values[10],
            'amount': values[11],
            'filled': values[12],
            'remaining': values[13],
            'cost': values[14],
            'average': values[15],
            'trades': values[16],
            'fee': values[17],
            'info': values[18],
            'deal_id': str(sample_order.deal_id),
            'local_order_id': values[20],
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'error_message': None,
            'retries': 0,
            'metadata': values[-1],
        }

        loaded = repo._row_to_order(row)
        assert loaded.trades == sample_order.trades
        assert loaded.fee == sample_order.fee
        assert loaded.info == sample_order.info
        assert loaded.metadata == sample_order.metadata

    @pytest.mark.asyncio
    async def test_save_order_new(self, repository, sample_order):
        """Тест сохранения нового ордера"""
        repo, conn = repository
        
        # Настраиваем моки
        conn.fetchrow.return_value = None  # Ордер не существует
        conn.execute.return_value = "INSERT 0 1"
        
        result = await repo.save_order(sample_order)
        
        assert result is True
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_order_update_existing(self, repository, sample_order):
        """Тест обновления существующего ордера"""
        repo, conn = repository
        
        # Настраиваем моки - ордер существует
        conn.fetchrow.return_value = {'id': '12345', 'symbol': 'BTC/USDT'}
        conn.execute.return_value = "UPDATE 1"
        
        result = await repo.save_order(sample_order)
        
        assert result is True
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_order_by_id(self, repository, sample_order):
        """Тест получения ордера по ID"""
        repo, conn = repository
        
        # Настраиваем мок возврата
        mock_row = {
            'id': '12345',
            'client_order_id': 'client_123',
            'datetime': datetime.now(timezone.utc),
            'timestamp': 1705315800000,
            'last_trade_timestamp': None,
            'status': 'open',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'time_in_force': 'GTC',
            'side': 'buy',
            'price': 50000.0,
            'amount': 0.001,
            'filled': 0.0,
            'remaining': 0.001,
            'cost': None,
            'average': None,
            'trades': '[]',
            'fee': '{}',
            'info': '{}',
            'deal_id': None,
            'local_order_id': 1001,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'error_message': None,
            'retries': 0,
            'metadata': '{}'
        }
        
        conn.fetchrow.return_value = mock_row
        
        order = await repo.get_order("12345")
        
        assert order is not None
        assert order.id == "12345"
        assert order.symbol == "BTC/USDT"
        conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, repository):
        """Тест получения несуществующего ордера"""
        repo, conn = repository
        
        conn.fetchrow.return_value = None
        
        order = await repo.get_order("nonexistent")
        
        assert order is None

    @pytest.mark.asyncio
    async def test_get_active_orders(self, repository):
        """Тест получения активных ордеров"""
        repo, conn = repository
        
        mock_rows = [
            {
                'id': '1',
                'status': 'open',
                'symbol': 'BTC/USDT',
                'side': 'buy',
                'price': 50000.0,
                'amount': 0.001,
                'filled': 0.0,
                'remaining': 0.001,
                'trades': '[]',
                'fee': '{}',
                'info': '{}',
                'metadata': '{}',
                'client_order_id': None,
                'datetime': datetime.now(timezone.utc),
                'timestamp': 1705315800000,
                'last_trade_timestamp': None,
                'type': 'limit',
                'time_in_force': 'GTC',
                'cost': None,
                'average': None,
                'deal_id': None,
                'local_order_id': 1001,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'error_message': None,
                'retries': 0
            }
        ]
        
        conn.fetch.return_value = mock_rows
        
        orders = await repo.get_active_orders()
        
        assert len(orders) == 1
        assert orders[0].status == "open"

    @pytest.mark.asyncio
    async def test_count_active_orders(self, repository):
        """Тест подсчета активных ордеров"""
        repo, conn = repository
        
        conn.fetchval.return_value = 5
        
        count = await repo.count_active_orders()
        
        assert count == 5
        conn.fetchval.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_order(self, repository):
        """Тест удаления ордера (мягкое удаление)"""
        repo, conn = repository
        
        conn.execute.return_value = "UPDATE 1"
        
        result = await repo.delete_order("12345")
        
        assert result is True
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_orders_by_symbol(self, repository):
        """Тест получения ордеров по символу"""
        repo, conn = repository
        
        conn.fetch.return_value = []
        
        orders = await repo.get_orders_by_symbol("BTC/USDT")
        
        assert orders == []
        conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, repository):
        """Тест проверки здоровья - успешный случай"""
        repo, conn = repository
        
        # Настраиваем моки
        conn.fetchval.side_effect = [1, 100, 5]  # connection test, total_orders, active_orders
        repo.pool.get_size.return_value = 10
        repo.pool.get_busy_size.return_value = 3
        
        health = await repo.health_check()
        
        assert health['status'] == 'healthy'
        assert health['total_orders'] == 100
        assert health['active_orders'] == 5
        assert health['connection_pool_size'] == 10
        assert health['connection_pool_free'] == 7

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, repository):
        """Тест проверки здоровья - ошибка"""
        repo, conn = repository
        
        conn.fetchval.side_effect = Exception("Database error")
        
        health = await repo.health_check()
        
        assert health['status'] == 'unhealthy'
        assert 'error' in health

    @pytest.mark.asyncio
    async def test_get_order_statistics(self, repository):
        """Тест получения статистики ордеров"""
        repo, conn = repository
        
        mock_stats = [
            {
                'status': 'open',
                'side': 'buy',
                'count': 10,
                'total_cost': 500000.0,
                'avg_cost': 50000.0
            },
            {
                'status': 'closed',
                'side': 'sell', 
                'count': 5,
                'total_cost': 250000.0,
                'avg_cost': 50000.0
            }
        ]
        
        conn.fetch.return_value = mock_stats
        
        stats = await repo.get_order_statistics()
        
        assert 'open_buy' in stats
        assert 'closed_sell' in stats
        assert stats['open_buy']['count'] == 10
        assert stats['closed_sell']['count'] == 5

    @pytest.mark.asyncio
    async def test_save_orders_batch(self, repository, sample_order):
        repo, conn = repository

        conn.fetchrow.return_value = None
        conn.execute.return_value = "INSERT 0 1"

        result = await repo.save_orders_batch([sample_order])

        assert result == 1
        assert conn.execute.call_count == 1

    def test_validate_ccxt_compliance(self, sample_order):
        """Тест валидации CCXT соответствия"""
        is_valid, errors = sample_order.validate_ccxt_compliance()
        
        assert is_valid is True
        assert len(errors) == 0

    def test_ccxt_dict_conversion(self, sample_order):
        """Тест конвертации в CCXT словарь"""
        ccxt_dict = sample_order.to_ccxt_dict()
        
        # Проверяем наличие всех CCXT полей
        required_fields = [
            'id', 'clientOrderId', 'datetime', 'timestamp', 'status',
            'symbol', 'type', 'side', 'amount', 'price', 'filled',
            'remaining', 'cost', 'average', 'trades', 'fee', 'info'
        ]
        
        for field in required_fields:
            assert field in ccxt_dict

    def test_from_ccxt_response(self):
        """Тест создания Order из CCXT ответа"""
        ccxt_response = {
            'id': '12345',
            'clientOrderId': 'client_123',
            'datetime': '2024-01-15T10:30:00.000Z',
            'timestamp': 1705315800000,
            'status': 'open',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'amount': 0.001,
            'price': 50000.0,
            'filled': 0.0,
            'remaining': 0.001,
            'cost': None,
            'average': None,
            'trades': [],
            'fee': {'cost': 0.0, 'currency': 'USDT', 'rate': None},
            'info': {}
        }
        
        order = Order.from_ccxt_response(ccxt_response, deal_id=1)
        
        assert order.id == '12345'
        assert order.symbol == 'BTC/USDT'
        assert order.deal_id == 1
        assert order.status == 'open'


if __name__ == "__main__":
    pytest.main([__file__])