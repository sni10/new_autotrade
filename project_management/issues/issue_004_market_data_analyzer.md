# Issue #004: MarketDataAnalyzer - Улучшенный анализ рынка
### Статус: запланировано

**🏗️ Milestone:** M1  
**📈 Приоритет:** MEDIUM  
**🔗 Зависимости:** Issue #1 (TradingOrchestrator)

---

## 📝 Описание проблемы


### 🔍 Текущее состояние:
- `MarketAnalysisService` анализирует волатильность каждые 50 тиков
- Анализ трендов встроен в `TickerService`
- Нет единого API для получения рыночной информации
- Дублирование логики между сервисами

### 🎯 Желаемый результат:
- Единый `MarketDataAnalyzer` для всего рыночного анализа
- Структурированные данные о состоянии рынка
- Лучшие торговые решения на основе глубокого анализа

---

## 📋 Технические требования

### 🏗️ Архитектура

```python
class MarketDataAnalyzer:
    \"\"\"Централизованный анализ рыночных данных\"\"\"
    
    def __init__(self, tickers_repo: TickersRepository):
        self.tickers_repo = tickers_repo
        self.cache_ttl = 60  # Cache for 60 seconds
        
    async def analyze_market_conditions(self, symbol: str) -> MarketConditions:
        \"\"\"Полный анализ рыночных условий\"\"\"
        
    async def calculate_volatility(self, symbol: str, period: int = 50) -> VolatilityData:
        \"\"\"Расчет волатильности за период\"\"\"
        
    async def detect_trend(self, symbol: str, period: int = 100) -> TrendData:
        \"\"\"Определение тренда и его силы\"\"\"
        
    async def analyze_volume_profile(self, symbol: str) -> VolumeProfile:
        \"\"\"Анализ объемов торгов\"\"\"
        
    async def get_trading_recommendation(self, conditions: MarketConditions) -> TradingRecommendation:
        \"\"\"Рекомендации по торговле\"\"\"
```

### 📊 Структуры данных

```python
@dataclass
class MarketConditions:
    symbol: str
    timestamp: int
    volatility: VolatilityData
    trend: TrendData
    volume_profile: VolumeProfile
    trading_recommendation: TradingRecommendation
    confidence_score: float

@dataclass  
class VolatilityData:
    current_volatility: float
    average_volatility: float
    volatility_percentile: float
    is_high_volatility: bool
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH'

@dataclass
class TrendData:
    direction: str  # 'BULLISH', 'BEARISH', 'SIDEWAYS'
    strength: float  # 0.0 to 1.0
    duration_ticks: int
    support_level: Optional[float]
    resistance_level: Optional[float]

@dataclass
class VolumeProfile:
    average_volume: float
    current_volume_ratio: float  # vs average
    high_volume_threshold: float
    is_above_average: bool

@dataclass
class TradingRecommendation:
    action: str  # 'BUY', 'SELL', 'HOLD', 'AVOID'
    confidence: float
    reasons: List[str]
    risk_assessment: str
```

---

## 🛠️ Детальная реализация

### 1. **Создание основного анализатора**

**Файл:** `domain/services/market_data_analyzer.py`

```python
import asyncio
from typing import Optional, List
from dataclasses import dataclass
from statistics import stdev, mean

from domain.entities.ticker import Ticker
from infrastructure.repositories.tickers_repository import TickersRepository

class MarketDataAnalyzer:
    def __init__(self, tickers_repo: TickersRepository):
        self.tickers_repo = tickers_repo
        self._cache = {}
        self._cache_ttl = 60
        
    async def analyze_market_conditions(self, symbol: str) -> MarketConditions:
        \"\"\"Полный анализ рыночных условий\"\"\"
        
        # Get recent tickers for analysis
        recent_tickers = await self.tickers_repo.get_recent(symbol, limit=200)
        
        if len(recent_tickers) < 50:
            raise ValueError(f"Not enough data for analysis: {len(recent_tickers)}")
            
        # Parallel analysis
        volatility_task = self.calculate_volatility_data(recent_tickers)
        trend_task = self.detect_trend_data(recent_tickers)
        volume_task = self.analyze_volume_data(recent_tickers)
        
        volatility, trend, volume = await asyncio.gather(
            volatility_task, trend_task, volume_task
        )
        
        # Generate recommendation
        recommendation = await self.get_trading_recommendation(volatility, trend, volume)
        
        # Calculate overall confidence
        confidence = self._calculate_overall_confidence(volatility, trend, volume, recommendation)
        
        return MarketConditions(
            symbol=symbol,
            timestamp=recent_tickers[0].timestamp,
            volatility=volatility,
            trend=trend,
            volume_profile=volume,
            trading_recommendation=recommendation,
            confidence_score=confidence
        )
        
    async def calculate_volatility_data(self, tickers: List[Ticker]) -> VolatilityData:
        \"\"\"Детальный анализ волатильности\"\"\"
        
        prices = [t.price for t in tickers[-50:]]  # Last 50 ticks
        
        # Current volatility (standard deviation of recent prices)
        current_volatility = stdev(prices) if len(prices) > 1 else 0.0
        
        # Average volatility over longer period
        if len(tickers) >= 200:
            historical_prices = [t.price for t in tickers[-200:]]
            windows = [historical_prices[i:i+50] for i in range(0, len(historical_prices)-50, 10)]
            historical_volatilities = [stdev(window) for window in windows if len(window) == 50]
            average_volatility = mean(historical_volatilities) if historical_volatilities else current_volatility
        else:
            average_volatility = current_volatility
            
        # Volatility percentile
        volatility_ratio = current_volatility / average_volatility if average_volatility > 0 else 1.0
        
        # Risk assessment
        if volatility_ratio > 1.5:
            risk_level = 'HIGH'
        elif volatility_ratio > 1.2:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
            
        return VolatilityData(
            current_volatility=current_volatility,
            average_volatility=average_volatility,
            volatility_percentile=volatility_ratio,
            is_high_volatility=volatility_ratio > 1.3,
            risk_level=risk_level
        )
        
    async def detect_trend_data(self, tickers: List[Ticker]) -> TrendData:
        \"\"\"Определение тренда и уровней поддержки/сопротивления\"\"\"
        
        prices = [t.price for t in tickers[-100:]]  # Last 100 ticks
        
        # Simple trend detection using linear regression slope
        n = len(prices)
        x_mean = (n - 1) / 2
        y_mean = mean(prices)
        
        slope_numerator = sum((i - x_mean) * (prices[i] - y_mean) for i in range(n))
        slope_denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = slope_numerator / slope_denominator if slope_denominator != 0 else 0
        
        # Determine trend direction and strength
        if slope > 0.0001:
            direction = 'BULLISH'
            strength = min(abs(slope) * 10000, 1.0)  # Normalize strength
        elif slope < -0.0001:
            direction = 'BEARISH'
            strength = min(abs(slope) * 10000, 1.0)
        else:
            direction = 'SIDEWAYS'
            strength = 0.1
            
        # Find support and resistance levels
        support_level = min(prices[-20:]) if len(prices) >= 20 else None
        resistance_level = max(prices[-20:]) if len(prices) >= 20 else None
        
        return TrendData(
            direction=direction,
            strength=strength,
            duration_ticks=len(tickers),
            support_level=support_level,
            resistance_level=resistance_level
        )
        
    async def analyze_volume_data(self, tickers: List[Ticker]) -> VolumeProfile:
        \"\"\"Анализ объемов торгов\"\"\"
        
        volumes = [t.volume for t in tickers if hasattr(t, 'volume') and t.volume]
        
        if not volumes:
            # Fallback if no volume data
            return VolumeProfile(
                average_volume=0.0,
                current_volume_ratio=1.0,
                high_volume_threshold=0.0,
                is_above_average=False
            )
            
        average_volume = mean(volumes)
        current_volume = volumes[-1] if volumes else 0.0
        current_ratio = current_volume / average_volume if average_volume > 0 else 1.0
        
        high_threshold = average_volume * 1.5
        
        return VolumeProfile(
            average_volume=average_volume,
            current_volume_ratio=current_ratio,
            high_volume_threshold=high_threshold,
            is_above_average=current_volume > average_volume
        )
        
    async def get_trading_recommendation(self, volatility: VolatilityData, 
                                       trend: TrendData, volume: VolumeProfile) -> TradingRecommendation:
        \"\"\"Генерация торговых рекомендаций\"\"\"
        
        reasons = []
        confidence = 0.0
        
        # Trend analysis
        if trend.direction == 'BULLISH' and trend.strength > 0.6:
            action = 'BUY'
            confidence += 0.4
            reasons.append(f\"Strong bullish trend (strength: {trend.strength:.2f})\")
        elif trend.direction == 'BEARISH' and trend.strength > 0.6:
            action = 'SELL'
            confidence += 0.4
            reasons.append(f\"Strong bearish trend (strength: {trend.strength:.2f})\")
        else:
            action = 'HOLD'
            confidence += 0.1
            reasons.append(\"Weak or sideways trend\")
            
        # Volatility analysis
        if volatility.risk_level == 'HIGH':
            if action in ['BUY', 'SELL']:
                action = 'AVOID'
                reasons.append(\"High volatility - avoiding trades\")
            confidence -= 0.2
        elif volatility.risk_level == 'LOW':
            confidence += 0.2
            reasons.append(\"Low volatility - favorable conditions\")
            
        # Volume analysis
        if volume.is_above_average:
            confidence += 0.1
            reasons.append(\"Above average volume\")
        else:
            confidence -= 0.1
            reasons.append(\"Below average volume\")
            
        # Risk assessment
        if volatility.risk_level == 'HIGH' or confidence < 0.3:
            risk_assessment = 'HIGH'
        elif confidence > 0.7:
            risk_assessment = 'LOW'
        else:
            risk_assessment = 'MEDIUM'
            
        return TradingRecommendation(
            action=action,
            confidence=max(0.0, min(1.0, confidence)),
            reasons=reasons,
            risk_assessment=risk_assessment
        )
        
    def _calculate_overall_confidence(self, volatility: VolatilityData, trend: TrendData, 
                                    volume: VolumeProfile, recommendation: TradingRecommendation) -> float:
        \"\"\"Расчет общей уверенности в анализе\"\"\"
        
        base_confidence = recommendation.confidence
        
        # Adjust based on data quality
        if trend.duration_ticks < 50:
            base_confidence *= 0.8  # Less data = less confidence
            
        if volatility.risk_level == 'HIGH':
            base_confidence *= 0.7  # High volatility = uncertainty
            
        return max(0.0, min(1.0, base_confidence))
```

### 2. **Интеграция с TradingOrchestrator**

```python
# В TradingOrchestrator добавить:
from domain.services.market_data_analyzer import MarketDataAnalyzer

class TradingOrchestrator:
    def __init__(self, ..., market_analyzer: MarketDataAnalyzer):
        # ...
        self.market_analyzer = market_analyzer
        
    async def process_tick(self, ticker: Ticker):
        # Получить рыночные условия
        market_conditions = await self.market_analyzer.analyze_market_conditions(ticker.symbol)
        
        # Использовать в принятии решений
        if market_conditions.trading_recommendation.action == 'AVOID':
            logger.info(f\"⚠️ Market analyzer recommends AVOID: {market_conditions.trading_recommendation.reasons}\")
            return
            
        # Продолжить обычную логику с учетом рекомендаций
        # ...
```

---

## ✅ Критерии приемки

### Функциональные требования:
- [ ] `MarketDataAnalyzer` предоставляет полный анализ рыночных условий
- [ ] Корректно рассчитывает волатильность, тренд и объемы
- [ ] Генерирует обоснованные торговые рекомендации
- [ ] Интегрирован с `TradingOrchestrator`
- [ ] Кеширование результатов для производительности

### Нефункциональные требования:
- [ ] Время анализа < 5ms для стандартного набора данных
- [ ] Покрытие тестами > 80%
- [ ] Обработка граничных случаев (мало данных, отсутствие объемов)
- [ ] Логирование всех ключевых решений

### Интеграционные тесты:
- [ ] Корректная работа с различными рыночными условиями
- [ ] Стабильность при длительной работе
- [ ] Правильная обработка исторических данных

---

## 🚧 Риски и митигация

### Риск 1: Недостаток исторических данных
**Митигация:** Graceful degradation - использовать доступные данные с соответствующим снижением confidence

### Риск 2: Ложные сигналы от анализатора
**Митигация:** Консервативные пороги и обязательная проверка confidence_score

### Риск 3: Производительность при больших объемах данных
**Митигация:** Кеширование результатов и оптимизация алгоритмов

---

## 📚 Связанные материалы

- [Technical Analysis Library Documentation](https://technical-analysis-library-in-python.readthedocs.io/)
- [Market Volatility Analysis Methods](https://www.investopedia.com/terms/v/volatility.asp)
- Existing: `domain/services/market_analysis_service.py`
- Existing: `domain/services/ticker_service.py`
