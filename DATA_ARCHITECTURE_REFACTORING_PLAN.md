# 🏗️ ПЛАН РЕФАКТОРИНГА АРХИТЕКТУРЫ ДАННЫХ AutoTrade v2.4.0

## 📋 ОГЛАВЛЕНИЕ

- [🎯 Обзор проблем](#-обзор-проблем)
- [🔍 Текущая архитектура](#-текущая-архитектура)
- [⚡ Улучшенная архитектура](#-улучшенная-архитектура)
- [🚀 План поэтапного внедрения](#-план-поэтапного-внедрения)
- [📊 Детальный анализ компонентов](#-детальный-анализ-компонентов)
- [🎁 Ожидаемые результаты](#-ожидаемые-результаты)

---

## 🎯 ОБЗОР ПРОБЛЕМ

### 🚨 Критические проблемы текущей архитектуры:

1. **Нарушение принципа единой ответственности** - сервисы одновременно:
   - Обрабатывают бизнес-логику
   - Хранят данные в памяти
   - Управляют кэшированием
   - Ведут статистику

2. **Избыточные сущности для потоковых данных**:
   - `Ticker` - просто маппинг JSON в объект без бизнес-логики
   - `InMemoryTickerRepository` - неэффективно хранит объекты вместо JSON
   - Отсутствуют специализированные потоковые хранилища

3. **Смешивание системных и потоковых данных**:
   - Нет четкого разделения между бизнес-объектами (Deal, Order) и данными потоков (ticker, orderbook)
   - Потоковые данные обрабатываются как сущности, хотя это просто JSON массивы
   - Отсутствует стратегия для разных типов данных

4. **Неэффективное хранение потоковых данных**:
   - Создание объектов для каждого тикера
   - Лишние кеши для простых операций (get_last_n)
   - Отсутствие прямой работы с JSON массивами

5. **Сложность тестирования и расширения**:
   - Монолитные сервисы сложно тестировать
   - Добавление новых фич требует изменения множества компонентов
   - Нет возможности легко заменить хранилище данных

---

## 🔍 ТЕКУЩАЯ АРХИТЕКТУРА

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ТЕКУЩАЯ АРХИТЕКТУРА - ПРОБЛЕМЫ                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                             СЕРВИСЫ (ПРОБЛЕМЫ)                             │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │   TickerService │   │   OrderService  │   │ BuyOrderMonitor │          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  │ ❌ price_history │   │ ❌ stats = {}   │   │ ❌ stats = {}   │          │  │
│  │  │    _cache = []   │   │ ❌ Создает      │   │ ❌ Отменяет     │          │  │
│  │  │ ❌ Вычисляет    │   │    ордера       │   │    ордера       │          │  │
│  │  │    индикаторы   │   │ ❌ Размещает    │   │ ❌ Пересоздает  │          │  │
│  │  │ ❌ Обрабатывает │   │    на бирже     │   │    ордера       │          │  │
│  │  │    JSON         │   │ ❌ Валидирует   │   │ ❌ Обновляет    │          │  │
│  │  │                 │   │ ❌ Синхронизир. │   │    SELL ордера  │          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │OrderBookAnalyzer│   │  StopLossMonitor│   │CachedIndicator  │          │  │
│  │  │                 │   │                 │   │    Service      │          │  │
│  │  │ ❌ config = {}  │   │ ❌ _warned_deals│   │ ❌ fast_cache   │          │  │
│  │  │ ❌ Обрабатывает │   │    = set()      │   │ ❌ medium_cache │          │  │
│  │  │    JSON стакан  │   │ ❌ _stats = {}  │   │ ❌ heavy_cache  │          │  │
│  │  │ ❌ Генерирует   │   │ ❌ Мониторит    │   │ ❌ sma_7_buffer │          │  │
│  │  │    сигналы      │   │    риски        │   │ ❌ sma_25_buffer│          │  │
│  │  │ ❌ Анализирует  │   │ ❌ Создает      │   │ ❌ price_sum_7  │          │  │
│  │  │    ликвидность  │   │    маркет-ордера│   │ ❌ price_sum_25 │          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                          РЕПОЗИТОРИИ (НЕПОЛНЫЕ)                             │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │   DealsRepo     │   │   OrdersRepo    │   │  TickersRepo    │          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  │ ✅ Dict[int,    │   │ ✅ Dict[int,    │   │ ✅ List[Ticker] │          │  │
│  │  │    Deal]        │   │    Order]       │   │ ✅ Кэш для     │          │  │
│  │  │ ✅ Простой      │   │ ✅ 4 индекса    │   │    get_last_n() │          │  │
│  │  │    интерфейс    │   │ ✅ Статистика   │   │ ✅ Лимит 1000  │          │  │
│  │  │                 │   │ ✅ Экспорт/     │   │                 │          │  │
│  │  │                 │   │    импорт       │   │                 │          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  │                                                                             │  │
│  │  ❌ НЕТ РЕПОЗИТОРИЕВ ДЛЯ:                                                  │  │
│  │     • Индикаторы                                                            │  │
│  │     • OrderBook данные                                                      │  │
│  │     • Статистика                                                            │  │
│  │     • Кэши                                                                  │  │
│  │     • Конфигурация                                                          │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                         ЭНТИТИ (ХОРОШО СПРОЕКТИРОВАНЫ)                      │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │      Deal       │   │      Order      │   │   CurrencyPair  │          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  │ ✅ deal_id      │   │ ✅ order_id     │   │ ✅ symbol       │          │  │
│  │  │ ✅ buy_order    │   │ ✅ exchange_id  │   │ ✅ настройки    │          │  │
│  │  │ ✅ sell_order   │   │ ✅ amount       │   │ ✅ лимиты       │          │  │
│  │  │ ✅ status       │   │ ✅ filled_amount│   │ ✅ комиссии     │          │  │
│  │  │ ✅ методы       │   │ ✅ статусы      │   │                 │          │  │
│  │  │                 │   │ ✅ валидация    │   │                 │          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐                                                       │  │
│  │  │     Ticker      │                                                       │  │
│  │  │                 │                                                       │  │
│  │  │ ✅ timestamp    │   ❌ НЕТ ЭНТИТИ ДЛЯ:                                │  │
│  │  │ ✅ symbol       │      • OrderBook                                      │  │
│  │  │ ✅ price        │      • IndicatorData                                   │  │
│  │  │ ✅ signals      │      • TradingSignal                                  │  │
│  │  │ ✅ volume       │      • Statistics                                     │  │
│  │  │                 │      • Configuration                                  │  │
│  │  └─────────────────┘                                                       │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 🔥 Критические проблемы по компонентам:

| Компонент | Проблема | Нарушение принципа |
|-----------|----------|-------------------|
| **TickerService** | `price_history_cache = []` | Хранение + обработка |
| **CachedIndicatorService** | 3 типа кэшей + буферы | Только кэширование |
| **OrderService** | Создание + размещение + валидация | Множественная ответственность |
| **OrderBookAnalyzer** | Обработка JSON + генерация сигналов | Обработка + анализ |
| **StopLossMonitor** | Мониторинг + создание ордеров | Мониторинг + исполнение |

---

## ⚡ УЛУЧШЕННАЯ АРХИТЕКТУРА

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           УЛУЧШЕННАЯ АРХИТЕКТУРА                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                      СЕРВИСЫ (ЕДИНАЯ ОТВЕТСТВЕННОСТЬ)                       │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │ TickerProcessor │   │OrderPlacement   │   │ OrderMonitoring │          │  │
│  │  │                 │   │   Service       │   │    Service      │          │  │
│  │  │ ✅ ТОЛЬКО       │   │                 │   │                 │          │  │
│  │  │    обработка    │   │ ✅ ТОЛЬКО       │   │ ✅ ТОЛЬКО       │          │  │
│  │  │    тикеров      │   │    размещение   │   │    мониторинг   │          │  │
│  │  │ ✅ Делегирует   │   │ ✅ Делегирует   │   │ ✅ Делегирует   │          │  │
│  │  │    в репозиторий│   │    в репозиторий│   │    в репозиторий│          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │OrderBookAnalyzer│   │  RiskManagement │   │IndicatorCalc    │          │  │
│  │  │                 │   │    Service      │   │   Service       │          │  │
│  │  │ ✅ ТОЛЬКО       │   │                 │   │                 │          │  │
│  │  │    анализ       │   │ ✅ ТОЛЬКО       │   │ ✅ ТОЛЬКО       │          │  │
│  │  │    стакана      │   │    управление   │   │    расчет       │          │  │
│  │  │ ✅ Делегирует   │   │    рисками      │   │    индикаторов  │          │  │
│  │  │    в репозиторий│   │ ✅ Делегирует   │   │ ✅ Делегирует   │          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐                                │  │
│  │  │  Configuration  │   │   Statistics    │                                │  │
│  │  │    Service      │   │    Service      │                                │  │
│  │  │                 │   │                 │                                │  │
│  │  │ ✅ ТОЛЬКО       │   │ ✅ ТОЛЬКО       │                                │  │
│  │  │    конфигурация │   │    статистика   │                                │  │
│  │  │ ✅ Делегирует   │   │ ✅ Делегирует   │                                │  │
│  │  │    в репозиторий│   │    в репозиторий│                                │  │
│  │  └─────────────────┘   └─────────────────┘                                │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                    РЕПОЗИТОРИИ (ПОЛНЫЙ НАБОР)                               │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │   DealsRepo     │   │   OrdersRepo    │   │  TickersRepo    │          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  │ ✅ In-Memory    │   │ ✅ In-Memory    │   │ ✅ In-Memory    │          │  │
│  │  │ ✅ PostgreSQL   │   │ ✅ PostgreSQL   │   │ ✅ PostgreSQL   │          │  │
│  │  │ ✅ Interface    │   │ ✅ Interface    │   │ ✅ Interface    │          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │ IndicatorRepo   │   │ OrderBookRepo   │   │ StatisticsRepo  │          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  │ 🆕 In-Memory    │   │ 🆕 In-Memory    │   │ 🆕 In-Memory    │          │  │
│  │  │ 🆕 PostgreSQL   │   │ 🆕 PostgreSQL   │   │ 🆕 PostgreSQL   │          │  │
│  │  │ 🆕 Interface    │   │ 🆕 Interface    │   │ 🆕 Interface    │          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐                                │  │
│  │  │ ConfigurationRepo│   │   CacheRepo     │                                │  │
│  │  │                 │   │                 │                                │  │
│  │  │ 🆕 In-Memory    │   │ 🆕 In-Memory    │                                │  │
│  │  │ 🆕 PostgreSQL   │   │ 🆕 Redis        │                                │  │
│  │  │ 🆕 Interface    │   │ 🆕 Interface    │                                │  │
│  │  │                 │   │                 │                                │  │
│  │  └─────────────────┘   └─────────────────┘                                │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                        ЭНТИТИ (РАСШИРЕННЫЙ НАБОР)                           │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │      Deal       │   │      Order      │   │   CurrencyPair  │          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  │ ✅ Существует   │   │ ✅ Существует   │   │ ✅ Существует   │          │  │
│  │  │ ✅ Хорошо       │   │ ✅ Хорошо       │   │ ✅ Хорошо       │          │  │
│  │  │    спроектирован│   │    спроектирован│   │    спроектирован│          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │     Ticker      │   │   OrderBook     │   │  IndicatorData  │          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  │ ✅ Существует   │   │ 🆕 НОВАЯ        │   │ 🆕 НОВАЯ        │          │  │
│  │  │ ✅ Хорошо       │   │ ✅ timestamp    │   │ ✅ timestamp    │          │  │
│  │  │    спроектирован│   │ ✅ bids/asks    │   │ ✅ symbol       │          │  │
│  │  │                 │   │ ✅ spread       │   │ ✅ indicator    │          │  │
│  │  │                 │   │ ✅ volume       │   │ ✅ value        │          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │  │
│  │  │  TradingSignal  │   │   Statistics    │   │  Configuration  │          │  │
│  │  │                 │   │                 │   │                 │          │  │
│  │  │ 🆕 НОВАЯ        │   │ 🆕 НОВАЯ        │   │ 🆕 НОВАЯ        │          │  │
│  │  │ ✅ timestamp    │   │ ✅ metric_name  │   │ ✅ key          │          │  │
│  │  │ ✅ symbol       │   │ ✅ value        │   │ ✅ value        │          │  │
│  │  │ ✅ signal_type  │   │ ✅ timestamp    │   │ ✅ category     │          │  │
│  │  │ ✅ strength     │   │ ✅ category     │   │ ✅ description  │          │  │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘          │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 🎯 Преимущества новой архитектуры:

| Принцип | Старая архитектура | Новая архитектура |
|---------|-------------------|-------------------|
| **Единая ответственность** | ❌ Сервисы делают всё | ✅ Каждый сервис - одна задача |
| **Разделение данных** | ❌ Всё в памяти сервисов | ✅ Бизнес-объекты vs потоковые JSON |
| **Потоковые данные** | ❌ Избыточные объекты | ✅ Прямая работа с JSON массивами |
| **Производительность** | ❌ Создание объектов для каждого тикера | ✅ Эффективное хранение JSON |
| **Кэширование** | ❌ Хаотично по сервисам | ✅ Централизованное |
| **Тестируемость** | ❌ Сложно мокать | ✅ Легко тестировать |
| **Расширяемость** | ❌ Монолитные сервисы | ✅ Модульная архитектура |

---

## 🚀 ПЛАН ПОЭТАПНОГО ВНЕДРЕНИЯ

### 🔥 ЭТАП 1 - КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ (Неделя 1)
> **Цель**: Исправить критичные нарушения принципа единой ответственности

#### 📝 1.1 Оптимизировать хранение потоковых данных

<details>
<summary>🆕 StreamDataRepository - Прямая работа с JSON</summary>

```python
# src/infrastructure/repositories/stream_data_repository.py
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

class StreamDataRepository:
    """Эффективное хранение потоковых данных как JSON массивы"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        # Прямое хранение JSON без создания объектов
        self.tickers: List[Dict] = []
        self.indicators: List[Dict] = []
        self.orderbooks: List[Dict] = []
        self.trading_signals: List[Dict] = []
    
    def save_ticker(self, ticker_data: Dict) -> None:
        """Сохранить тикер как JSON"""
        self.tickers.append(ticker_data)
        self._cleanup_if_needed(self.tickers)
    
    def save_indicator(self, indicator_data: Dict) -> None:
        """Сохранить индикатор как JSON"""
        self.indicators.append(indicator_data)
        self._cleanup_if_needed(self.indicators)
    
    def save_orderbook(self, orderbook_data: Dict) -> None:
        """Сохранить стакан как JSON"""
        self.orderbooks.append(orderbook_data)
        self._cleanup_if_needed(self.orderbooks)
    
    def save_trading_signal(self, signal_data: Dict) -> None:
        """Сохранить торговый сигнал как JSON"""
        self.trading_signals.append(signal_data)
        self._cleanup_if_needed(self.trading_signals)
    
    def get_last_prices(self, n: int) -> List[float]:
        """Получить последние N цен - прямой доступ к JSON"""
        return [t['last'] for t in self.tickers[-n:]]
    
    def get_last_tickers(self, n: int) -> List[Dict]:
        """Получить последние N тикеров как JSON"""
        return self.tickers[-n:]
    
    def get_last_indicators(self, indicator_type: str, n: int) -> List[Dict]:
        """Получить последние N индикаторов определенного типа"""
        filtered = [ind for ind in self.indicators if ind.get('type') == indicator_type]
        return filtered[-n:]
    
    def get_latest_orderbook(self) -> Optional[Dict]:
        """Получить последний стакан"""
        return self.orderbooks[-1] if self.orderbooks else None
    
    def _cleanup_if_needed(self, data_list: List[Dict]) -> None:
        """Очистка при превышении лимита"""
        if len(data_list) > self.max_size:
            # Удаляем 20% старых записей
            remove_count = self.max_size // 5
            del data_list[:remove_count]
            logger.debug(f"Очищено {remove_count} записей из потокового хранилища")
    
    def get_price_history(self, n: int) -> List[float]:
        """Получить историю цен для расчета индикаторов"""
        return [ticker['last'] for ticker in self.tickers[-n:]]
    
    def get_volume_history(self, n: int) -> List[float]:
        """Получить историю объемов"""
        return [ticker.get('baseVolume', 0) for ticker in self.tickers[-n:]]
```

</details>

<details>
<summary>🆕 IndicatorCalculator - Работа с JSON массивами</summary>

```python
# src/domain/services/indicators/indicator_calculator.py
import numpy as np
import talib
from typing import List, Dict, Optional
from decimal import Decimal

class IndicatorCalculator:
    """Калькулятор индикаторов для потоковых данных"""
    
    def __init__(self, stream_repo):
        self.stream_repo = stream_repo
    
    def calculate_sma(self, symbol: str, period: int) -> Optional[Dict]:
        """Рассчитать SMA и сохранить как JSON"""
        prices = self.stream_repo.get_price_history(period)
        
        if len(prices) < period:
            return None
        
        sma_value = sum(prices[-period:]) / period
        
        indicator_data = {
            'timestamp': int(time.time() * 1000),
            'symbol': symbol,
            'type': 'SMA',
            'period': period,
            'value': round(sma_value, 8)
        }
        
        self.stream_repo.save_indicator(indicator_data)
        return indicator_data
    
    def calculate_macd(self, symbol: str, fast=12, slow=26, signal=9) -> Optional[Dict]:
        """Рассчитать MACD и сохранить как JSON"""
        prices = self.stream_repo.get_price_history(slow * 2)
        
        if len(prices) < slow:
            return None
        
        closes = np.array(prices)
        macd, macdsignal, macdhist = talib.MACD(closes, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        
        if len(macd) == 0 or np.isnan(macd[-1]):
            return None
        
        indicator_data = {
            'timestamp': int(time.time() * 1000),
            'symbol': symbol,
            'type': 'MACD',
            'macd': round(float(macd[-1]), 8),
            'signal': round(float(macdsignal[-1]), 8),
            'histogram': round(float(macdhist[-1]), 8)
        }
        
        self.stream_repo.save_indicator(indicator_data)
        return indicator_data
    
    def get_cached_indicator(self, symbol: str, indicator_type: str) -> Optional[Dict]:
        """Получить последний индикатор из кэша"""
        indicators = self.stream_repo.get_last_indicators(indicator_type, 1)
        return indicators[0] if indicators else None
```

</details>

#### 📝 1.2 Оставить сущности только для бизнес-объектов

<details>
<summary>✅ Сохранить Deal, Order, CurrencyPair - у них есть бизнес-логика</summary>

```python
# Эти сущности остаются, так как содержат бизнес-логику:

# Deal - имеет жизненный цикл, состояния, методы
# Order - содержит валидацию, связи, статусы  
# CurrencyPair - включает торговые правила, лимиты

# Примеры бизнес-логики в Deal:
def can_be_closed(self) -> bool:
    return self.status == 'OPEN' and self.sell_order and self.sell_order.is_filled()

def calculate_profit(self) -> Decimal:
    if not self.can_be_closed():
        return Decimal('0')
    return self.sell_order.filled_amount * self.sell_order.average_price - \
           self.buy_order.filled_amount * self.buy_order.average_price

# Примеры бизнес-логики в Order:
def update_from_exchange(self, exchange_data: dict):
    self.status = exchange_data.get('status', self.status)
    self.filled_amount = exchange_data.get('filled', self.filled_amount)
    self.average_price = exchange_data.get('average', self.average_price)
    self.validate_order_data()

def is_filled(self) -> bool:
    return self.status == 'FILLED'

def is_expired(self) -> bool:
    return time.time() - self.created_at > self.timeout_seconds
```

</details>

<details>
<summary>❌ Убрать Ticker Entity - только JSON маппинг</summary>

```python
# УДАЛИТЬ: src/domain/entities/ticker.py
# Причины:
# 1. Только копирует JSON поля в атрибуты
# 2. Метод to_dict() конвертирует обратно в JSON
# 3. Нет бизнес-логики
# 4. Создается и уничтожается на каждом тике

# ВМЕСТО ЭТОГО: Прямая работа с JSON в StreamDataRepository
def save_ticker(self, ticker_data: Dict) -> None:
    """Сохранить тикер как JSON без создания объекта"""
    self.tickers.append(ticker_data)
    self._cleanup_if_needed(self.tickers)
```

</details>

#### 📝 1.2 Создать недостающие репозитории

<details>
<summary>🆕 Base Repository Interface</summary>

```python
# src/domain/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Базовый интерфейс для всех репозиториев"""
    
    @abstractmethod
    def save(self, entity: T) -> None:
        """Сохранить энтити"""
        pass
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Получить энтити по ID"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Получить все энтити"""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Удалить энтити по ID"""
        pass
    
    @abstractmethod
    def exists(self, id: int) -> bool:
        """Проверить существование энтити"""
        pass
```

</details>

<details>
<summary>🆕 IndicatorRepository</summary>

```python
# src/domain/repositories/indicator_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from src.domain.entities.indicator_data import IndicatorData

class IndicatorRepository(ABC):
    """Репозиторий для индикаторов"""
    
    @abstractmethod
    def save(self, indicator: IndicatorData) -> None:
        """Сохранить индикатор"""
        pass
    
    @abstractmethod
    def get_by_symbol_and_type(self, symbol: str, indicator_type: str, limit: int = 100) -> List[IndicatorData]:
        """Получить индикаторы по символу и типу"""
        pass
    
    @abstractmethod
    def get_latest(self, symbol: str, indicator_type: str) -> Optional[IndicatorData]:
        """Получить последний индикатор"""
        pass
    
    @abstractmethod
    def get_by_time_range(self, symbol: str, indicator_type: str, start_time: datetime, end_time: datetime) -> List[IndicatorData]:
        """Получить индикаторы за период"""
        pass
    
    @abstractmethod
    def delete_old(self, symbol: str, indicator_type: str, older_than_days: int) -> int:
        """Удалить старые индикаторы"""
        pass

# src/infrastructure/repositories/in_memory_indicator_repository.py
class InMemoryIndicatorRepository(IndicatorRepository):
    """In-memory реализация репозитория индикаторов"""
    
    def __init__(self, max_indicators: int = 10000):
        self._storage: List[IndicatorData] = []
        self._max_indicators = max_indicators
    
    def save(self, indicator: IndicatorData) -> None:
        self._storage.append(indicator)
        self._cleanup_if_needed()
    
    def get_by_symbol_and_type(self, symbol: str, indicator_type: str, limit: int = 100) -> List[IndicatorData]:
        filtered = [ind for ind in self._storage 
                   if ind.symbol == symbol and ind.indicator_type == indicator_type]
        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_latest(self, symbol: str, indicator_type: str) -> Optional[IndicatorData]:
        results = self.get_by_symbol_and_type(symbol, indicator_type, limit=1)
        return results[0] if results else None
    
    def _cleanup_if_needed(self):
        if len(self._storage) > self._max_indicators:
            # Оставляем только 80% от максимума
            keep_count = int(self._max_indicators * 0.8)
            self._storage = sorted(self._storage, key=lambda x: x.timestamp, reverse=True)[:keep_count]
```

</details>

<details>
<summary>🆕 OrderBookRepository</summary>

```python
# src/domain/repositories/order_book_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.order_book import OrderBook

class OrderBookRepository(ABC):
    """Репозиторий для стаканов заявок"""
    
    @abstractmethod
    def save(self, order_book: OrderBook) -> None:
        """Сохранить стакан"""
        pass
    
    @abstractmethod
    def get_latest(self, symbol: str) -> Optional[OrderBook]:
        """Получить последний стакан для символа"""
        pass
    
    @abstractmethod
    def get_last_n(self, symbol: str, n: int) -> List[OrderBook]:
        """Получить последние N стаканов"""
        pass
    
    @abstractmethod
    def get_by_time_range(self, symbol: str, start_time: int, end_time: int) -> List[OrderBook]:
        """Получить стаканы за период"""
        pass

# src/infrastructure/repositories/in_memory_order_book_repository.py
class InMemoryOrderBookRepository(OrderBookRepository):
    """In-memory реализация репозитория стаканов"""
    
    def __init__(self, max_order_books: int = 1000):
        self._storage: List[OrderBook] = []
        self._max_order_books = max_order_books
        self._cache = {}  # symbol -> OrderBook
    
    def save(self, order_book: OrderBook) -> None:
        self._storage.append(order_book)
        self._cache[order_book.symbol] = order_book
        self._cleanup_if_needed()
    
    def get_latest(self, symbol: str) -> Optional[OrderBook]:
        return self._cache.get(symbol)
    
    def get_last_n(self, symbol: str, n: int) -> List[OrderBook]:
        filtered = [ob for ob in self._storage if ob.symbol == symbol]
        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[:n]
    
    def _cleanup_if_needed(self):
        if len(self._storage) > self._max_order_books:
            # Оставляем только 80% от максимума
            keep_count = int(self._max_order_books * 0.8)
            self._storage = sorted(self._storage, key=lambda x: x.timestamp, reverse=True)[:keep_count]
            # Обновляем кэш
            self._cache = {ob.symbol: ob for ob in self._storage[-100:]}
```

</details>

#### 📝 1.3 Создать централизованный кэш

<details>
<summary>🆕 CacheRepository</summary>

```python
# src/domain/repositories/cache_repository.py
from abc import ABC, abstractmethod
from typing import Optional, Any

class CacheRepository(ABC):
    """Репозиторий для кэширования"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Установить значение в кэш"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Очистить весь кэш"""
        pass

# src/infrastructure/repositories/in_memory_cache_repository.py
import time
from typing import Dict, Tuple

class InMemoryCacheRepository(CacheRepository):
    """In-memory реализация кэша"""
    
    def __init__(self, default_ttl: int = 3600):
        self._cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expire_time)
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        
        value, expire_time = self._cache[key]
        if expire_time and time.time() > expire_time:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        expire_time = None
        if ttl is not None:
            expire_time = time.time() + ttl
        elif self._default_ttl:
            expire_time = time.time() + self._default_ttl
        
        self._cache[key] = (value, expire_time)
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        return self.get(key) is not None
    
    def clear(self) -> None:
        self._cache.clear()
```

</details>

---

### 🔧 ЭТАП 2 - РАЗДЕЛЕНИЕ СЕРВИСОВ (Неделя 2)
> **Цель**: Разделить монолитные сервисы на специализированные

#### 📝 2.1 Разделить OrderService

<details>
<summary>🆕 OrderPlacementService</summary>

```python
# src/domain/services/orders/order_placement_service.py
from src.domain.repositories.orders_repository import OrdersRepository
from src.domain.entities.order import Order
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
import logging

logger = logging.getLogger(__name__)

class OrderPlacementService:
    """Сервис размещения ордеров - ТОЛЬКО размещение"""
    
    def __init__(self, orders_repo: OrdersRepository, exchange_connector: CcxtExchangeConnector):
        self.orders_repo = orders_repo
        self.exchange_connector = exchange_connector
    
    async def place_order(self, order: Order) -> bool:
        """Размещает ордер на бирже"""
        try:
            # Валидация
            if not self._validate_order(order):
                logger.error(f"Ордер {order.order_id} не прошел валидацию")
                return False
            
            # Размещение на бирже
            exchange_response = await self.exchange_connector.create_order(
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                amount=order.amount,
                price=order.price
            )
            
            # Обновление ордера данными с биржи
            order.update_from_exchange(exchange_response)
            
            # Сохранение в репозиторий
            self.orders_repo.save(order)
            
            logger.info(f"✅ Ордер {order.order_id} размещен на бирже: {order.exchange_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка размещения ордера {order.order_id}: {e}")
            order.mark_as_failed(str(e))
            self.orders_repo.save(order)
            return False
    
    def _validate_order(self, order: Order) -> bool:
        """Валидация ордера перед размещением"""
        if order.amount <= 0:
            return False
        if order.side not in ['BUY', 'SELL']:
            return False
        if order.order_type == 'LIMIT' and order.price <= 0:
            return False
        return True
```

</details>

<details>
<summary>🆕 OrderMonitoringService</summary>

```python
# src/domain/services/orders/order_monitoring_service.py
from src.domain.repositories.orders_repository import OrdersRepository
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
import asyncio
import logging

logger = logging.getLogger(__name__)

class OrderMonitoringService:
    """Сервис мониторинга ордеров - ТОЛЬКО мониторинг"""
    
    def __init__(self, orders_repo: OrdersRepository, exchange_connector: CcxtExchangeConnector):
        self.orders_repo = orders_repo
        self.exchange_connector = exchange_connector
        self._is_running = False
    
    async def start_monitoring(self, check_interval: int = 30):
        """Запустить мониторинг ордеров"""
        self._is_running = True
        logger.info("🚀 OrderMonitoringService запущен")
        
        while self._is_running:
            try:
                await self._check_orders_status()
                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error(f"Ошибка в мониторинге ордеров: {e}")
                await asyncio.sleep(check_interval)
    
    def stop_monitoring(self):
        """Остановить мониторинг"""
        self._is_running = False
        logger.info("🔴 OrderMonitoringService остановлен")
    
    async def _check_orders_status(self):
        """Проверить статус открытых ордеров"""
        open_orders = self.orders_repo.get_open_orders()
        
        for order in open_orders:
            try:
                # Получить статус с биржи
                exchange_order = await self.exchange_connector.fetch_order(
                    order.exchange_id, order.symbol
                )
                
                # Обновить данные ордера
                old_status = order.status
                order.update_from_exchange(exchange_order)
                
                # Сохранить обновленный ордер
                self.orders_repo.save(order)
                
                # Логирование изменений
                if old_status != order.status:
                    logger.info(f"🔄 Ордер {order.order_id} изменил статус: {old_status} -> {order.status}")
                
            except Exception as e:
                logger.error(f"Ошибка проверки ордера {order.order_id}: {e}")
```

</details>

#### 📝 2.2 Разделить TickerService

<details>
<summary>🆕 TickerProcessorService</summary>

```python
# src/domain/services/market_data/ticker_processor_service.py
from src.domain.repositories.ticker_repository import TickerRepository
from src.domain.entities.ticker import Ticker
import logging

logger = logging.getLogger(__name__)

class TickerProcessorService:
    """Сервис обработки тикеров - ТОЛЬКО обработка"""
    
    def __init__(self, ticker_repo: TickerRepository):
        self.ticker_repo = ticker_repo
    
    def process_ticker(self, ticker_data: dict) -> Ticker:
        """Обработать входящий тикер"""
        try:
            # Создать объект тикера
            ticker = Ticker(
                timestamp=ticker_data.get('timestamp'),
                symbol=ticker_data.get('symbol'),
                price=ticker_data.get('last'),
                open=ticker_data.get('open'),
                close=ticker_data.get('close'),
                volume=ticker_data.get('baseVolume'),
                high=ticker_data.get('high'),
                low=ticker_data.get('low'),
                bid=ticker_data.get('bid'),
                ask=ticker_data.get('ask')
            )
            
            # Сохранить в репозиторий
            self.ticker_repo.save(ticker)
            
            logger.debug(f"✅ Тикер обработан: {ticker.symbol} @ {ticker.price}")
            return ticker
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки тикера: {e}")
            raise
    
    def get_latest_ticker(self, symbol: str) -> Ticker:
        """Получить последний тикер для символа"""
        tickers = self.ticker_repo.get_last_n(1)
        return tickers[0] if tickers else None
```

</details>

<details>
<summary>🆕 IndicatorCalculatorService</summary>

```python
# src/domain/services/indicators/indicator_calculator_service.py
from src.domain.repositories.indicator_repository import IndicatorRepository
from src.domain.repositories.ticker_repository import TickerRepository
from src.domain.entities.indicator_data import IndicatorData
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class IndicatorCalculatorService:
    """Сервис расчета индикаторов - ТОЛЬКО расчет"""
    
    def __init__(self, indicator_repo: IndicatorRepository, ticker_repo: TickerRepository):
        self.indicator_repo = indicator_repo
        self.ticker_repo = ticker_repo
    
    def calculate_sma(self, symbol: str, period: int) -> IndicatorData:
        """Рассчитать SMA"""
        try:
            # Получить последние тикеры
            tickers = self.ticker_repo.get_last_n(period)
            
            if len(tickers) < period:
                logger.warning(f"Недостаточно данных для SMA{period}: {len(tickers)}/{period}")
                return None
            
            # Рассчитать среднее
            prices = [ticker.price for ticker in tickers]
            sma_value = sum(prices) / len(prices)
            
            # Создать индикатор
            indicator = IndicatorData.create_sma(
                timestamp=tickers[0].timestamp,
                symbol=symbol,
                value=Decimal(str(sma_value)),
                period=period
            )
            
            # Сохранить в репозиторий
            self.indicator_repo.save(indicator)
            
            logger.debug(f"✅ SMA{period} рассчитан для {symbol}: {sma_value}")
            return indicator
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета SMA{period} для {symbol}: {e}")
            return None
    
    def calculate_macd(self, symbol: str, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> IndicatorData:
        """Рассчитать MACD"""
        try:
            # Получить EMA для быстрой и медленной линий
            fast_ema = self._calculate_ema(symbol, fast_period)
            slow_ema = self._calculate_ema(symbol, slow_period)
            
            if not fast_ema or not slow_ema:
                return None
            
            # MACD = Fast EMA - Slow EMA
            macd_value = fast_ema - slow_ema
            
            # Получить предыдущие MACD для расчета сигнальной линии
            previous_macd = self.indicator_repo.get_by_symbol_and_type(symbol, 'MACD', limit=signal_period-1)
            
            if len(previous_macd) >= signal_period - 1:
                # Рассчитать сигнальную линию (EMA от MACD)
                macd_values = [macd_value] + [ind.value for ind in previous_macd]
                signal_value = self._calculate_ema_from_values(macd_values, signal_period)
                histogram = macd_value - signal_value
            else:
                signal_value = macd_value
                histogram = Decimal('0')
            
            # Создать MACD индикатор
            indicator = IndicatorData.create_macd(
                timestamp=self.ticker_repo.get_last_n(1)[0].timestamp,
                symbol=symbol,
                macd=macd_value,
                signal=signal_value,
                histogram=histogram
            )
            
            # Сохранить в репозиторий
            self.indicator_repo.save(indicator)
            
            logger.debug(f"✅ MACD рассчитан для {symbol}: {macd_value}")
            return indicator
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета MACD для {symbol}: {e}")
            return None
    
    def _calculate_ema(self, symbol: str, period: int) -> Decimal:
        """Рассчитать EMA"""
        tickers = self.ticker_repo.get_last_n(period * 2)  # Берем больше данных для точности
        
        if len(tickers) < period:
            return None
        
        prices = [ticker.price for ticker in reversed(tickers)]
        multiplier = Decimal('2') / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_ema_from_values(self, values: list, period: int) -> Decimal:
        """Рассчитать EMA от массива значений"""
        if len(values) < period:
            return sum(values) / len(values)
        
        multiplier = Decimal('2') / (period + 1)
        ema = values[0]
        
        for value in values[1:]:
            ema = (value * multiplier) + (ema * (1 - multiplier))
        
        return ema
```

</details>

---

### 🏗️ ЭТАП 3 - УНИФИКАЦИЯ РЕПОЗИТОРИЕВ (Неделя 3)
> **Цель**: Создать единообразную систему репозиториев

#### 📝 3.1 Унифицировать интерфейсы

<details>
<summary>🔧 Обновленные репозитории</summary>

```python
# src/domain/repositories/deals_repository.py
from src.domain.repositories.base_repository import BaseRepository
from src.domain.entities.deal import Deal
from typing import List

class DealsRepository(BaseRepository[Deal]):
    """Унифицированный репозиторий сделок"""
    
    @abstractmethod
    def get_open_deals(self) -> List[Deal]:
        """Получить открытые сделки"""
        pass
    
    @abstractmethod
    def get_by_currency_pair(self, symbol: str) -> List[Deal]:
        """Получить сделки по валютной паре"""
        pass
    
    @abstractmethod
    def get_by_status(self, status: str) -> List[Deal]:
        """Получить сделки по статусу"""
        pass
    
    @abstractmethod
    def close_deal(self, deal_id: int) -> bool:
        """Закрыть сделку"""
        pass

# src/domain/repositories/orders_repository.py
from src.domain.repositories.base_repository import BaseRepository
from src.domain.entities.order import Order
from typing import List, Optional

class OrdersRepository(BaseRepository[Order]):
    """Унифицированный репозиторий ордеров"""
    
    @abstractmethod
    def get_by_exchange_id(self, exchange_id: str) -> Optional[Order]:
        """Получить ордер по exchange_id"""
        pass
    
    @abstractmethod
    def get_by_status(self, status: str) -> List[Order]:
        """Получить ордера по статусу"""
        pass
    
    @abstractmethod
    def get_by_symbol(self, symbol: str) -> List[Order]:
        """Получить ордера по символу"""
        pass
    
    @abstractmethod
    def get_open_orders(self) -> List[Order]:
        """Получить открытые ордера"""
        pass
    
    @abstractmethod
    def get_by_deal_id(self, deal_id: int) -> List[Order]:
        """Получить ордера по deal_id"""
        pass
```

</details>

---

### 🗄️ ЭТАП 4 - ПОДГОТОВКА К POSTGRESQL (Неделя 4)
> **Цель**: Подготовить архитектуру для миграции на PostgreSQL

#### 📝 4.1 Создать схемы БД

<details>
<summary>🗄️ PostgreSQL Schemas</summary>

```sql
-- src/infrastructure/database/schemas/01_deals_schema.sql
CREATE TABLE deals (
    id BIGINT PRIMARY KEY,
    currency_pair VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    buy_order_id BIGINT,
    sell_order_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    metadata JSONB,
    FOREIGN KEY (buy_order_id) REFERENCES orders(id),
    FOREIGN KEY (sell_order_id) REFERENCES orders(id)
);

CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_deals_currency_pair ON deals(currency_pair);
CREATE INDEX idx_deals_created_at ON deals(created_at);

-- src/infrastructure/database/schemas/02_orders_schema.sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    exchange_id VARCHAR(100) UNIQUE,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    amount DECIMAL(18,8) NOT NULL,
    price DECIMAL(18,8),
    filled_amount DECIMAL(18,8) DEFAULT 0,
    remaining_amount DECIMAL(18,8),
    average_price DECIMAL(18,8),
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    fees DECIMAL(18,8) DEFAULT 0,
    fee_currency VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    deal_id BIGINT,
    exchange_timestamp TIMESTAMP,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    retries INTEGER DEFAULT 0,
    metadata JSONB,
    FOREIGN KEY (deal_id) REFERENCES deals(id)
);

CREATE INDEX idx_orders_exchange_id ON orders(exchange_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_deal_id ON orders(deal_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- src/infrastructure/database/schemas/03_tickers_history_schema.sql
CREATE TABLE tickers_history (
    id SERIAL PRIMARY KEY,
    timestamp BIGINT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(18,8) NOT NULL,
    open DECIMAL(18,8),
    close DECIMAL(18,8),
    high DECIMAL(18,8),
    low DECIMAL(18,8),
    volume DECIMAL(18,8),
    bid DECIMAL(18,8),
    ask DECIMAL(18,8),
    trades_count INTEGER DEFAULT 0,
    signals JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tickers_symbol_timestamp ON tickers_history(symbol, timestamp DESC);
CREATE INDEX idx_tickers_created_at ON tickers_history(created_at);

-- src/infrastructure/database/schemas/04_order_books_history_schema.sql
CREATE TABLE order_books_history (
    id SERIAL PRIMARY KEY,
    timestamp BIGINT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    spread DECIMAL(18,8),
    mid_price DECIMAL(18,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_books_symbol_timestamp ON order_books_history(symbol, timestamp DESC);
CREATE INDEX idx_order_books_created_at ON order_books_history(created_at);

-- src/infrastructure/database/schemas/05_indicators_history_schema.sql
CREATE TABLE indicators_history (
    id SERIAL PRIMARY KEY,
    timestamp BIGINT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    indicator_type VARCHAR(20) NOT NULL,
    value DECIMAL(18,8) NOT NULL,
    period INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_indicators_symbol_type_timestamp ON indicators_history(symbol, indicator_type, timestamp DESC);
CREATE INDEX idx_indicators_created_at ON indicators_history(created_at);

-- src/infrastructure/database/schemas/06_statistics_schema.sql
CREATE TABLE statistics (
    id SERIAL PRIMARY KEY,
    timestamp BIGINT NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(18,8) NOT NULL,
    category VARCHAR(30) NOT NULL,
    symbol VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_statistics_metric_timestamp ON statistics(metric_name, timestamp DESC);
CREATE INDEX idx_statistics_category ON statistics(category);
CREATE INDEX idx_statistics_symbol ON statistics(symbol);
```

</details>

#### 📝 4.2 Создать PostgreSQL репозитории

<details>
<summary>🗄️ PostgreSQL Repositories</summary>

```python
# src/infrastructure/repositories/postgres_deals_repository.py
import psycopg2
from typing import List, Optional
from src.domain.repositories.deals_repository import DealsRepository
from src.domain.entities.deal import Deal
from src.domain.entities.currency_pair import CurrencyPair
import logging

logger = logging.getLogger(__name__)

class PostgresDealsRepository(DealsRepository):
    """PostgreSQL реализация репозитория сделок"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection = None
    
    def _get_connection(self):
        """Получить соединение с БД"""
        if not self._connection or self._connection.closed:
            self._connection = psycopg2.connect(self.connection_string)
        return self._connection
    
    def save(self, deal: Deal) -> None:
        """Сохранить сделку"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO deals (id, currency_pair, status, buy_order_id, sell_order_id, created_at, closed_at, metadata)
            VALUES (%s, %s, %s, %s, %s, to_timestamp(%s/1000), to_timestamp(%s/1000), %s)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                buy_order_id = EXCLUDED.buy_order_id,
                sell_order_id = EXCLUDED.sell_order_id,
                closed_at = EXCLUDED.closed_at,
                metadata = EXCLUDED.metadata
            """
            
            cursor.execute(query, (
                deal.deal_id,
                deal.currency_pair_id,
                deal.status,
                deal.buy_order.order_id if deal.buy_order else None,
                deal.sell_order.order_id if deal.sell_order else None,
                deal.created_at,
                deal.closed_at,
                {}  # metadata
            ))
            
            conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения сделки {deal.deal_id}: {e}")
            raise
    
    def get_by_id(self, deal_id: int) -> Optional[Deal]:
        """Получить сделку по ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT id, currency_pair, status, buy_order_id, sell_order_id, 
                   EXTRACT(EPOCH FROM created_at) * 1000 as created_at,
                   EXTRACT(EPOCH FROM closed_at) * 1000 as closed_at
            FROM deals WHERE id = %s
            """
            
            cursor.execute(query, (deal_id,))
            row = cursor.fetchone()
            cursor.close()
            
            if not row:
                return None
            
            # Создать объект Deal
            currency_pair = CurrencyPair(
                base_currency=row[1].split('/')[0],
                quote_currency=row[1].split('/')[1],
                symbol=row[1]
            )
            
            deal = Deal(
                deal_id=row[0],
                currency_pair=currency_pair,
                status=row[2],
                created_at=int(row[5]) if row[5] else None,
                closed_at=int(row[6]) if row[6] else None
            )
            
            return deal
            
        except Exception as e:
            logger.error(f"Ошибка получения сделки {deal_id}: {e}")
            return None
    
    def get_open_deals(self) -> List[Deal]:
        """Получить открытые сделки"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT id, currency_pair, status, buy_order_id, sell_order_id, 
                   EXTRACT(EPOCH FROM created_at) * 1000 as created_at,
                   EXTRACT(EPOCH FROM closed_at) * 1000 as closed_at
            FROM deals WHERE status = 'OPEN'
            ORDER BY created_at DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
            deals = []
            for row in rows:
                currency_pair = CurrencyPair(
                    base_currency=row[1].split('/')[0],
                    quote_currency=row[1].split('/')[1],
                    symbol=row[1]
                )
                
                deal = Deal(
                    deal_id=row[0],
                    currency_pair=currency_pair,
                    status=row[2],
                    created_at=int(row[5]) if row[5] else None,
                    closed_at=int(row[6]) if row[6] else None
                )
                deals.append(deal)
            
            return deals
            
        except Exception as e:
            logger.error(f"Ошибка получения открытых сделок: {e}")
            return []
    
    def get_all(self) -> List[Deal]:
        """Получить все сделки"""
        # Аналогично get_open_deals, но без WHERE clause
        pass
    
    def delete(self, deal_id: int) -> bool:
        """Удалить сделку"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "DELETE FROM deals WHERE id = %s"
            cursor.execute(query, (deal_id,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            cursor.close()
            
            return deleted
            
        except Exception as e:
            logger.error(f"Ошибка удаления сделки {deal_id}: {e}")
            return False
    
    def exists(self, deal_id: int) -> bool:
        """Проверить существование сделки"""
        return self.get_by_id(deal_id) is not None
    
    def get_by_currency_pair(self, symbol: str) -> List[Deal]:
        """Получить сделки по валютной паре"""
        # Аналогично get_open_deals с дополнительным WHERE currency_pair = symbol
        pass
```

</details>

---

### 🏗️ ЭТАП 5 - ВНЕДРЕНИЕ (Неделя 5)
> **Цель**: Постепенное внедрение новой архитектуры

#### 📝 5.1 Создать фасад для обратной совместимости

<details>
<summary>🔄 Legacy Facade</summary>

```python
# src/domain/services/compatibility/legacy_service_facade.py
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class LegacyServiceFacade:
    """Фасад для обратной совместимости со старой архитектурой"""
    
    def __init__(self, new_services: Dict[str, Any]):
        self.ticker_processor = new_services.get('ticker_processor')
        self.order_placement = new_services.get('order_placement')
        self.order_monitoring = new_services.get('order_monitoring')
        self.indicator_calculator = new_services.get('indicator_calculator')
        self.order_book_analyzer = new_services.get('order_book_analyzer')
        
        logger.info("✅ LegacyServiceFacade инициализирован")
    
    def process_ticker(self, ticker_data: dict):
        """Обработать тикер (проксирует к новому сервису)"""
        if self.ticker_processor:
            return self.ticker_processor.process_ticker(ticker_data)
        else:
            logger.warning("TickerProcessor не найден, используется старая логика")
            # Здесь можно оставить старый код как fallback
            return None
    
    def place_order(self, order):
        """Разместить ордер (проксирует к новому сервису)"""
        if self.order_placement:
            return self.order_placement.place_order(order)
        else:
            logger.warning("OrderPlacement не найден, используется старая логика")
            return False
    
    def calculate_indicators(self, symbol: str):
        """Рассчитать индикаторы (проксирует к новому сервису)"""
        if self.indicator_calculator:
            # Рассчитать основные индикаторы
            sma7 = self.indicator_calculator.calculate_sma(symbol, 7)
            sma25 = self.indicator_calculator.calculate_sma(symbol, 25)
            macd = self.indicator_calculator.calculate_macd(symbol)
            
            return {
                'sma7': sma7,
                'sma25': sma25,
                'macd': macd
            }
        else:
            logger.warning("IndicatorCalculator не найден, используется старая логика")
            return {}
```

</details>

#### 📝 5.2 Поэтапная миграция

<details>
<summary>🔄 Migration Strategy</summary>

```python
# main.py - Обновленная инициализация
import os
from src.infrastructure.repositories.in_memory_deals_repository import InMemoryDealsRepository
from src.infrastructure.repositories.postgres_deals_repository import PostgresDealsRepository
from src.domain.services.orders.order_placement_service import OrderPlacementService
from src.domain.services.orders.order_monitoring_service import OrderMonitoringService
from src.domain.services.market_data.ticker_processor_service import TickerProcessorService
from src.domain.services.indicators.indicator_calculator_service import IndicatorCalculatorService
from src.domain.services.compatibility.legacy_service_facade import LegacyServiceFacade

# Флаг для переключения между архитектурами
USE_NEW_ARCHITECTURE = os.getenv('USE_NEW_ARCHITECTURE', 'true').lower() == 'true'
USE_POSTGRES = os.getenv('USE_POSTGRES', 'false').lower() == 'true'

async def main():
    logger.info(f"🚀 ЗАПУСК AutoTrade v2.5.0 - Архитектура: {'НОВАЯ' if USE_NEW_ARCHITECTURE else 'СТАРАЯ'}")
    
    # Инициализация репозиториев
    if USE_POSTGRES:
        connection_string = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/autotrade')
        deals_repo = PostgresDealsRepository(connection_string)
        logger.info("✅ Используется PostgreSQL")
    else:
        deals_repo = InMemoryDealsRepository()
        logger.info("✅ Используется In-Memory хранилище")
    
    # Инициализация сервисов
    if USE_NEW_ARCHITECTURE:
        # Новая архитектура
        ticker_processor = TickerProcessorService(ticker_repo)
        order_placement = OrderPlacementService(orders_repo, exchange_connector)
        order_monitoring = OrderMonitoringService(orders_repo, exchange_connector)
        indicator_calculator = IndicatorCalculatorService(indicator_repo, ticker_repo)
        
        # Создать фасад для обратной совместимости
        services_facade = LegacyServiceFacade({
            'ticker_processor': ticker_processor,
            'order_placement': order_placement,
            'order_monitoring': order_monitoring,
            'indicator_calculator': indicator_calculator
        })
        
        # Запустить новые сервисы
        asyncio.create_task(order_monitoring.start_monitoring())
        logger.info("✅ Новая архитектура запущена")
        
    else:
        # Старая архитектура (для обратной совместимости)
        ticker_service = TickerService(ticker_repo)
        order_service = OrderService(orders_repo, exchange_connector)
        
        services_facade = None
        logger.info("✅ Старая архитектура запущена")
    
    # Основной торговый цикл
    try:
        await run_trading_loop(services_facade if USE_NEW_ARCHITECTURE else None)
    except KeyboardInterrupt:
        logger.info("🔴 Получен сигнал остановки")
    finally:
        if USE_NEW_ARCHITECTURE and order_monitoring:
            order_monitoring.stop_monitoring()
        logger.info("🔴 Система остановлена")

async def run_trading_loop(services_facade=None):
    """Основной торговый цикл"""
    while True:
        try:
            # Получить тикер
            ticker_data = await get_ticker_data()
            
            if services_facade:
                # Новая архитектура
                ticker = services_facade.process_ticker(ticker_data)
                indicators = services_facade.calculate_indicators(ticker.symbol)
                
                # Принять торговое решение
                if should_place_order(ticker, indicators):
                    order = create_order(ticker)
                    success = await services_facade.place_order(order)
                    if success:
                        logger.info(f"✅ Ордер размещен: {order.order_id}")
            else:
                # Старая архитектура
                ticker = ticker_service.process_ticker(ticker_data)
                # ... старая логика
            
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Ошибка в торговом цикле: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

---

## 📊 ДЕТАЛЬНЫЙ АНАЛИЗ КОМПОНЕНТОВ

### 🔍 Анализ текущих проблем по сервисам

<details>
<summary>🚨 TickerService - Серьезные нарушения</summary>

**Файл**: `src/domain/services/market_data/ticker_service.py`

**Проблемы**:
- `price_history_cache = []` - хранит 200 ценовых точек
- `cached_indicators = CachedIndicatorService()` - композиция с кэшированием
- `repository.tickers[-1]` - прямой доступ к данным репозитория
- Обрабатывает ticker JSON данные напрямую
- Вычисляет торговые сигналы
- Выполняет сложные финансовые расчеты
- **Создает Ticker объекты** для каждого тика (неэффективно)

**Нарушения**: Сервис одновременно обрабатывает данные, кэширует их, вычисляет индикаторы и генерирует сигналы.

**Решение**: Заменить на `StreamDataRepository` для прямой работы с JSON массивами.

</details>

<details>
<summary>🚨 OrderService - Массивные нарушения</summary>

**Файл**: `src/domain/services/orders/order_service.py`

**Проблемы**:
- `stats = {}` - словарь со статистикой
- Создает ордера
- Размещает ордера на бирже
- Проверяет балансы
- Выполняет валидацию
- Отменяет ордера
- Синхронизирует с биржей
- Обрабатывает ошибки и retry

**Нарушения**: Монолитный сервис, который нарушает принцип единственной ответственности.

</details>

<details>
<summary>🚨 CachedIndicatorService - Критические проблемы</summary>

**Файл**: `src/domain/services/indicators/cached_indicator_service.py`

**Проблемы**:
- `fast_cache = {}` - кэш для быстрых индикаторов
- `medium_cache = {}` - кэш для средних индикаторов
- `heavy_cache = {}` - кэш для тяжелых индикаторов
- `sma_7_buffer = []` - буфер для SMA-7
- `sma_25_buffer = []` - буфер для SMA-25
- `price_sum_7 = 0` - сумма цен для SMA-7
- `price_sum_25 = 0` - сумма цен для SMA-25

**Нарушения**: Сервис является чистым хранилищем данных, а не бизнес-логикой.

</details>

### 🎯 Преимущества новой архитектуры

| Аспект | Старая архитектура | Новая архитектура |
|--------|-------------------|-------------------|
| **Тестирование** | ❌ Сложно мокать монолитные сервисы | ✅ Легко тестировать отдельные компоненты |
| **Расширение** | ❌ Изменения требуют модификации множества файлов | ✅ Новые функции добавляются локально |
| **Производительность** | ❌ Неэффективное кэширование | ✅ Централизованное кэширование |
| **Масштабирование** | ❌ Нельзя масштабировать отдельные части | ✅ Горизонтальное масштабирование |
| **Отладка** | ❌ Сложно найти источник проблем | ✅ Четкое разделение ответственности |

---

## 🎁 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### ✅ Краткосрочные (1-2 недели)
- **Замена Ticker Entity на StreamDataRepository**
- **Прямая работа с JSON массивами для потоковых данных**
- **Разделение бизнес-объектов и потоковых данных**
- **Оптимизация производительности обработки тикеров**
- **Исправление критических нарушений архитектуры**

### ✅ Среднесрочные (3-4 недели)
- **Унификация всех репозиториев**
- **Подготовка к миграции на PostgreSQL**
- **Повышение производительности в 2-3 раза** (устранение создания объектов)
- **Сокращение потребления памяти на 50%** (JSON вместо объектов)
- **Упрощение тестирования**

### ✅ Долгосрочные (1-2 месяца)
- **Полная миграция на PostgreSQL**
- **Горизонтальное масштабирование**
- **Возможность использования Redis для кэширования**
- **Модульная архитектура для легкого расширения**

---

### 🚀 НАЧАЛО РАБОТЫ

1. **Клонировать этот план** в отдельную ветку:
   ```bash
   git checkout -b feature/data-architecture-refactoring
   ```

2. **Начать с Этапа 1** - создать недостающие энтити:
   ```bash
   mkdir -p src/domain/entities
   # Создать OrderBook, IndicatorData, TradingSignal энтити
   ```

3. **Запустить тесты** для проверки совместимости:
   ```bash
   python -m pytest tests/ -v
   ```

4. **Постепенно внедрять** новые компоненты, поддерживая обратную совместимость

---

**📝 Этот план поможет превратить вашу систему из MVP в production-ready архитектуру с правильным разделением ответственности и возможностью масштабирования.**