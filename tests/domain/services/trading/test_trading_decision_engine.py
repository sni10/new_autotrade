import pytest
from unittest.mock import Mock, MagicMock
from decimal import Decimal

from src.domain.services.trading.trading_decision_engine import TradingDecisionEngine
from src.domain.services.market_data.orderbook_analyzer import OrderBookMetrics, OrderBookSignal


class TestTradingDecisionEngine:
    """Comprehensive tests for TradingDecisionEngine"""

    @pytest.fixture
    def mock_orderbook_analyzer(self):
        """Mock orderbook analyzer"""
        return Mock()

    @pytest.fixture
    def mock_exchange_connector(self):
        """Mock exchange connector"""
        mock = Mock()
        mock.get_balance = Mock()
        return mock

    @pytest.fixture
    def trading_engine(self, mock_orderbook_analyzer, mock_exchange_connector):
        """Create TradingDecisionEngine instance"""
        return TradingDecisionEngine(mock_orderbook_analyzer, mock_exchange_connector)

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

    # === check_balance() Tests ===

    def test_check_balance_sufficient_funds(self, trading_engine, mock_exchange_connector):
        """Test balance check with sufficient funds"""
        mock_exchange_connector.get_balance.return_value = 1000.0
        
        has_balance, message = trading_engine.check_balance("USDT", 500.0)
        
        assert has_balance is True
        assert "достаточен" in message
        assert "1000.00" in message
        mock_exchange_connector.get_balance.assert_called_once_with("USDT")

    def test_check_balance_insufficient_funds(self, trading_engine, mock_exchange_connector):
        """Test balance check with insufficient funds"""
        mock_exchange_connector.get_balance.return_value = 300.0
        
        has_balance, message = trading_engine.check_balance("USDT", 500.0)
        
        assert has_balance is False
        assert "Недостаточно средств" in message
        assert "500.00" in message
        assert "300.00" in message

    def test_check_balance_exception(self, trading_engine, mock_exchange_connector):
        """Test balance check with exchange error"""
        mock_exchange_connector.get_balance.side_effect = Exception("API Error")
        
        has_balance, message = trading_engine.check_balance("USDT", 500.0)
        
        assert has_balance is False
        assert "Ошибка при проверке баланса" in message
        assert "API Error" in message

    # === should_execute_trade() Tests ===

    def test_should_execute_trade_insufficient_balance(self, trading_engine, mock_exchange_connector, sample_orderbook_metrics):
        """Test trade decision with insufficient balance"""
        mock_exchange_connector.get_balance.return_value = 100.0
        
        result = trading_engine.should_execute_trade(True, sample_orderbook_metrics, "USDT", 500.0)
        
        assert result['execute'] is False
        assert "БАЛАНС" in result['reason']
        assert result['confidence'] == 0

    def test_should_execute_trade_orderbook_reject(self, trading_engine, mock_exchange_connector):
        """Test trade decision with orderbook rejection"""
        mock_exchange_connector.get_balance.return_value = 1000.0
        
        reject_metrics = OrderBookMetrics(
            bid_ask_spread=2.0,
            bid_volume=100.0,
            ask_volume=100.0,
            volume_imbalance=0.0,
            liquidity_depth=1.0,
            support_level=None,
            resistance_level=None,
            slippage_buy=5.0,
            slippage_sell=5.0,
            big_walls=[],
            signal=OrderBookSignal.REJECT,
            confidence=0.0
        )
        
        result = trading_engine.should_execute_trade(True, reject_metrics, "USDT", 500.0)
        
        assert result['execute'] is False
        assert "СТАКАН" in result['reason']
        assert "Отклонено" in result['reason']

    def test_should_execute_trade_no_macd_signal(self, trading_engine, mock_exchange_connector, sample_orderbook_metrics):
        """Test trade decision without MACD signal"""
        mock_exchange_connector.get_balance.return_value = 1000.0
        
        result = trading_engine.should_execute_trade(False, sample_orderbook_metrics, "USDT", 500.0)
        
        assert result['execute'] is False
        assert "MACD" in result['reason']
        assert "Нет сигнала" in result['reason']

    def test_should_execute_trade_strong_buy(self, trading_engine, mock_exchange_connector, sample_orderbook_metrics):
        """Test trade decision with strong buy signal"""
        mock_exchange_connector.get_balance.return_value = 1000.0
        
        result = trading_engine.should_execute_trade(True, sample_orderbook_metrics, "USDT", 500.0)
        
        assert result['execute'] is True
        assert result['confidence'] == 0.85
        assert "СТАКАН ПОДДЕРЖИВАЕТ" in result['reason']
        assert "🟢🔥" in result['reason']
        assert 'entry_price_hint' in result['modifications']
        assert 'exit_price_hint' in result['modifications']

    def test_should_execute_trade_weak_buy(self, trading_engine, mock_exchange_connector):
        """Test trade decision with weak buy signal"""
        mock_exchange_connector.get_balance.return_value = 1000.0
        
        weak_buy_metrics = OrderBookMetrics(
            bid_ask_spread=0.1,
            bid_volume=600.0,
            ask_volume=500.0,
            volume_imbalance=5.0,
            liquidity_depth=6.0,
            support_level=None,
            resistance_level=None,
            slippage_buy=0.2,
            slippage_sell=0.3,
            big_walls=[],
            signal=OrderBookSignal.WEAK_BUY,
            confidence=0.65
        )
        
        result = trading_engine.should_execute_trade(True, weak_buy_metrics, "USDT", 500.0)
        
        assert result['execute'] is True
        assert result['confidence'] == 0.65
        assert "🟡" in result['reason']

    def test_should_execute_trade_neutral(self, trading_engine, mock_exchange_connector):
        """Test trade decision with neutral orderbook"""
        mock_exchange_connector.get_balance.return_value = 1000.0
        
        neutral_metrics = OrderBookMetrics(
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
        
        result = trading_engine.should_execute_trade(True, neutral_metrics, "USDT", 500.0)
        
        assert result['execute'] is True
        assert result['confidence'] == 0.6
        assert "СТАКАН НЕЙТРАЛЕН" in result['reason']

    def test_should_execute_trade_high_slippage_reduction(self, trading_engine, mock_exchange_connector):
        """Test position size reduction with high slippage"""
        mock_exchange_connector.get_balance.return_value = 1000.0
        
        high_slippage_metrics = OrderBookMetrics(
            bid_ask_spread=0.1,
            bid_volume=700.0,
            ask_volume=600.0,
            volume_imbalance=10.0,
            liquidity_depth=7.0,
            support_level=0.4000,
            resistance_level=0.4200,
            slippage_buy=0.8,  # High slippage
            slippage_sell=0.4,
            big_walls=[],
            signal=OrderBookSignal.STRONG_BUY,
            confidence=0.8
        )
        
        result = trading_engine.should_execute_trade(True, high_slippage_metrics, "USDT", 500.0)
        
        assert result['execute'] is True
        assert 'reduce_position_size' in result['modifications']
        assert result['modifications']['reduce_position_size'] == 0.7

    def test_should_execute_trade_sell_signal(self, trading_engine, mock_exchange_connector):
        """Test trade decision with sell signal"""
        mock_exchange_connector.get_balance.return_value = 1000.0
        
        sell_metrics = OrderBookMetrics(
            bid_ask_spread=0.1,
            bid_volume=600.0,
            ask_volume=800.0,
            volume_imbalance=-15.0,
            liquidity_depth=7.0,
            support_level=None,
            resistance_level=None,
            slippage_buy=0.3,
            slippage_sell=0.4,
            big_walls=[],
            signal=OrderBookSignal.STRONG_SELL,
            confidence=0.8
        )
        
        result = trading_engine.should_execute_trade(True, sell_metrics, "USDT", 500.0)
        
        assert result['execute'] is False
        assert "СТАКАН ПРОТИВ" in result['reason']

    # === format_orderbook_info() Tests ===

    def test_format_orderbook_info_complete(self, trading_engine, sample_orderbook_metrics):
        """Test orderbook info formatting with complete data"""
        info = trading_engine.format_orderbook_info(sample_orderbook_metrics)
        
        assert "📊 АНАЛИЗ СТАКАНА:" in info
        assert "💱 Спред: 0.050%" in info
        assert "⚖️ Дисбаланс: +15.0% (покупатели)" in info
        assert "💧 Ликвидность: 8.5" in info
        assert "📉 Слиппедж покупки: 0.30%" in info
        assert "📈 Слиппедж продажи: 0.40%" in info
        assert "🛡️ Поддержка: 0.4000" in info
        assert "🚧 Сопротивление: 0.4200" in info

    def test_format_orderbook_info_negative_imbalance(self, trading_engine):
        """Test orderbook info formatting with negative volume imbalance"""
        metrics = OrderBookMetrics(
            bid_ask_spread=0.1,
            bid_volume=450.0,
            ask_volume=550.0,
            volume_imbalance=-10.0,  # Negative imbalance
            liquidity_depth=5.0,
            support_level=None,
            resistance_level=None,
            slippage_buy=0.5,
            slippage_sell=0.6,
            big_walls=[{'price': 0.4100, 'size': 1000}],
            signal=OrderBookSignal.WEAK_SELL,
            confidence=0.3
        )
        
        info = trading_engine.format_orderbook_info(metrics)
        
        assert "⚖️ Дисбаланс: -10.0% (продавцы)" in info
        assert "🧱 Больших стен: 1" in info

    def test_format_orderbook_info_minimal(self, trading_engine):
        """Test orderbook info formatting with minimal data"""
        metrics = OrderBookMetrics(
            bid_ask_spread=0.2,
            bid_volume=300.0,
            ask_volume=300.0,
            volume_imbalance=0.0,
            liquidity_depth=3.0,
            support_level=None,
            resistance_level=None,
            slippage_buy=0.4,
            slippage_sell=0.4,
            big_walls=[],
            signal=OrderBookSignal.NEUTRAL,
            confidence=0.5
        )
        
        info = trading_engine.format_orderbook_info(metrics)
        
        assert "📊 АНАЛИЗ СТАКАНА:" in info
        assert "🛡️ Поддержка:" not in info
        assert "🚧 Сопротивление:" not in info
        assert "🧱 Больших стен:" not in info

    # === apply_orderbook_modifications() Tests ===

    def test_apply_orderbook_modifications_entry_price_valid(self, trading_engine):
        """Test applying valid entry price modification"""
        current_price = 0.4100
        modifications = {'entry_price_hint': 0.4020}  # Within 2% range
        
        result = trading_engine.apply_orderbook_modifications(current_price, 1000.0, modifications)
        
        assert result['entry_price'] == 0.4020
        assert len(result['modifications_applied']) == 1
        assert "поддержки" in result['modifications_applied'][0]

    def test_apply_orderbook_modifications_entry_price_too_far(self, trading_engine):
        """Test rejecting entry price modification that's too far"""
        current_price = 0.4100
        modifications = {'entry_price_hint': 0.3900}  # More than 2% away
        
        result = trading_engine.apply_orderbook_modifications(current_price, 1000.0, modifications)
        
        assert result['entry_price'] == current_price  # Should use current price
        assert len(result['modifications_applied']) == 0

    def test_apply_orderbook_modifications_entry_price_higher(self, trading_engine):
        """Test rejecting entry price modification that's higher than current"""
        current_price = 0.4100
        modifications = {'entry_price_hint': 0.4150}  # Higher than current
        
        result = trading_engine.apply_orderbook_modifications(current_price, 1000.0, modifications)
        
        assert result['entry_price'] == current_price
        assert len(result['modifications_applied']) == 0

    def test_apply_orderbook_modifications_exit_price_valid(self, trading_engine):
        """Test applying valid exit price modification"""
        current_price = 0.4100
        modifications = {'exit_price_hint': 0.4180}  # Within 2% range and higher
        
        result = trading_engine.apply_orderbook_modifications(current_price, 1000.0, modifications)
        
        assert result['exit_price_hint'] == 0.4180
        assert any("сопротивления" in mod for mod in result['modifications_applied'])

    def test_apply_orderbook_modifications_exit_price_too_far(self, trading_engine):
        """Test rejecting exit price modification that's too far"""
        current_price = 0.4100
        modifications = {'exit_price_hint': 0.4300}  # More than 2% away
        
        result = trading_engine.apply_orderbook_modifications(current_price, 1000.0, modifications)
        
        assert result['exit_price_hint'] is None
        assert not any("сопротивления" in mod for mod in result['modifications_applied'])

    def test_apply_orderbook_modifications_position_size_reduction(self, trading_engine):
        """Test applying position size reduction"""
        current_price = 0.4100
        modifications = {'reduce_position_size': 0.7}
        
        result = trading_engine.apply_orderbook_modifications(current_price, 1000.0, modifications)
        
        assert result['budget_multiplier'] == 0.7
        assert any("размер позиции" in mod for mod in result['modifications_applied'])

    def test_apply_orderbook_modifications_all_modifications(self, trading_engine):
        """Test applying all types of modifications"""
        current_price = 0.4100
        modifications = {
            'entry_price_hint': 0.4020,
            'exit_price_hint': 0.4180,
            'reduce_position_size': 0.8
        }
        
        result = trading_engine.apply_orderbook_modifications(current_price, 1000.0, modifications)
        
        assert result['entry_price'] == 0.4020
        assert result['exit_price_hint'] == 0.4180
        assert result['budget_multiplier'] == 0.8
        assert len(result['modifications_applied']) == 3

    def test_apply_orderbook_modifications_no_modifications(self, trading_engine):
        """Test with no modifications"""
        current_price = 0.4100
        modifications = {}
        
        result = trading_engine.apply_orderbook_modifications(current_price, 1000.0, modifications)
        
        assert result['entry_price'] == current_price
        assert result['exit_price_hint'] is None
        assert result['budget_multiplier'] == 1.0
        assert len(result['modifications_applied']) == 0