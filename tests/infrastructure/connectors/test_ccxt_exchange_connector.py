# tests/infrastructure/connectors/test_ccxt_exchange_connector.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.infrastructure.connectors.ccxt_exchange_connector import CCXTExchangeConnector
from src.domain.entities.order import Order


class TestCCXTExchangeConnector:
    """
    🚀 Тесты для CCXT Exchange Connector
    """

    @pytest.fixture
    def mock_config(self):
        """Мок конфигурации"""
        return {
            'binance': {
                'production': {
                    'apiKey': 'test_api_key',
                    'secret': 'test_secret'
                },
                'sandbox': {
                    'apiKey': 'test_sandbox_api_key',
                    'secret': 'test_sandbox_secret'
                }
            }
        }

    @pytest.fixture
    def sample_ccxt_order(self):
        """Образец CCXT ордера"""
        return {
            'id': '12345',
            'clientOrderId': 'client_123',
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

    @pytest.fixture
    def sample_ccxt_ticker(self):
        """Образец CCXT тикера"""
        return {
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

    @pytest.fixture
    def sample_ccxt_balance(self):
        """Образец CCXT баланса"""
        return {
            'info': {},
            'BTC': {'free': 1.0, 'used': 0.0, 'total': 1.0},
            'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0},
            'free': {'BTC': 1.0, 'USDT': 10000.0},
            'used': {'BTC': 0.0, 'USDT': 0.0},
            'total': {'BTC': 1.0, 'USDT': 10000.0}
        }

    @pytest.fixture
    def sample_ccxt_markets(self):
        """Образец CCXT рынков"""
        return {
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

    @pytest.fixture
    async def connector_with_mocks(self, mock_config):
        """Коннектор с мокированными клиентами"""
        with patch('src.infrastructure.connectors.ccxt_exchange_connector.load_config', return_value=mock_config):
            with patch('ccxt.binance') as mock_rest_class:
                with patch('ccxt.pro.binance') as mock_stream_class:
                    # Настраиваем моки клиентов
                    mock_rest_client = AsyncMock()
                    mock_stream_client = AsyncMock()
                    
                    mock_rest_class.return_value = mock_rest_client
                    mock_stream_class.return_value = mock_stream_client
                    
                    # Создаем коннектор
                    connector = CCXTExchangeConnector('binance', use_sandbox=True)
                    
                    # Возвращаем коннектор с моками
                    yield connector, mock_rest_client, mock_stream_client

    @pytest.mark.asyncio
    async def test_connector_initialization(self, connector_with_mocks):
        """Тест инициализации коннектора"""
        connector, rest_client, stream_client = connector_with_mocks
        
        assert connector.exchange_name == 'binance'
        assert connector.use_sandbox is True
        assert connector.rest_client is not None
        assert connector.stream_client is not None

    @pytest.mark.asyncio
    async def test_load_markets(self, connector_with_mocks, sample_ccxt_markets):
        """Тест загрузки рынков"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем мок
        rest_client.load_markets.return_value = sample_ccxt_markets
        
        # Тестируем
        markets = await connector.load_markets()
        
        assert markets == sample_ccxt_markets
        assert 'BTC/USDT' in markets
        assert markets['BTC/USDT']['symbol'] == 'BTC/USDT'
        rest_client.load_markets.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_ticker(self, connector_with_mocks, sample_ccxt_ticker):
        """Тест получения тикера"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем мок
        rest_client.fetch_ticker.return_value = sample_ccxt_ticker
        
        # Тестируем
        ticker = await connector.fetch_ticker('BTC/USDT')
        
        assert ticker == sample_ccxt_ticker
        assert ticker['symbol'] == 'BTC/USDT'
        assert ticker['last'] == 50000.0
        rest_client.fetch_ticker.assert_called_once_with('BTC/USDT')

    @pytest.mark.asyncio
    async def test_fetch_balance(self, connector_with_mocks, sample_ccxt_balance):
        """Тест получения баланса"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем мок
        rest_client.fetch_balance.return_value = sample_ccxt_balance
        
        # Тестируем
        balance = await connector.fetch_balance()
        
        assert balance == sample_ccxt_balance
        assert balance['USDT']['free'] == 10000.0
        rest_client.fetch_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_balance(self, connector_with_mocks, sample_ccxt_balance):
        """Тест получения доступного баланса"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем мок
        rest_client.fetch_balance.return_value = sample_ccxt_balance
        
        # Тестируем
        usdt_balance = await connector.get_available_balance('USDT')
        btc_balance = await connector.get_available_balance('BTC')
        
        assert usdt_balance == 10000.0
        assert btc_balance == 1.0

    @pytest.mark.asyncio
    async def test_create_order(self, connector_with_mocks, sample_ccxt_order):
        """Тест создания ордера"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем мок
        rest_client.create_order.return_value = sample_ccxt_order
        
        # Тестируем
        result = await connector.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=50000.0
        )
        
        assert result == sample_ccxt_order
        assert result['id'] == '12345'
        assert result['symbol'] == 'BTC/USDT'
        
        rest_client.create_order.assert_called_once_with(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=50000.0,
            params={}
        )

    @pytest.mark.asyncio
    async def test_create_limit_order(self, connector_with_mocks, sample_ccxt_order):
        """Тест создания лимитного ордера"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем мок
        rest_client.create_order.return_value = sample_ccxt_order
        
        # Тестируем
        result = await connector.create_limit_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.001,
            price=50000.0
        )
        
        assert result == sample_ccxt_order
        rest_client.create_order.assert_called_once_with(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=50000.0,
            params={}
        )

    @pytest.mark.asyncio
    async def test_create_market_order(self, connector_with_mocks, sample_ccxt_order):
        """Тест создания маркет ордера"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Модифицируем ордер для маркет типа
        market_order = sample_ccxt_order.copy()
        market_order['type'] = 'market'
        market_order['price'] = None
        
        rest_client.create_order.return_value = market_order
        
        # Тестируем
        result = await connector.create_market_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.001
        )
        
        assert result['type'] == 'market'
        assert result['price'] is None
        rest_client.create_order.assert_called_once_with(
            symbol='BTC/USDT',
            type='market',
            side='buy',
            amount=0.001,
            price=None,
            params={}
        )

    @pytest.mark.asyncio
    async def test_cancel_order(self, connector_with_mocks, sample_ccxt_order):
        """Тест отмены ордера"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Модифицируем ордер для отмененного статуса
        canceled_order = sample_ccxt_order.copy()
        canceled_order['status'] = 'canceled'
        
        rest_client.cancel_order.return_value = canceled_order
        
        # Тестируем
        result = await connector.cancel_order('12345', 'BTC/USDT')
        
        assert result['status'] == 'canceled'
        rest_client.cancel_order.assert_called_once_with('12345', 'BTC/USDT')

    @pytest.mark.asyncio
    async def test_fetch_order(self, connector_with_mocks, sample_ccxt_order):
        """Тест получения ордера"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем мок
        rest_client.fetch_order.return_value = sample_ccxt_order
        
        # Тестируем
        result = await connector.fetch_order('12345', 'BTC/USDT')
        
        assert result == sample_ccxt_order
        rest_client.fetch_order.assert_called_once_with('12345', 'BTC/USDT')

    @pytest.mark.asyncio
    async def test_fetch_open_orders(self, connector_with_mocks, sample_ccxt_order):
        """Тест получения открытых ордеров"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем мок
        rest_client.fetch_open_orders.return_value = [sample_ccxt_order]
        
        # Тестируем
        result = await connector.fetch_open_orders('BTC/USDT')
        
        assert len(result) == 1
        assert result[0] == sample_ccxt_order
        rest_client.fetch_open_orders.assert_called_once_with('BTC/USDT')

    @pytest.mark.asyncio
    async def test_check_sufficient_balance(self, connector_with_mocks, sample_ccxt_balance, sample_ccxt_markets):
        """Тест проверки достаточности баланса"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем моки
        rest_client.load_markets.return_value = sample_ccxt_markets
        rest_client.fetch_balance.return_value = sample_ccxt_balance
        
        # Тестируем покупку (нужен USDT)
        has_balance, currency, available = await connector.check_sufficient_balance(
            'BTC/USDT', 'buy', 0.001, 50000.0
        )
        
        assert has_balance is True
        assert currency == 'USDT'
        assert available == 10000.0
        
        # Тестируем продажу (нужен BTC)
        has_balance, currency, available = await connector.check_sufficient_balance(
            'BTC/USDT', 'sell', 0.5
        )
        
        assert has_balance is True
        assert currency == 'BTC'
        assert available == 1.0

    @pytest.mark.asyncio
    async def test_get_market_info(self, connector_with_mocks, sample_ccxt_markets):
        """Тест получения информации о рынке"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем мок
        rest_client.load_markets.return_value = sample_ccxt_markets
        
        # Тестируем
        market = await connector.get_market_info('BTC/USDT')
        
        assert market == sample_ccxt_markets['BTC/USDT']
        assert market['symbol'] == 'BTC/USDT'
        assert market['base'] == 'BTC'
        assert market['quote'] == 'USDT'

    @pytest.mark.asyncio
    async def test_get_trading_fees(self, connector_with_mocks, sample_ccxt_markets):
        """Тест получения торговых комиссий"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем мок
        rest_client.load_markets.return_value = sample_ccxt_markets
        
        # Тестируем
        fees = await connector.get_trading_fees('BTC/USDT')
        
        assert fees['maker'] == 0.001
        assert fees['taker'] == 0.001

    @pytest.mark.asyncio
    async def test_calculate_order_cost(self, connector_with_mocks, sample_ccxt_ticker, sample_ccxt_markets):
        """Тест расчета стоимости ордера"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем моки
        rest_client.fetch_ticker.return_value = sample_ccxt_ticker
        rest_client.load_markets.return_value = sample_ccxt_markets
        
        # Тестируем расчет для покупки
        cost_info = await connector.calculate_order_cost('BTC/USDT', 'buy', 0.001, 50000.0)
        
        assert cost_info['base_cost'] == 50.0
        assert cost_info['fee_rate'] == 0.001
        assert cost_info['fee_cost'] == 0.05
        assert cost_info['total_cost'] == 50.05
        assert cost_info['price'] == 50000.0
        assert cost_info['amount'] == 0.001

    @pytest.mark.asyncio
    async def test_sync_order_with_exchange(self, connector_with_mocks, sample_ccxt_order):
        """Тест синхронизации ордера с биржей"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Создаем AutoTrade ордер
        order = Order.from_ccxt_response(sample_ccxt_order)
        
        # Модифицируем CCXT ответ (ордер частично исполнен)
        updated_ccxt_order = sample_ccxt_order.copy()
        updated_ccxt_order['filled'] = 0.0005
        updated_ccxt_order['remaining'] = 0.0005
        updated_ccxt_order['status'] = 'partial'
        
        # Настраиваем мок
        rest_client.fetch_order.return_value = updated_ccxt_order
        
        # Тестируем
        synced_order = await connector.sync_order_with_exchange(order)
        
        assert synced_order.filled == 0.0005
        assert synced_order.remaining == 0.0005
        assert synced_order.status == 'partial'

    @pytest.mark.asyncio
    async def test_test_connection(self, connector_with_mocks, sample_ccxt_balance, sample_ccxt_markets):
        """Тест проверки соединения"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем моки для успешного подключения
        rest_client.fetch_balance.return_value = sample_ccxt_balance
        rest_client.load_markets.return_value = sample_ccxt_markets
        
        # Тестируем
        result = await connector.test_connection()
        
        assert result is True
        rest_client.fetch_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_streaming_methods(self, connector_with_mocks, sample_ccxt_ticker):
        """Тест streaming методов"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Настраиваем моки
        stream_client.watch_ticker.return_value = sample_ccxt_ticker
        stream_client.watch_order_book.return_value = {'bids': [], 'asks': []}
        stream_client.watch_trades.return_value = []
        stream_client.watch_ohlcv.return_value = []
        
        # Тестируем
        ticker = await connector.watch_ticker('BTC/USDT')
        order_book = await connector.watch_order_book('BTC/USDT')
        trades = await connector.watch_trades('BTC/USDT')
        ohlcv = await connector.watch_ohlcv('BTC/USDT')
        
        assert ticker == sample_ccxt_ticker
        assert 'bids' in order_book
        assert isinstance(trades, list)
        assert isinstance(ohlcv, list)

    @pytest.mark.asyncio
    async def test_get_exchange_info(self, connector_with_mocks):
        """Тест получения информации о коннекторе"""
        connector, rest_client, stream_client = connector_with_mocks
        
        info = connector.get_exchange_info()
        
        assert info['exchange_name'] == 'binance'
        assert info['use_sandbox'] is True
        assert info['has_rest_client'] is True
        assert info['has_stream_client'] is True
        assert 'ccxt_version' in info

    @pytest.mark.asyncio
    async def test_close_connections(self, connector_with_mocks):
        """Тест закрытия соединений"""
        connector, rest_client, stream_client = connector_with_mocks
        
        # Тестируем
        await connector.close()
        
        rest_client.close.assert_called_once()
        stream_client.close.assert_called_once()

    def test_repr(self, connector_with_mocks):
        """Тест строкового представления"""
        connector, rest_client, stream_client = connector_with_mocks
        
        repr_str = repr(connector)
        
        assert 'CCXTExchangeConnector' in repr_str
        assert 'binance' in repr_str
        assert 'sandbox=True' in repr_str


if __name__ == "__main__":
    pytest.main([__file__])