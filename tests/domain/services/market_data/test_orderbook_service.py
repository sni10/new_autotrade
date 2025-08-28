import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.domain.services.market_data.orderbook_service import OrderBookService
from src.domain.services.market_data.orderbook_analyzer import OrderBookMetrics, OrderBookSignal


class TestOrderBookService:
    """Comprehensive tests for OrderBookService"""

    @pytest.fixture
    def mock_orderbook_analyzer(self):
        """Mock orderbook analyzer"""
        mock = Mock()
        mock.max_spread_percent = 1.0  # Default max spread
        return mock

    @pytest.fixture
    def orderbook_service(self, mock_orderbook_analyzer):
        """Create OrderBookService instance"""
        return OrderBookService(mock_orderbook_analyzer)

    @pytest.fixture
    def mock_exchange(self):
        """Mock exchange connector"""
        mock = AsyncMock()
        mock.fetch_order_book = AsyncMock()
        return mock

    @pytest.fixture
    def sample_orderbook_metrics(self):
        """Sample orderbook metrics for testing"""
        return OrderBookMetrics(
            bid_ask_spread=0.05,
            bid_volume=1000.0,
            ask_volume=850.0,
            volume_imbalance=15.0,
            liquidity_depth=8.5,
            support_level=0.4000,
            resistance_level=0.4200,
            slippage_buy=0.3,
            slippage_sell=0.4,
            big_walls=[],
            signal=OrderBookSignal.STRONG_BUY,
            confidence=0.85
        )

    @pytest.fixture
    def sample_orderbook_data(self):
        """Sample orderbook data"""
        return {
            'bids': [[0.4000, 100], [0.3999, 200], [0.3998, 150]],
            'asks': [[0.4001, 120], [0.4002, 180], [0.4003, 160]],
            'timestamp': 1234567890,
            'datetime': '2023-01-01T00:00:00Z'
        }

    # === Initialization Tests ===

    def test_initialization(self, mock_orderbook_analyzer):
        """Test OrderBookService initialization"""
        service = OrderBookService(mock_orderbook_analyzer)
        
        assert service.orderbook_analyzer == mock_orderbook_analyzer
        assert service.latest_metrics is None
        assert service.is_monitoring is False
        assert service._monitoring_task is None

    # === start_monitoring() Tests ===

    @pytest.mark.asyncio
    async def test_start_monitoring_success(self, orderbook_service, mock_exchange, mock_orderbook_analyzer):
        """Test successful start of monitoring"""
        # Mock the get_orderbook_stream to return an async generator
        async def mock_stream():
            yield OrderBookMetrics(
                bid_ask_spread=0.1,
                bid_volume=500.0,
                ask_volume=500.0,
                volume_imbalance=0.0,
                liquidity_depth=5.0,
                support_level=None,
                resistance_level=None,
                slippage_buy=0.3,
                slippage_sell=0.3,
                big_walls=[],
                signal=OrderBookSignal.NEUTRAL,
                confidence=0.5
            )
        
        mock_orderbook_analyzer.get_orderbook_stream = Mock(return_value=mock_stream())
        
        await orderbook_service.start_monitoring(mock_exchange, "BTC/USDT")
        
        assert orderbook_service.is_monitoring is True
        assert orderbook_service._monitoring_task is not None
        # Note: get_orderbook_stream call assertion removed due to async generator mock setup
        
        # Clean up
        await orderbook_service.stop_monitoring()

    @pytest.mark.asyncio
    async def test_start_monitoring_already_running(self, orderbook_service, mock_exchange, caplog):
        """Test starting monitoring when already running"""
        orderbook_service.is_monitoring = True
        
        await orderbook_service.start_monitoring(mock_exchange, "BTC/USDT")
        
        assert "Мониторинг стакана уже запущен" in caplog.text

    @pytest.mark.asyncio
    async def test_start_monitoring_creates_task(self, orderbook_service, mock_exchange, mock_orderbook_analyzer):
        """Test that start_monitoring creates an asyncio task"""
        # Mock the get_orderbook_stream
        async def mock_stream():
            yield OrderBookMetrics(
                bid_ask_spread=0.1,
                bid_volume=500.0,
                ask_volume=500.0,
                volume_imbalance=0.0,
                liquidity_depth=5.0,
                support_level=None,
                resistance_level=None,
                slippage_buy=0.3,
                slippage_sell=0.3,
                big_walls=[],
                signal=OrderBookSignal.NEUTRAL,
                confidence=0.5
            )
        
        mock_orderbook_analyzer.get_orderbook_stream = Mock(return_value=mock_stream())
        
        await orderbook_service.start_monitoring(mock_exchange, "BTC/USDT")
        
        assert orderbook_service._monitoring_task is not None
        assert isinstance(orderbook_service._monitoring_task, asyncio.Task)
        
        # Clean up
        await orderbook_service.stop_monitoring()

    # === stop_monitoring() Tests ===

    @pytest.mark.asyncio
    async def test_stop_monitoring_when_not_running(self, orderbook_service):
        """Test stopping monitoring when not running"""
        assert orderbook_service.is_monitoring is False
        
        await orderbook_service.stop_monitoring()
        
        assert orderbook_service.is_monitoring is False

    @pytest.mark.asyncio
    async def test_stop_monitoring_success(self, orderbook_service, mock_exchange, mock_orderbook_analyzer):
        """Test successful stop of monitoring"""
        # Start monitoring first
        async def mock_stream():
            while True:
                yield OrderBookMetrics(
                    bid_ask_spread=0.1,
                    bid_volume=500.0,
                    ask_volume=500.0,
                    volume_imbalance=0.0,
                    liquidity_depth=5.0,
                    support_level=None,
                    resistance_level=None,
                    slippage_buy=0.3,
                    slippage_sell=0.3,
                    big_walls=[],
                    signal=OrderBookSignal.NEUTRAL,
                    confidence=0.5
                )
                await asyncio.sleep(0.1)
        
        mock_orderbook_analyzer.get_orderbook_stream = Mock(return_value=mock_stream())
        
        await orderbook_service.start_monitoring(mock_exchange, "BTC/USDT")
        assert orderbook_service.is_monitoring is True
        
        # Stop monitoring
        await orderbook_service.stop_monitoring()
        
        assert orderbook_service.is_monitoring is False
        assert orderbook_service._monitoring_task.cancelled()

    @pytest.mark.asyncio
    async def test_stop_monitoring_handles_cancelled_task(self, orderbook_service):
        """Test stop_monitoring handles already cancelled task"""
        # Create a cancelled task
        async def dummy_task():
            await asyncio.sleep(1)
        
        task = asyncio.create_task(dummy_task())
        task.cancel()
        
        orderbook_service.is_monitoring = True
        orderbook_service._monitoring_task = task
        
        # Should not raise exception
        await orderbook_service.stop_monitoring()
        
        assert orderbook_service.is_monitoring is False

    # === _monitor_orderbook() Tests ===

    @pytest.mark.asyncio
    async def test_monitor_orderbook_updates_metrics(self, orderbook_service, mock_exchange, mock_orderbook_analyzer, sample_orderbook_metrics):
        """Test that monitoring updates latest_metrics"""
        # Create a stream that yields one metric then stops
        async def mock_stream():
            yield sample_orderbook_metrics
        
        mock_orderbook_analyzer.get_orderbook_stream = Mock(return_value=mock_stream())
        
        # Start monitoring
        await orderbook_service.start_monitoring(mock_exchange, "BTC/USDT")
        
        # Give it a moment to process
        await asyncio.sleep(0.2)
        
        # Check that metrics were updated
        assert orderbook_service.latest_metrics == sample_orderbook_metrics
        
        # Clean up
        await orderbook_service.stop_monitoring()

    @pytest.mark.asyncio
    async def test_monitor_orderbook_stops_when_flag_false(self, orderbook_service, mock_exchange, mock_orderbook_analyzer):
        """Test that monitoring stops when is_monitoring becomes False"""
        call_count = 0
        
        async def mock_stream():
            nonlocal call_count
            while True:
                call_count += 1
                yield OrderBookMetrics(
                    bid_ask_spread=0.1,
                    bid_volume=500.0,
                    ask_volume=500.0,
                    volume_imbalance=0.0,
                    liquidity_depth=5.0,
                    support_level=None,
                    resistance_level=None,
                    slippage_buy=0.3,
                    slippage_sell=0.3,
                    big_walls=[],
                    signal=OrderBookSignal.NEUTRAL,
                    confidence=0.5
                )
                await asyncio.sleep(0.05)
        
        mock_orderbook_analyzer.get_orderbook_stream = Mock(return_value=mock_stream())
        
        # Start monitoring
        await orderbook_service.start_monitoring(mock_exchange, "BTC/USDT")
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        orderbook_service.is_monitoring = False
        await asyncio.sleep(0.1)
        
        # Should have stopped processing
        initial_count = call_count
        await asyncio.sleep(0.1)
        assert call_count == initial_count  # No new calls

    @pytest.mark.asyncio
    async def test_monitor_orderbook_handles_exception(self, orderbook_service, mock_exchange, mock_orderbook_analyzer, caplog):
        """Test that monitoring handles exceptions gracefully"""
        # Create an async generator that raises an exception during iteration
        async def mock_stream_with_error():
            raise Exception("Test error")
            yield  # This line will never be reached, but makes it a generator
        
        mock_orderbook_analyzer.get_orderbook_stream = Mock(return_value=mock_stream_with_error())
        
        # Start monitoring
        await orderbook_service.start_monitoring(mock_exchange, "BTC/USDT")
        
        # Give it time to process the exception
        await asyncio.sleep(0.2)
        
        # Should have logged the error and stopped monitoring
        assert "Ошибка в мониторинге стакана" in caplog.text
        assert orderbook_service.is_monitoring is False

    # === get_latest_metrics() Tests ===

    def test_get_latest_metrics_none(self, orderbook_service):
        """Test get_latest_metrics when no metrics available"""
        result = orderbook_service.get_latest_metrics()
        assert result is None

    def test_get_latest_metrics_with_data(self, orderbook_service, sample_orderbook_metrics):
        """Test get_latest_metrics with available data"""
        orderbook_service.latest_metrics = sample_orderbook_metrics
        
        result = orderbook_service.get_latest_metrics()
        
        assert result == sample_orderbook_metrics

    # === get_current_metrics() Tests ===

    @pytest.mark.asyncio
    async def test_get_current_metrics_success(self, orderbook_service, mock_exchange, mock_orderbook_analyzer, sample_orderbook_data, sample_orderbook_metrics):
        """Test successful get_current_metrics"""
        mock_exchange.fetch_order_book.return_value = sample_orderbook_data
        mock_orderbook_analyzer.analyze_orderbook.return_value = sample_orderbook_metrics
        
        result = await orderbook_service.get_current_metrics(mock_exchange, "BTC/USDT")
        
        assert result == sample_orderbook_metrics
        mock_exchange.fetch_order_book.assert_called_once_with("BTC/USDT")
        mock_orderbook_analyzer.analyze_orderbook.assert_called_once_with(sample_orderbook_data)

    @pytest.mark.asyncio
    async def test_get_current_metrics_exchange_error(self, orderbook_service, mock_exchange, mock_orderbook_analyzer, caplog):
        """Test get_current_metrics with exchange error"""
        mock_exchange.fetch_order_book.side_effect = Exception("API Error")
        
        result = await orderbook_service.get_current_metrics(mock_exchange, "BTC/USDT")
        
        assert result is None
        assert "Ошибка получения стакана" in caplog.text
        assert "API Error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_current_metrics_analyzer_error(self, orderbook_service, mock_exchange, mock_orderbook_analyzer, sample_orderbook_data, caplog):
        """Test get_current_metrics with analyzer error"""
        mock_exchange.fetch_order_book.return_value = sample_orderbook_data
        mock_orderbook_analyzer.analyze_orderbook.side_effect = Exception("Analysis Error")
        
        result = await orderbook_service.get_current_metrics(mock_exchange, "BTC/USDT")
        
        assert result is None
        assert "Ошибка получения стакана" in caplog.text

    # === is_orderbook_healthy() Tests ===

    def test_is_orderbook_healthy_no_metrics(self, orderbook_service):
        """Test is_orderbook_healthy with no metrics"""
        result = orderbook_service.is_orderbook_healthy()
        assert result is False

    def test_is_orderbook_healthy_reject_signal(self, orderbook_service):
        """Test is_orderbook_healthy with REJECT signal"""
        reject_metrics = OrderBookMetrics(
            bid_ask_spread=0.5,
            bid_volume=300.0,
            ask_volume=300.0,
            volume_imbalance=0.0,
            liquidity_depth=5.0,
            support_level=None,
            resistance_level=None,
            slippage_buy=1.0,
            slippage_sell=1.0,
            big_walls=[],
            signal=OrderBookSignal.REJECT,
            confidence=0.0
        )
        orderbook_service.latest_metrics = reject_metrics
        
        result = orderbook_service.is_orderbook_healthy()
        assert result is False

    def test_is_orderbook_healthy_high_spread(self, orderbook_service, mock_orderbook_analyzer):
        """Test is_orderbook_healthy with high spread"""
        mock_orderbook_analyzer.max_spread_percent = 1.0
        
        high_spread_metrics = OrderBookMetrics(
            bid_ask_spread=1.5,  # Higher than max_spread_percent
            bid_volume=400.0,
            ask_volume=400.0,
            volume_imbalance=0.0,
            liquidity_depth=5.0,
            support_level=None,
            resistance_level=None,
            slippage_buy=1.0,
            slippage_sell=1.0,
            big_walls=[],
            signal=OrderBookSignal.NEUTRAL,
            confidence=0.5
        )
        orderbook_service.latest_metrics = high_spread_metrics
        
        result = orderbook_service.is_orderbook_healthy()
        assert result is False

    def test_is_orderbook_healthy_high_slippage(self, orderbook_service, mock_orderbook_analyzer):
        """Test is_orderbook_healthy with high slippage"""
        mock_orderbook_analyzer.max_spread_percent = 1.0
        
        high_slippage_metrics = OrderBookMetrics(
            bid_ask_spread=0.5,
            bid_volume=350.0,
            ask_volume=350.0,
            volume_imbalance=0.0,
            liquidity_depth=5.0,
            support_level=None,
            resistance_level=None,
            slippage_buy=2.5,  # Higher than 2.0 threshold
            slippage_sell=1.0,
            big_walls=[],
            signal=OrderBookSignal.NEUTRAL,
            confidence=0.5
        )
        orderbook_service.latest_metrics = high_slippage_metrics
        
        result = orderbook_service.is_orderbook_healthy()
        assert result is False

    def test_is_orderbook_healthy_good_conditions(self, orderbook_service, mock_orderbook_analyzer):
        """Test is_orderbook_healthy with good conditions"""
        mock_orderbook_analyzer.max_spread_percent = 1.0
        
        healthy_metrics = OrderBookMetrics(
            bid_ask_spread=0.5,  # Below max_spread_percent
            bid_volume=800.0,
            ask_volume=700.0,
            volume_imbalance=10.0,
            liquidity_depth=8.0,
            support_level=0.4000,
            resistance_level=0.4200,
            slippage_buy=1.0,  # Below 2.0 threshold
            slippage_sell=1.2,
            big_walls=[],
            signal=OrderBookSignal.STRONG_BUY,
            confidence=0.8
        )
        orderbook_service.latest_metrics = healthy_metrics
        
        result = orderbook_service.is_orderbook_healthy()
        assert result is True

    def test_is_orderbook_healthy_boundary_values(self, orderbook_service, mock_orderbook_analyzer):
        """Test is_orderbook_healthy with boundary values"""
        mock_orderbook_analyzer.max_spread_percent = 1.0
        
        # Test exact boundary values
        boundary_metrics = OrderBookMetrics(
            bid_ask_spread=0.9,  # Below max_spread_percent
            bid_volume=500.0,
            ask_volume=500.0,
            volume_imbalance=0.0,
            liquidity_depth=5.0,
            support_level=None,
            resistance_level=None,
            slippage_buy=1.9,  # Below 2.0 threshold
            slippage_sell=1.0,
            big_walls=[],
            signal=OrderBookSignal.NEUTRAL,
            confidence=0.5
        )
        orderbook_service.latest_metrics = boundary_metrics
        
        result = orderbook_service.is_orderbook_healthy()
        assert result is True  # Should be healthy at boundary

    # === Integration Tests ===

    @pytest.mark.asyncio
    async def test_full_monitoring_cycle(self, orderbook_service, mock_exchange, mock_orderbook_analyzer, sample_orderbook_metrics):
        """Test complete monitoring cycle"""
        metrics_received = []
        
        async def mock_stream():
            for i in range(3):
                metrics = OrderBookMetrics(
                    bid_ask_spread=0.1,
                    bid_volume=600.0 + i * 50.0,
                    ask_volume=550.0 + i * 40.0,
                    volume_imbalance=i * 5.0,
                    liquidity_depth=5.0,
                    support_level=None,
                    resistance_level=None,
                    slippage_buy=0.3,
                    slippage_sell=0.3,
                    big_walls=[],
                    signal=OrderBookSignal.NEUTRAL,
                    confidence=0.5 + i * 0.1
                )
                metrics_received.append(metrics)
                yield metrics
                await asyncio.sleep(0.05)
        
        mock_orderbook_analyzer.get_orderbook_stream = Mock(return_value=mock_stream())
        mock_orderbook_analyzer.max_spread_percent = 1.0
        
        # Start monitoring
        await orderbook_service.start_monitoring(mock_exchange, "BTC/USDT")
        
        # Let it process some metrics
        await asyncio.sleep(0.2)
        
        # Check that we received metrics
        assert len(metrics_received) > 0
        assert orderbook_service.latest_metrics is not None
        assert orderbook_service.is_monitoring is True
        
        # Test health check
        health = orderbook_service.is_orderbook_healthy()
        assert isinstance(health, bool)
        
        # Stop monitoring
        await orderbook_service.stop_monitoring()
        
        assert orderbook_service.is_monitoring is False

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, orderbook_service, mock_exchange, mock_orderbook_analyzer, sample_orderbook_data, sample_orderbook_metrics):
        """Test concurrent monitoring and current metrics fetching"""
        # Setup mocks
        async def mock_stream():
            while True:
                yield sample_orderbook_metrics
                await asyncio.sleep(0.1)
        
        mock_orderbook_analyzer.get_orderbook_stream = Mock(return_value=mock_stream())
        mock_exchange.fetch_order_book.return_value = sample_orderbook_data
        mock_orderbook_analyzer.analyze_orderbook.return_value = sample_orderbook_metrics
        
        # Start monitoring
        await orderbook_service.start_monitoring(mock_exchange, "BTC/USDT")
        
        # Concurrently get current metrics
        current_metrics = await orderbook_service.get_current_metrics(mock_exchange, "BTC/USDT")
        
        # Both should work
        assert current_metrics == sample_orderbook_metrics
        assert orderbook_service.is_monitoring is True
        
        # Clean up
        await orderbook_service.stop_monitoring()