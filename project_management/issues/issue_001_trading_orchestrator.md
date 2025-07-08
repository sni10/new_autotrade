# Issue #1: TradingOrchestrator - Главный дирижер

**💰 Стоимость:** $240 (16 часов × $15/час)  
**🔥 Приоритет:** КРИТИЧЕСКИЙ  
**🏗️ Milestone:** M1 - Основные сервисы  
**🏷️ Labels:** `critical`, `architecture`, `refactoring`

## 📝 Описание проблемы

Вся торговая логика сосредоточена в `run_realtime_trading.py` (400+ строк). Это создает:
- Сложность в понимании и поддержке кода
- Невозможность изолированного тестирования компонентов  
- Смешивание разных уровней ответственности
- Высокую связанность между компонентами

## 🎯 Цель

Создать центральный сервис-оркестратор, который будет координировать все торговые операции и станет единой точкой входа для торговой логики.

## 🔧 Техническое решение

### 1. Создать `domain/services/trading_orchestrator.py`

```python
class TradingOrchestrator:
    def __init__(
        self,
        signal_aggregator: SignalAggregationService,
        order_executor: OrderExecutionService, 
        risk_manager: RiskManagementService,
        market_analyzer: MarketDataAnalyzer,
        state_manager: StateManagementService
    ):
        self.signal_aggregator = signal_aggregator
        self.order_executor = order_executor
        self.risk_manager = risk_manager  
        self.market_analyzer = market_analyzer
        self.state_manager = state_manager
        
    async def process_market_tick(self, ticker_data: Dict) -> None:
        \"\"\"Главный метод обработки рыночного тика\"\"\"
        
    async def handle_buy_signal(self, signal_data: Dict) -> None:
        \"\"\"Обработка сигнала покупки\"\"\"
        
    async def handle_sell_signal(self, signal_data: Dict) -> None:
        \"\"\"Обработка сигнала продажи\"\"\"
        
    async def update_open_positions(self) -> None:
        \"\"\"Обновление статуса открытых позиций\"\"\"
```

### 2. Вынести из `run_realtime_trading.py`:

- **Логика принятия торговых решений** → `TradingOrchestrator.handle_buy_signal()`
- **Координация между сервисами** → `TradingOrchestrator.process_market_tick()`  
- **Управление жизненным циклом сделок** → `TradingOrchestrator.update_open_positions()`
- **State management** → отдельный `StateManagementService`

### 3. Упростить `run_realtime_trading.py`:

```python
async def run_realtime_trading(...):
    orchestrator = TradingOrchestrator(...)
    
    while True:
        ticker_data = await connector.watch_ticker(symbol)
        await orchestrator.process_market_tick(ticker_data)
```

## ✅ Критерии готовности

- [ ] Создан `TradingOrchestrator` с четким API
- [ ] Размер `run_realtime_trading.py` уменьшен с 400+ до <100 строк
- [ ] Логика принятия торговых решений вынесена в оркестратор
- [ ] Координация между всеми торговыми сервисами работает
- [ ] Написаны unit-тесты для основных методов оркестратора
- [ ] Документация API для других разработчиков

## 🧪 План тестирования

1. **Unit тесты:**
   - Тест логики принятия решений в `handle_buy_signal`
   - Тест координации сервисов в `process_market_tick`
   - Mock все зависимости

2. **Integration тесты:**
   - Тест работы с реальными сервисами (но mock биржи)
   - Тест обработки различных сценариев рынка

3. **Performance тесты:**
   - Время обработки одного тика должно быть < 5мс
   - Memory leaks при длительной работе

## 🔗 Связанные задачи

- **Блокирует:** Issue #2 (OrderExecutionService), Issue #3 (RiskManagementService)
- **Зависит от:** Нет (может начинаться немедленно)
- **Связано с:** Issue #5 (SignalAggregationService), Issue #7 (StateManagementService)

## 📋 Подзадачи

- [ ] Спроектировать интерфейс TradingOrchestrator
- [ ] Реализовать базовую структуру класса  
- [ ] Вынести логику обработки buy signals
- [ ] Вынести логику обработки market ticks
- [ ] Добавить координацию между сервисами
- [ ] Рефакторить run_realtime_trading.py
- [ ] Написать unit тесты
- [ ] Написать integration тесты
- [ ] Добавить документацию
- [ ] Code review и оптимизация

## 💡 Дополнительные заметки

- Оркестратор должен быть stateless - все состояние хранится в StateManagementService
- Предусмотреть возможность горячей замены стратегий торговли
- Добавить метрики производительности и мониторинг
- Архитектура должна поддерживать будущее расширение на multiple trading pairs
