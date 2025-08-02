# 🔧 API Reference - AutoTrade v2.4.0

> **Справочник ключевых сервисов и их API**

---

## 📋 Содержание

- [🔄 Асинхронный жизненный цикл](#-асинхронный-жизненный-цикл)
- [🛡️ Управление рисками](#️-управление-рисками)
- [📊 Рыночные данные](#-рыночные-данные)
- [⚙️ Утилиты](#️-утилиты)
- [🏗️ Базовые сервисы](#️-базовые-сервисы)
- [🎯 Примеры использования](#-примеры-использования)

---

## 🔄 Асинхронный жизненный цикл

### 🚀 OrderExecutionService

**Расположение**: `src/domain/services/orders/order_execution_service.py`  
**Назначение**: Оркестратор начала сделки

#### Основные методы:

```python
class OrderExecutionService:
    async def create_and_execute_deal(
        self, 
        signal: TradingSignal,
        currency_pair: CurrencyPair
    ) -> Deal:
        """
        Создает сделку и размещает только BUY ордер
        
        Args:
            signal: Торговый сигнал
            currency_pair: Валютная пара
            
        Returns:
            Deal: Созданная сделка
        """
        
    async def create_virtual_sell_order(
        self,
        deal: Deal,
        buy_order: Order
    ) -> Order:
        """
        Создает виртуальный SELL ордер со статусом PENDING
        
        Args:
            deal: Сделка
            buy_order: Исполненный BUY ордер
            
        Returns:
            Order: Виртуальный SELL ордер
        """
```

### 🎯 FilledBuyOrderHandler (🆕)

**Расположение**: `src/domain/services/orders/filled_buy_order_handler.py`  
**Назначение**: Обработчик исполненных BUY ордеров

#### Основные методы:

```python
class FilledBuyOrderHandler:
    async def start_monitoring(self) -> None:
        """Запуск мониторинга исполненных BUY ордеров"""
        
    async def handle_filled_buy_order(self, order: Order) -> None:
        """
        Обработка исполненного BUY ордера
        
        Args:
            order: Исполненный BUY ордер
        """
        
    async def place_pending_sell_order(self, deal: Deal) -> None:
        """
        Размещение PENDING SELL ордера на бирже
        
        Args:
            deal: Сделка с PENDING SELL ордером
        """
```

### 📋 DealCompletionMonitor (🆕)

**Расположение**: `src/domain/services/deals/deal_completion_monitor.py`  
**Назначение**: Мониторинг завершения сделок

#### Основные методы:

```python
class DealCompletionMonitor:
    async def start_monitoring(self) -> None:
        """Запуск мониторинга завершения сделок"""
        
    async def check_deal_completion(self, deal: Deal) -> bool:
        """
        Проверка завершения сделки
        
        Args:
            deal: Сделка для проверки
            
        Returns:
            bool: True если сделка завершена
        """
        
    async def close_completed_deal(self, deal: Deal) -> None:
        """
        Закрытие завершенной сделки
        
        Args:
            deal: Завершенная сделка
        """
```

---

## 🛡️ Управление рисками

### 🔴 StopLossMonitor (🆕)

**Расположение**: `src/domain/services/risk/stop_loss_monitor.py`  
**Назначение**: Умная система защиты от убытков

#### Основные методы:

```python
class StopLossMonitor:
    async def start_monitoring(self) -> None:
        """Запуск мониторинга стоп-лосса"""
        
    async def check_position_loss(self, deal: Deal) -> LossLevel:
        """
        Проверка уровня убытка позиции
        
        Args:
            deal: Сделка для проверки
            
        Returns:
            LossLevel: Уровень убытка (WARNING, CRITICAL, EMERGENCY)
        """
        
    async def analyze_market_conditions(self, deal: Deal) -> MarketConditions:
        """
        Анализ рыночных условий перед закрытием
        
        Args:
            deal: Сделка для анализа
            
        Returns:
            MarketConditions: Условия рынка
        """
        
    async def close_position_if_needed(self, deal: Deal) -> bool:
        """
        Закрытие позиции при необходимости
        
        Args:
            deal: Сделка для возможного закрытия
            
        Returns:
            bool: True если позиция была закрыта
        """
```

#### Уровни защиты:

```python
class LossLevel(Enum):
    WARNING = "warning"      # 5% убытка - предупреждение
    CRITICAL = "critical"    # 10% убытка - критический анализ
    EMERGENCY = "emergency"  # 15% убытка - экстренное закрытие
```

### 🔄 Enhanced BuyOrderMonitor

**Расположение**: `src/domain/services/orders/buy_order_monitor.py`  
**Назначение**: Мониторинг устаревших BUY ордеров + синхронизация SELL

#### Новые методы в v2.4.0:

```python
class BuyOrderMonitor:
    async def recreate_stale_order(self, order: Order) -> Order:
        """
        Пересоздание устаревшего ордера
        
        Args:
            order: Устаревший ордер
            
        Returns:
            Order: Новый ордер
        """
        
    async def update_pending_sell_order(self, deal: Deal, new_buy_order: Order) -> None:
        """
        Обновление параметров виртуального SELL ордера
        
        Args:
            deal: Сделка
            new_buy_order: Новый BUY ордер
        """
        
    def is_order_stale(self, order: Order) -> bool:
        """
        Проверка устаревания ордера
        
        Args:
            order: Ордер для проверки
            
        Returns:
            bool: True если ордер устарел
        """
```

---

## 📊 Рыночные данные

### 📈 OrderBookAnalyzer

**Расположение**: `src/domain/services/market_data/orderbook_analyzer.py`  
**Назначение**: Анализ биржевого стакана

#### Основные методы:

```python
class OrderBookAnalyzer:
    async def analyze_orderbook(self, symbol: str) -> OrderBookSignal:
        """
        Анализ стакана ордеров
        
        Args:
            symbol: Торговая пара
            
        Returns:
            OrderBookSignal: Сигнал анализа стакана
        """
        
    def calculate_spread(self, orderbook: OrderBook) -> float:
        """Расчет спреда"""
        
    def analyze_liquidity(self, orderbook: OrderBook) -> float:
        """Анализ ликвидности"""
        
    def find_support_resistance(self, orderbook: OrderBook) -> SupportResistance:
        """Поиск уровней поддержки/сопротивления"""
```

### 📊 TickerService

**Расположение**: `src/domain/services/market_data/ticker_service.py`  
**Назначение**: Обработка рыночных данных

#### Основные методы:

```python
class TickerService:
    async def get_macd_signal_data(self, symbol: str) -> MACDSignal:
        """
        Получение MACD сигнала
        
        Args:
            symbol: Торговая пара
            
        Returns:
            MACDSignal: MACD сигнал
        """
        
    async def calculate_strategy_with_orderbook(
        self, 
        symbol: str, 
        orderbook_data: OrderBookData
    ) -> TradingStrategy:
        """Расчет стратегии с учетом стакана"""
```

---

## ⚙️ Утилиты

### 🔢 DecimalRoundingService (🆕)

**Расположение**: `src/domain/services/utils/decimal_rounding_service.py`  
**Назначение**: Точное округление для торговых операций

#### Основные методы:

```python
class DecimalRoundingService:
    @staticmethod
    def round_price(price: float, precision: int = 8) -> Decimal:
        """
        Округление цены
        
        Args:
            price: Цена для округления
            precision: Точность округления
            
        Returns:
            Decimal: Округленная цена
        """
        
    @staticmethod
    def round_quantity(quantity: float, step_size: float) -> Decimal:
        """
        Округление количества
        
        Args:
            quantity: Количество для округления
            step_size: Шаг округления
            
        Returns:
            Decimal: Округленное количество
        """
        
    @staticmethod
    def calculate_order_cost(price: Decimal, quantity: Decimal) -> Decimal:
        """Расчет стоимости ордера"""
```

### 💾 OrderbookCache (🆕)

**Расположение**: `src/domain/services/utils/orderbook_cache.py`  
**Назначение**: Кэширование данных стакана

#### Основные методы:

```python
class OrderbookCache:
    def __init__(self, ttl_seconds: int = 60):
        """
        Инициализация кэша
        
        Args:
            ttl_seconds: Время жизни кэша в секундах
        """
        
    async def get_orderbook(self, symbol: str) -> Optional[OrderBook]:
        """
        Получение стакана из кэша
        
        Args:
            symbol: Торговая пара
            
        Returns:
            Optional[OrderBook]: Кэшированный стакан или None
        """
        
    async def set_orderbook(self, symbol: str, orderbook: OrderBook) -> None:
        """
        Сохранение стакана в кэш
        
        Args:
            symbol: Торговая пара
            orderbook: Стакан ордеров
        """
        
    def clear_cache(self) -> None:
        """Очистка кэша"""
```

---

## 🏗️ Базовые сервисы

### 🎯 TradingDecisionEngine

**Расположение**: `src/domain/services/trading/trading_decision_engine.py`  
**Назначение**: Принятие торговых решений

#### Основные методы:

```python
class TradingDecisionEngine:
    async def make_trading_decision(
        self,
        macd_signal: MACDSignal,
        orderbook_signal: OrderBookSignal
    ) -> TradingDecision:
        """
        Принятие торгового решения
        
        Args:
            macd_signal: MACD сигнал
            orderbook_signal: Сигнал стакана
            
        Returns:
            TradingDecision: Торговое решение
        """
        
    def combine_signals(self, signals: List[Signal]) -> CombinedSignal:
        """Комбинирование сигналов"""
        
    def calculate_confidence(self, decision: TradingDecision) -> float:
        """Расчет уверенности в решении"""
```

### 🔄 SignalCooldownManager

**Расположение**: `src/domain/services/trading/signal_cooldown_manager.py`  
**Назначение**: Управление задержками между сигналами

#### Основные методы:

```python
class SignalCooldownManager:
    def is_signal_allowed(self, symbol: str) -> bool:
        """
        Проверка разрешения сигнала
        
        Args:
            symbol: Торговая пара
            
        Returns:
            bool: True если сигнал разрешен
        """
        
    def register_signal(self, symbol: str) -> None:
        """
        Регистрация сигнала
        
        Args:
            symbol: Торговая пара
        """
        
    def get_remaining_cooldown(self, symbol: str) -> int:
        """Получение оставшегося времени задержки"""
```

---

## 🎯 Примеры использования

### 🚀 Создание и исполнение сделки

```python
# Инициализация сервисов
order_execution_service = OrderExecutionService(
    order_service=order_service,
    deal_service=deal_service,
    exchange_connector=exchange_connector
)

# Создание сделки
signal = TradingSignal(action="BUY", confidence=0.85)
currency_pair = CurrencyPair("ETH", "USDT")

deal = await order_execution_service.create_and_execute_deal(
    signal=signal,
    currency_pair=currency_pair
)

print(f"Сделка создана: {deal.id}")
print(f"BUY ордер размещен: {deal.buy_order.id}")
print(f"SELL ордер создан виртуально: {deal.sell_order.id}")
```

### 🛡️ Мониторинг стоп-лосса

```python
# Инициализация мониторинга
stop_loss_monitor = StopLossMonitor(
    deal_service=deal_service,
    order_service=order_service,
    orderbook_analyzer=orderbook_analyzer
)

# Запуск мониторинга
await stop_loss_monitor.start_monitoring()

# Проверка конкретной сделки
loss_level = await stop_loss_monitor.check_position_loss(deal)

if loss_level == LossLevel.WARNING:
    print("🟡 Предупреждение: убыток 5%")
elif loss_level == LossLevel.CRITICAL:
    print("🟠 Критический уровень: убыток 10%")
elif loss_level == LossLevel.EMERGENCY:
    print("🔴 Экстренное закрытие: убыток 15%")
```

### 📊 Анализ стакана с кэшированием

```python
# Инициализация с кэшем
orderbook_cache = OrderbookCache(ttl_seconds=30)
orderbook_analyzer = OrderBookAnalyzer(cache=orderbook_cache)

# Анализ стакана
symbol = "ETH/USDT"
orderbook_signal = await orderbook_analyzer.analyze_orderbook(symbol)

print(f"Сигнал стакана: {orderbook_signal.signal}")
print(f"Уверенность: {orderbook_signal.confidence}")
print(f"Спред: {orderbook_signal.spread_percent}%")
```

### 🔢 Точное округление

```python
from decimal import Decimal

# Округление цены
price = 1234.567890123
rounded_price = DecimalRoundingService.round_price(price, precision=8)
print(f"Округленная цена: {rounded_price}")

# Округление количества
quantity = 0.123456789
step_size = 0.0001
rounded_quantity = DecimalRoundingService.round_quantity(quantity, step_size)
print(f"Округленное количество: {rounded_quantity}")

# Расчет стоимости ордера
cost = DecimalRoundingService.calculate_order_cost(rounded_price, rounded_quantity)
print(f"Стоимость ордера: {cost}")
```

---

## 🔧 Конфигурация сервисов

### 📋 Настройки в config.json

```json
{
  "risk_management": {
    "stop_loss_percent": 2.0,
    "enable_stop_loss": true,
    "smart_stop_loss": {
      "enabled": true,
      "warning_percent": 5.0,
      "critical_percent": 10.0,
      "emergency_percent": 15.0
    }
  },
  "buy_order_monitor": {
    "enabled": true,
    "max_age_minutes": 5.0,
    "max_price_deviation_percent": 3.0,
    "check_interval_seconds": 10
  },
  "orderbook_analyzer": {
    "min_volume_threshold": 1000,
    "big_wall_threshold": 5000,
    "max_spread_percent": 0.3
  }
}
```

---

## 🚨 Обработка ошибок

### 🔴 Типичные исключения

```python
class TradingError(Exception):
    """Базовое исключение торговли"""
    pass

class OrderExecutionError(TradingError):
    """Ошибка исполнения ордера"""
    pass

class StopLossError(TradingError):
    """Ошибка стоп-лосса"""
    pass

class OrderbookAnalysisError(TradingError):
    """Ошибка анализа стакана"""
    pass
```

### 🛠️ Обработка ошибок

```python
try:
    deal = await order_execution_service.create_and_execute_deal(signal, currency_pair)
except OrderExecutionError as e:
    logger.error(f"Ошибка создания сделки: {e}")
except Exception as e:
    logger.error(f"Неожиданная ошибка: {e}")
```

---

## 📚 Дополнительные ресурсы

### 🔗 Связанные документы:
- [Installation Guide](../installation/INSTALLATION.md)
- [Configuration Guide](../configuration/CONFIGURATION.md)
- [Release Notes v2.4.0](../../RELEASE_NOTES_v2.4.0.md)

### 📖 Исходный код:
- [src/domain/services/](../../src/domain/services/)
- [src/application/](../../src/application/)
- [src/infrastructure/](../../src/infrastructure/)

---

**Успешной интеграции!** 🔧

> *"Правильное использование API - основа стабильной торговли"*