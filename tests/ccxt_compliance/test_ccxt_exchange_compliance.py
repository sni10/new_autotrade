# tests/ccxt_compliance/test_ccxt_exchange_compliance.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.infrastructure.connectors.ccxt_exchange_connector import CCXTExchangeConnector


class TestCCXTExchangeCompliance:
    """
    🚀 CCXT Exchange Connector Compliance Tests
    
    Тесты проверяют полное соответствие Exchange Connector стандарту CCXT Unified API.
    Проверяются форматы запросов, ответов и методы согласно CCXT спецификации.
    """

    @pytest.fixture
    def mock_ccxt_clients(self):
        """Мокированные CCXT клиенты"""
        rest_client = AsyncMock()
        stream_client = AsyncMock()
        
        # Мокируем методы создания клиентов
        with patch('ccxt.binance', return_value=rest_client):
            with patch('ccxt.pro.binance', return_value=stream_client):
                yield rest_client, stream_client

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
    async def connector(self, mock_ccxt_clients, mock_config):
        """CCXT коннектор с мокированными клиентами"""
        rest_client, stream_client = mock_ccxt_clients
        
        with patch('src.infrastructure.connectors.ccxt_exchange_connector.load_config', return_value=mock_config):
            connector = CCXTExchangeConnector('binance', use_sandbox=False)
            yield connector, rest_client, stream_client

    def test_ccxt_unified_api_methods_exist(self, connector):
        """Проверка наличия всех методов CCXT Unified API"""
        connector_instance, _, _ = connector
        
        # Market Data methods
        assert hasattr(connector_instance, 'load_markets')
        assert hasattr(connector_instance, 'fetch_ticker')
        assert hasattr(connector_instance, 'fetch_order_book')
        assert hasattr(connector_instance, 'fetch_trades')
        assert hasattr(connector_instance, 'fetch_ohlcv')
        
        # Trading methods
        assert hasattr(connector_instance, 'create_order')
        assert hasattr(connector_instance, 'cancel_order')
        assert hasattr(connector_instance, 'fetch_order')
        assert hasattr(connector_instance, 'fetch_orders')
        assert hasattr(connector_instance, 'fetch_open_orders')
        assert hasattr(connector_instance, 'fetch_closed_orders')
        
        # Account methods
        assert hasattr(connector_instance, 'fetch_balance')
        
        # Streaming methods
        assert hasattr(connector_instance, 'watch_ticker')
        assert hasattr(connector_instance, 'watch_order_book')
        assert hasattr(connector_instance, 'watch_trades')
        assert hasattr(connector_instance, 'watch_ohlcv')

    @pytest.mark.asyncio
    async def test_load_markets_ccxt_compliance(self, connector):
        """Тест load_markets на соответствие CCXT"""
        connector_instance, rest_client, _ = connector
        
        # CCXT markets structure
        ccxt_markets = {
            'BTC/USDT': {
                'id': 'BTCUSDT',
                'symbol': 'BTC/USDT',
                'base': 'BTC',
                'quote': 'USDT',
                'baseId': 'BTC',
                'quoteId': 'USDT',
                'active': True,
                'type': 'spot',
                'spot': True,
                'margin': False,
                'future': False,
                'swap': False,
                'option': False,
                'contract': False,
                'precision': {'amount': 8, 'price': 2},
                'limits': {
                    'amount': {'min': 0.00001, 'max': 1000},
                    'price': {'min': 0.01, 'max': 1000000},
                    'cost': {'min': 10}
                },
                'maker': 0.001,
                'taker': 0.001,
                'info': {}
            }
        }
        
        rest_client.load_markets.return_value = ccxt_markets
        
        # Тестируем
        markets = await connector_instance.load_markets()
        
        # Проверяем CCXT compliance
        assert isinstance(markets, dict)
        assert 'BTC/USDT' in markets
        
        market = markets['BTC/USDT']
        required_fields = ['id', 'symbol', 'base', 'quote', 'active', 'precision', 'limits']
        for field in required_fields:
            assert field in market
        
        rest_client.load_markets.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_ticker_ccxt_compliance(self, connector):
        """Тест fetch_ticker на соответствие CCXT"""
        connector_instance, rest_client, _ = connector
        
        # CCXT ticker structure
        ccxt_ticker = {
            'symbol': 'BTC/USDT',
            'timestamp': 1705315800000,
            'datetime': '2024-01-15T10:30:00.000Z',
            'high': 51000.0,
            'low': 49000.0,
            'bid': 49900.0,
            'bidVolume': 1.5,
            'ask': 50100.0,
            'askVolume': 2.0,
            'vwap': 50000.0,
            'open': 50000.0,
            'close': 50000.0,
            'last': 50000.0,
            'previousClose': 49800.0,
            'change': 200.0,
            'percentage': 0.4,
            'average': 50000.0,
            'baseVolume': 1000.0,
            'quoteVolume': 50000000.0,
            'info': {}
        }
        
        rest_client.fetch_ticker.return_value = ccxt_ticker
        
        # Тестируем
        ticker = await connector_instance.fetch_ticker('BTC/USDT')
        
        # Проверяем CCXT compliance
        required_fields = ['symbol', 'timestamp', 'datetime', 'last', 'bid', 'ask']
        for field in required_fields:
            assert field in ticker
        
        assert ticker['symbol'] == 'BTC/USDT'
        assert isinstance(ticker['timestamp'], int)
        assert ticker['datetime'].endswith('Z')
        
        rest_client.fetch_ticker.assert_called_once_with('BTC/USDT')

    @pytest.mark.asyncio
    async def test_create_order_ccxt_compliance(self, connector):
        """Тест create_order на соответствие CCXT"""
        connector_instance, rest_client, _ = connector
        
        # CCXT order response
        ccxt_order_response = {
            'id': '12345',
            'clientOrderId': 'myorder123',
            'datetime': '2024-01-15T10:30:00.000Z',
            'timestamp': 1705315800000,
            'lastTradeTimestamp': None,
            'status': 'open',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'timeInForce': 'GTC',
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
        
        rest_client.create_order.return_value = ccxt_order_response
        
        # Тестируем
        result = await connector_instance.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=50000.0
        )
        
        # Проверяем CCXT compliance
        required_fields = ['id', 'symbol', 'type', 'side', 'amount', 'status']
        for field in required_fields:
            assert field in result
        
        # Проверяем параметры вызова
        rest_client.create_order.assert_called_once_with(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=50000.0,
            params={}
        )

    @pytest.mark.asyncio
    async def test_fetch_balance_ccxt_compliance(self, connector):
        """Тест fetch_balance на соответствие CCXT"""
        connector_instance, rest_client, _ = connector
        
        # CCXT balance structure
        ccxt_balance = {
            'info': {},
            'BTC': {'free': 1.0, 'used': 0.0, 'total': 1.0},
            'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0},
            'free': {'BTC': 1.0, 'USDT': 10000.0},
            'used': {'BTC': 0.0, 'USDT': 0.0},
            'total': {'BTC': 1.0, 'USDT': 10000.0}
        }
        
        rest_client.fetch_balance.return_value = ccxt_balance
        
        # Тестируем
        balance = await connector_instance.fetch_balance()
        
        # Проверяем CCXT compliance
        assert 'info' in balance
        assert 'free' in balance
        assert 'used' in balance
        assert 'total' in balance
        
        # Проверяем структуру валют
        assert 'BTC' in balance
        assert 'USDT' in balance
        
        for currency in ['BTC', 'USDT']:
            assert 'free' in balance[currency]
            assert 'used' in balance[currency]
            assert 'total' in balance[currency]

    @pytest.mark.asyncio
    async def test_cancel_order_ccxt_compliance(self, connector):
        """Тест cancel_order на соответствие CCXT"""
        connector_instance, rest_client, _ = connector
        
        # CCXT cancel order response
        ccxt_cancel_response = {
            'id': '12345',
            'clientOrderId': 'myorder123',
            'datetime': '2024-01-15T10:30:00.000Z',
            'timestamp': 1705315800000,
            'lastTradeTimestamp': None,
            'status': 'canceled',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'timeInForce': 'GTC',
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
        
        rest_client.cancel_order.return_value = ccxt_cancel_response
        
        # Тестируем
        result = await connector_instance.cancel_order('12345', 'BTC/USDT')
        
        # Проверяем статус отмены
        assert result['status'] == 'canceled'
        assert result['id'] == '12345'
        
        rest_client.cancel_order.assert_called_once_with('12345', 'BTC/USDT')

    @pytest.mark.asyncio
    async def test_fetch_order_ccxt_compliance(self, connector):
        """Тест fetch_order на соответствие CCXT"""
        connector_instance, rest_client, _ = connector
        
        # CCXT order response
        ccxt_order = {
            'id': '12345',
            'symbol': 'BTC/USDT',
            'status': 'closed',
            'type': 'limit',
            'side': 'buy',
            'amount': 0.001,
            'price': 50000.0,
            'filled': 0.001,
            'remaining': 0.0,
            'cost': 50.0,
            'average': 50000.0,
            'datetime': '2024-01-15T10:30:00.000Z',
            'timestamp': 1705315800000,
            'trades': [],
            'fee': {'cost': 0.05, 'currency': 'USDT'},
            'info': {}
        }
        
        rest_client.fetch_order.return_value = ccxt_order
        
        # Тестируем
        result = await connector_instance.fetch_order('12345', 'BTC/USDT')
        
        # Проверяем CCXT compliance
        assert result['id'] == '12345'
        assert result['symbol'] == 'BTC/USDT'
        assert result['status'] == 'closed'
        
        rest_client.fetch_order.assert_called_once_with('12345', 'BTC/USDT')

    @pytest.mark.asyncio
    async def test_streaming_methods_ccxt_compliance(self, connector):
        """Тест streaming методов на соответствие CCXT"""
        connector_instance, _, stream_client = connector
        
        # Мокируем streaming ответы
        stream_client.watch_ticker.return_value = {'symbol': 'BTC/USDT', 'last': 50000.0}
        stream_client.watch_order_book.return_value = {'bids': [], 'asks': []}
        stream_client.watch_trades.return_value = []
        stream_client.watch_ohlcv.return_value = []
        
        # Тестируем каждый streaming метод
        ticker = await connector_instance.watch_ticker('BTC/USDT')
        assert 'symbol' in ticker
        
        order_book = await connector_instance.watch_order_book('BTC/USDT')
        assert 'bids' in order_book
        assert 'asks' in order_book
        
        trades = await connector_instance.watch_trades('BTC/USDT')
        assert isinstance(trades, list)
        
        ohlcv = await connector_instance.watch_ohlcv('BTC/USDT')
        assert isinstance(ohlcv, list)

    @pytest.mark.asyncio
    async def test_error_handling_ccxt_compliance(self, connector):
        """Тест обработки ошибок согласно CCXT"""
        connector_instance, rest_client, _ = connector
        
        # Тестируем различные CCXT исключения
        import ccxt
        
        # InsufficientFunds
        rest_client.create_order.side_effect = ccxt.InsufficientFunds("Insufficient balance")
        
        with pytest.raises(ccxt.InsufficientFunds):
            await connector_instance.create_order('BTC/USDT', 'limit', 'buy', 0.001, 50000.0)
        
        # InvalidOrder
        rest_client.create_order.side_effect = ccxt.InvalidOrder("Invalid order parameters")
        
        with pytest.raises(ccxt.InvalidOrder):
            await connector_instance.create_order('BTC/USDT', 'limit', 'buy', 0.001, 50000.0)
        
        # OrderNotFound
        rest_client.cancel_order.side_effect = ccxt.OrderNotFound("Order not found")
        
        with pytest.raises(ccxt.OrderNotFound):
            await connector_instance.cancel_order('nonexistent', 'BTC/USDT')

    @pytest.mark.asyncio
    async def test_check_sufficient_balance_logic(self, connector):
        """Тест логики проверки баланса"""
        connector_instance, rest_client, _ = connector
        
        # Мокируем markets и balance
        markets = {
            'BTC/USDT': {
                'base': 'BTC',
                'quote': 'USDT'
            }
        }
        balance = {
            'BTC': {'free': 1.0},
            'USDT': {'free': 10000.0}
        }
        
        rest_client.load_markets.return_value = markets
        rest_client.fetch_balance.return_value = balance
        
        # Проверка для покупки (нужен USDT)
        has_balance, currency, available = await connector_instance.check_sufficient_balance(
            'BTC/USDT', 'buy', 0.001, 50000.0
        )
        
        assert has_balance is True
        assert currency == 'USDT'
        assert available == 10000.0
        
        # Проверка для продажи (нужен BTC)
        has_balance, currency, available = await connector_instance.check_sufficient_balance(
            'BTC/USDT', 'sell', 0.5
        )
        
        assert has_balance is True
        assert currency == 'BTC'
        assert available == 1.0

    @pytest.mark.asyncio
    async def test_market_order_vs_limit_order(self, connector):
        """Тест различий между market и limit ордерами"""
        connector_instance, rest_client, _ = connector
        
        # Limit order response
        limit_response = {
            'id': '12345',
            'type': 'limit',
            'price': 50000.0,
            'status': 'open'
        }
        
        # Market order response
        market_response = {
            'id': '12346',
            'type': 'market',
            'price': None,
            'status': 'closed'
        }
        
        rest_client.create_order.side_effect = [limit_response, market_response]
        
        # Тестируем limit order
        limit_result = await connector_instance.create_limit_order(
            'BTC/USDT', 'buy', 0.001, 50000.0
        )
        assert limit_result['type'] == 'limit'
        assert limit_result['price'] == 50000.0
        
        # Тестируем market order
        market_result = await connector_instance.create_market_order(
            'BTC/USDT', 'buy', 0.001
        )
        assert market_result['type'] == 'market'
        assert market_result['price'] is None

    def test_exchange_info_method(self, connector):
        """Тест метода получения информации о коннекторе"""
        connector_instance, _, _ = connector
        
        info = connector_instance.get_exchange_info()
        
        # Проверяем обязательные поля
        required_fields = ['exchange_name', 'use_sandbox', 'has_rest_client', 'has_stream_client']
        for field in required_fields:
            assert field in info
        
        assert info['exchange_name'] == 'binance'
        assert info['has_rest_client'] is True
        assert info['has_stream_client'] is True

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, connector):
        """Тест жизненного цикла соединения"""
        connector_instance, rest_client, stream_client = connector
        
        # Тестируем проверку соединения
        rest_client.fetch_balance.return_value = {'BTC': {'free': 1.0}}
        rest_client.load_markets.return_value = {'BTC/USDT': {}}
        
        connection_ok = await connector_instance.test_connection()
        assert connection_ok is True
        
        # Тестируем закрытие соединений
        await connector_instance.close()
        
        rest_client.close.assert_called_once()
        stream_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_autotrade_integration_methods(self, connector):
        """Тест методов интеграции с AutoTrade"""
        connector_instance, rest_client, _ = connector
        
        from src.domain.entities.order import Order
        
        # Создаем AutoTrade Order
        order = Order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=50000.0
        )
        
        # Тестируем создание CCXT параметров
        ccxt_params = connector_instance.create_order_from_autotrade(order)
        
        assert ccxt_params['symbol'] == 'BTC/USDT'
        assert ccxt_params['type'] == 'limit'
        assert ccxt_params['side'] == 'buy'
        assert ccxt_params['amount'] == 0.001
        assert ccxt_params['price'] == 50000.0
        
        # Тестируем синхронизацию с биржей
        ccxt_response = {
            'id': '12345',
            'status': 'open',
            'filled': 0.0005
        }
        rest_client.fetch_order.return_value = ccxt_response
        
        synced_order = await connector_instance.sync_order_with_exchange(order)
        
        # Order должен быть обновлен данными с биржи
        assert synced_order.filled == 0.0005


if __name__ == "__main__":
    pytest.main([__file__, "-v"])