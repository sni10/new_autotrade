# Issue #005: SignalAggregationService - Агрегация сигналов

**💰 Стоимость:** $120 (8 часов × $15/час)  
**🏗️ Milestone:** M1  
**📈 Приоритет:** MEDIUM  
**🔗 Зависимости:** Issue #4 (MarketDataAnalyzer)

---

## 📝 Описание проблемы

Сейчас сигналы от разных источников (MACD, OrderBook, Volatility) обрабатываются разрозненно. Нужен централизованный сервис для объединения всех сигналов и принятия финального решения.

### 🔍 Текущее состояние:
- MACD сигналы генерируются в `SignalService`
- OrderBook анализ в `OrderBookAnalyzer`
- Market условия в `MarketAnalysisService`
- Нет единой логики принятия решений
- Конфликтующие сигналы могут привести к ошибкам

### 🎯 Желаемый результат:
- Единый `SignalAggregationService` для всех типов сигналов
- Взвешенное принятие решений
- Меньше ложных сигналов
- Структурированная система confidence scoring

---

## 📋 Технические требования

### 🏗️ Архитектура

```python
class SignalAggregationService:
    \"\"\"Агрегация и взвешивание торговых сигналов\"\"\"
    
    def __init__(self, signal_service: SignalService, 
                 orderbook_analyzer: OrderBookAnalyzer,
                 market_analyzer: MarketDataAnalyzer):
        self.signal_service = signal_service
        self.orderbook_analyzer = orderbook_analyzer
        self.market_analyzer = market_analyzer
        
    async def aggregate_signals(self, ticker: Ticker) -> AggregatedSignal:
        \"\"\"Объединение всех типов сигналов\"\"\"
        
    async def calculate_final_decision(self, aggregated: AggregatedSignal) -> TradingDecision:
        \"\"\"Финальное решение на основе всех сигналов\"\"\"
        
    def _weight_signals(self, signals: Dict[str, Signal]) -> Dict[str, float]:
        \"\"\"Взвешивание сигналов по важности\"\"\"
        
    def _resolve_conflicts(self, signals: Dict[str, Signal]) -> ConflictResolution:
        \"\"\"Разрешение конфликтующих сигналов\"\"\"
```

### 📊 Структуры данных

```python
@dataclass
class Signal:
    source: str  # 'MACD', 'ORDERBOOK', 'MARKET', 'VOLATILITY'
    action: str  # 'BUY', 'SELL', 'HOLD', 'REJECT'
    confidence: float  # 0.0 to 1.0
    strength: float   # Signal strength
    reasons: List[str]
    timestamp: int
    metadata: Dict[str, Any]

@dataclass
class AggregatedSignal:
    signals: Dict[str, Signal]
    weighted_scores: Dict[str, float]
    conflicts: List[SignalConflict]
    overall_confidence: float
    recommended_action: str
    timestamp: int

@dataclass  
class TradingDecision:
    action: str  # 'BUY', 'SELL', 'HOLD', 'REJECT'
    confidence: float
    reasoning: List[str]
    risk_level: str
    signal_breakdown: Dict[str, float]
    metadata: Dict[str, Any]

@dataclass
class SignalConflict:
    signal1: str
    signal2: str
    conflict_type: str  # 'DIRECTION', 'CONFIDENCE', 'TIMING'
    resolution: str
    impact_on_confidence: float
```

---

## 🛠️ Детальная реализация

### 1. **Основной сервис агрегации**

**Файл:** `domain/services/signal_aggregation_service.py`

```python
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from statistics import mean, stdev

from domain.entities.ticker import Ticker
from domain.services.signal_service import SignalService
from domain.services.orderbook_analyzer import OrderBookAnalyzer  
from domain.services.market_data_analyzer import MarketDataAnalyzer

class SignalAggregationService:
    def __init__(self, signal_service: SignalService,
                 orderbook_analyzer: OrderBookAnalyzer,
                 market_analyzer: MarketDataAnalyzer):
        self.signal_service = signal_service
        self.orderbook_analyzer = orderbook_analyzer
        self.market_analyzer = market_analyzer
        
        # Веса для разных типов сигналов
        self.signal_weights = {
            'MACD': 0.4,      # Основной технический индикатор
            'ORDERBOOK': 0.3,  # Анализ ликвидности
            'MARKET': 0.2,     # Рыночные условия
            'VOLATILITY': 0.1  # Волатильность
        }
        
        # Минимальные пороги для принятия решений
        self.thresholds = {
            'min_confidence': 0.6,
            'min_signal_agreement': 0.7,
            'max_conflict_impact': -0.3
        }
        
    async def aggregate_signals(self, ticker: Ticker) -> AggregatedSignal:
        \"\"\"Объединение всех типов сигналов\"\"\"
        
        # Параллельное получение всех сигналов
        macd_task = self._get_macd_signal(ticker)
        orderbook_task = self._get_orderbook_signal(ticker)
        market_task = self._get_market_signal(ticker)
        
        macd_signal, orderbook_signal, market_signal = await asyncio.gather(
            macd_task, orderbook_task, market_task
        )
        
        # Создание словаря сигналов
        signals = {}
        if macd_signal:
            signals['MACD'] = macd_signal
        if orderbook_signal:
            signals['ORDERBOOK'] = orderbook_signal  
        if market_signal:
            signals['MARKET'] = market_signal
            
        # Взвешивание сигналов
        weighted_scores = self._weight_signals(signals)
        
        # Обнаружение конфликтов
        conflicts = self._detect_conflicts(signals)
        
        # Расчет общей уверенности
        overall_confidence = self._calculate_overall_confidence(signals, weighted_scores, conflicts)
        
        # Рекомендуемое действие
        recommended_action = self._determine_recommended_action(weighted_scores, overall_confidence)
        
        return AggregatedSignal(
            signals=signals,
            weighted_scores=weighted_scores,
            conflicts=conflicts,
            overall_confidence=overall_confidence,
            recommended_action=recommended_action,
            timestamp=ticker.timestamp
        )
        
    async def calculate_final_decision(self, aggregated: AggregatedSignal) -> TradingDecision:
        \"\"\"Финальное решение на основе всех сигналов\"\"\"
        
        # Базовое решение из агрегированного сигнала
        action = aggregated.recommended_action
        confidence = aggregated.overall_confidence
        
        # Проверка минимальных порогов
        if confidence < self.thresholds['min_confidence']:
            action = 'HOLD'
            reasoning = [f\"Confidence too low: {confidence:.2f} < {self.thresholds['min_confidence']}\"]
        else:
            reasoning = self._build_reasoning(aggregated)
            
        # Оценка риска
        risk_level = self._assess_risk_level(aggregated)
        
        # Дополнительные проверки безопасности
        if len(aggregated.conflicts) > 2:
            action = 'HOLD'
            reasoning.append(\"Too many signal conflicts detected\")
            
        return TradingDecision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            risk_level=risk_level,
            signal_breakdown=aggregated.weighted_scores,
            metadata={
                'conflicts_count': len(aggregated.conflicts),
                'signals_count': len(aggregated.signals),
                'strongest_signal': max(aggregated.signals.keys(), 
                                      key=lambda k: aggregated.signals[k].confidence)
            }
        )
        
    async def _get_macd_signal(self, ticker: Ticker) -> Optional[Signal]:
        \"\"\"Получение MACD сигнала\"\"\"
        try:
            # Используем существующий SignalService
            macd_signal = self.signal_service.get_macd_signal(ticker.signals)
            
            if macd_signal in ['BUY', 'SELL']:
                # Получаем дополнительную информацию
                macd_data = ticker.signals.get('macd', {})
                macd_value = macd_data.get('macd', 0)
                signal_value = macd_data.get('signal', 0)
                histogram = macd_data.get('histogram', 0)
                
                # Расчет уверенности на основе силы сигнала
                confidence = min(abs(histogram) * 1000, 1.0)  # Normalize histogram
                
                return Signal(
                    source='MACD',
                    action=macd_signal,
                    confidence=confidence,
                    strength=abs(macd_value - signal_value),
                    reasons=[f\"MACD {macd_signal.lower()}: {macd_value:.6f} vs {signal_value:.6f}\"],
                    timestamp=ticker.timestamp,
                    metadata={'macd': macd_value, 'signal': signal_value, 'histogram': histogram}
                )
        except Exception as e:
            # Log error but don't fail entire aggregation
            pass
            
        return None
        
    async def _get_orderbook_signal(self, ticker: Ticker) -> Optional[Signal]:
        \"\"\"Получение сигнала от анализа стакана\"\"\"
        try:
            # Анализ текущего состояния стакана
            orderbook_analysis = await self.orderbook_analyzer.analyze_current_orderbook()
            
            if orderbook_analysis:
                signal_mapping = {
                    'strong_buy': 'BUY',
                    'weak_buy': 'BUY', 
                    'neutral': 'HOLD',
                    'weak_sell': 'SELL',
                    'strong_sell': 'SELL',
                    'reject': 'REJECT'
                }
                
                action = signal_mapping.get(orderbook_analysis.get('signal', 'neutral'), 'HOLD')
                confidence = orderbook_analysis.get('confidence', 0.5)
                
                reasons = []
                if 'spread' in orderbook_analysis:
                    reasons.append(f\"Spread: {orderbook_analysis['spread']:.3f}%\")
                if 'imbalance' in orderbook_analysis:
                    reasons.append(f\"Imbalance: {orderbook_analysis['imbalance']:.1f}%\")
                    
                return Signal(
                    source='ORDERBOOK',
                    action=action,
                    confidence=confidence,
                    strength=abs(orderbook_analysis.get('imbalance', 0)) / 100,
                    reasons=reasons,
                    timestamp=ticker.timestamp,
                    metadata=orderbook_analysis
                )
        except Exception as e:
            pass
            
        return None
        
    async def _get_market_signal(self, ticker: Ticker) -> Optional[Signal]:
        \"\"\"Получение сигнала от анализа рынка\"\"\"
        try:
            market_conditions = await self.market_analyzer.analyze_market_conditions(ticker.symbol)
            
            if market_conditions and market_conditions.trading_recommendation:
                rec = market_conditions.trading_recommendation
                
                return Signal(
                    source='MARKET',
                    action=rec.action,
                    confidence=rec.confidence,
                    strength=market_conditions.trend.strength if market_conditions.trend else 0.5,
                    reasons=rec.reasons,
                    timestamp=ticker.timestamp,
                    metadata={
                        'trend_direction': market_conditions.trend.direction if market_conditions.trend else None,
                        'volatility_risk': market_conditions.volatility.risk_level if market_conditions.volatility else None,
                        'overall_confidence': market_conditions.confidence_score
                    }
                )
        except Exception as e:
            pass
            
        return None
        
    def _weight_signals(self, signals: Dict[str, Signal]) -> Dict[str, float]:
        \"\"\"Взвешивание сигналов по важности\"\"\"
        weighted_scores = {}
        
        for signal_type, signal in signals.items():
            base_weight = self.signal_weights.get(signal_type, 0.1)
            
            # Корректировка веса на основе уверенности
            confidence_multiplier = signal.confidence
            
            # Корректировка веса на основе силы сигнала
            strength_multiplier = min(signal.strength * 2, 1.0)  # Cap at 1.0
            
            final_weight = base_weight * confidence_multiplier * strength_multiplier
            
            # Направление сигнала влияет на знак
            if signal.action == 'BUY':
                weighted_scores[signal_type] = final_weight
            elif signal.action == 'SELL':
                weighted_scores[signal_type] = -final_weight
            else:  # HOLD, REJECT
                weighted_scores[signal_type] = 0.0
                
        return weighted_scores
        
    def _detect_conflicts(self, signals: Dict[str, Signal]) -> List[SignalConflict]:
        \"\"\"Обнаружение конфликтующих сигналов\"\"\"
        conflicts = []
        signal_items = list(signals.items())
        
        for i, (type1, signal1) in enumerate(signal_items):
            for type2, signal2 in signal_items[i+1:]:
                
                # Конфликт направления (BUY vs SELL)
                if (signal1.action == 'BUY' and signal2.action == 'SELL') or \
                   (signal1.action == 'SELL' and signal2.action == 'BUY'):
                    
                    conflicts.append(SignalConflict(
                        signal1=type1,
                        signal2=type2,
                        conflict_type='DIRECTION',
                        resolution=f\"Weighted by confidence: {signal1.confidence:.2f} vs {signal2.confidence:.2f}\",
                        impact_on_confidence=-0.2
                    ))
                    
                # Конфликт уверенности (высокая vs низкая при одном направлении)
                elif signal1.action == signal2.action and \
                     abs(signal1.confidence - signal2.confidence) > 0.4:
                    
                    conflicts.append(SignalConflict(
                        signal1=type1,
                        signal2=type2,
                        conflict_type='CONFIDENCE',
                        resolution=\"Using higher confidence signal\",
                        impact_on_confidence=-0.1
                    ))
                    
        return conflicts
        
    def _calculate_overall_confidence(self, signals: Dict[str, Signal], 
                                    weighted_scores: Dict[str, float],
                                    conflicts: List[SignalConflict]) -> float:
        \"\"\"Расчет общей уверенности\"\"\"
        
        if not signals:
            return 0.0
            
        # Базовая уверенность как среднее взвешенное
        confidences = [signal.confidence for signal in signals.values()]
        base_confidence = mean(confidences)
        
        # Корректировка на конфликты
        conflict_penalty = sum(conflict.impact_on_confidence for conflict in conflicts)
        
        # Корректировка на согласованность сигналов
        buy_signals = sum(1 for s in signals.values() if s.action == 'BUY')
        sell_signals = sum(1 for s in signals.values() if s.action == 'SELL')
        
        if len(signals) > 1:
            agreement_ratio = max(buy_signals, sell_signals) / len(signals)
            if agreement_ratio < self.thresholds['min_signal_agreement']:
                base_confidence *= 0.8
                
        final_confidence = base_confidence + conflict_penalty
        return max(0.0, min(1.0, final_confidence))
        
    def _determine_recommended_action(self, weighted_scores: Dict[str, float], 
                                    overall_confidence: float) -> str:
        \"\"\"Определение рекомендуемого действия\"\"\"
        
        if not weighted_scores:
            return 'HOLD'
            
        # Суммарный взвешенный скор
        total_score = sum(weighted_scores.values())
        
        # Пороги для принятия решений
        if overall_confidence < self.thresholds['min_confidence']:
            return 'HOLD'
            
        if total_score > 0.3:
            return 'BUY'
        elif total_score < -0.3:
            return 'SELL'
        else:
            return 'HOLD'
            
    def _build_reasoning(self, aggregated: AggregatedSignal) -> List[str]:
        \"\"\"Построение объяснения решения\"\"\"
        reasoning = []
        
        # Основные сигналы
        for signal_type, signal in aggregated.signals.items():
            weight = aggregated.weighted_scores.get(signal_type, 0)
            reasoning.append(f\"{signal_type}: {signal.action} (confidence: {signal.confidence:.2f}, weight: {weight:.2f})\")
            
        # Конфликты
        if aggregated.conflicts:
            reasoning.append(f\"Conflicts detected: {len(aggregated.conflicts)}\")
            
        # Общая уверенность
        reasoning.append(f\"Overall confidence: {aggregated.overall_confidence:.2f}\")
        
        return reasoning
        
    def _assess_risk_level(self, aggregated: AggregatedSignal) -> str:
        \"\"\"Оценка уровня риска\"\"\"
        
        risk_factors = 0
        
        # Низкая уверенность
        if aggregated.overall_confidence < 0.5:
            risk_factors += 1
            
        # Много конфликтов
        if len(aggregated.conflicts) > 1:
            risk_factors += 1
            
        # Высокая волатильность (из market signal)
        market_signal = aggregated.signals.get('MARKET')
        if market_signal and market_signal.metadata.get('volatility_risk') == 'HIGH':
            risk_factors += 1
            
        if risk_factors >= 2:
            return 'HIGH'
        elif risk_factors == 1:
            return 'MEDIUM'
        else:
            return 'LOW'
```

### 2. **Интеграция с TradingOrchestrator**

```python
# В TradingOrchestrator:
class TradingOrchestrator:
    def __init__(self, ..., signal_aggregator: SignalAggregationService):
        self.signal_aggregator = signal_aggregator
        
    async def process_tick(self, ticker: Ticker):
        # Получить агрегированные сигналы
        aggregated_signal = await self.signal_aggregator.aggregate_signals(ticker)
        final_decision = await self.signal_aggregator.calculate_final_decision(aggregated_signal)
        
        # Логирование детального анализа
        logger.info(f\"📊 Signal Breakdown: {final_decision.signal_breakdown}\")
        logger.info(f\"🎯 Final Decision: {final_decision.action} (confidence: {final_decision.confidence:.2f})\")
        logger.info(f\"📝 Reasoning: {'; '.join(final_decision.reasoning)}\")
        
        # Принятие решения на основе агрегированного сигнала
        if final_decision.action == 'BUY' and final_decision.confidence > 0.7:
            await self._execute_buy_decision(ticker, final_decision)
        elif final_decision.action == 'SELL' and final_decision.confidence > 0.7:
            await self._execute_sell_decision(ticker, final_decision)
        else:
            logger.info(f\"💤 Holding position: {final_decision.action} with {final_decision.confidence:.2f} confidence\")
```

---

## ✅ Критерии приемки

### Функциональные требования:
- [ ] Агрегирует сигналы из всех источников (MACD, OrderBook, Market)
- [ ] Корректно взвешивает сигналы по важности
- [ ] Обнаруживает и разрешает конфликты между сигналами
- [ ] Генерирует финальное решение с обоснованием
- [ ] Интегрирован с TradingOrchestrator

### Нефункциональные требования:
- [ ] Время агрегации < 2ms
- [ ] Покрытие тестами > 85%
- [ ] Graceful handling отсутствующих сигналов
- [ ] Подробное логирование решений

### Тестовые сценарии:
- [ ] Все сигналы указывают BUY - должен вернуть BUY с высокой уверенностью
- [ ] Конфликтующие сигналы (BUY vs SELL) - должен снизить уверенность
- [ ] Отсутствие некоторых сигналов - должен работать с доступными
- [ ] Все сигналы слабые - должен вернуть HOLD

---

## 🚧 Риски и митигация

### Риск 1: Переоптимизация весов сигналов
**Митигация:** Простые веса на старте, эволюция на основе реальной торговли

### Риск 2: Слишком консервативная агрегация  
**Митигация:** A/B тестирование разных стратегий агрегации

### Риск 3: Производительность при многих сигналах
**Митигация:** Асинхронная обработка и кеширование

---

## 📚 Связанные материалы

- Issue #4: MarketDataAnalyzer
- Existing: `domain/services/signal_service.py`
- Existing: `domain/services/orderbook_analyzer.py`
