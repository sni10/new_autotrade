import pytest
import time
from datetime import datetime

from src.domain.entities.trading_signal import (
    TradingSignal, SignalType, SignalSource, SignalConfidence
)


class TestSignalType:
    """Тесты для SignalType enum"""
    
    def test_signal_types_exist(self):
        """Тест наличия всех типов сигналов"""
        assert SignalType.BUY
        assert SignalType.SELL
        assert SignalType.HOLD
        assert SignalType.STRONG_BUY
        assert SignalType.STRONG_SELL
        assert SignalType.WEAK_BUY
        assert SignalType.WEAK_SELL
    
    def test_signal_type_values(self):
        """Тест значений типов сигналов"""
        assert SignalType.BUY.value == "buy"
        assert SignalType.SELL.value == "sell"
        assert SignalType.HOLD.value == "hold"
        assert SignalType.STRONG_BUY.value == "strong_buy"
        assert SignalType.STRONG_SELL.value == "strong_sell"
        assert SignalType.WEAK_BUY.value == "weak_buy"
        assert SignalType.WEAK_SELL.value == "weak_sell"


class TestSignalSource:
    """Тесты для SignalSource enum"""
    
    def test_signal_sources_exist(self):
        """Тест наличия всех источников сигналов"""
        assert SignalSource.MACD
        assert SignalSource.RSI
        assert SignalSource.SMA_CROSSOVER
        assert SignalSource.BOLLINGER_BANDS
        assert SignalSource.ORDERBOOK_ANALYSIS
        assert SignalSource.VOLUME_ANALYSIS
        assert SignalSource.COMBINED
    
    def test_signal_source_values(self):
        """Тест значений источников"""
        assert SignalSource.MACD.value == "macd"
        assert SignalSource.RSI.value == "rsi"
        assert SignalSource.COMBINED.value == "combined"


class TestSignalConfidence:
    """Тесты для SignalConfidence enum"""
    
    def test_confidence_levels_exist(self):
        """Тест наличия всех уровней уверенности"""
        assert SignalConfidence.VERY_LOW
        assert SignalConfidence.LOW
        assert SignalConfidence.MEDIUM
        assert SignalConfidence.HIGH
        assert SignalConfidence.VERY_HIGH
    
    def test_confidence_values(self):
        """Тест значений уровней уверенности"""
        assert SignalConfidence.VERY_LOW.value == 0.2
        assert SignalConfidence.LOW.value == 0.4
        assert SignalConfidence.MEDIUM.value == 0.6
        assert SignalConfidence.HIGH.value == 0.8
        assert SignalConfidence.VERY_HIGH.value == 0.95


class TestTradingSignal:
    """Тесты для TradingSignal"""
    
    def test_create_trading_signal_minimal(self):
        """Тест создания сигнала с минимальными параметрами"""
        timestamp = int(time.time() * 1000)
        
        signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.7
        )
        
        assert signal.symbol == "BTCUSDT"
        assert signal.timestamp == timestamp
        assert signal.signal_type == SignalType.BUY
        assert signal.source == SignalSource.MACD
        assert signal.strength == 0.7
        assert signal.confidence == 0.5  # default
        assert signal.price is None
        assert signal.metadata == {}
        assert signal.signal_id.startswith("BTCUSDT_")
        assert signal.signal_id.endswith("_macd_buy")
    
    def test_create_trading_signal_full(self):
        """Тест создания сигнала со всеми параметрами"""
        timestamp = int(time.time() * 1000)
        metadata = {"source_details": "MACD crossover", "volume": 1000}
        
        signal = TradingSignal(
            symbol="ETHUSDT",
            timestamp=timestamp,
            signal_type=SignalType.STRONG_BUY,
            source=SignalSource.RSI,
            strength=0.85,
            confidence=0.9,
            price=3000.5,
            metadata=metadata
        )
        
        assert signal.symbol == "ETHUSDT"
        assert signal.timestamp == timestamp
        assert signal.signal_type == SignalType.STRONG_BUY
        assert signal.source == SignalSource.RSI
        assert signal.strength == 0.85
        assert signal.confidence == 0.9
        assert signal.price == 3000.5
        assert signal.metadata == metadata
    
    def test_strength_validation(self):
        """Тест валидации силы сигнала"""
        # Значение выше 1.0 должно быть обрезано до 1.0
        signal_high = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=1.5
        )
        assert signal_high.strength == 1.0
        
        # Отрицательное значение должно быть обрезано до 0.0
        signal_negative = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=-0.5
        )
        assert signal_negative.strength == 0.0
    
    def test_confidence_validation(self):
        """Тест валидации уверенности в сигнале"""
        # Значение выше 1.0 должно быть обрезано до 1.0
        signal_high = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.7,
            confidence=1.5
        )
        assert signal_high.confidence == 1.0
        
        # Отрицательное значение должно быть обрезано до 0.0
        signal_negative = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.7,
            confidence=-0.3
        )
        assert signal_negative.confidence == 0.0
    
    def test_is_actionable_property(self):
        """Тест свойства is_actionable"""
        # Должен быть actionable: сильный BUY с высокой уверенностью
        actionable_signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.8,
            confidence=0.7
        )
        assert actionable_signal.is_actionable
        
        # Не должен быть actionable: HOLD сигнал
        hold_signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.HOLD,
            source=SignalSource.MACD,
            strength=0.8,
            confidence=0.7
        )
        assert not hold_signal.is_actionable
        
        # Не должен быть actionable: низкая уверенность
        low_confidence_signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.8,
            confidence=0.4
        )
        assert not low_confidence_signal.is_actionable
        
        # Не должен быть actionable: слабая сила
        weak_signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.2,
            confidence=0.7
        )
        assert not weak_signal.is_actionable
    
    def test_is_strong_property(self):
        """Тест свойства is_strong"""
        # Сильный сигнал по типу
        strong_buy = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.STRONG_BUY,
            source=SignalSource.MACD,
            strength=0.5,
            confidence=0.5
        )
        assert strong_buy.is_strong
        
        # Сильный сигнал по метрикам
        strong_metrics = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.8,
            confidence=0.85
        )
        assert strong_metrics.is_strong
        
        # Слабый сигнал
        weak_signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.WEAK_BUY,
            source=SignalSource.MACD,
            strength=0.3,
            confidence=0.4
        )
        assert not weak_signal.is_strong
    
    def test_is_bullish_property(self):
        """Тест свойства is_bullish"""
        buy_signals = [SignalType.BUY, SignalType.STRONG_BUY, SignalType.WEAK_BUY]
        
        for signal_type in buy_signals:
            signal = TradingSignal(
                symbol="BTCUSDT",
                timestamp=123456789,
                signal_type=signal_type,
                source=SignalSource.MACD,
                strength=0.7
            )
            assert signal.is_bullish
        
        # Медвежий сигнал не должен быть бычьим
        sell_signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.SELL,
            source=SignalSource.MACD,
            strength=0.7
        )
        assert not sell_signal.is_bullish
    
    def test_is_bearish_property(self):
        """Тест свойства is_bearish"""
        sell_signals = [SignalType.SELL, SignalType.STRONG_SELL, SignalType.WEAK_SELL]
        
        for signal_type in sell_signals:
            signal = TradingSignal(
                symbol="BTCUSDT",
                timestamp=123456789,
                signal_type=signal_type,
                source=SignalSource.MACD,
                strength=0.7
            )
            assert signal.is_bearish
        
        # Бычий сигнал не должен быть медвежьим
        buy_signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.7
        )
        assert not buy_signal.is_bearish
    
    def test_score_property(self):
        """Тест свойства score"""
        signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.8,
            confidence=0.6
        )
        
        expected_score = 0.8 * 0.6  # strength * confidence
        assert abs(signal.score - expected_score) < 0.001
    
    def test_get_recommendation(self):
        """Тест получения рекомендации"""
        # Сильный бычий сигнал
        strong_buy = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.STRONG_BUY,
            source=SignalSource.MACD,
            strength=0.9,
            confidence=0.8
        )
        recommendation = strong_buy.get_recommendation()
        assert "ПОКУПАТЬ" in recommendation
        assert "сильный сигнал" in recommendation
        
        # Слабый медвежий сигнал
        weak_sell = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.WEAK_SELL,
            source=SignalSource.RSI,
            strength=0.4,
            confidence=0.3
        )
        recommendation = weak_sell.get_recommendation()
        assert "HOLD" in recommendation
        assert "недостаточно сильный" in recommendation
    
    def test_conflicts_with(self):
        """Тест проверки конфликта с другим сигналом"""
        timestamp = int(time.time() * 1000)
        
        # Конфликтующие сигналы (разные направления, близкое время)
        buy_signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.7
        )
        
        sell_signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp + 30000,  # 30 секунд позже
            signal_type=SignalType.SELL,
            source=SignalSource.RSI,
            strength=0.8
        )
        
        assert buy_signal.conflicts_with(sell_signal)
        assert sell_signal.conflicts_with(buy_signal)
        
        # Не конфликтующие сигналы (то же направление)
        another_buy = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp + 30000,
            signal_type=SignalType.STRONG_BUY,
            source=SignalSource.RSI,
            strength=0.8
        )
        
        assert not buy_signal.conflicts_with(another_buy)
        
        # Не конфликтующие сигналы (большая временная разница)
        old_sell = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp - 120000,  # 2 минуты назад
            signal_type=SignalType.SELL,
            source=SignalSource.RSI,
            strength=0.8
        )
        
        assert not buy_signal.conflicts_with(old_sell)
    
    def test_combine_with(self):
        """Тест комбинирования сигналов"""
        timestamp = int(time.time() * 1000)
        
        # Комбинируемые сигналы (одно направление)
        macd_buy = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.7,
            confidence=0.6
        )
        
        rsi_buy = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp + 10000,
            signal_type=SignalType.STRONG_BUY,
            source=SignalSource.RSI,
            strength=0.8,
            confidence=0.7
        )
        
        combined = macd_buy.combine_with(rsi_buy)
        
        assert combined is not None
        assert combined.source == SignalSource.COMBINED
        assert combined.symbol == "BTCUSDT"
        assert combined.timestamp == timestamp  # Минимальный timestamp
        assert combined.strength == (0.7 + 0.8) / 2  # Среднее
        assert combined.confidence == min(0.6 + 0.7, 1.0)  # Сумма с ограничением
        assert "combined_from" in combined.metadata
        
        # Не комбинируемые сигналы (разные направления)
        sell_signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp,
            signal_type=SignalType.SELL,
            source=SignalSource.RSI,
            strength=0.8
        )
        
        not_combined = macd_buy.combine_with(sell_signal)
        assert not_combined is None
    
    def test_to_dict(self):
        """Тест сериализации в словарь"""
        timestamp = int(time.time() * 1000)
        metadata = {"volume": 1000, "price_change": 0.05}
        
        signal = TradingSignal(
            symbol="ETHUSDT",
            timestamp=timestamp,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.8,
            confidence=0.7,
            price=3000.5,
            metadata=metadata
        )
        
        data = signal.to_dict()
        
        assert data['symbol'] == "ETHUSDT"
        assert data['timestamp'] == timestamp
        assert data['signal_type'] == "buy"
        assert data['source'] == "macd"
        assert data['strength'] == 0.8
        assert data['confidence'] == 0.7
        assert data['price'] == 3000.5
        assert data['metadata'] == metadata
        assert 'signal_id' in data
        assert 'score' in data
        assert 'is_actionable' in data
        assert 'is_strong' in data
        assert 'created_at' in data
    
    def test_from_dict(self):
        """Тест десериализации из словаря"""
        timestamp = int(time.time() * 1000)
        data = {
            'symbol': 'BTCUSDT',
            'timestamp': timestamp,
            'signal_type': 'strong_sell',
            'source': 'rsi',
            'strength': 0.9,
            'confidence': 0.85,
            'price': 45000.0,
            'metadata': {'rsi_value': 80, 'overbought': True}
        }
        
        signal = TradingSignal.from_dict(data)
        
        assert signal.symbol == 'BTCUSDT'
        assert signal.timestamp == timestamp
        assert signal.signal_type == SignalType.STRONG_SELL
        assert signal.source == SignalSource.RSI
        assert signal.strength == 0.9
        assert signal.confidence == 0.85
        assert signal.price == 45000.0
        assert signal.metadata == {'rsi_value': 80, 'overbought': True}
    
    def test_json_serialization(self):
        """Тест JSON сериализации"""
        signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.7,
            confidence=0.6
        )
        
        json_str = signal.to_json()
        assert isinstance(json_str, str)
        assert "BTCUSDT" in json_str
        assert "buy" in json_str
        assert "macd" in json_str
        
        # Тест обратной конвертации
        restored_signal = TradingSignal.from_json(json_str)
        assert restored_signal.symbol == signal.symbol
        assert restored_signal.signal_type == signal.signal_type
        assert restored_signal.source == signal.source
        assert restored_signal.strength == signal.strength
        assert restored_signal.confidence == signal.confidence
    
    def test_equality(self):
        """Тест равенства сигналов"""
        timestamp = int(time.time() * 1000)
        
        signal1 = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.7
        )
        
        signal2 = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp,
            signal_type=SignalType.BUY,
            source=SignalSource.MACD,
            strength=0.8  # Другая сила, но тот же ID
        )
        
        signal3 = TradingSignal(
            symbol="BTCUSDT",
            timestamp=timestamp,
            signal_type=SignalType.SELL,  # Другой тип
            source=SignalSource.MACD,
            strength=0.7
        )
        
        # Равенство основано на signal_id
        assert signal1 == signal2  # Same ID components except strength
        assert signal1 != signal3  # Different signal type
    
    def test_string_representation(self):
        """Тест строкового представления"""
        signal = TradingSignal(
            symbol="BTCUSDT",
            timestamp=123456789,
            signal_type=SignalType.STRONG_BUY,
            source=SignalSource.MACD,
            strength=0.8,
            confidence=0.7
        )
        
        str_repr = str(signal)
        assert "strong_buy" in str_repr
        assert "macd" in str_repr
        assert "BTCUSDT" in str_repr
        assert "score=" in str_repr