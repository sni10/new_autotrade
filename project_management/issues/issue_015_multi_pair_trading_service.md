# Issue #015: MultiPairTradingService
### Статус: запланировано

**🏗️ Milestone:** M4  
**📈 Приоритет:** LOW  
**🔗 Зависимости:** Issue #1 (TradingOrchestrator), Issue #14 (PerformanceOptimization)

---

## 📝 Описание проблемы


### 🔍 Текущие ограничения:
- Hardcoded работа с одной парой (FIS/USDT)
- Глобальные переменные для символа
- Нет управления ресурсами между парами
- Отсутствие portfolio balance управления
- Нет корреляционного анализа между парами

### 🎯 Желаемый результат:
- Одновременная торговля 3-5 парами
- Intelligent resource allocation между парами
- Корреляционный анализ для снижения рисков
- Portfolio rebalancing автоматически
- Масштабируемая архитектура для добавления пар

---

## 📋 Технические требования

### 🏗️ Архитектура

```python
class MultiPairTradingService:
    \"\"\"Сервис для торговли несколькими парами\"\"\"
    
    def __init__(self, trading_pairs: List[TradingPairConfig]):
        self.trading_pairs = trading_pairs
        self.portfolio_manager = PortfolioManager()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.resource_allocator = ResourceAllocator()
        
    async def start_multi_pair_trading(self):
    async def stop_trading_pair(self, symbol: str):
    async def add_trading_pair(self, config: TradingPairConfig):
    async def rebalance_portfolio(self);
    async def get_portfolio_status(self) -> PortfolioStatus;

class PortfolioManager:
    \"\"\"Управление портфелем\"\"\"
    
    async def allocate_budget(self, symbol: str, amount: float) -> bool:
    async def check_available_balance(self, symbol: str) -> float:
    async def calculate_portfolio_performance(self) -> PortfolioPerformance:
    async def suggest_rebalancing(self) -> List[RebalanceAction];

class CorrelationAnalyzer:
    \"\"\"Анализ корреляций между парами\"\"\"
    
    async def calculate_correlation_matrix(self) -> Dict[Tuple[str, str], float]:
    async def detect_high_correlation_risk(self) -> List[CorrelationRisk]:
    async def suggest_diversification(self) -> List[DiversificationSuggestion];

class ResourceAllocator:
    \"\"\"Распределение ресурсов между парами\"\"\"
    
    async def distribute_cpu_time(self, pairs: List[str]) -> Dict[str, float]:
    async def manage_api_rate_limits(self, pairs: List[str]);
    async def optimize_websocket_connections(self);
```

### 📊 Структуры данных

```python
@dataclass
class TradingPairConfig:
    symbol: str
    budget_allocation: float  # Percentage of total budget
    max_open_deals: int
    profit_markup: float
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH'
    enabled: bool
    
@dataclass
class PortfolioStatus:
    total_balance_usdt: float
    allocated_balances: Dict[str, float]
    available_balance: float
    total_profit_loss: float
    active_pairs: List[str]
    pair_performances: Dict[str, PairPerformance]
    
@dataclass
class PairPerformance:
    symbol: str
    total_trades: int
    profitable_trades: int
    total_profit_usdt: float
    profit_percentage: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    
@dataclass
class CorrelationRisk:
    pair1: str
    pair2: str  
    correlation: float
    risk_level: str
    suggested_action: str
```

---

## 🛠️ Детальная реализация

### 1. **Основной MultiPairTradingService**

**Файл:** `domain/services/multi_pair_trading_service.py`

```python
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

class MultiPairTradingService:
    def __init__(self, initial_budget_usdt: float = 100.0):
        self.initial_budget = initial_budget_usdt
        self.trading_pairs = {}
        self.pair_orchestrators = {}
        
        # Основные компоненты
        self.portfolio_manager = PortfolioManager(initial_budget_usdt)
        self.correlation_analyzer = CorrelationAnalyzer()
        self.resource_allocator = ResourceAllocator()
        
        # Мониторинг производительности
        self.pair_performances = {}
        self.is_running = False
        
    async def start_multi_pair_trading(self):
        \"\"\"Запуск торговли всеми настроенными парами\"\"\"
        
        if self.is_running:
            return
            
        print(\"🚀 Starting multi-pair trading system...\")
        
        # Проверка корреляций перед стартом
        correlation_risks = await self.correlation_analyzer.detect_high_correlation_risk()
        if correlation_risks:
            print(f\"⚠️ Detected {len(correlation_risks)} correlation risks\")
            for risk in correlation_risks:
                print(f\"   {risk.pair1} ↔️ {risk.pair2}: {risk.correlation:.2f} correlation\")
                
        # Распределение ресурсов
        await self.resource_allocator.optimize_websocket_connections()
        
        # Запуск торговли для каждой пары
        for symbol, config in self.trading_pairs.items():
            if config.enabled:
                await self._start_pair_trading(symbol, config)
                
        # Запуск фоновых задач
        self.is_running = True
        asyncio.create_task(self._portfolio_monitoring_loop())
        asyncio.create_task(self._correlation_monitoring_loop())
        asyncio.create_task(self._rebalancing_loop())
        
        print(f\"✅ Multi-pair trading started with {len(self.trading_pairs)} pairs\")
        
    async def add_trading_pair(self, config: TradingPairConfig):
        \"\"\"Добавление новой торговой пары\"\"\"
        
        # Валидация конфигурации
        if not await self._validate_pair_config(config):
            raise ValueError(f\"Invalid configuration for {config.symbol}\")
            
        # Проверка достаточности бюджета
        required_budget = self.initial_budget * config.budget_allocation
        available_budget = await self.portfolio_manager.check_available_balance('USDT')
        
        if required_budget > available_budget:
            raise ValueError(f\"Insufficient budget: need {required_budget}, have {available_budget}\")
            
        # Добавление пары
        self.trading_pairs[config.symbol] = config
        
        # Выделение бюджета
        await self.portfolio_manager.allocate_budget(config.symbol, required_budget)
        
        # Запуск торговли если система уже работает
        if self.is_running:
            await self._start_pair_trading(config.symbol, config)
            
        print(f\"✅ Added trading pair {config.symbol} with {config.budget_allocation*100:.1f}% budget allocation\")
        
    async def stop_trading_pair(self, symbol: str):
        \"\"\"Остановка торговли парой\"\"\"
        
        if symbol not in self.trading_pairs:
            return False
            
        # Остановка orchestrator для пары
        if symbol in self.pair_orchestrators:
            orchestrator = self.pair_orchestrators[symbol]
            await orchestrator.stop_trading()
            del self.pair_orchestrators[symbol]
            
        # Закрытие открытых позиций
        await self._close_open_positions(symbol)
        
        # Освобождение бюджета
        await self.portfolio_manager.release_budget(symbol)
        
        # Удаление из активных пар
        self.trading_pairs[symbol].enabled = False
        
        print(f\"🛑 Stopped trading pair {symbol}\")
        return True
        
    async def rebalance_portfolio(self):
        \"\"\"Ребалансировка портфеля\"\"\"
        
        # Получение текущих показателей
        portfolio_performance = await self.portfolio_manager.calculate_portfolio_performance()
        
        # Анализ необходимости ребалансировки
        rebalance_actions = await self.portfolio_manager.suggest_rebalancing()
        
        if not rebalance_actions:
            print(\"📊 Portfolio is well balanced, no actions needed\")
            return
            
        print(f\"📊 Executing {len(rebalance_actions)} rebalancing actions...\")
        
        for action in rebalance_actions:
            await self._execute_rebalance_action(action)
            
        print(\"✅ Portfolio rebalancing completed\")
        
    async def get_portfolio_status(self) -> PortfolioStatus:
        \"\"\"Получение статуса портфеля\"\"\"
        
        # Расчет балансов
        total_balance = await self.portfolio_manager.get_total_balance()
        allocated_balances = await self.portfolio_manager.get_allocated_balances()
        available_balance = await self.portfolio_manager.check_available_balance('USDT')
        
        # Расчет общей прибыли/убытка
        total_pnl = total_balance - self.initial_budget
        
        # Получение производительности по парам
        pair_performances = {}
        for symbol in self.trading_pairs.keys():
            if symbol in self.pair_performances:
                pair_performances[symbol] = self.pair_performances[symbol]
                
        return PortfolioStatus(
            total_balance_usdt=total_balance,
            allocated_balances=allocated_balances,
            available_balance=available_balance,
            total_profit_loss=total_pnl,
            active_pairs=list(self.trading_pairs.keys()),
            pair_performances=pair_performances
        )
        
    async def _start_pair_trading(self, symbol: str, config: TradingPairConfig):
        \"\"\"Запуск торговли для конкретной пары\"\"\"
        
        # Создание orchestrator для пары
        pair_orchestrator = await self._create_pair_orchestrator(symbol, config)
        self.pair_orchestrators[symbol] = pair_orchestrator
        
        # Запуск торговли
        await pair_orchestrator.start_trading()
        
        # Инициализация tracking производительности
        self.pair_performances[symbol] = PairPerformance(
            symbol=symbol,
            total_trades=0,
            profitable_trades=0,
            total_profit_usdt=0.0,
            profit_percentage=0.0,
            win_rate=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0
        )
        
        print(f\"🎯 Started trading for {symbol}\")
        
    async def _create_pair_orchestrator(self, symbol: str, config: TradingPairConfig):
        \"\"\"Создание TradingOrchestrator для пары\"\"\"
        
        # Создание отдельных сервисов для пары
        # В реальности это будет injection dependency
        
        class PairSpecificOrchestrator:
            def __init__(self, symbol: str, config: TradingPairConfig):
                self.symbol = symbol
                self.config = config
                self.is_trading = False
                
            async def start_trading(self):
                self.is_trading = True
                # Запуск торгового цикла для пары
                asyncio.create_task(self._trading_loop())
                
            async def stop_trading(self):
                self.is_trading = False
                
            async def _trading_loop(self):
                while self.is_trading:
                    try:
                        # Имитация торгового цикла
                        # В реальности это будет полноценный TradingOrchestrator
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f\"❌ Trading error for {self.symbol}: {str(e)}\")
                        
        return PairSpecificOrchestrator(symbol, config)
        
    async def _portfolio_monitoring_loop(self):
        \"\"\"Цикл мониторинга портфеля\"\"\"
        while self.is_running:
            try:
                # Обновление производительности пар
                await self._update_pair_performances()
                
                # Проверка лимитов риска
                await self._check_risk_limits()
                
                # Логирование статуса каждые 5 минут
                portfolio_status = await self.get_portfolio_status()
                print(f\"📊 Portfolio Status: {portfolio_status.total_balance_usdt:.2f} USDT, P&L: {portfolio_status.total_profit_loss:.2f} USDT\")
                
            except Exception as e:
                print(f\"❌ Portfolio monitoring error: {str(e)}\")
                
            await asyncio.sleep(300)  # 5 минут
            
    async def _correlation_monitoring_loop(self):
        \"\"\"Цикл мониторинга корреляций\"\"\"
        while self.is_running:
            try:
                correlation_matrix = await self.correlation_analyzer.calculate_correlation_matrix()
                high_risks = await self.correlation_analyzer.detect_high_correlation_risk()
                
                if high_risks:
                    print(f\"⚠️ High correlation detected between {len(high_risks)} pairs\")
                    
                    # Автоматическое снижение экспозиции при высокой корреляции
                    for risk in high_risks:
                        if risk.correlation > 0.8:  # Очень высокая корреляция
                            await self._reduce_exposure_for_correlation(risk)
                            
            except Exception as e:
                print(f\"❌ Correlation monitoring error: {str(e)}\")
                
            
    async def _rebalancing_loop(self):
        \"\"\"Цикл ребалансировки\"\"\"
        while self.is_running:
            try:
                await self.rebalance_portfolio()
            except Exception as e:
                print(f\"❌ Rebalancing error: {str(e)}\")
                

class PortfolioManager:
    def __init__(self, initial_budget: float):
        self.initial_budget = initial_budget
        self.allocated_budgets = {}
        self.pair_balances = defaultdict(float)
        
    async def allocate_budget(self, symbol: str, amount: float) -> bool:
        \"\"\"Выделение бюджета для пары\"\"\"
        total_allocated = sum(self.allocated_budgets.values())
        
        if total_allocated + amount > self.initial_budget:
            return False
            
        self.allocated_budgets[symbol] = amount
        self.pair_balances[symbol] = amount
        return True
        
    async def check_available_balance(self, currency: str = 'USDT') -> float:
        \"\"\"Проверка доступного баланса\"\"\"
        total_allocated = sum(self.allocated_budgets.values())
        return self.initial_budget - total_allocated
        
    async def get_total_balance(self) -> float:
        \"\"\"Получение общего баланса\"\"\"
        # В реальности будет запрос к бирже
        return sum(self.pair_balances.values())
        
    async def get_allocated_balances(self) -> Dict[str, float]:
        \"\"\"Получение распределенных балансов\"\"\"
        return dict(self.pair_balances)
        
    async def calculate_portfolio_performance(self) -> 'PortfolioPerformance':
        \"\"\"Расчет производительности портфеля\"\"\"
        
        total_balance = await self.get_total_balance()
        total_return = (total_balance - self.initial_budget) / self.initial_budget
        
        return PortfolioPerformance(
            total_return=total_return,
            total_balance=total_balance,
            sharpe_ratio=0.0,  # TODO: calculate properly
            max_drawdown=0.0,  # TODO: calculate properly
            volatility=0.0     # TODO: calculate properly
        )
        
    async def suggest_rebalancing(self) -> List['RebalanceAction']:
        \"\"\"Предложения по ребалансировке\"\"\"
        actions = []
        
        # Простая логика ребалансировки
        for symbol, current_balance in self.pair_balances.items():
            target_balance = self.allocated_budgets.get(symbol, 0)
            difference = current_balance - target_balance
            
            # Если отклонение > 20%, предлагаем ребалансировку
            if abs(difference / target_balance) > 0.2:
                action_type = 'REDUCE' if difference > 0 else 'INCREASE'
                actions.append(RebalanceAction(
                    symbol=symbol,
                    action_type=action_type,
                    amount=abs(difference * 0.5),  # Корректируем на 50% от разности
                    reason=f\"Deviation from target: {difference:.2f} USDT\"
                ))
                
        return actions

class CorrelationAnalyzer:
    def __init__(self):
        self.price_history = defaultdict(list)
        self.correlation_threshold = 0.7
        
    async def calculate_correlation_matrix(self) -> Dict[Tuple[str, str], float]:
        \"\"\"Расчет матрицы корреляций\"\"\"
        
        correlations = {}
        symbols = list(self.price_history.keys())
        
        for i, symbol1 in enumerate(symbols):
            for symbol2 in symbols[i+1:]:
                if len(self.price_history[symbol1]) > 20 and len(self.price_history[symbol2]) > 20:
                    # Берем последние 50 цен для корреляции
                    prices1 = self.price_history[symbol1][-50:]
                    prices2 = self.price_history[symbol2][-50:]
                    
                    # Выравниваем длины
                    min_len = min(len(prices1), len(prices2))
                    prices1 = prices1[-min_len:]
                    prices2 = prices2[-min_len:]
                    
                    # Расчет корреляции
                    correlation = np.corrcoef(prices1, prices2)[0, 1]
                    correlations[(symbol1, symbol2)] = correlation
                    
        return correlations
        
    async def detect_high_correlation_risk(self) -> List[CorrelationRisk]:
        \"\"\"Обнаружение высоких корреляционных рисков\"\"\"
        
        correlation_matrix = await self.calculate_correlation_matrix()
        risks = []
        
        for (symbol1, symbol2), correlation in correlation_matrix.items():
            if abs(correlation) > self.correlation_threshold:
                risk_level = 'HIGH' if abs(correlation) > 0.8 else 'MEDIUM'
                suggested_action = 'REDUCE_EXPOSURE' if correlation > 0 else 'MONITOR'
                
                risks.append(CorrelationRisk(
                    pair1=symbol1,
                    pair2=symbol2,
                    correlation=correlation,
                    risk_level=risk_level,
                    suggested_action=suggested_action
                ))
                
        return risks

@dataclass
class PortfolioPerformance:
    total_return: float
    total_balance: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float

@dataclass
class RebalanceAction:
    symbol: str
    action_type: str  # 'INCREASE', 'REDUCE'
    amount: float
    reason: str
```

### 2. **Конфигурация для мультипар**

**Файл:** `config/multi_pair_config.json`

```json
{
  \"multi_pair_trading\": {
    \"enabled\": true,
    \"total_budget_usdt\": 100.0,
    \"max_concurrent_pairs\": 5,
    \"rebalancing_frequency_hours\": 24,
    \"correlation_threshold\": 0.7,
    \"risk_management\": {
      \"max_portfolio_drawdown\": 0.15,
      \"max_pair_allocation\": 0.4,
      \"min_pair_allocation\": 0.1
    }
  },
  \"trading_pairs\": [
    {
      \"symbol\": \"FIS/USDT\",
      \"budget_allocation\": 0.3,
      \"max_open_deals\": 1,
      \"profit_markup\": 1.5,
      \"risk_level\": \"MEDIUM\",
      \"enabled\": true
    },
    {
      \"symbol\": \"BTC/USDT\",
      \"budget_allocation\": 0.25,
      \"max_open_deals\": 1,
      \"profit_markup\": 1.0,
      \"risk_level\": \"LOW\",
      \"enabled\": true
    },
    {
      \"symbol\": \"ETH/USDT\",
      \"budget_allocation\": 0.25,
      \"max_open_deals\": 1,
      \"profit_markup\": 1.2,
      \"risk_level\": \"LOW\",
      \"enabled\": true
    },
    {
      \"symbol\": \"ADA/USDT\",
      \"budget_allocation\": 0.2,
      \"max_open_deals\": 2,
      \"profit_markup\": 2.0,
      \"risk_level\": \"HIGH\",
      \"enabled\": false
    }
  ]
}
```

---

## ✅ Критерии приемки

### Функциональные требования:
- [ ] Одновременная торговля 3-5 парами
- [ ] Динамическое добавление/удаление пар
- [ ] Автоматическая ребалансировка портфеля
- [ ] Корреляционный анализ и risk management
- [ ] Performance tracking по каждой паре

### Производительность:
- [ ] Добавление пары не влияет на существующие
- [ ] Scalable архитектура для 10+ пар
- [ ] Efficient resource utilization

### Risk Management:
- [ ] Portfolio drawdown limits
- [ ] Correlation risk detection
- [ ] Automatic exposure reduction
- [ ] Emergency stop для всех пар

---

## 🚧 Риски и митигация

### Риск 1: Корреляция между парами увеличивает общий риск
**Митигация:** Continuous correlation monitoring, automatic exposure reduction

### Риск 2: Сложность debugging при множественных парах
**Митигация:** Подробное логирование по парам, isolated error handling

### Риск 3: API rate limits при множественных парах  
**Митигация:** Intelligent rate limiting, connection pooling

---

## 📚 Связанные материалы

- Issue #1: TradingOrchestrator
- Issue #14: PerformanceOptimization
- [Portfolio Theory](https://en.wikipedia.org/wiki/Modern_portfolio_theory)
- [Risk Management in Trading](https://www.investopedia.com/articles/trading/09/risk-management.asp)
