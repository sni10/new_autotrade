import pytest
from datetime import datetime
import time
import math

from src.domain.entities.indicator_data import (
    IndicatorData, IndicatorType, IndicatorLevel
)


class TestIndicatorType:
    """Тесты для IndicatorType enum"""
    
    def test_indicator_types_exist(self):
        """Тест наличия всех типов индикаторов"""
        assert IndicatorType.SMA
        assert IndicatorType.EMA
        assert IndicatorType.RSI
        assert IndicatorType.MACD
        assert IndicatorType.MACD_SIGNAL
        assert IndicatorType.MACD_HISTOGRAM
        assert IndicatorType.BOLLINGER_UPPER
        assert IndicatorType.BOLLINGER_MIDDLE
        assert IndicatorType.BOLLINGER_LOWER
        assert IndicatorType.VOLUME
        assert IndicatorType.VOLATILITY
    
    def test_indicator_type_values(self):
        """Тест значений типов индикаторов"""
        assert IndicatorType.SMA.value == "sma"
        assert IndicatorType.RSI.value == "rsi"
        assert IndicatorType.MACD.value == "macd"


class TestIndicatorLevel:
    """Тесты для IndicatorLevel enum"""
    
    def test_indicator_levels_exist(self):
        """Тест наличия всех уровней сложности"""
        assert IndicatorLevel.FAST
        assert IndicatorLevel.MEDIUM
        assert IndicatorLevel.HEAVY
    
    def test_indicator_level_values(self):
        """Тест значений уровней"""
        assert IndicatorLevel.FAST.value == "fast"
        assert IndicatorLevel.MEDIUM.value == "medium"
        assert IndicatorLevel.HEAVY.value == "heavy"


class TestIndicatorData:
    """Тесты для IndicatorData"""
    
    def test_create_indicator_data_minimal(self):
        """Тест создания индикатора с минимальными параметрами"""
        timestamp = int(time.time() * 1000)
        
        indicator = IndicatorData(
            symbol="BTCUSDT",
            timestamp=timestamp,
            indicator_type=IndicatorType.SMA,
            value=45000.5
        )
        
        assert indicator.symbol == "BTCUSDT"
        assert indicator.timestamp == timestamp
        assert indicator.indicator_type == IndicatorType.SMA
        assert indicator.value == 45000.5
        assert indicator.period is None
        assert indicator.level == IndicatorLevel.FAST
        assert indicator.metadata == {}
    
    def test_create_indicator_data_full(self):
        """Тест создания индикатора со всеми параметрами"""
        timestamp = int(time.time() * 1000)
        metadata = {"source": "manual", "confidence": 0.95}
        
        indicator = IndicatorData(
            symbol="ETHUSDT",
            timestamp=timestamp,
            indicator_type=IndicatorType.RSI,
            value=65.75,
            period=14,
            level=IndicatorLevel.MEDIUM,
            metadata=metadata
        )
        
        assert indicator.symbol == "ETHUSDT"
        assert indicator.timestamp == timestamp
        assert indicator.indicator_type == IndicatorType.RSI
        assert indicator.value == 65.75
        assert indicator.period == 14
        assert indicator.level == IndicatorLevel.MEDIUM
        assert indicator.metadata == metadata
    
    def test_indicator_name_property(self):
        """Тест свойства indicator_name"""
        # С периодом
        indicator_with_period = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.SMA,
            value=45000.0,
            period=20
        )
        assert indicator_with_period.indicator_name == "sma_20"
        
        # Без периода
        indicator_without_period = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=65.0
        )
        assert indicator_without_period.indicator_name == "rsi"
    
    def test_is_valid(self):
        """Тест валидации данных индикатора"""
        # Валидный индикатор
        valid_indicator = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.SMA,
            value=45000.0
        )
        assert valid_indicator.is_valid()
        
        # Индикатор с NaN
        nan_indicator = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.SMA,
            value=float('nan')
        )
        assert not nan_indicator.is_valid()
        
        # Индикатор с бесконечностью
        inf_indicator = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.SMA,
            value=float('inf')
        )
        assert not inf_indicator.is_valid()
        
        # Индикатор с нулевым timestamp
        zero_timestamp_indicator = IndicatorData(
            symbol="BTCUSDT",
            timestamp=0,
            indicator_type=IndicatorType.SMA,
            value=45000.0
        )
        assert not zero_timestamp_indicator.is_valid()
    
    def test_is_bullish_signal(self):
        """Тест определения бычьего сигнала"""
        # RSI в нейтральной зоне
        rsi_neutral = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=50.0
        )
        assert rsi_neutral.is_bullish_signal() is True
        
        # RSI перекупленность
        rsi_overbought = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=75.0
        )
        assert rsi_overbought.is_bullish_signal() is False
        
        # RSI перепроданность
        rsi_oversold = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=25.0
        )
        assert rsi_oversold.is_bullish_signal() is False
        
        # MACD гистограмма положительная
        macd_positive = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.MACD_HISTOGRAM,
            value=5.0
        )
        assert macd_positive.is_bullish_signal() is True
        
        # MACD гистограмма отрицательная
        macd_negative = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.MACD_HISTOGRAM,
            value=-5.0
        )
        assert macd_negative.is_bullish_signal() is False
        
        # SMA/EMA (возвращает None)
        sma = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.SMA,
            value=45000.0
        )
        assert sma.is_bullish_signal() is None
    
    def test_is_bearish_signal(self):
        """Тест определения медвежьего сигнала"""
        # RSI перекупленность
        rsi_overbought = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=75.0
        )
        assert rsi_overbought.is_bearish_signal() is True
        
        # RSI перепроданность
        rsi_oversold = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=25.0
        )
        assert rsi_oversold.is_bearish_signal() is True
        
        # RSI в нейтральной зоне
        rsi_neutral = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=50.0
        )
        assert rsi_neutral.is_bearish_signal() is False
        
        # MACD гистограмма отрицательная
        macd_negative = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.MACD_HISTOGRAM,
            value=-5.0
        )
        assert macd_negative.is_bearish_signal() is True
        
        # MACD гистограмма положительная
        macd_positive = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.MACD_HISTOGRAM,
            value=5.0
        )
        assert macd_positive.is_bearish_signal() is False
    
    def test_get_signal_strength(self):
        """Тест расчета силы сигнала"""
        # RSI экстремальные значения
        rsi_extreme_high = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=85.0
        )
        strength_high = rsi_extreme_high.get_signal_strength()
        expected_high = min((85.0 - 70) / 30, 1.0)  # (85-70)/30 = 0.5
        assert abs(strength_high - expected_high) < 0.001
        
        rsi_extreme_low = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=15.0
        )
        strength_low = rsi_extreme_low.get_signal_strength()
        expected_low = min((30 - 15.0) / 30, 1.0)  # (30-15)/30 = 0.5
        assert abs(strength_low - expected_low) < 0.001
        
        # RSI в нейтральной зоне
        rsi_neutral = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=50.0
        )
        assert rsi_neutral.get_signal_strength() == 0.0
        
        # MACD гистограмма
        macd_histogram = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.MACD_HISTOGRAM,
            value=50.0
        )
        strength_macd = macd_histogram.get_signal_strength()
        expected_macd = min(abs(50.0) / 100, 1.0)  # 50/100 = 0.5
        assert abs(strength_macd - expected_macd) < 0.001
        
        # Другие типы индикаторов
        sma = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.SMA,
            value=45000.0
        )
        assert sma.get_signal_strength() == 0.5  # Дефолтное значение
    
    def test_to_dict(self):
        """Тест сериализации в словарь"""
        metadata = {"source": "calculation", "confidence": 0.9}
        
        indicator = IndicatorData(
            symbol="ETHUSDT",
            timestamp=1234567890,
            indicator_type=IndicatorType.RSI,
            value=65.5,
            period=14,
            level=IndicatorLevel.MEDIUM,
            metadata=metadata
        )
        
        data = indicator.to_dict()
        
        assert data['symbol'] == "ETHUSDT"
        assert data['timestamp'] == 1234567890
        assert data['indicator_type'] == "rsi"
        assert data['value'] == 65.5
        assert data['period'] == 14
        assert data['level'] == "medium"
        assert data['metadata'] == metadata
        assert 'created_at' in data
    
    def test_from_dict(self):
        """Тест десериализации из словаря"""
        data = {
            'symbol': 'BTCUSDT',
            'timestamp': 9876543210,
            'indicator_type': 'macd',
            'value': 125.75,
            'period': 26,
            'level': 'heavy',
            'metadata': {'source': 'auto', 'version': '1.0'}
        }
        
        indicator = IndicatorData.from_dict(data)
        
        assert indicator.symbol == 'BTCUSDT'
        assert indicator.timestamp == 9876543210
        assert indicator.indicator_type == IndicatorType.MACD
        assert indicator.value == 125.75
        assert indicator.period == 26
        assert indicator.level == IndicatorLevel.HEAVY
        assert indicator.metadata == {'source': 'auto', 'version': '1.0'}
    
    def test_from_dict_minimal(self):
        """Тест десериализации с минимальными данными"""
        data = {
            'symbol': 'ADAUSDT',
            'timestamp': 1111111111,
            'indicator_type': 'sma',
            'value': 1.25
        }
        
        indicator = IndicatorData.from_dict(data)
        
        assert indicator.symbol == 'ADAUSDT'
        assert indicator.indicator_type == IndicatorType.SMA
        assert indicator.value == 1.25
        assert indicator.period is None
        assert indicator.level == IndicatorLevel.FAST
        assert indicator.metadata == {}
    
    def test_json_serialization(self):
        """Тест JSON сериализации"""
        indicator = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=65.5
        )
        
        json_str = indicator.to_json()
        assert isinstance(json_str, str)
        assert "BTCUSDT" in json_str
        assert "rsi" in json_str
        
        # Тест обратной конвертации
        restored_indicator = IndicatorData.from_json(json_str)
        assert restored_indicator.symbol == indicator.symbol
        assert restored_indicator.indicator_type == indicator.indicator_type
        assert restored_indicator.value == indicator.value
    
    def test_equality(self):
        """Тест равенства индикаторов"""
        indicator1 = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.SMA,
            value=45000.0,
            period=20
        )
        indicator2 = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.SMA,
            value=46000.0,  # Другое значение
            period=20
        )
        indicator3 = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,  # Другой тип
            value=45000.0,
            period=20
        )
        
        # Равенство основано на symbol, timestamp, indicator_type и period
        assert indicator1 == indicator2  # Разные значения, но остальное одинаково
        assert indicator1 != indicator3  # Разные типы индикаторов
    
    def test_string_representation(self):
        """Тест строкового представления"""
        indicator = IndicatorData(
            symbol="BTCUSDT",
            timestamp=123456789,
            indicator_type=IndicatorType.RSI,
            value=65.123456,
            period=14
        )
        
        str_repr = str(indicator)
        assert "BTCUSDT" in str_repr
        assert "rsi_14" in str_repr  # indicator_name
        assert "65.123456" in str_repr
        assert "fast" in str_repr  # default level