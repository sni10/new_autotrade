# 🚀 AutoTrade v2.3.0 - "Refactoring & Docs Edition"

> **Intelligent Trading System** with OrderBook Analysis & MACD Indicators  
> **Architecture**: Domain-Driven Design (DDD)  
> **Status**: Production Ready

[![Tests](https://github.com/sni10/new_autotrade/actions/workflows/python-tests.yml/badge.svg)](https://github.com/sni10/new_autotrade/actions)
[![Versioning](https://github.com/sni10/new_autotrade/actions/workflows/versioning.yml/badge.svg)](https://github.com/sni10/new_autotrade/actions)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)

![Trading System](schema-app.svg)

---

## 📋 Table of Contents
- [🎯 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [📊 Performance](#-performance)
- [🔧 Configuration](#-configuration)
- [📈 Trading Process](#-trading-process)
- [🛡️ Safety Features](#️-safety-features)
- [📋 Development Roadmap](#-development-roadmap)
- [🎯 Issues Overview](#-issues-overview)
- [📖 Documentation](#-documentation)

---

## 🎯 Overview

**AutoTrade** - профессиональная система автоматической торговли криптовалютами с интеллектуальным анализом биржевого стакана и техническими индикаторами. Система построена на принципах Domain-Driven Design и использует асинхронную архитектуру для максимальной производительности.

### 🔥 Latest Release: v2.3.0 - "Refactoring & Docs Edition"
- 📚 **Полная актуализация документации** и создание руководств по реализации.
- ⚙️ **Улучшенная конфигурация** с поддержкой переменных окружения.
- 💾 **Персистентность данных** через JSON-репозитории.
- 🛡️ **Уточненные механизмы риска**, включая мониторинг "протухших" ордеров.

---

## ✨ Key Features

### 🧠 Intelligent Trading
- **MACD Technical Analysis** с histogram анализом
- **OrderBook Intelligence** - анализ спреда, ликвидности, поддержки/сопротивления
- **Smart Order Modifications** - корректировка цен на основе технических уровней  
- **Signal Confidence Scoring** - система оценки уверенности сигналов

### ⚡ Performance & Reliability
- **Async Architecture** на базе asyncio для максимальной скорости
- **WebSocket Integration** через ccxt.pro для real-time данных
- **Performance Monitoring** с детальными метриками
- **JSON-based Persistence** для сохранения состояния.

### 🛡️ Safety Systems  
- **StopLossMonitor** - для ограничения убытков.
- **Signal Cooldown Manager** - защита от переторговки.
- **Stale Order Monitoring** (`BuyOrderMonitor`) - отмена и пересоздание "застрявших" ордеров.
- **OrderBook Validation** - отклонение сделок при плохой ликвидности.
- **Environment-based Configuration** через `.env` файлы.

### 📊 Analytics & Monitoring
- **Market Analysis Service** - анализ волатильности и трендов
- **Real-time Performance Logging** 
- **Trading Recommendations** на основе рыночных условий
- **OrderBook Health Monitoring**

---

## 🏗️ Architecture

### 📐 Domain-Driven Design Structure (Реальная структура проекта)

```
new_autotrade/
│
├── domain/                    # 🧠 Business Logic
│   ├── entities/              # Core business objects
│   │   ├── deal.py           # Trading deals
│   │   ├── order.py          # Exchange orders  
│   │   ├── currency_pair.py  # Trading pairs
│   │   └── ticker.py         # Market tickers
│   ├── factories/             # Object creation
│   │   ├── deal_factory.py
│   │   └── order_factory.py
│   └── services/              # Business services
│       ├── trading_service.py        # Core trading logic
│       ├── deal_service.py           # Deal management
│       ├── order_service.py          # Order management
│       ├── signal_service.py         # Signal processing
│       ├── ticker_service.py         # Market data
│       ├── orderbook_analyzer.py     # 🆕 OrderBook analysis
│       ├── orderbook_service.py      # 🆕 OrderBook monitoring
│       ├── trading_decision_engine.py # 🆕 Decision engine
│       ├── market_analysis_service.py # Market analysis
│       ├── cached_indicator_service.py # Performance optimization
│       └── signal_cooldown_manager.py # Protection system
│
├── application/               # 🚀 Use Cases  
│   ├── use_cases/
│   │   └── run_realtime_trading.py   # 🆕 Real-time with OrderBook
│   └── utils/
│       └── performance_logger.py     # Performance monitoring
│
├── infrastructure/            # 🔌 External Integrations
│   ├── repositories/          # Data storage (JSON-based)
│   │   ├── deals_repository.py
│   │   ├── orders_repository.py
│   │   └── tickers_repository.py
│   └── connectors/            # External services
│       ├── exchange_connector.py     # Exchange API
│       └── pro_exchange_connector.py # 🆕 WebSocket ccxt.pro
│
├── config/
│   └── config_loader.py       # Configuration loader
│
├── binance_keys/              # 🔐 API Keys storage
│
├── project_management/        # Project docs & issues
│
├── sandbox*.py                # Testing scripts
├── main.py                    # 🎯 Application entry point
└── *.md                       # Documentation
```

### 🎨 Architecture Diagram

[schema-app.puml](schema-app.puml)

<details>
  <summary>📐 Plant UML Schema</summary>

```
@startuml
namespace domain.entities {
  class Deal {
    - id: int
    - currency_pair_id: int
    - status: string
    - buy_order: Order
    - sell_order: Order
    - created_at: int
    - closed_at: int
    + open()
    + close()
    + cancel()
  }

  class Order {
    - id: int
    - type: string
    - side: string
    - status: string
    - price: float
    - amount: float
    - exchange_id: string
    + place()
    + cancel()
    + is_open()
    + is_closed()
  }

  class CurrencyPair {
    - base_currency: string
    - quote_currency: string
    - symbol: string
    - order_life_time: int
    - deal_quota: float
    - profit_markup: float
    - deal_count: int
  }

  class Ticker {
    - symbol: string
    - price: float
    - timestamp: int
    - volume: float
    - signals: Dict
    + update_signals()
  }
}

namespace domain.factories {
  class DealFactory {
    + create_new_deal(cp: CurrencyPair, ...): Deal
  }

  class OrderFactory {
    + create_buy_order(cp: CurrencyPair, ...): Order
    + create_sell_order(cp: CurrencyPair, ...): Order
  }
}

namespace domain.services {
  class TradingService {
    - deal_factory: DealFactory
    - deals_repo: DealsRepository
    - order_service: OrderService
    + open_deal_if_needed(signals, cp: CurrencyPair)
    + update_deal_status(deal: Deal, orders_info): void
  }

  class OrderService {
    - order_factory: OrderFactory
    - orders_repo: OrdersRepository
    - exchange_connector: ExchangeConnector
    + place_buy_order(...)
    + place_sell_order(...)
    + cancel_order(...)
  }

  class OrderBookAnalyzer {
    + analyze_spread()
    + analyze_liquidity()
    + find_support_resistance()
    + calculate_slippage()
    + generate_signal()
  }

  class TradingDecisionEngine {
    + combine_signals()
    + generate_modifications()
    + calculate_confidence()
  }
}

namespace infrastructure.connectors {
  interface ExchangeConnector {
    + fetch_balance()
    + create_order(symbol, side, type, amount, price)
    + cancel_order(order_id, symbol)
    + fetch_ohlcv(symbol, timeframe, since, limit)
    + fetch_orders(symbol)
  }

  class ProExchangeConnector {
    + watch_ticker()
    + watch_orderbook()
    + create_order_async()
  }
}

namespace infrastructure.repositories {
  interface DealsRepository {
    + save(deal: Deal)
    + get_by_id(deal_id: int): Deal
    + get_open_deals(): List<Deal>
  }

  interface OrdersRepository {
    + save(order: Order)
    + get_by_id(order_id: int): Order
    + get_all_by_deal(deal_id: int): List<Order>
  }

  interface TickersRepository {
    + save(ticker: Ticker)
    + get_latest(): Ticker
    + get_history(): List<Ticker>
  }
}

@enduml
```

</details>

---

## 🚀 Quick Start

### 📦 Installation

```bash
# Clone repository
git clone <repository-url>
cd new_autotrade

# Install dependencies
pip install -r requirements.txt

# Configure API keys
# Create `.env` from `.env.example` and add your API keys
```

### ⚙️ Configuration

Configuration is loaded from `config/config.json` and can be overridden by creating a `.env` file in the project root. See `.env.example` for required variables.

### 🎯 Run Trading

```bash
# Start the trading system
python main.py
```

---

## 📊 Performance

### 📈 **Real-time Metrics**
- **Tick Processing**: < 1ms под нормальными условиями
- **WebSocket Latency**: минимальная задержка данных  
- **Memory Efficiency**: оптимизированное хранение истории
- **CPU Optimization**: эффективные вычисления индикаторов

### 🎯 **Trading Statistics**
- **Signal Accuracy**: улучшена благодаря OrderBook анализу
- **Slippage Control**: автоматическая валидация ликвидности
- **Risk Management**: многоуровневая система защиты

### 📊 **System Components**
- **~500+ lines** основного торгового кода
- **11+ domain services** для разных аспектов торговли
- **4 types of analysis**: MACD, volatility, trends, orderbook
- **3 protection levels**: cooldown, limits, liquidity validation

---

## 🔧 Configuration

### 🎛️ **OrderBook Analysis Settings**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `min_volume_threshold` | Minimum volume for analysis | 1000 |
| `big_wall_threshold` | Big wall detection threshold | 5000 |
| `max_spread_percent` | Max allowed spread | 0.3% |
| `min_liquidity_depth` | Min liquidity depth | 15 |
| `typical_order_size` | Typical order size | 10 USDT |
| `monitoring_interval` | Monitoring interval | 0.1 sec |

### 🛡️ **Trading Protection Settings**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `enable_orderbook_validation` | Enable orderbook validation | true |
| `orderbook_confidence_threshold` | Confidence threshold | 0.6 |
| `require_orderbook_support` | Require orderbook support | false |
| `log_orderbook_analysis` | Log orderbook analysis | true |

---

## 📈 Trading Process

### 🔄 **Main Trading Loop**

```python
🟢🔥 MACD СИГНАЛ → 📊 АНАЛИЗ СТАКАНА → ✅/❌ РЕШЕНИЕ → 🧮 КАЛЬКУЛЯТОР → 🆕 СДЕЛКА
```

### ✅ **Successful Signal Example**
```
🟢🔥 MACD СИГНАЛ ПОКУПКИ ОБНАРУЖЕН! ПРОВЕРЯЕМ СТАКАН...
   📈 MACD > Signal: -0.000050 > -0.000064
   📊 Анализ стакана: спред 0.23%, дисбаланс +15.3% (покупатели)
   ✅ СТАКАН ПОДДЕРЖИВАЕТ: strong_buy (доверие: 85%)
   🔧 Используем цену поддержки: 0.3255 вместо 0.3259
   💰 Создана оптимизированная сделка с прибылью 0.80%
```

### ❌ **Rejected Signal Example**
```
🟢🔥 MACD СИГНАЛ ПОКУПКИ ОБНАРУЖЕН! ПРОВЕРЯЕМ СТАКАН...
   📊 Анализ стакана: спред 0.85%, слиппедж 2.45%
   ❌ СТАКАН: Отклонено (критические проблемы ликвидности)
```

---

## 🛡️ Safety Features

### 🔒 **Protection Mechanisms**
- **SignalCooldownManager** - предотвращение переторговки.
- **Position Limits** - ограничение количества активных сделок.
- **OrderBook Validation** - проверка качества стакана.
- **Stale Order Monitoring** - отмена "застрявших" ордеров для предотвращения потерь.

### ⚠️ **Risk Management**
- **Stale Order Monitoring** - отмена "застрявших" ордеров по времени и отклонению цены.
- **Emergency Shutdown** - возможность экстренно остановить всю торговлю и отменить ордера.
- **Price Deviation Check** - часть мониторинга "протухших" ордеров.
- **Position Sizing** - адаптивный размер позиций.
- **Market Analysis** - анализ рыночных условий.

### 🔐 **Security Features**
- **Separate API Keys** для sandbox и production.
- **Environment-based Configuration** - безопасное управление ключами через переменные окружения.
- **Private Key Storage** в отдельной папке binance_keys/.

---

## 📋 Development Roadmap

### ✅ **Phase 1 & 2: Foundation & Core Logic (Completed)**
- [x] **Асинхронная архитектура**
- [x] **Безопасная конфигурация** (через .env)
- [x] **Реализация торговой логики** (размещение ордеров)
- [x] **Управление рисками** (мониторинг ордеров, cooldown)
- [x] **Персистентность данных** (через JSON)

### 🚀 **Phase 3: Production Readiness (Next Steps)**
- [ ] **Продвинутая обработка ошибок** (Reconnect, Retry)
- [ ] **Мониторинг и алерты** (Health checks, Telegram)
- [ ] **Комплексное тестирование** (Unit, Integration, Backtests)
- [ ] **State Management** (восстановление состояния при перезапуске)

### ✨ **Phase 4: Advanced Features (Future)**
- [ ] **Multi-pair торговля**
- [ ] **ML-предсказания**
- [ ] **REST API** для управления ботом

---

## 🎯 Issues Overview


### 🔥 **Critical Issues** (Must Have для v3.0.0)

🏗️ **M1** | [x] Главный дирижер - разделить монолитную логику run_realtime_trading.py на управляемые компоненты

🏗️ **M1** | [x] Реальное выставление ордеров - бот фактически торгует и зарабатывает деньги

🏗️ **M2** | [x] Система хранения данных - данные не теряются при перезапуске

### ⚡ **High Priority Issues** (Important для стабильности)

🏗️ **M1** | [x] Управление рисками - защита от потери средств через stop-loss и лимиты

🏗️ **M2** | [ ] Управление состоянием - graceful restart без потери контекста

🏗️ **M2** | [x] Управление конфигурацией - security compliance и удобство настройки

🏗️ **M3** | [ ] Обработка ошибок - устойчивость к сбоям и автовосстановление

🏗️ **M3** | [ ] Безопасность - шифрование sensitive данных и защита от атак

### 📈 **Medium Priority Issues** (Nice to Have улучшения)

🏗️ **M1** | [x] Улучшенный анализ рынка - лучшие торговые решения

🏗️ **M1** | [x] Агрегация сигналов - меньше ложных сигналов

🏗️ **M3** | [ ] Мониторинг системы - proactive обнаружение проблем

🏗️ **M4** | [ ] Оптимизация производительности - < 1ms обработка тика в 95% случаев

### 🎯 **Low Priority Issues** (Future Features)

🏗️ **M2** | [x] Улучшенные репозитории - быстрые database операции

🏗️ **M3** | Резервное копирование - защита от потери данных

🏗️ **M4** | Мульти-валютная торговля - масштабирование на множественные активы



---

## 📖 Documentation

### 📋 **Available Documents**
- [`RELEASE_NOTES.md`](RELEASE_NOTES.md) - Полные релизные заметки v2.2.0
- [`RELEASE_NOTES_v2.1.0.md`](RELEASE_NOTES_v2.1.0.md) - Детальная документация релиза
- [`ROADMAP.md`](ROADMAP.md) - Детальная техническая оценка и планы развития
- [`ORDERBOOK_INTEGRATION.md`](ORDERBOOK_INTEGRATION.md) - Документация по интеграции анализа стакана
- [`CHANGELOG.md`](CHANGELOG.md) - История изменений

### 🗂️ **Project Management**
- [`project_management/issues_summary.md`](project_management/issues_summary.md) - Полный список всех issues
- [`project_management/milestones.md`](project_management/milestones.md) - 4 milestone с временными рамками
- [`project_management/implementation_plan.md`](project_management/implementation_plan.md) - Готовый план реализации
- [`project_management/issues/`](project_management/issues/) - 15 детальных технических заданий
- [`ISSUE_06_IMPLEMENTATION_GUIDE.md`](ISSUE_06_IMPLEMENTATION_GUIDE.md) - отчет по реализации #6
- [`ISSUE_07_IMPLEMENTATION_GUIDE.md`](ISSUE_07_IMPLEMENTATION_GUIDE.md) - отчет по реализации #7
- [`ISSUE_08_IMPLEMENTATION_GUIDE.md`](ISSUE_08_IMPLEMENTATION_GUIDE.md) - отчет по реализации #8
- [`ISSUE_15_IMPLEMENTATION_GUIDE.md`](ISSUE_15_IMPLEMENTATION_GUIDE.md) - отчет по реализации #15
- [`ISSUE_18_IMPLEMENTATION_GUIDE.md`](ISSUE_18_IMPLEMENTATION_GUIDE.md) - отчет по реализации #18
- [`ISSUE_19_IMPLEMENTATION_GUIDE.md`](ISSUE_19_IMPLEMENTATION_GUIDE.md) - пример полного отчета по реализации
- [`ISSUE_20_IMPLEMENTATION_GUIDE.md`](ISSUE_20_IMPLEMENTATION_GUIDE.md) - отчет по реализации #20

### 🛠️ **Technical Specs**
**Language**: Python 3.10
**Main Dependencies**: `requirements.txt`

- **Architecture**: Clean Architecture / DDD
- **Concurrency**: asyncio-based

### 🔗 **Useful Links**
- **Exchange**: Binance API
- **Technical Analysis**: TA-Lib
- **WebSocket**: ccxt.pro
- **Time Sync**: Binance Time API

## 🌿 Branch Strategy
AutoTrade now follows the **GitFlow** workflow:
- `main` – production ready code
- `stage` – pre-production testing
- `dev` – integration branch for features
- `feature/*` – new functionality based on `dev`
- `release/*` – release preparation based on `stage`
- `hotfix/*` – urgent fixes based on `main`

```
feature/*   -> dev
dev         -> stage
stage       -> release/*
release/*   -> main + dev
hotfix/*    -> main + dev
```

### 🔖 Versioning
Releases are created automatically on pushes to `main`. The workflow analyzes commit messages
and increments **major**, **minor** or **patch** version accordingly, tagging the repository with
`vX.Y.Z` and generating release notes.

---

## 🚀 Deployment

### 📦 **Real File Structure**
```
new_autotrade/
├── main.py              # Start here
├── config/config.json   # Main configuration
├── .env.example         # Environment overrides
├── binance_keys/        # Your API keys here
├── domain/              # Core business logic
├── application/         # Use cases & utilities
├── infrastructure/      # External integrations
├── project_management/  # Issues & planning docs
└── *.md                # Documentation
```

### 🎯 **Getting Started**
1. **Configure API Keys** in `binance_keys/`
2. **Create `.env`** based on `.env.example` to override settings
3. **Run** `python main.py`
4. **Monitor** logs for trading activity

---

## 💎 Conclusion

**AutoTrade v2.3.0** представляет собой профессиональную торговую систему с интеллектуальным анализом рынка. Интеграция анализа биржевого стакана в сочетании с MACD индикаторами создает мощный инструмент для автоматической торговли.

**Ключевые преимущества:**
- ✅ **Умные решения** на основе анализа ликвидности
- ✅ **Высокая производительность** благодаря асинхронной архитектуре  
- ✅ **Надежная защита** от переторговки и плохих сигналов
- ✅ **Гибкая конфигурация** под разные торговые стратегии

> *"Торгуйте умнее, а не больше"* 🎯

---

**Разработчик**: Dmitry Strelets (sni10)  
**Репозиторий**: `velostour/new_autotrade`  
**Лицензия**: Private
