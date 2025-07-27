# tests/ccxt_compliance/test_ccxt_integration.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.infrastructure.connectors.ccxt_exchange_connector import CCXTExchangeConnector
from src.domain.services.orders.ccxt_order_execution_service import CCXTOrderExecutionService
from src.infrastructure.repositories.postgresql.postgresql_orders_repository_ccxt import PostgreSQLOrdersRepositoryCCXT
from src.domain.entities.order import Order


class TestCCXTIntegration:
    """
    🚀 CCXT Integration Tests
    
    Интеграционные тесты проверяют работу всех CCXT-совместимых компонентов вместе.
    Проверяется полный цикл создания, размещения и синхронизации ордеров.
    """

    @pytest.fixture
    def mock_pool(self):
        """Мок пула PostgreSQL соединений"""
        pool = AsyncMock()
        conn = AsyncMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        return pool, conn

    @pytest.fixture
    def mock_config(self):
        """Мок конфигурации"""
        return {
            'binance': {
                'production': {
                    'apiKey': 'test_api_key',
                    'secret': 'test_secret'
                }
            }
        }

    @pytest.fixture
    async def ccxt_system(self, mock_pool, mock_config):
        """Полная CCXT система"""
        pool, conn = mock_pool
        
        # Мокируем CCXT клиенты
        rest_client = AsyncMock()
        stream_client = AsyncMock()
        
        with patch('ccxt.binance', return_value=rest_client):
            with patch('ccxt.pro.binance', return_value=stream_client):
                with patch('src.infrastructure.connectors.ccxt_exchange_connector.load_config', return_value=mock_config):
                    
                    # Создаем компоненты
                    exchange_connector = CCXTExchangeConnector('binance', use_sandbox=False)
                    orders_repository = PostgreSQLOrdersRepositoryCCXT(pool)
                    execution_service = CCXTOrderExecutionService(
                        exchange_connector=exchange_connector,
                        orders_repository=orders_repository
                    )
                    
                    yield {
                        'exchange_connector': exchange_connector,
                        'orders_repository': orders_repository,
                        'execution_service': execution_service,
                        'rest_client': rest_client,
                        'stream_client': stream_client,
                        'db_conn': conn
                    }

    @pytest.mark.asyncio
    async def test_full_order_lifecycle_integration(self, ccxt_system):
        """Тест полного жизненного цикла ордера через CCXT систему"""
        components = ccxt_system
        
        # Настраиваем моки для полного цикла
        ccxt_order_response = {
            'id': '12345',
            'clientOrderId': 'autotrade_test',
            'datetime': '2024-01-15T10:30:00.000Z',
            'timestamp': 1705315800000,
            'status': 'open',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'price': 50000.0,
            'amount': 0.001,
            'filled': 0.0,
            'remaining': 0.001,
            'cost': None,
            'average': None,
            'trades': [],
            'fee': {'cost': 0.0, 'currency': 'USDT', 'rate': None},
            'info': {}
        }
        
        # Мокируем методы биржи
        components['rest_client'].create_order.return_value = ccxt_order_response
        
        # Мокируем сохранение в БД
        components['db_conn'].execute.return_value = "INSERT 0 1"
        components['db_conn'].fetchrow.return_value = None  # Order не существует
        
        # Тестируем создание ордера
        result = await components['execution_service'].execute_ccxt_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=50000.0
        )
        
        # Проверяем успешное выполнение
        assert result.success is True
        assert result.order is not None
        assert result.order.id == '12345'
        assert result.order.symbol == 'BTC/USDT'
        assert result.order.status == 'open'
        
        # Проверяем вызовы
        components['rest_client'].create_order.assert_called_once()
        components['db_conn'].execute.assert_called()  # Сохранение в БД

    @pytest.mark.asyncio
    async def test_order_synchronization_integration(self, ccxt_system):
        """Тест синхронизации ордера с биржей"""
        components = ccxt_system
        
        # Создаем ордер
        order = Order(
            id='12345',
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=50000.0,
            status='open'
        )
        
        # Обновленные данные с биржи
        updated_ccxt_response = {
            'id': '12345',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'amount': 0.001,
            'price': 50000.0,
            'filled': 0.0005,
            'remaining': 0.0005,
            'status': 'partial',
            'cost': 25.0,
            'average': 50000.0,
            'trades': [
                {
                    'id': 'trade1',
                    'timestamp': 1705315850000,
                    'amount': 0.0005,
                    'price': 50000.0,
                    'cost': 25.0
                }
            ],
            'fee': {'cost': 0.025, 'currency': 'USDT'},
            'info': {},
            'datetime': '2024-01-15T10:30:00.000Z',
            'timestamp': 1705315800000
        }
        
        # Мокируем fetch_order
        components['rest_client'].fetch_order.return_value = updated_ccxt_response
        
        # Мокируем обновление в БД
        components['db_conn'].execute.return_value = "UPDATE 1"
        
        # Синхронизируем ордер
        synced_order = await components['execution_service'].sync_order_with_exchange(order)
        
        # Проверяем обновление
        assert synced_order.filled == 0.0005
        assert synced_order.remaining == 0.0005
        assert synced_order.cost == 25.0
        assert synced_order.average == 50000.0
        assert len(synced_order.trades) == 1
        assert synced_order.fee['cost'] == 0.025

    @pytest.mark.asyncio
    async def test_balance_check_integration(self, ccxt_system):
        """Тест интеграции проверки баланса"""
        components = ccxt_system
        
        # Мокируем markets
        markets = {
            'BTC/USDT': {
                'base': 'BTC',
                'quote': 'USDT',
                'limits': {
                    'amount': {'min': 0.00001},
                    'price': {'min': 0.01},
                    'cost': {'min': 10}
                }
            }
        }
        
        # Мокируем balance
        balance = {
            'BTC': {'free': 1.0, 'used': 0.0, 'total': 1.0},
            'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0}
        }
        
        components['rest_client'].load_markets.return_value = markets
        components['rest_client'].fetch_balance.return_value = balance
        
        # Проверяем баланс для покупки
        has_balance, currency, available = await components['exchange_connector'].check_sufficient_balance(
            'BTC/USDT', 'buy', 0.001, 50000.0
        )
        
        assert has_balance is True
        assert currency == 'USDT'
        assert available == 10000.0
        
        # Проверяем недостаточный баланс
        has_balance, currency, available = await components['exchange_connector'].check_sufficient_balance(
            'BTC/USDT', 'buy', 1.0, 50000.0  # Требует 50000 USDT
        )
        
        assert has_balance is False
        assert currency == 'USDT'

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, ccxt_system):
        """Тест интеграции обработки ошибок"""
        components = ccxt_system
        
        import ccxt
        
        # Тестируем InsufficientFunds
        components['rest_client'].create_order.side_effect = ccxt.InsufficientFunds("Insufficient balance")
        
        result = await components['execution_service'].execute_ccxt_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=50000.0
        )
        
        # Проверяем обработку ошибки
        assert result.success is False
        assert 'Insufficient' in result.error_message
        
        # Проверяем, что ордер был помечен как failed
        if result.order:
            assert result.order.status == Order.STATUS_REJECTED
            assert result.order.error_message is not None

    @pytest.mark.asyncio
    async def test_database_persistence_integration(self, ccxt_system):
        """Тест интеграции с базой данных"""
        components = ccxt_system
        
        # Создаем ордер
        order = Order(
            id='12345',
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=50000.0,
            status='open'
        )
        
        # Мокируем сохранение
        components['db_conn'].execute.return_value = "INSERT 0 1"
        
        # Тестируем сохранение
        success = await components['orders_repository'].save_order(order)
        assert success is True
        
        # Проверяем вызов БД
        components['db_conn'].execute.assert_called()
        
        # Мокируем получение ордера
        mock_row = {
            'id': '12345',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'amount': 0.001,
            'price': 50000.0,
            'status': 'open',
            'filled': 0.0,
            'remaining': 0.001,
            'cost': None,
            'average': None,
            'trades': '[]',
            'fee': '{}',
            'info': '{}',
            'metadata': '{}',
            'client_order_id': None,
            'datetime': '2024-01-15T10:30:00.000Z',
            'timestamp': 1705315800000,
            'last_trade_timestamp': None,
            'time_in_force': 'GTC',
            'deal_id': None,
            'local_order_id': 1001,
            'created_at': '2024-01-15T10:30:00.000Z',
            'updated_at': '2024-01-15T10:30:00.000Z',
            'error_message': None,
            'retries': 0
        }
        
        components['db_conn'].fetchrow.return_value = mock_row
        
        # Тестируем получение
        retrieved_order = await components['orders_repository'].get_order('12345')
        
        assert retrieved_order is not None
        assert retrieved_order.id == '12345'
        assert retrieved_order.symbol == 'BTC/USDT'

    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(self, ccxt_system):
        """Тест интеграции конкурентных операций"""
        components = ccxt_system
        
        # Мокируем ответы для множественных ордеров
        def create_order_side_effect(*args, **kwargs):
            return {
                'id': f'order_{len(components["rest_client"].create_order.call_args_list)}',
                'symbol': kwargs.get('symbol', 'BTC/USDT'),
                'type': kwargs.get('type', 'limit'),
                'side': kwargs.get('side', 'buy'),
                'amount': kwargs.get('amount', 0.001),
                'price': kwargs.get('price', 50000.0),
                'status': 'open',
                'filled': 0.0,
                'remaining': kwargs.get('amount', 0.001),
                'datetime': '2024-01-15T10:30:00.000Z',
                'timestamp': 1705315800000,
                'trades': [],
                'fee': {'cost': 0.0, 'currency': 'USDT'},
                'info': {}
            }
        
        components['rest_client'].create_order.side_effect = create_order_side_effect
        components['db_conn'].execute.return_value = "INSERT 0 1"
        components['db_conn'].fetchrow.return_value = None
        
        # Создаем несколько ордеров одновременно
        tasks = []
        for i in range(3):
            task = components['execution_service'].execute_ccxt_order(
                symbol='BTC/USDT',
                type='limit',
                side='buy',
                amount=0.001,
                price=50000.0 + i * 100  # Разные цены
            )
            tasks.append(task)
        
        # Выполняем одновременно
        results = await asyncio.gather(*tasks)
        
        # Проверяем результаты
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.success is True
            assert result.order.id == f'order_{i+1}'
            assert result.order.price == 50000.0 + i * 100

    @pytest.mark.asyncio
    async def test_streaming_integration(self, ccxt_system):
        """Тест интеграции streaming данных"""
        components = ccxt_system
        
        # Мокируем streaming данные
        mock_ticker = {
            'symbol': 'BTC/USDT',
            'timestamp': 1705315800000,
            'datetime': '2024-01-15T10:30:00.000Z',
            'last': 50000.0,
            'bid': 49990.0,
            'ask': 50010.0,
            'high': 51000.0,
            'low': 49000.0,
            'baseVolume': 1000.0,
            'quoteVolume': 50000000.0,
            'info': {}
        }
        
        components['stream_client'].watch_ticker.return_value = mock_ticker
        
        # Тестируем получение streaming данных
        ticker = await components['exchange_connector'].watch_ticker('BTC/USDT')
        
        assert ticker['symbol'] == 'BTC/USDT'
        assert ticker['last'] == 50000.0
        assert 'timestamp' in ticker
        assert 'datetime' in ticker

    @pytest.mark.asyncio
    async def test_trading_strategy_integration(self, ccxt_system):
        """Тест интеграции торговой стратегии"""
        components = ccxt_system
        
        # Имитируем результат стратегии
        strategy_result = (
            50000.0,  # buy_price
            0.001,    # buy_amount
            50750.0,  # sell_price (1.5% профит)
            0.001,    # sell_amount
            {'signal_strength': 0.8}  # info
        )
        
        # Создаем mock CurrencyPair
        from src.domain.entities.currency_pair import CurrencyPair
        currency_pair = CurrencyPair(
            base_currency='BTC',
            quote_currency='USDT',
            symbol='BTC/USDT',
            deal_quota=100.0,
            profit_markup=0.015
        )
        
        # Мокируем создание BUY ордера
        buy_order_response = {
            'id': 'buy_12345',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'amount': 0.001,
            'price': 50000.0,
            'status': 'open',
            'filled': 0.0,
            'remaining': 0.001,
            'datetime': '2024-01-15T10:30:00.000Z',
            'timestamp': 1705315800000,
            'trades': [],
            'fee': {'cost': 0.0, 'currency': 'USDT'},
            'info': {}
        }
        
        components['rest_client'].create_order.return_value = buy_order_response
        components['db_conn'].execute.return_value = "INSERT 0 1"
        components['db_conn'].fetchrow.return_value = None
        
        # Выполняем стратегию
        result = await components['execution_service'].execute_trading_strategy(
            currency_pair=currency_pair,
            strategy_result=strategy_result
        )
        
        # Проверяем результат
        assert result.success is True
        assert result.buy_order is not None
        assert result.sell_order is not None
        assert result.buy_order.price == 50000.0
        assert result.sell_order.price == 50750.0
        assert result.expected_profit > 0

    @pytest.mark.asyncio 
    async def test_system_health_integration(self, ccxt_system):
        """Тест интеграции проверки здоровья системы"""
        components = ccxt_system
        
        # Мокируем health check компонентов
        components['rest_client'].fetch_balance.return_value = {'BTC': {'free': 1.0}}
        components['db_conn'].fetchval.side_effect = [1, 10, 5]  # connection, total_orders, active_orders
        
        # Проверяем здоровье exchange connector
        exchange_info = components['exchange_connector'].get_exchange_info()
        assert exchange_info['has_rest_client'] is True
        assert exchange_info['has_stream_client'] is True
        
        # Проверяем здоровье orders repository
        repo_health = await components['orders_repository'].health_check()
        assert repo_health['status'] == 'healthy'
        assert 'total_orders' in repo_health
        
        # Проверяем здоровье execution service
        exec_report = await components['execution_service'].get_execution_report()
        assert 'execution_stats' in exec_report
        assert 'system_health' in exec_report

    @pytest.mark.asyncio
    async def test_cleanup_integration(self, ccxt_system):
        """Тест интеграции cleanup операций"""
        components = ccxt_system
        
        # Тестируем emergency cancel
        components['db_conn'].fetch.return_value = [
            {
                'id': 'order1',
                'symbol': 'BTC/USDT',
                'status': 'open',
                'client_order_id': None,
                'datetime': '2024-01-15T10:30:00.000Z',
                'timestamp': 1705315800000,
                'last_trade_timestamp': None,
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
                'created_at': '2024-01-15T10:30:00.000Z',
                'updated_at': '2024-01-15T10:30:00.000Z',
                'error_message': None,
                'retries': 0,
                'metadata': '{}'
            }
        ]
        
        components['rest_client'].cancel_order.return_value = {
            'id': 'order1',
            'status': 'canceled'
        }
        components['db_conn'].execute.return_value = "UPDATE 1"
        
        # Выполняем emergency cancel
        cancelled_count = await components['execution_service'].emergency_cancel_all_orders()
        
        assert cancelled_count == 1
        components['rest_client'].cancel_order.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])