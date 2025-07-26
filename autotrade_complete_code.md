# 🤖 AutoTrade - Полный код проекта

**Сгенерировано:** 2025-07-26 19:06:35  
**Проект:** F:\HOME\new_autotrade  
**Файлов обработано:** 59 из 71  
**Общий размер:** 0 байт  
**Строк кода:** 0  

---

## 📑 Оглавление

- [🌳 Структура проекта](#-структура-проекта)
- [📊 Статистика файлов](#-статистика-файлов)
- [📝 Документация](#-документация)
- [🐍 Python файлы](#-python-файлы)
- [📄 TXT файлы](#txt-файлы)
- [📄 YML файлы](#yml-файлы)

---

## 🌳 Структура проекта

```
📁 new_autotrade/
├── .coverage
├── .dockerignore
├── .env
├── .env.example
├── .github
│   └── workflows
│       ├── auto-sync-branches.yml
│       ├── python-tests.yml
│       └── versioning.yml
├── .gitignore
├── 22.py
├── AGENTS.md
├── binance_keys
│   ├── .gitignore
│   ├── id_ed25519.pem
│   └── id_ed25519pub.pem
├── CLAUDE.md
├── DATA_ARCHITECTURE_REFACTORING_PLAN.md
├── DATA_ARCHITECTURE_REFACTORING_PLAN_FIXED.md
├── Dockerfile
├── exchange_analysis_report.txt
├── GEMINI.md
├── main.py
├── order_history_viewer.py
├── quick_swap.py
├── README.md
├── requirements.txt
├── sandbox.py
├── sandbox_analysis.py
├── schema-app.puml
├── schema-app.svg
├── src
│   ├── __init__.py
│   ├── application
│   │   ├── __init__.py
│   │   └── use_cases
│   │       ├── __init__.py
│   │       └── run_realtime_trading.py
│   ├── domain
│   │   ├── __init__.py
│   │   ├── entities
│   │   │   ├── __init__.py
│   │   │   ├── currency_pair.py
│   │   │   ├── deal.py
│   │   │   ├── order.py
│   │   │   └── ticker.py
│   │   ├── factories
│   │   │   ├── __init__.py
│   │   │   ├── deal_factory.py
│   │   │   └── order_factory.py
│   │   └── services
│   │       ├── __init__.py
│   │       ├── deals
│   │       │   ├── __init__.py
│   │       │   ├── deal_completion_monitor.py
│   │       │   └── deal_service.py
│   │       ├── indicators
│   │       │   ├── __init__.py
│   │       │   └── cached_indicator_service.py
│   │       ├── market_data
│   │       │   ├── __init__.py
│   │       │   ├── market_analysis_service.py
│   │       │   ├── orderbook_analyzer.py
│   │       │   ├── orderbook_service.py
│   │       │   └── ticker_service.py
│   │       ├── orders
│   │       │   ├── __init__.py
│   │       │   ├── buy_order_monitor.py
│   │       │   ├── filled_buy_order_handler.py
│   │       │   ├── order_execution_service.py
│   │       │   ├── order_service.py
│   │       │   └── order_timeout_service.py
│   │       ├── risk
│   │       │   └── stop_loss_monitor.py
│   │       └── trading
│   │           ├── __init__.py
│   │           ├── signal_cooldown_manager.py
│   │           ├── trading_decision_engine.py
│   │           └── trading_service.py
│   └── infrastructure
│       ├── __init__.py
│       ├── connectors
│       │   ├── __init__.py
│       │   └── exchange_connector.py
│       ├── database
│       └── repositories
│           ├── __init__.py
│           ├── deals_repository.py
│           ├── orders_repository.py
│           └── tickers_repository.py
└── test_prod.py
```

## 📊 Статистика файлов

| Метрика | Значение |
|---------|----------|
| Всего файлов найдено | 71 |
| Обработано файлов | 59 |
| Пропущено файлов | 12 |
| Общее количество строк | 0 |
| Общий размер (байт) | 0 |

### Распределение по типам файлов:

| Тип | Количество |
|-----|------------|
| .md | 6 |
| .py | 48 |
| .txt | 2 |
| .yml | 3 |

## 📝 Markdown документация

### 📄 `AGENTS.md`

```markdown
# Инструкция для Codex и внешних контрибьюторов

Этот репозиторий содержит торговую систему **AutoTrade**, построенную на принципах Domain-Driven Design и асинхронной архитектуре. Пожалуйста, соблюдайте следующие правила при работе с кодом.

## Общая структура проекта
```
new_autotrade/
├── domain/            # бизнес-логика
├── application/       # сценарии использования
├── infrastructure/    # интеграции и хранилища
├── config/            # конфигурация
├── binance_keys/      # API‑ключи
└── tests/             # тесты pytest
```

Ниже приведён фрагмент из README с подробным описанием структуры:
```
### 📐 Domain-Driven Design Structure (Реальная структура проекта)

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
│   ├── repositories/          # Data storage
│   │   ├── deals_repository.py
│   │   ├── orders_repository.py
│   │   └── tickers_repository.py
│   └── connectors/            # External services
│       ├── exchange_connector.py     # Exchange API
│       └── pro_exchange_connector.py # 🆕 WebSocket ccxt.pro
│
├── config/
│   └── config.json            # Configuration file
│
├── binance_keys/              # 🔐 API Keys storage
│
├── project_management/        # Project docs & issues
│
├── sandbox*.py                # Testing scripts
├── main.py                    # 🎯 Application entry point
└── *.md                       # Documentation
```

## Правила разработки
1. **Не коммитить .env и ключи.** Файл `.env.example` используется как шаблон, реальные переменные окружения не добавляйте в репозиторий. Это указано в issue:
```
- Предусмотреть backward compatibility при миграции с текущего config.json
- Добавить configuration schema для IDE autocompletion
- Рассмотреть integration с external config management (Consul, etcd в будущем)
- Важно: never commit .env файлы в git, всегда использовать .env.example
```
2. **Соблюдайте асинхронный стиль.** В README подчёркивается важность асинхронной архитектуры:
```
- 📊 **Двухуровневая фильтрация сигналов**: MACD + OrderBook
- ⚡ **Асинхронная архитектура** на базе asyncio и WebSocket
- 🛡️ **Система защиты** от переторговки и плохих сделок

### 🧠 Intelligent Trading
- **MACD Technical Analysis** с histogram анализом
- **OrderBook Intelligence** - анализ спреда, ликвидности, поддержки/сопротивления
- **Smart Order Modifications** - корректировка цен на основе технических уровней
- **Signal Confidence Scoring** - система оценки уверенности сигналов

### ⚡ Performance & Reliability
- **Async Architecture** на базе asyncio для максимальной скорости
- **WebSocket Integration** через ccxt.pro для real-time данных
```
3. **Следуйте структуре DDD.** Бизнес‑логика должна находиться в `domain/`, прикладные сценарии в `application/`, работу с внешними сервисами располагайте в `infrastructure/`.
4. **Пишите docstring’и и используйте типизацию.** Код оформлен по PEP8 и применяет typing.
5. **Устанавливайте зависимости** командой:
```bash
pip install -r requirements.txt
```
6. **Запуск тестов** – перед коммитом убедитесь, что проходят все тесты:
```bash
pytest
```
7. **Коммит сообщения** должны быть лаконичными и описывать сделанные изменения.

Следование этим правилам поможет поддерживать целостность архитектуры и стабильность проекта.

```

### 📄 `CLAUDE.md`

```markdown
# CLAUDE_RU.md

Этот файл предоставляет рекомендации Claude Code (claude.ai/code) при работе с кодом в данном репозитории.

## Обзор
AutoTrade v2.4.0 - это профессиональная система торговли криптовалютами с асинхронным жизненным циклом сделок и умным риск-менеджментом. Система построена на архитектуре Domain-Driven Design (DDD) и выполняет автоматическую торговлю через поэтапное исполнение BUY→SELL ордеров с трёхуровневой защитой от убытков.

## Архитектура
Кодовая база следует принципам чистой архитектуры с четким разделением ответственности:

### Основная структура
- **src/** - Основной исходный код
  - **domain/** - Бизнес-логика и сущности
    - **entities/** - Основные бизнес-объекты (Deal, Order, CurrencyPair, Ticker)
    - **services/** - Бизнес-сервисы (модульная структура по назначению)
      - **deals/** - Управление сделками (DealService, DealCompletionMonitor)
      - **orders/** - Управление ордерами (OrderService, BuyOrderMonitor, FilledBuyOrderHandler)
      - **trading/** - Торговая логика (TradingService, TradingDecisionEngine)
      - **risk/** - Управление рисками (StopLossMonitor)
      - **market_data/** - Рыночные данные (TickerService, OrderBookAnalyzer)
      - **utils/** - Утилиты (DecimalRoundingService, OrderbookCache)
    - **factories/** - Паттерны создания объектов
  - **application/** - Сценарии использования и сервисы приложения
    - **use_cases/** - Основные торговые рабочие процессы
    - **utils/** - Утилиты приложения, такие как PerformanceLogger
  - **infrastructure/** - Внешние интеграции
    - **connectors/** - Подключения к API бирж (интеграция ccxt)
    - **repositories/** - Сохранение данных (реализации в памяти)
  - **config/** - Файлы конфигурации
- **docs/** - Документация
- **tests/** - Тесты
- **binance_keys/** - Хранение API ключей

### Ключевые компоненты v2.4.0
- **TradingService** - Главный оркестратор торговых операций
- **OrderExecutionService** - Обрабатывает реальное размещение ордеров (Issue #19)
- **FilledBuyOrderHandler** (🆕) - Обработчик исполненных BUY ордеров
- **DealCompletionMonitor** (🆕) - Мониторинг завершения сделок
- **BuyOrderMonitor** (улучшен) - Мониторит устаревшие ордера и синхронизирует виртуальные SELL
- **StopLossMonitor** (🆕) - Умная трёхуровневая защита от убытков
- **OrderBookAnalyzer** - Анализирует ликвидность и спред стакана заявок
- **TradingDecisionEngine** - Комбинирует сигналы MACD с данными стакана заявок
- **SignalCooldownManager** - Предотвращает переторговку
- **DecimalRoundingService** (🆕) - Точное округление для торговых операций
- **OrderbookCache** (🆕) - Кэширование данных стакана

## Общие команды разработки

### Запуск системы
```bash
# Основная торговая система
python main.py
```

### Зависимости
Система требует следующие основные зависимости:
```bash
pip install requirements.txt
```

### Конфигурация
- Основная конфигурация: `config/config.json`
- API ключи: каталог `binance_keys/`
- Поддерживает как песочницу, так и производственную среду

## Руководство по разработке

### Паттерны архитектуры кода
- Следуйте принципам DDD: храните бизнес-логику в доменном слое
- Используйте фабрики для создания объектов
- Реализуйте паттерн репозитория для доступа к данным
- Сервисы должны быть без состояния и сосредоточены на единственной ответственности

### Асинхронное программирование
- Использует asyncio для параллельных операций
- WebSocket соединения через ccxt.pro
- Будьте осторожны с границами синхронизации/асинхронности - избегайте ненужных async/await
- Используйте `await asyncio.sleep()` вместо `time.sleep()` в асинхронных контекстах

### Поток торговой логики
1. **Сбор данных**: WebSocket тикеры → TickerService → Репозиторий
2. **Генерация сигналов**: Анализ MACD → Технические сигналы
3. **Анализ стакана заявок**: Валидация спреда/ликвидности → Торговое решение
4. **Исполнение сделок**: OrderExecutionService → API биржи
5. **Мониторинг ордеров**: BuyOrderMonitor → Управление устаревшими ордерами

### Безопасность и управление рисками
- SignalCooldownManager предотвращает переторговку
- Валидация стакана заявок обеспечивает достаточную ликвидность
- Лимиты размера позиции и механизмы стоп-лосса
- Отдельные конфигурации для песочницы/производства

## Ключевые файлы для понимания

### Точки входа
- `main.py` - Основная точка входа приложения с полной торговой настройкой
- `application/use_cases/run_realtime_trading.py` - Основной торговый цикл

### Основная бизнес-логика
- `domain/services/trading_service.py` - Главный торговый оркестратор
- `domain/services/order_execution_service.py` - Реальное размещение ордеров
- `domain/services/orderbook_analyzer.py` - Анализ глубины рынка
- `domain/services/trading_decision_engine.py` - Логика комбинирования сигналов

### Управление данными
- `domain/entities/deal.py` - Сущность торговой сделки
- `domain/entities/order.py` - Сущность ордера с интеграцией биржи
- `infrastructure/repositories/` - Слой сохранения данных

### Внешние интеграции
- `infrastructure/connectors/exchange_connector.py` - Обертка API биржи
- `infrastructure/connectors/pro_exchange_connector.py` - WebSocket коннектор

## Подход к тестированию
- Используйте режим песочницы для разработки (`use_sandbox=True`)
- Тестовые скрипты в файлах sandbox*.py
- Производственное тестирование с `test_prod.py`
- В настоящее время нет формального фреймворка модульного тестирования - полагается на интеграционное тестирование

## Управление конфигурацией
- Конфигурация на основе JSON в `config/config.json`
- Настройки для конкретной среды (песочница/производство)
- API ключи хранятся в отдельных файлах с надлежащей безопасностью
- Параметры анализатора стакана заявок настраиваются

## Соображения производительности
- Кэшированные вычисления индикаторов для предотвращения пересчета
- WebSocket соединения для данных в реальном времени
- Логирование производительности с детальными метриками
- Эффективное по памяти хранение тикеров с ограничениями по размеру

## Заметки о безопасности
- API ключи хранятся в отдельных файлах (не в коде)
- Приватные ключи для аутентификации API
- Отдельные среды песочницы/производства
- Никаких конфиденциальных данных в коде или логах

## Общие проблемы и решения

### Проблемы с WebSocket соединением
- Проверьте сетевое подключение
- Проверьте API ключи и разрешения
- Используйте политику цикла событий для Windows в системах Windows

### Отладка торговой логики
- Мониторьте логи производительности для времени обработки тиков
- Проверьте статус задержки сигнала
- Проверьте состояние стакана заявок перед торговлей
- Просмотрите количество активных сделок и лимиты

### Управление ордерами
- BuyOrderMonitor автоматически обрабатывает устаревшие ордера
- Проверьте подключение к бирже перед размещением ордеров
- Убедитесь в достаточном балансе перед торговлей

## Рабочий процесс разработки
1. Внесите изменения в соответствующие слои домена/инфраструктуры
2. Сначала протестируйте в режиме песочницы
3. Проверьте через скрипты песочницы
4. Обновите конфигурацию при необходимости
5. Протестируйте интеграцию через main.py
6. Используйте производственный режим только после полного тестирования

## Будущая разработка
Система спроектирована для расширяемости:
- Поддержка нескольких валютных пар
- Улучшенная генерация сигналов на основе ML
- REST API для внешнего управления
- Слой сохранения базы данных
- Продвинутые функции управления рисками

Обратитесь к ROADMAP.md и каталогу project_management/ для подробных планов разработки и задач.

```

### 📄 `DATA_ARCHITECTURE_REFACTORING_PLAN.md`

```markdown
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
```

### 📄 `DATA_ARCHITECTURE_REFACTORING_PLAN_FIXED.md`

```markdown
# 🏗️ ПЛАН РЕФАКТОРИНГА АРХИТЕКТУРЫ ДАННЫХ AutoTrade v2.4.0 (ИСПРАВЛЕННАЯ ВЕРСИЯ)

## 📋 ПРОБЛЕМЫ ТЕКУЩЕЙ АРХИТЕКТУРЫ

### 🔥 Главная проблема - избыточная Ticker Entity:

**Текущая проблема:**
```python
# src/domain/entities/ticker.py - ИЗБЫТОЧНО
class Ticker:
    def __init__(self, data: Dict):
        self.timestamp = data.get("timestamp", int(time.time() * 1000))
        self.symbol = data.get("symbol", "")
        self.price = data.get("last", 0.0)
        # ... просто копирует JSON поля
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "price": self.price,
            # ... конвертирует обратно в JSON
        }
```

**Проблема в InMemoryTickerRepository:**
```python
# src/infrastructure/repositories/tickers_repository.py - НЕЭФФЕКТИВНО
class InMemoryTickerRepository:
    def __init__(self):
        self.tickers = []  # Хранит объекты Ticker вместо JSON
    
    def save(self, ticker: Ticker):  # Создает объект для каждого тика
        self.tickers.append(ticker)
```

### 🚨 Реальные проблемы в существующих сервисах:

| Сервис | Проблема | Что делает |
|--------|----------|------------|
| **TickerService** | `price_history_cache = []` | Хранит данные + обрабатывает |
| **CachedIndicatorService** | 3 типа кэшей + буферы | Только кэширование |
| **OrderService** | Размещение + мониторинг + валидация | Всё подряд |
| **OrderBookAnalyzer** | Анализ + сигналы | Анализ + генерация |

---

## ✅ РЕШЕНИЕ - РАЗДЕЛЕНИЕ ДАННЫХ

### 🎯 Основной принцип:
- **Бизнес-объекты** (Deal, Order) → Entities + Repositories
- **Потоковые данные** (ticker, indicators) → JSON массивы в StreamRepository

### 📊 Что оставить как есть:
```python
# Эти сущности ПРАВИЛЬНЫЕ - у них есть бизнес-логика:
- Deal (статусы, жизненный цикл, расчет прибыли)
- Order (валидация, связи с биржей, состояния)
- CurrencyPair (торговые правила, лимиты)
```

### 🗑️ Что убрать:
```python
# УДАЛИТЬ: Ticker Entity - просто JSON маппинг
# ЗАМЕНИТЬ НА: Прямую работу с JSON в repositories
```

---

## 🚀 КОНКРЕТНЫЙ ПЛАН РЕФАКТОРИНГА

### ЭТАП 1 - Заменить Ticker Entity на JSON хранилище

<details>
<summary>🆕 StreamDataRepository</summary>

```python
# src/infrastructure/repositories/stream_data_repository.py
class StreamDataRepository:
    def __init__(self, max_size: int = 1000):
        self.tickers: List[Dict] = []  # Прямое хранение JSON
        self.indicators: List[Dict] = []
        self.max_size = max_size
    
    def save_ticker(self, ticker_data: Dict) -> None:
        """Сохранить тикер без создания объекта"""
        self.tickers.append(ticker_data)
        if len(self.tickers) > self.max_size:
            self.tickers = self.tickers[-self.max_size:]
    
    def get_last_prices(self, n: int) -> List[float]:
        """Прямой доступ к ценам из JSON"""
        return [t['last'] for t in self.tickers[-n:]]
    
    def get_price_history(self, n: int) -> List[float]:
        """Для расчета индикаторов"""
        return [t['last'] for t in self.tickers[-n:]]
```

</details>

### ЭТАП 2 - Обновить TickerService

<details>
<summary>🔧 Обновленный TickerService</summary>

```python
# src/domain/services/market_data/ticker_service.py
class TickerService:
    def __init__(self, stream_repo: StreamDataRepository):
        self.stream_repo = stream_repo
        # Убираем все кэши и буферы
    
    def process_ticker(self, ticker_data: dict) -> dict:
        """Обработать тикер как JSON"""
        # Простая обработка без создания объекта
        processed_data = {
            'timestamp': ticker_data.get('timestamp', int(time.time() * 1000)),
            'symbol': ticker_data.get('symbol'),
            'last': ticker_data.get('last'),
            'bid': ticker_data.get('bid'),
            'ask': ticker_data.get('ask'),
            'volume': ticker_data.get('baseVolume', 0)
        }
        
        # Сохранить в потоковое хранилище
        self.stream_repo.save_ticker(processed_data)
        return processed_data
    
    def get_latest_price(self, symbol: str) -> float:
        """Получить последнюю цену"""
        tickers = self.stream_repo.get_last_tickers(1)
        return tickers[0]['last'] if tickers else 0.0
```

</details>

### ЭТАП 3 - Обновить CachedIndicatorService

<details>
<summary>🔧 Упрощенный CachedIndicatorService</summary>

```python
# src/domain/services/indicators/cached_indicator_service.py
class CachedIndicatorService:
    def __init__(self, stream_repo: StreamDataRepository):
        self.stream_repo = stream_repo
        # Убираем все буферы и кэши
    
    def update_fast_indicators(self, price: float) -> Dict:
        """Рассчитать быстрые индикаторы"""
        prices = self.stream_repo.get_price_history(25)
        
        if len(prices) < 25:
            return {}
        
        sma_7 = sum(prices[-7:]) / 7 if len(prices) >= 7 else 0
        sma_25 = sum(prices[-25:]) / 25
        
        indicator_data = {
            'timestamp': int(time.time() * 1000),
            'sma_7': round(sma_7, 8),
            'sma_25': round(sma_25, 8)
        }
        
        # Сохранить в потоковое хранилище
        self.stream_repo.save_indicator(indicator_data)
        return indicator_data
```

</details>

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### ✅ Производительность:
- **+200%** скорость обработки тикеров (нет создания объектов)
- **-50%** потребление памяти (JSON вместо объектов)
- **-70%** строк кода в репозиториях

### ✅ Архитектура:
- Четкое разделение бизнес-объектов и потоковых данных
- Упрощение сервисов - каждый делает одну вещь
- Легкость тестирования и расширения

### ✅ Совместимость:
- Все существующие сервисы продолжают работать
- Постепенная миграция без поломок
- Возможность отката к старой версии

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

1. **Создать StreamDataRepository** 
2. **Обновить TickerService** для работы с JSON
3. **Упростить CachedIndicatorService**
4. **Протестировать производительность**
5. **Постепенно мигрировать остальные сервисы**

**Главное**: Не изобретать новые сущности, а оптимизировать существующие!
```

### 📄 `GEMINI.md`

```markdown
# Конфигурация проекта Gemini: AutoTrade

## 1. 🎯 Обзор проекта

- **Название проекта:** AutoTrade
- **Версия:** v2.4.0 "Smart Risk Management & Infrastructure"
- **Описание:** Интеллектуальная система автоматической торговли с асинхронным жизненным циклом сделок и умным риск-менеджментом.
- **Основные технологии:** Python 3.10+, asyncio, ccxt.pro, TA-Lib, numpy.
- **Основная цель:** Выполнение прибыльных сделок с минимальными рисками через поэтапное исполнение BUY→SELL ордеров и трёхуровневую систему защиты от убытков.

## 2. 🏗️ Архитектура

Проект следует подходам **предметно-ориентированного проектирования (DDD)** и **чистой архитектуры**, разделяя ответственности на отдельные слои.

```
new_autotrade/
├── src/                 # 🎯 Основной исходный код
│   ├── domain/          # 🧠 Основная бизнес-логика (сущности, сервисы, фабрики)
│   ├── application/     # 🚀 Сценарии использования и логика приложения
│   ├── infrastructure/  # 🔌 Внешние интеграции (API бирж, репозитории)
│   └── config/          # ⚙️ Управление конфигурацией
├── docs/                # 📚 Документация
├── tests/               # 🧪 Тесты
└── project_management/  # 📋 Управление проектом
```

### Ключевые модули и новый жизненный цикл сделки

Архитектура была значительно переработана для внедрения более надежной и асинхронной модели управле��ия сделками. Центральным изменением стал отказ от одновременного размещения `BUY` и `SELL` ордеров.

**Новый жизненный цикл сделки:**

1.  **Инициация:** `OrderExecutionService` получает сигнал. Он создает сущность `Deal` и немедленно размещает на бирже только `BUY` ордер. Одновременно он создает `SELL` ордер, но сохраняет его локально со статусом `PENDING`.
2.  **Исполнение покупки:** `FilledBuyOrderHandler` (новый сервис) периодически проверяет статусы ордеров. Как только он обнаруживает исполненный (`FILLED`) `BUY` ордер, он находит связанный с ним `PENDING SELL` и размещает его на бирже.
3.  **Мониторинг "тухлых" ордеров:** `BuyOrderMonitor` отслеживает активные `BUY` ордера. Если ордер "протух" (цена ушла), он отменяет его, размещает новый `BUY` по актуальной цене, а затем **обновляет** параметры связанного с ним `PENDING SELL` ордера в локальной базе данных.
4.  **Завершение сделки:** `DealCompletionMonitor` (новый сервис) отслеживает открытые сделки. Когда он видит, что и `BUY`, и `SELL` ордера в рамках одной сделки получили статус `FILLED`, он закрывает сделку, меняя ее статус на `CLOSED`.

**Описание ключевых сервисов в новой архитектуре:**

- **`OrderExecutionService`**: **Оркестратор начала сделки.** Его главная задача — инициировать сделку: создать `Deal`, разместить `BUY` ордер на бирже и создать "виртуальный" `SELL` ордер в системе.
- **`FilledBuyOrderHandler`**: **Исполнитель `SELL` ордеров.** Этот сервис является "второй рукой" системы. Он ждет, пока `BUY` ордер будет исполнен, и только после этого отправляет соответствующий `SELL` ордер на биржу.
- **`BuyOrderMonitor`**: **Менеджер рисков для `BUY` ордеров.** Отслеживает "застрявшие" ордера на покупку. При пересоздании "тухлого" ордера он теперь также отвечает за обновление "виртуального" `SELL` ордера, чтобы он соответствовал новым условиям входа.
- **`DealCompletionMonitor`**: **Контролер завершения сделок.** Этот сервис следит за общим состоянием открытых сделок и является единственным компонентом, который переводит сделку в статус `CLOSED` после успешного исполнения обоих ордеров.
- **`TickerService`**: **Генератор первичных сигналов.** Анализирует поток цен и вычисляет индикаторы (MACD), генерируя потенциальные точки входа.
- **`OrderBookAnalyzer`**: **Фильтр сигналов и риск-анализатор.** Проверяет сигнал от `TickerService` на соответствие реальной рыночной ситуации в стакане ордеров, отсеивая ложные или рискованные сигнал��.
- **`StopLossMonitor`** (🆕): **Умная система защиты от убытков.** Трёхуровневая система (предупреждение, критический, экстренный) с анализом стакана перед принятием решений о закрытии позиций.
- **`SignalCooldownManager`**: Функция управления рисками для предотвращения чрезмерной торговли путем введения задержки между сделками для одной и той же пары.
- **`DecimalRoundingService`** (🆕): **Точное округление для торговых операций.** Обеспечивает корректные вычисления с торговыми суммами и ценами.
- **`OrderbookCache`** (🆕): **Кэширование данных стакана.** Оптимизирует производительность анализа стакана заявок.
- **Репозитории (`infrastructure/repositories/`)**: Обрабатывают сохранение данных. В настоящее время реализованы как кэши в памяти, которые записывают данные в файлы JSON (`deals.json`, `orders.json`).

## 3. ⚙️ Основные команды и рабочий процесс

### Установка
Установите все необходимые зависимости из `requirements.txt`.
```bash
pip install -r requirements.txt
```

### Запуск тестов
Проект использует `pytest` для тестирования. Рабочий процесс GitHub Actions (`.github/workflows/python-tests.yml`) автоматически запускает тесты при отправке изменений в ветки `dev`, `stage` и `release`.
```bash
pytest pytest/
```

### Запуск приложения
Основная точка входа — `main.py`. Он инициализирует все сервисы и запускает цикл торговли в реальном времени.
```bash
python main.py
```

## 4. 🔧 Конфигурация

Конфигурация управляется с помощью комбинации файла JSON и переменных окружения, что является безопасным и гибким подходом.

1.  **Базовая конфигурация:** `config/config.json` содержит настройки по умолчанию, не являющиеся конфиденциальными.
2.  **Переопределения окружения:** Файл `.env` в корневом каталоге используется для переопределения любых настроек из файла JSON. Это **предпочтительный метод для хранения конфиденциальных данных**, таких как ключи API.
3.  **Загрузка:** Скрипт `config/config_loader.py` обрабатывает загрузку `config.json` и применяет переопределения из файла `.env`.

**Для настройки локальной разработки:**
1.  Скопируйте `.env.example` в `.env`.
2.  Заполните необходимые значения, особенно `BINANCE_API_KEY_SANDBOX` и `BINANCE_PRIVATE_KEY_PATH_SANDBOX`.
3.  **Важно: файл `.env` указан в `.gitignore` и никогда не должен быть закоммичен в репозиторий.**

## 5. 📈 Основная торговая логика

Интеллект системы основан на двухэтапном процессе проверки сигнала:

1.  **Генерация сигнала MACD:** `TickerService` постоянно анализирует входящие данные о ценах для поиска потенциальных сигналов на ПОКУПКУ на основе пересечений линий MACD и анализа гистограммы.
2.  **Проверка стакана ордеров:** При обнаружении сигнала MACD `TradingDecisionEngine` запрашивает `OrderBookAnalyzer` для проверки сигнала. Анализатор проверяет:
    - **Спред:** Слишком ли велик спред между покупкой и продажей?
    - **Ликвидность:** Достаточно ли объема для совершения сделки без значительного проскальзывания?
    - **Настроение рынка:** Есть ли сильный дисбаланс между покупкой и продажей?
    - **Поддержка/Сопротивление:** Существуют ли значительные "стенки", которые могут выступать в качестве ценовых ориентиров или стопов?
3.  **Решение и модификация:**
    - Если анализ стакана ордеров возвращает сигнал `REJECT` (ОТКЛОНИТЬ), сделка отменяется.
    - Если стакан ордеров предоставляет сигнал `STRONG_BUY` (СИЛЬНАЯ ПОКУПКА) или `WEAK_BUY` (СЛАБАЯ ПОКУПКА), сделка продолжается.
    - `TradingDecisionEngine` может применять "умные модификации", например, корректировать цену входа до ближайшего уровня поддержки, определенного анализатором.

Этот процесс значительно сокращает количество ложных срабатываний и повышает качество исполняемых сделок.

## 6. 🗺️ Краткий обзор дорожной карты разработки

У проекта есть четкий и подробный план развития.

### Завершено:
- **Основная архитектура:** Структура DDD внедрена.
- **Реальная торговля:** `OrderExecutionService` может размещать реальные ордера.
- **Управление рисками:** Реализованы `BuyOrderMonitor` и `SignalCooldownManager`.
- **Сохранение данных:** Функционирует система репозиториев на основе JSON.
- **Конфигурация:** Реализована безопасная загрузка конфигурации через `.env`.

### Следующие шаги (высокий приоритет):
- **Задача №17 (DatabaseService):** Миграция с хранения файлов JSON на надежную базу данных (например, SQLite или PostgreSQL) для повышения производительности и надежности.
- **Задача №16 (StateManagementService):** Внедрить систему для сохранения и восстановления состояния приложения, что позволит корректно перезапускать его без потери открытых сделок.
- **Задача №14 (ErrorHandlingService):** Создать комплексную систему обработки ошибок с повторными попытками и автоматическими выключателями для повышения стабильности.
```

### 📄 `README.md`

```markdown
# 🚀 AutoTrade v2.4.0 - "Интеллектуальное Управление Рисками и Инфраструктура"

> **Интеллектуальная торговая система** с анализом биржевого стакана и индикаторами MACD  
> **Архитектура**: Предметно-ориентированное проектирование (DDD)  
> **Статус**: Готов к работе

[![Тесты](https://github.com/sni10/new_autotrade/actions/workflows/python-tests.yml/badge.svg)](https://github.com/sni10/new_autotrade/actions)
[![Версионирование](https://github.com/sni10/new_autotrade/actions/workflows/versioning.yml/badge.svg)](https://github.com/sni10/new_autotrade/actions)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)

![Торговая система](schema-app.svg)

---

## 📋 Содержание
- [🎯 Обзор](#-обзор)
- [📖 Документация](#-документация)
- [✨ Ключевые возможности](#-ключевые-возможности)
- [���️ Архитектура](#️-архитектура)
- [🚀 Быстрый старт](#-быстрый-старт)
- [📊 Производительность](#-производительность)
- [🔧 Конфигурация](#-конфигурация)
- [📈 Торговый процесс](#-торговый-процесс)
- [🛡️ Системы безопасности](#️-системы-безопасности)
- [📋 План развития](#-план-развития)
- [🎯 Обзор задач](#-обзор-задач)
- [🌿 Стратегия ветвления](#-стратегия-ветвления)
- [🚀 Развертывание](#-развертывание)
- [💎 Заключение](#-заключение)

---

## 🎯 Обзор

**AutoTrade** - профессиональная система для автоматической торговли криптовалютами с интеллектуальным анализом биржевого стакана и техническими индикаторами. Система построена на принципах предметно-ориентированного проектирования (DDD) и использует асинхронную архитектуру для максимальной производительности.

### 🔥 Последний релиз: v2.4.0 - "Интеллектуальное Управление Рисками и Инфраструктура"
- 🔄 **Асинхронный жизненный цикл сделок** - поэтапное исполнение `BUY` → `SELL` ордеров.
- 🛡️ **Умная система стоп-лосса** с трёхуровневой защитой и анализом стакана.
- 🏗️ **Новая архитектура сервисов** - `FilledBuyOrderHandler`, `DealCompletionMonitor`, `StopLossMonitor`.
- ⚙️ **Улучшенное управление рисками** с `DecimalRoundingService` и `OrderbookCache`.

---

## 📖 Документация

### 📚 **Полное руководство**
- [📖 Центр документации](docs/README.md) - Главная страница документации

### 🚀 **Быстрый старт**
- [📦 Установка и настройка](docs/getting-started/INSTALLATION.md)
- [⚙️ Конфигурация системы](docs/getting-started/CONFIGURATION.md)
- [🏃 Быстрый запуск](docs/getting-started/QUICK_START.md)

### 🛠️ **Практические руководства**
- [📊 Инте��рация анализа стакана](docs/guides/ORDERBOOK_INTEGRATION.md)
- [🔍 Мониторинг BUY ордеров](docs/guides/BUY_ORDER_MONITOR.md)

### 🏗️ **Архитектура и разработка**
- [🏗️ Архитектура проекта](docs/architecture/PROJECT_OVERVIEW.md)
- [📋 Обзор модулей](docs/architecture/MODULE_OVERVIEW.md)
- [📂 Структура файлов](docs/architecture/FILE_STRUCTURE.md)

### 🔧 **API и интеграция**
- [🔧 Справочник API](docs/api/API_REFERENCE.md)
- [🏪 Интеграция с биржами](docs/api/EXCHANGE_INTEGRATION.md)

### 📋 **Разработка**
- [📋 Руководства по реализации](docs/development/IMPLEMENTATION_GUIDES.md)
- [📊 Управление проектом](docs/development/project_management/)

### 📦 **Релизы**
- [📝 История изменений](docs/releases/CHANGELOG.md)
- [🗺️ Дорожная карта](docs/releases/ROADMAP.md)
- [📦 Заметки о релизах](docs/releases/release-notes/)

### 🛠️ **Помощь**
- [🔧 Устранение неполадок](docs/troubleshooting/TROUBLESHOOTING.md)
- [❓ Часто задаваемые вопросы](docs/troubleshooting/FAQ.md)

### ���️ **Технические спецификации**
**Язык**: Python 3.10
**Основные зависимости**: `requirements.txt`

- **Архитектура**: Clean Architecture / DDD
- **Конкурентность**: на базе asyncio

### 🔗 **Полезные ссылки**
- **Биржа**: Binance API
- **Технический анализ**: TA-Lib
- **WebSocket**: ccxt.pro
- **Синхронизация времени**: Binance Time API

## 🌿 Стратегия ветвления
AutoTrade теперь следует рабочему процессу **GitFlow**:
- `main` – готовый к продакшену код
- `stage` – предпродакшн тестирование
- `dev` – интеграционная ветка для новых фич
- `feature/*` – новая функциональность на основе `dev`
- `release/*` – подготовка релиза на основе `stage`
- `hotfix/*` – срочные исправления на основе `main`

```
feature/*   -> dev
dev         -> stage
stage       -> release/*
release/*   -> main + dev
hotfix/*    -> main + dev
```

### 🔖 Версионирование
Релизы создаются автоматически при п��ше в `main`. Рабочий процесс анализирует коммиты
и увеличивает **мажорную**, **минорную** или **патч** версию соответственно, тегируя репозиторий
`vX.Y.Z` и генерируя заметки о релизе.

---

## ✨ Ключевые возможности

### 🧠 Интеллектуальная торговля
- **Технический анализ `MACD`** с анализом гистограммы
- **Анализ биржевого стакана (`OrderBook Intelligence`)** - спред, ликвидность, поддержка/сопротивление
- **Умные модификации ордеров (`Smart Order Modifications`)** - корректировка цен на основе технических уровней  
- **Оценка уверенности сигнала (`Signal Confidence Scoring`)** - система скоринга сигналов

### ⚡ Производительность и надежность
- **Асинхронная архитектура** на базе `asyncio` для максимальной скорости
- **Интеграция `WebSocket`** через `ccxt.pro` для real-time данных
- **Мониторинг производительности (`Performance Monitoring`)** с детальными метриками
- **Сохранение состояния (`JSON-based Persistence`)** на основе JSON.

### 🛡️ Системы безопасности  
- **`Smart StopLossMonitor`** - трёхуровневая защита от убытков с анализом стакана.
- **`SignalCooldownManager`** - защита от переторговки.
- **`Enhanced BuyOrderMonitor`** - синхронизация виртуальных `SELL` ордеров при пересоздании.
- **Валидация по стакану (`OrderBook Validation`)** - отклонение сделок при плохой ликвидности.
- **Конфигурация через окружение (`Environment-based`)** с помощью `.env` файлов.

### 📊 Аналитика и мониторинг
- **`MarketAnalysisService`** - анализ волатильности и трендов
- **Логирование производительности (`Real-time Performance Logging`)** в реальном времени 
- **Торговые рекомендации (`Trading Recommendations`)** на основе рыночных условий
- **Мониторинг состояния стакана (`OrderBook Health Monitoring`)**

---

## 🏗️ Архитектура

### 📐 Структура на основе Domain-Driven Design (Реальная структура проекта)

```
new_autotrade/
├── src/                       # 🎯 Основной исходный код
│   ├── domain/                # 🧠 Бизнес-логика
│   │   ├── entities/          # Ключевые бизнес-сущности
│   │   │   ├── deal.py       # Торговые сделки
│   │   │   ├── order.py      # Биржевые ордера  
│   │   │   ├── currency_pair.py # Торговые пары
│   │   │   └── ticker.py     # Рыночные тикеры
│   │   ├── factories/         # Создание объектов
│   │   │   ├── deal_factory.py
│   │   │   └── order_factory.py
│   │   └── services/          # Бизнес-сервисы
│   │       ├── deals/
│   │       │   ├── deal_service.py           # Управление сделками
│   │       │   └── deal_completion_monitor.py # 🆕 Завершение сделок
│   │       ├── orders/
│   │       │   ├── order_service.py          # Уп��авление ордерами
│   │       │   ├── order_execution_service.py # Исполнение ордеров
│   │       │   ├── buy_order_monitor.py      # 🔄 Улучшенный мониторинг
│   │       │   └── filled_buy_order_handler.py # 🆕 Обработчик BUY ордеров
│   │       ├── market_data/
│   │       │   ├── ticker_service.py         # Рыночные данные
│   │       │   ├── orderbook_analyzer.py     # Анализ стакана
│   │       │   ├── orderbook_service.py      # Мониторинг стакана
│   │       │   └── market_analysis_service.py # Анализ рынка
│   │       ├── trading/
│   │       │   ├── trading_service.py        # Основная логика торговли
│   │       │   ├── trading_decision_engine.py # Механизм принятия решений
│   │       │   └── signal_cooldown_manager.py # Система защиты
│   │       ├── risk/
│   │       │   └── stop_loss_monitor.py      # 🆕 Умный стоп-лосс
│   │       ├── indicators/
│   │       │   └── cached_indicator_service.py # Оптимизаци�� производительности
│   │       └── utils/
│   │           ├── decimal_rounding_service.py # 🆕 Точное округление
│   │           └── orderbook_cache.py         # 🆕 Кеширование стакана
│   │
│   ├── application/           # 🚀 Сценарии использования  
│   │   ├── use_cases/
│   │   │   └── run_realtime_trading.py # Торговля в реальном времени
│   │   └── utils/
│   │       └── performance_logger.py   # Логирование производительности
│   │
│   ├── infrastructure/        # 🔌 Внешние интеграции
│   │   ├── repositories/      # Хранение данных (на основе JSON)
│   │   │   ├── deals_repository.py
│   │   │   ├── orders_repository.py
│   │   │   └── tickers_repository.py
│   │   └── connectors/        # Внешние сервисы
│   │       └── exchange_connector.py   # API биржи
│   │
│   └── config/
│       ├── config.json        # Основная конфигурация
│       └── config_loader.py   # Загрузчик конфигурации
│
├── binance_keys/              # 🔐 Хранилище API ключей
├── project_management/        # Документация и задачи
├── tests/                     # 🧪 Наборы тестов
├── .env.example              # Шаблон переменных окружения
├── main.py                   # 🎯 Точка входа в приложение
└── *.md                      # Документация
```

### 🎨 Схема архитектуры

[schema-app.puml](schema-app.puml)

<details>
  <summary>📐 Схема Plant UML</summary>

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

## 🚀 Быстрый старт

### 📦 Установка

```bash
# Клонировать репозиторий
git clone <repository-url>
cd new_autotrade

# Установить зависимости
pip install -r requirements.txt

# Настроить API ключи
# Создайте `.env` из `.env.example` и добавьте ваши API ключи
```

### ⚙️ Конфигурация

Конфигурация загружается из `config/config.json` и может быть переопределена созданием файла `.env` в корне проекта. Смотрите `.env.example` для необходимых переменны��.

### 🎯 Запуск торговли

```bash
# Запустить торговую систему
python main.py
```

---

## 📊 Производительность

### 📈 **Метрики в реальном времени**
- **Обработка тика**: < 1ms в нормальных условиях
- **Задержка WebSocket**: минимальная задержка данных  
- **Эффективность памяти**: оптимизированное хранение истории
- **Оптимизация CPU**: эффективные вычисления индикаторов

### 🎯 **Торговая статистика**
- **Точность сигнала**: улучшена благодаря анализу стакана
- **Контроль проскальзывания**: автоматическая валидация ликвидности
- **Управление рисками**: многоуровневая система защиты

### 📊 **Компоненты системы**
- **~500+ строк** основного торгового кода
- **11+ доменных сервисов** для разных аспектов торговли
- **4 типа анализа**: MACD, волатильность, тренды, стак��н
- **3 уровня защиты**: "остывание", лимиты, валидация ликвидности

---

## 🔧 Конфигурация

### 🎛️ **Настройки анализа стакана**

| Параметр | Описание | По умолчанию |
|-----------|-------------|---------|
| `min_volume_threshold` | Минимальный объем для анализа | 1000 |
| `big_wall_threshold` | Порог для определения "стенки" | 5000 |
| `max_spread_percent` | Максимально допустимый спред | 0.3% |
| `min_liquidity_depth` | Минимальная глубина ликвидности | 15 |
| `typical_order_size` | Типичный размер ордера | 10 USDT |
| `monitoring_interval` | Интервал мониторинга | 0.1 сек |

### 🛡️ **Настройки защиты**

| Параметр | Описание | По умолчанию |
|-----------|-------------|---------|
| `enable_orderbook_validation` | Включить валидацию по стакану | true |
| `orderbook_confidence_threshold` | Порог уверенности | 0.6 |
| `require_orderbook_support` | Требовать поддержку от стакана | false |
| `log_orderbook_analysis` | Л��гировать анализ стакана | true |

---

## 📈 Торговый процесс

Система работает по асинхронной, событийно-ориентированной модели, что делает ее надежной и быстрой. Жизненный цикл сделки разделен на несколько независимых этапов, управляемых разными сервисами.

### 🔄 **Асинхронный жизненный цикл сделки (v2.4.0)**

**Революционное изменение**: Отказ от одновременного размещения `BUY` и `SELL` ордеров в пользу поэтапного исполнения.

1.  **Сигнал и Валидация**:
    -   `TickerService` анализирует график и генерирует первичный сигнал `BUY` по индикатору MACD.
    -   `OrderBookAnalyzer` немедленно проверяет сигнал по стакану. Если ликвидность низкая или дисбаланс объемов негативный, сигнал отклоняется.

2.  **Инициация Сделки**:
    -   Если сигнал подтвержден, `OrderExecutionService` с��здает `Deal` (сделку).
    -   На биржу отправляется **только `BUY` ордер**.
    -   `SELL` ордер создается "виртуально" (в памяти, со статусом `PENDING`) и ждет своего часа.

3.  **Мониторинг и Адаптация (параллельные процессы)**:
    -   **`BuyOrderMonitor`**: Если `BUY` ордер "застрял" (цена ушла), этот сервис отменит его, создаст новый по актуальной цене и, что важно, **обновит** параметры "виртуального" `SELL` ордера в локальной памяти.
    -   **`FilledBuyOrderHandler`** (🆕): Как только `BUY` ордер исполняется, этот сервис "замечает" это и **отправляет на биржу** связанный с ним `SELL` ордер.

4.  **Завершение Сделки**:
    -   **`DealCompletionMonitor`** (🆕): Этот сервис отслеживает общее состояние сделок. Когда и `BUY`, и `SELL` ордера исполнены (`FILLED`), он закрывает сделку, меняя ее статус на `CLOSED`.

5.  **Защита от потерь**:
    -   **`StopLossMonitor`** (🆕): Трёхуровневая система защиты с анализом стакана перед принятием решений о закрытии убыточных позиций.

Эта архитектура гарантирует, что система не "забывает" про сделки и гибко адаптируется к рыночным изменениям, при этом обеспечивая максимальную безопасность.

### ✅ **Пример успешного сигнала**
```
🟢🔥 MACD СИГНАЛ ПОКУПКИ → 📊 АНАЛИЗ СТАКАНА: OK → 🚀 OrderExecutionService:
   - Создана сделка #123
   - На биржу отправлен BUY ордер #BUY-A
   - В памяти создан PENDING SELL ордер #SELL-A
```

### ❌ **Пример отклоненного сигнала**
```
🟢🔥 MACD СИГНАЛ ПОКУПКИ → 📊 АНАЛИЗ СТАКАНА: ОТКЛОНЕНО (слабый спрос) → 🚫 Сделка отменена
```

---

## 🛡️ Системы безопасности

### 🔒 **Механизмы защиты**
- **`SignalCooldownManager`** - предотвращение переторговки.
- **Лимит�� позиций** - ограничение количества активных сделок.
- **Валидация по стакану** - проверка качества стакана.
- **Мониторинг "тухлых" ордеров** - отмена "застрявших" ордеров для предотвращения потерь.

### ⚠️ **Управление рисками**
- **Мониторинг "тухлых" ордеров** - отмена "застрявших" ордеров по времени и отклонению цены.
- **Экстренное отключение** - возможность экстренно остановить всю торговлю и отменить ордера.
- **Проверка отклонения цены** - часть мониторинга "протухших" ордеров.
- **Размер позиции** - адаптивный размер позиций.
- **Анализ рынка** - анализ рыночных условий.

### 🔐 **Функции безопасности**
- **Раздельные API ключи** для песочницы и продакшена.
- **Конфигурация через окружение** - безопасное управление ключами через перемен��ые окружения.
- **Хранение приватных ключей** в отдельной папке `binance_keys/`.

---

## 📋 План развития

### ✅ **Фаза 1 и 2: Основа и ядро логики (Завершено)**
- [x] **Асинхронная архитектура**
- [x] **Безопасная конфигурация** (через .env)
- [x] **Реализация торговой логики** (размещение ордеров)
- [x] **Управление рисками** (мониторинг ордеров, "остывание")
- [x] **Сохранение данных** (через JSON)

### 🚀 **Фаза 3: Готовность к продакшену (Следующие шаги)**
- [ ] **Продвинутая обработка ошибок** (переподключение, повторные попытки)
- [ ] **Мониторинг и оповещения** (проверки состояния, Telegram)
- [ ] **Комплексное тестирование** (модульное, интеграционное, бэктесты)
- [ ] **Управление состоянием** (восстановление состояния при перезапуске)

### ✨ **Фаза 4: Продвинутые возможности (��удущее)**
- [ ] **Торговля несколькими парами**
- [ ] **ML-прогнозирование**
- [ ] **REST API** для управления ботом

---

## 🎯 Обзор задач


### 🔥 **Критические задачи** (Обязательно для v3.0.0)

🏗️ **M1** | ✅ **ЗАВЕРШЕНО** - [Issue #20](https://github.com/sni10/new_autotrade/issues/20) - Главный дирижер - разделить монолитную логику `run_realtime_trading.py` на управляемые компоненты

🏗️ **M1** | ✅ **ЗАВЕРШЕНО** - [Issue #19](https://github.com/sni10/new_autotrade/issues/19) - Реальное выставление ордеров - бот фактически торгует и зарабатывает деньги

🏗️ **M2** | ✅ **ЗАВЕРШЕНО** - [Issue #6](https://github.com/sni10/new_autotrade/issues/6) - Система хранения данных - данные не теряются при перезапуске

### ⚡ **Высокоприоритетные задачи** (Важно для стабильности)

🏗️ **M1** | ✅ **ЗАВЕРШЕНО** - [Issue #18](https://github.com/sni10/new_autotrade/issues/18) - Управление рисками - защита от потери средств через stop-loss и лимиты

🏗️ **M2** | [ ] [Issue #16](https://github.com/sni10/new_autotrade/issues/16) - Управление состоянием - "грациозный" перезапуск без потери контекста

🏗️ **M2** | ✅ **ЗАВЕРШЕНО** - [Issue #15](https://github.com/sni10/new_autotrade/issues/15) - Управление конфигурацией - соответствие стандартам безопасности и удобство настройки

🏗️ **M3** | [ ] [Issue #14](https://github.com/sni10/new_autotrade/issues/14) - Обработка ошибок - устойчивость к сбоям и автовосстановление

🏗️ **M3** | [ ] [Issue #13](https://github.com/sni10/new_autotrade/issues/13) - Безопасность - шифрование чувствительных данных и защита от атак

### 📈 **Среднеприоритетные задачи** (Желательные улучшения)

🏗️ **M1** | ✅ **ЗАВЕРШЕНО** - [Issue #8](https://github.com/sni10/new_autotrade/issues/8) - Улучшенный анализ рынка - лучшие торговые решения

🏗️ **M1** | ✅ **ЗАВЕРШЕНО** - [Issue #7](https://github.com/sni10/new_autotrade/issues/7) - Агрегация сигналов - меньше ложных сигналов

🏗️ **M3** | [ ] [Issue #21](https://github.com/sni10/new_autotrade/issues/21) - Мониторинг системы - проактивное об��аружение проблем

🏗️ **M4** | [ ] [Issue #12](https://github.com/sni10/new_autotrade/issues/12) - Оптимизация производительности - < 1ms обработка тика в 95% случаев

### 🎯 **Низкоприоритетные задачи** (Будущие возможности)

🏗️ **M2** | ✅ **ЗАВЕРШЕНО** - [Issue #6](https://github.com/sni10/new_autotrade/issues/6) - Улучшенные репозитории - быстрые операции с данными

🏗️ **M3** | [ ] [Issue #5](https://github.com/sni10/new_autotrade/issues/5) - Резервное копирование - защита от потери данных

🏗️ **M4** | [ ] [Issue #11](https://github.com/sni10/new_autotrade/issues/11) - Мультивалютная торговля - масштабирование на множественные активы



---

## 🚀 Развертывание

### 📦 **Реальная структура файлов**
```
new_autotrade/
├── main.py              # Начать здесь
├── config/config.json   # Основная конфигурация
├── .env.example         # Переопределения окружения
├── binance_keys/        # Ваши API кл��чи здесь
├── domain/              # Основная бизнес-логика
├── application/         # Сценарии использования и утилиты
├── infrastructure/      # Внешние интеграции
├── project_management/  # Документация и задачи
└── *.md                # Документация
```

### 🎯 **Начало работы**
1. **Настройте API ключи** в `binance_keys/`
2. **Создайте `.env`** на основе `.env.example` для переопределения настроек
3. **Запустите** `python main.py`
4. **Отслеживайте** логи для мониторинга торговой активности

---

## 💎 Заключение

**AutoTrade v2.3.0** представляет собой профессиональную торговую систему с интеллектуальным анализом рынка. Интеграция анализа биржевого ��такана в сочетании с индикаторами MACD создает мощный инструмент для автоматической торговли.

**Ключевые преимущества:**
- ✅ **��мные решения** на основе анал��за ликвидности
- ✅ **Высокая производительность** благодаря асинхронной архитектуре  
- ✅ **Надежная защита** от переторговки и плохих сигналов
- ✅ **Гибкая конфигурация** под разные торговые стратегии

> *"Торгуйте умнее, а не больше"* 🎯

---

**Разработчик**: Dmitry Strelets (sni10)  
**Репозиторий**: `velostour/new_autotrade`  
**Лицензия**: Private
```

## 🐍 Python файлы

### 📄 `22.py`

```python
#!/usr/bin/env python3
"""
AutoTrade Code Collector
Собирает весь код проекта (кроме тестов) в один markdown файл
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set


class CodeCollector:
    """Класс для сборки всего кода проекта в единый markdown файл"""

    def __init__(self, project_path: str, output_file: str = None):
        self.project_path = Path(project_path)
        self.output_file = output_file or f"autotrade_complete_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        # Расширения файлов для включения
        self.include_extensions = {
            '.py', '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini',
            '.txt', '.md', '.rst', '.requirements'
        }

        # Папки и файлы для исключения
        self.exclude_dirs = {
            '__pycache__', '.git', '.gitignore', 'venv', 'env', '.env',
            'node_modules', '.pytest_cache', '.mypy_cache', '.tox',
            'build', 'dist', '*.egg-info', '.idea', '.vscode',
            'test', 'tests', 'testing',  # Исключаем тесты
            'docker', 'Docker', 'dockerfile', 'Dockerfile',  # Docker
            'docs', 'documentation', 'doc',  # Документация
            'assets', 'static', 'media', 'images', 'img',  # Медиа
            'logs', 'log', 'tmp', 'temp', 'cache',  # Временные
            'backup', 'backups', 'old', 'archive',  # Бэкапы
            'vendor', 'lib', 'libs', 'external',  # Внешние либы
            'migrations', 'seeds', 'fixtures',  # БД файлы
            'coverage', 'htmlcov', '.coverage',  # Покрытие кода
            'scripts', 'tools', 'utils', 'bin',  # Утилиты
            'config', 'configs', 'settings',  # Конфиги (отдельно обработаем)
            'project_management', 'pm', 'roadmap'  # Управление проектом
        }

        self.exclude_files = {
            '.gitignore', '.dockerignore', '.DS_Store', 'Thumbs.db',
            '*.pyc', '*.pyo', '*.pyd', '__pycache__', '*.so',
            '*.log', '*.tmp', '*.temp', '*.swp', '*.swo'
        }

        # Конфиденциальные файлы (показываем структуру, но не содержимое)
        self.sensitive_files = {
            'config.json', 'secrets.json', 'credentials.json',
            '.env', '.env.local', '.env.production',
            'id_ed25519.pem', 'test-prv-key.pem'
        }

        # Статистика
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'skipped_files': 0,
            'total_lines': 0,
            'total_size': 0
        }

    def should_exclude_dir(self, dir_name: str) -> bool:
        """Проверяет, нужно ли исключить директорию"""
        dir_lower = dir_name.lower()

        # Проверяем точные совпадения
        if dir_lower in self.exclude_dirs:
            return True

        # Проверяем частичные совпадения для тестов
        test_keywords = ['test', 'testing', 'spec', 'specs']
        if any(keyword in dir_lower for keyword in test_keywords):
            return True

        # Скрытые папки (начинающиеся с точки)
        if dir_name.startswith('.') and dir_name not in {'.github', '.gitlab'}:
            return True

        return False

    def should_exclude_file(self, file_path: Path) -> bool:
        """Проверяет, нужно ли исключить файл"""
        file_name = file_path.name.lower()

        # Проверяем расширение
        if file_path.suffix not in self.include_extensions:
            return True

        # Проверяем имя файла
        if any(pattern in file_name for pattern in self.exclude_files):
            return True

        # Проверяем на тестовые файлы
        test_keywords = ['test_', '_test', 'test.py', 'tests.py', 'spec_', '_spec']
        if any(keyword in file_name for keyword in test_keywords):
            return True

        return False

    def is_sensitive_file(self, file_path: Path) -> bool:
        """Проверяет, является ли файл конфиденциальным"""
        return file_path.name in self.sensitive_files

    def get_file_tree(self) -> List[str]:
        """Генерирует дерево файлов проекта"""
        tree_lines = []

        def add_tree_node(path: Path, prefix: str = "", is_last: bool = True):
            if self.should_exclude_dir(path.name) and path.is_dir():
                return

            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{path.name}")

            if path.is_dir():
                try:
                    children = sorted([p for p in path.iterdir()
                                       if not self.should_exclude_dir(p.name) or not p.is_dir()])
                    for i, child in enumerate(children):
                        child_is_last = i == len(children) - 1
                        extension = "    " if is_last else "│   "
                        add_tree_node(child, prefix + extension, child_is_last)
                except PermissionError:
                    pass

        tree_lines.append(f"📁 {self.project_path.name}/")
        try:
            children = sorted([p for p in self.project_path.iterdir()
                               if not self.should_exclude_dir(p.name) or not p.is_dir()])
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                add_tree_node(child, "", is_last)
        except PermissionError:
            tree_lines.append("❌ Нет доступа к директории")

        return tree_lines

    def collect_files(self) -> Dict[str, List[Path]]:
        """Собирает все файлы проекта, группируя по типам"""
        files_by_type = {}

        def scan_directory(directory: Path):
            try:
                for item in directory.iterdir():
                    if item.is_dir():
                        if not self.should_exclude_dir(item.name):
                            scan_directory(item)
                    elif item.is_file():
                        self.stats['total_files'] += 1

                        if not self.should_exclude_file(item):
                            # Группируем по расширению
                            ext = item.suffix or 'no_extension'
                            if ext not in files_by_type:
                                files_by_type[ext] = []
                            files_by_type[ext].append(item)
                            self.stats['processed_files'] += 1
                        else:
                            self.stats['skipped_files'] += 1
            except PermissionError:
                print(f"⚠️  Нет доступа к директории: {directory}")

        scan_directory(self.project_path)
        return files_by_type

    def read_file_safely(self, file_path: Path) -> str:
        """Безопасно читает файл с обработкой различных кодировок"""
        encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    self.stats['total_lines'] += len(content.splitlines())
                    self.stats['total_size'] += len(content.encode('utf-8'))
                    return content
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                return f"❌ Ошибка чтения файла: {e}"

        return "❌ Не удалось декодировать файл с поддерживаемыми кодировками"

    def generate_markdown(self, files_by_type: Dict[str, List[Path]]) -> str:
        """Генерирует markdown файл с кодом"""
        md_content = []

        # Заголовок
        md_content.extend([
            f"# 🤖 AutoTrade - Полный код проекта",
            f"",
            f"**Сгенерировано:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Проект:** {self.project_path}  ",
            f"**Файлов обработано:** {self.stats['processed_files']} из {self.stats['total_files']}  ",
            f"**Общий размер:** {self.stats['total_size']:,} байт  ",
            f"**Строк кода:** {self.stats['total_lines']:,}  ",
            f"",
            "---",
            ""
        ])

        # Оглавление
        md_content.extend([
            "## 📑 Оглавление",
            "",
            "- [🌳 Структура проекта](#-структура-проекта)",
            "- [📊 Статистика файлов](#-статистика-файлов)"
        ])

        # Добавляем ссылки на секции
        for ext in sorted(files_by_type.keys()):
            if ext == '.py':
                md_content.append("- [🐍 Python файлы](#-python-файлы)")
            elif ext == '.json':
                md_content.append("- [⚙️ JSON конфигурации](#️-json-конфигурации)")
            elif ext in ['.md', '.rst']:
                md_content.append("- [📝 Документация](#-документация)")
            else:
                section_name = f"{ext.upper()[1:]} файлы" if ext.startswith('.') else f"{ext} файлы"
                anchor = section_name.lower().replace(' ', '-').replace('.', '')
                md_content.append(f"- [📄 {section_name}](#{anchor})")

        md_content.extend(["", "---", ""])

        # Структура проекта
        md_content.extend([
            "## 🌳 Структура проекта",
            "",
            "```",
            *self.get_file_tree(),
            "```",
            ""
        ])

        # Статистика
        md_content.extend([
            "## 📊 Статистика файлов",
            "",
            f"| Метрика | Значение |",
            f"|---------|----------|",
            f"| Всего файлов найдено | {self.stats['total_files']} |",
            f"| Обработано файлов | {self.stats['processed_files']} |",
            f"| Пропущено файлов | {self.stats['skipped_files']} |",
            f"| Общее количество строк | {self.stats['total_lines']:,} |",
            f"| Общий размер (байт) | {self.stats['total_size']:,} |",
            ""
        ])

        # Группировка файлов по типам
        type_stats = {}
        for ext, files in files_by_type.items():
            type_stats[ext] = len(files)

        if type_stats:
            md_content.extend([
                "### Распределение по типам файлов:",
                "",
                "| Тип | Количество |",
                "|-----|------------|"
            ])

            for ext in sorted(type_stats.keys()):
                ext_name = ext if ext != 'no_extension' else 'без расширения'
                md_content.append(f"| {ext_name} | {type_stats[ext]} |")

            md_content.append("")

        # Содержимое файлов по типам
        for ext in sorted(files_by_type.keys()):
            files = sorted(files_by_type[ext], key=lambda x: x.relative_to(self.project_path))

            # Определяем заголовок секции
            if ext == '.py':
                section_title = "🐍 Python файлы"
                lang = "python"
            elif ext == '.json':
                section_title = "⚙️ JSON конфигурации"
                lang = "json"
            elif ext in ['.yaml', '.yml']:
                section_title = "📋 YAML файлы"
                lang = "yaml"
            elif ext == '.md':
                section_title = "📝 Markdown документация"
                lang = "markdown"
            elif ext == '.rst':
                section_title = "📝 RestructuredText документация"
                lang = "rst"
            elif ext == '.toml':
                section_title = "⚙️ TOML конфигурации"
                lang = "toml"
            else:
                section_title = f"📄 {ext.upper()[1:]} файлы" if ext.startswith('.') else f"📄 {ext} файлы"
                lang = "text"

            md_content.extend([
                f"## {section_title}",
                ""
            ])

            for file_path in files:
                relative_path = file_path.relative_to(self.project_path)

                md_content.extend([
                    f"### 📄 `{relative_path}`",
                    ""
                ])

                # Проверяем, конфиденциальный ли файл
                if self.is_sensitive_file(file_path):
                    md_content.extend([
                        "```text",
                        "🔒 КОНФИДЕНЦИАЛЬНЫЙ ФАЙЛ - СОДЕРЖИМОЕ СКРЫТО",
                        f"Размер файла: {file_path.stat().st_size} байт",
                        f"Последнее изменение: {datetime.fromtimestamp(file_path.stat().st_mtime)}",
                        "```",
                        ""
                    ])
                else:
                    content = self.read_file_safely(file_path)

                    md_content.extend([
                        f"```{lang}",
                        content,
                        "```",
                        ""
                    ])

        return "\n".join(md_content)

    def run(self) -> bool:
        """Запускает процесс сборки"""
        print(f"🚀 Начинаем сборку кода проекта: {self.project_path}")

        if not self.project_path.exists():
            print(f"❌ Проект не найден: {self.project_path}")
            return False

        print("📁 Сканируем файлы...")
        files_by_type = self.collect_files()

        if not files_by_type:
            print("❌ Не найдено файлов для обработки")
            return False

        print(f"📝 Генерируем markdown файл: {self.output_file}")
        markdown_content = self.generate_markdown(files_by_type)

        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"✅ Успешно создан файл: {self.output_file}")
            print(f"📊 Статистика:")
            print(f"   - Обработано файлов: {self.stats['processed_files']}")
            print(f"   - Пропущено файлов: {self.stats['skipped_files']}")
            print(f"   - Строк кода: {self.stats['total_lines']:,}")
            print(f"   - Размер: {self.stats['total_size']:,} байт")

            return True

        except Exception as e:
            print(f"❌ Ошибка при записи файла: {e}")
            return False


def main():
    """Главная функция"""
    # Захардкоженный путь к проекту
    project_path = r"F:\HOME\new_autotrade"
    output_file = r"F:\HOME\new_autotrade\src\autotrade_complete_code.md"

    print(f"🎯 Собираем код проекта: {project_path}")
    print(f"📝 Выходной файл: {output_file}")

    collector = CodeCollector(project_path, output_file)

    success = collector.run()

    if success:
        print(f"\n🎉 ГОТОВО! Файл создан: {output_file}")
    else:
        print(f"\n💥 ОШИБКА! Не удалось создать файл")

    input("\nНажмите Enter для выхода...")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
```

### 📄 `main.py`

```python
# main.py - Полностью исправленная версия с особым запуском для Windows
import asyncio
import sys
import os
import logging
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv

# --- Условная настройка для Windows ---
# Этот блок должен быть в самом верху, до любых вызовов asyncio
if sys.platform == "win32":
    # Устанавливаем политику цикла событий ДО его создания
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        import win32api
    except ImportError:
        win32api = None
        print("ПРЕДУПРЕЖДЕНИЕ: Модуль 'pywin32' не найден. Синхронизация времени будет пропущена.")
else:
    win32api = None

# --- Основные импорты проекта ---
# Добавляем src в sys.path ПЕРЕД всеми импортами из проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from domain.entities.currency_pair import CurrencyPair
from domain.services.deals.deal_service import DealService
from domain.services.orders.order_service import OrderService
from domain.services.orders.order_execution_service import OrderExecutionService
from domain.services.orders.buy_order_monitor import BuyOrderMonitor
from domain.factories.order_factory import OrderFactory
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from config.config_loader import load_config
from application.use_cases.run_realtime_trading import run_realtime_trading
from domain.services.risk.stop_loss_monitor import StopLossMonitor
from domain.services.deals.deal_completion_monitor import DealCompletionMonitor
from domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Имя файла лога с временной меткой
log_filename = f"autotrade_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
log_filepath = os.path.join(log_dir, log_filename)

# Создаем обработчики с явным указанием кодировки UTF-8
file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
stream_handler = logging.StreamHandler(sys.stdout) # Используем sys.stdout для лучшей совместимости

# Устанавливаем форматтер для обоих обработчиков
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Настраиваем корневой логгер
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        stream_handler
    ]
)
logger = logging.getLogger(__name__)

def time_sync_windows():
    """Синхронизация времени с серверами Binance для Windows."""
    if not win32api:
        return
    try:
        logger.info("Попытка синхронизации времени для Windows...")
        response = requests.get('https://api.binance.com/api/v3/time')
        server_time = response.json()['serverTime']
        utc_dt = datetime.fromtimestamp(server_time / 1000, tz=pytz.utc)
        day_of_week = (utc_dt.weekday() + 1) % 7
        win32api.SetSystemTime(utc_dt.year, utc_dt.month, day_of_week, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second, int(utc_dt.microsecond / 1000))
        logger.info(f"⏰ Время успешно синхронизировано: {utc_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось синхронизировать время: {e}")

async def main():
    """🚀 ГЛАВНАЯ функция с интеграцией OrderExecutionService и мониторинга"""
    if sys.platform == "win32":
        time_sync_windows()

    config = load_config()
    pair_cfg = config.get("currency_pair", {})
    base_currency = pair_cfg.get("base_currency", "ETH")
    quote_currency = pair_cfg.get("quote_currency", "USDT")
    symbol_ccxt = f"{base_currency}{quote_currency}"
    symbol_display = f"{base_currency}/{quote_currency}"

    logger.info(f"🚀 ЗАПУСК AutoTrade v2.3.0 для {symbol_display}")
    
    buy_order_monitor = None
    stop_loss_monitor = None
    pro_exchange_connector_prod = None
    pro_exchange_connector_sandbox = None

    try:
        # 1. Инициализация коннекторов
        pro_exchange_connector_prod = CcxtExchangeConnector(use_sandbox=False)
        pro_exchange_connector_sandbox = CcxtExchangeConnector(use_sandbox=True)
        logger.info("✅ Коннекторы инициализированы (Production, Sandbox)")

        # 2. Инициализация репозиториев
        deals_repo = InMemoryDealsRepository()
        orders_repo = InMemoryOrdersRepository(max_orders=50000)
        logger.info("✅ Репозитории созданы (InMemory)")

        # 3. Инициализация фабрик
        order_factory = OrderFactory()
        symbol_info = await pro_exchange_connector_prod.get_symbol_info(symbol_ccxt)
        order_factory.update_exchange_info(symbol_ccxt, symbol_info)
        deal_factory = DealFactory(order_factory)
        logger.info(f"✅ Фабрики созданы, Exchange info для {symbol_ccxt} загружена")

        # 4. Инициализация сервисов
        order_service = OrderService(orders_repo, order_factory, pro_exchange_connector_sandbox, currency_pair_symbol=symbol_ccxt)
        deal_service = DealService(deals_repo, order_service, deal_factory, pro_exchange_connector_sandbox)
        order_execution_service = OrderExecutionService(order_service, deal_service, pro_exchange_connector_sandbox)
        orderbook_analyzer = OrderBookAnalyzer(config.get("orderbook_analyzer", {}))
        logger.info("✅ Основные сервисы созданы")

        # 5. Инициализация мониторинга
        buy_order_monitor_cfg = config.get("buy_order_monitor", {})
        buy_order_monitor = BuyOrderMonitor(
            order_service=order_service,
            deal_service=deal_service,
            exchange_connector=pro_exchange_connector_sandbox,
            max_age_minutes=buy_order_monitor_cfg.get("max_age_minutes", 15.0),
            max_price_deviation_percent=buy_order_monitor_cfg.get("max_price_deviation_percent", 3.0),
            check_interval_seconds=buy_order_monitor_cfg.get("check_interval_seconds", 60)
        )
        asyncio.create_task(buy_order_monitor.start_monitoring())
        logger.info("✅ BuyOrderMonitor запущен")

        # 5.2. Запуск мониторинга завершения сделок
        deal_completion_monitor = DealCompletionMonitor(
            deal_service=deal_service,
            order_service=order_service,
            check_interval_seconds=30  # Проверка каждые 30 секунд
        )
        asyncio.create_task(deal_completion_monitor.start_monitoring())
        logger.info("✅ DealCompletionMonitor запущен")

        risk_config = config.get("risk_management", {})
        if risk_config.get("enable_stop_loss", False):
            # Получаем настройки умного стоп-лосса
            smart_config = risk_config.get("smart_stop_loss", {})
            
            stop_loss_monitor = StopLossMonitor(
                deal_service=deal_service,
                order_execution_service=order_execution_service,
                exchange_connector=pro_exchange_connector_sandbox,
                orderbook_analyzer=orderbook_analyzer,  # Добавляем анализатор стакана
                stop_loss_percent=risk_config.get("stop_loss_percent", 2.0),
                check_interval_seconds=risk_config.get("stop_loss_check_interval_seconds", 60),
                warning_percent=smart_config.get("warning_percent", 5.0),
                critical_percent=smart_config.get("critical_percent", 10.0),
                emergency_percent=smart_config.get("emergency_percent", 15.0)
            )
            asyncio.create_task(stop_loss_monitor.start_monitoring())
            logger.info("✅ StopLossMonitor запущен с умным анализом стакана")

        # 6. Проверка подключения и баланса
        if not await pro_exchange_connector_sandbox.test_connection():
            logger.error("❌ Подключение к бирже неудачно. Завершение работы...")
            return
        
        balance = await pro_exchange_connector_sandbox.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0.0)
        logger.info(f"💰 Доступный баланс в песочнице: {usdt_balance:.4f} USDT")

        # 7. Создание объекта CurrencyPair
        currency_pair = CurrencyPair(
            base_currency=base_currency,
            quote_currency=quote_currency,
            symbol=symbol_ccxt,
            deal_quota=pair_cfg.get("deal_quota", 100.0),
            deal_count=pair_cfg.get("deal_count", 1),
            profit_markup=pair_cfg.get("profit_markup", 0.005)  # 0.5%
        )
        # ЗАГРУЗКА АКТУАЛЬНЫХ ДАННЫХ С БИРЖИ
        markets = await pro_exchange_connector_prod.load_markets()
        market_details = markets.get(currency_pair.symbol)
        if market_details:
            currency_pair.update_exchange_info(market_details)
            logger.info(f"✅ Config updated with precision and limits for {currency_pair.symbol}")

        # 8. Запуск основного цикла торговли
        logger.info("="*80)
        logger.info("🚀 СИСТЕМА ГОТОВА К ЗАПУСКУ ТОРГОВЛИ")
        logger.info(f'   - Валютная пара: {symbol_display}')
        logger.info(f'   - Бюджет на сделку: {currency_pair.deal_quota} USDT')
        logger.info(f'   - Режим: Sandbox (безопасно)')
        logger.info("="*80)

        await run_realtime_trading(
            pro_exchange_connector_prod=pro_exchange_connector_prod,
            pro_exchange_connector_sandbox=pro_exchange_connector_sandbox,
            currency_pair=currency_pair,
            deal_service=deal_service,
            order_execution_service=order_execution_service,
            buy_order_monitor=buy_order_monitor, # Возвращено
            orderbook_analyzer=orderbook_analyzer,
            deal_completion_monitor=deal_completion_monitor,  # Добавлен новый параметр
            stop_loss_monitor=stop_loss_monitor if 'stop_loss_monitor' in locals() else None  # Передаем StopLossMonitor
        )

    except Exception as e:
        logger.error(f"❌ Критическая ошибка в main(): {e}", exc_info=True)
    finally:
        logger.info("🔴 Завершение работы, закрытие соединений...")
        if buy_order_monitor:
            buy_order_monitor.stop_monitoring()
        if 'deal_completion_monitor' in locals() and deal_completion_monitor:
            deal_completion_monitor.stop_monitoring()
        if 'stop_loss_monitor' in locals() and stop_loss_monitor:
            stop_loss_monitor.stop_monitoring()
        if pro_exchange_connector_prod:
            await pro_exchange_connector_prod.close()
        if pro_exchange_connector_sandbox:
            await pro_exchange_connector_sandbox.close()
        logger.info("👋 AutoTrade завершен")

# --- Специальный запуск для Windows и других систем ---
if __name__ == "__main__":
    try:
        # Этот метод запуска является более надежным в сложных окружениях,
        # таких как запуск под отладчиком в Windows.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("🛑 Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}", exc_info=True)
    finally:
        logger.info("👋 AutoTrade завершен")
```

### 📄 `order_history_viewer.py`

```python
#!/usr/bin/env python3
"""
Скрипт для просмотра истории ордеров на бирже
Показывает все ордера (открытые, исполненные, отмененные)
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Добавляем src в путь для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.config_loader import load_config
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Основная функция для просмотра ордеров"""
    
    # Выбор режима
    print("🔍 ПРОСМОТР ИСТОРИИ ОРДЕРОВ")
    print("1. Sandbox (тестовый режим)")
    print("2. Production (реальные ордера)")
    
    choice = input("Выберите режим (1 или 2): ").strip()
    use_sandbox = choice == "1"
    mode_name = "SANDBOX" if use_sandbox else "PRODUCTION"
    
    print(f"\n📊 Загружаем данные из режима: {mode_name}")
    
    # Создаем коннектор
    connector = CcxtExchangeConnector("binance", use_sandbox=use_sandbox)
    
    try:
        # Проверяем подключение
        if not await connector.test_connection():
            logger.error("❌ Не удалось подключиться к бирже")
            return
        
        print(f"✅ Подключение к Binance {mode_name} успешно")
        
        # Символ для поиска
        symbol = input("\n🎯 Введите символ (например, TURBOUSDT) или Enter для всех: ").strip().upper()
        if not symbol:
            symbol = None
        
        print("\n" + "="*80)
        print(f"📋 ИСТОРИЯ ОРДЕРОВ {f'ДЛЯ {symbol}' if symbol else '(ВСЕ СИМВОЛЫ)'}")
        print("="*80)
        
        # 1. Открытые ордера
        print("\n🟢 ОТКРЫТЫЕ ОРДЕРА:")
        print("-" * 40)
        open_orders = await connector.fetch_open_orders(symbol)
        
        if open_orders:
            for order in open_orders:
                print_order_info(order, "ОТКРЫТ")
        else:
            print("   Нет открытых ордеров")
        
        # 2. Недавние ордера (последние 100)
        print(f"\n📜 ИСТОРИЯ ОРДЕРОВ (последние):")
        print("-" * 40)
        
        try:
            # Для истории ордеров нужен конкретный символ
            if symbol:
                # Получаем закрытые ордера (за последние 7 дней по умолчанию)
                closed_orders = await connector.client.fetch_closed_orders(symbol, limit=100)
                
                if closed_orders:
                    # Сортируем по времени (новые сначала)
                    closed_orders.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                    
                    for order in closed_orders:
                        print_order_info(order, order.get('status', 'UNKNOWN'))
                else:
                    print("   Нет истории ордеров")
            else:
                print("   ⚠️ Для просмотра истории укажите конкретный символ")
        
        except Exception as e:
            logger.warning(f"Не удалось получить историю ордеров: {e}")
            print("   ⚠️ История недоступна (возможно, нужны дополнительные права)")
        
        # 3. Статистика по балансу
        print(f"\n💰 ТЕКУЩИЙ БАЛАНС:")
        print("-" * 40)
        
        balance = await connector.fetch_balance()
        
        # Показываем только ненулевые балансы
        for currency, data in balance.items():
            if currency not in ['info', 'free', 'used', 'total']:
                free_balance = data.get('free', 0)
                used_balance = data.get('used', 0)
                total_balance = data.get('total', 0)
                
                if total_balance > 0:
                    print(f"   {currency}: {total_balance:.8f} (свободно: {free_balance:.8f}, в ордерах: {used_balance:.8f})")
    
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    finally:
        await connector.close()
        print(f"\n🔌 Соединение с {mode_name} закрыто")

def print_order_info(order, status_override=None):
    """Красивый вывод информации об ордере"""
    
    # Извлекаем основные данные
    order_id = order.get('id', 'N/A')
    symbol = order.get('symbol', 'N/A')
    side = order.get('side', 'N/A').upper()
    order_type = order.get('type', 'N/A').upper()
    amount = order.get('amount', 0)
    price = order.get('price', 0)
    filled = order.get('filled', 0)
    remaining = order.get('remaining', 0)
    status = status_override or order.get('status', 'UNKNOWN').upper()
    timestamp = order.get('timestamp')
    
    # Форматируем время
    time_str = "N/A"
    if timestamp:
        try:
            dt = datetime.fromtimestamp(timestamp / 1000)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = str(timestamp)
    
    # Выбираем эмодзи для статуса
    status_emoji = {
        'ОТКРЫТ': '🟢',
        'OPEN': '🟢',
        'FILLED': '✅',
        'CANCELED': '❌',
        'CANCELLED': '❌',
        'EXPIRED': '⏰',
        'REJECTED': '🚫',
        'PARTIALLY_FILLED': '🟡'
    }.get(status, '❓')
    
    # Форматируем цены
    price_str = f"{price:.8f}" if price else "MARKET"
    filled_percent = (filled / amount * 100) if amount > 0 else 0
    
    # Выводим информацию
    print(f"   {status_emoji} ID: {order_id}")
    print(f"      📊 {symbol} | {side} {order_type} | {status}")
    print(f"      💰 Цена: {price_str} | Количество: {amount:.8f}")
    print(f"      ✅ Исполнено: {filled:.8f} ({filled_percent:.1f}%) | Остаток: {remaining:.8f}")
    print(f"      🕐 Время: {time_str}")
    
    # Дополнительная информация если есть
    cost = order.get('cost', 0)
    if cost > 0:
        print(f"      💵 Стоимость: {cost:.8f}")
    
    fee = order.get('fee')
    if fee and fee.get('cost', 0) > 0:
        print(f"      💸 Комиссия: {fee['cost']:.8f} {fee.get('currency', '')}")
    
    print()

if __name__ == "__main__":
    asyncio.run(main())
```

### 📄 `quick_swap.py`

```python
# quick_swap.py (версия 4, с исправлением для Windows)
import asyncio
import sys
import os
import logging
from decimal import Decimal

# --- Исправление для Windows ---
# Этот блок должен быть в самом верху, до любых вызовов asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Добавляем src в sys.path для доступа к модулям проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

# --- НАСТРОЙКИ ОПЕРАЦИИ ---
# ====================================================================
SIDE = "sell"  # Укажите 'buy' для покупки или 'sell' для продажи
SYMBOL = "TURBO/USDT"  # Укажите торговую пару, например 'ETH/USDT'
AMOUNT = "0"  # Количество в БАЗОВОЙ валюте. Если 0, покажет только баланс.
EXCHANGE_NAME = "binance" # Биржа (используется только секция sandbox)
# ====================================================================

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    """
    Основная функция для выполнения рыночного обмена или показа баланса.
    """
    logger.info(f"🚀 Запуск скрипта quick_swap.py")
    amount_dec = Decimal(AMOUNT)
    connector = None
    
    try:
        # --- Инициализация коннектора ---
        connector = CcxtExchangeConnector(exchange_name=EXCHANGE_NAME, use_sandbox=True)
        logger.info("✅ Коннектор к песочнице инициализирован.")

        # --- Загрузка рынков и определение валют ---
        await connector.load_markets(reload=True)
        market = connector.client.markets.get(SYMBOL)
        if not market:
            logger.error(f"❌ Символ '{SYMBOL}' не найден на бирже '{EXCHANGE_NAME}'.")
            return

        base_currency = market['base']
        quote_currency = market['quote']

        # --- Проверка и вывод баланса ---
        logger.info("🔍 Получение баланса...")
        balance = await connector.fetch_balance()
        base_balance = Decimal(str(balance.get(base_currency, {}).get('free', 0.0)))
        quote_balance = Decimal(str(balance.get(quote_currency, {}).get('free', 0.0)))

        logger.info(f"💰 Баланс: {base_balance:.8f} {base_currency}")
        logger.info(f"💰 Баланс: {quote_balance:.4f} {quote_currency}")

        # --- Если количество 0, выходим после показа баланса ---
        if amount_dec == 0:
            logger.info("🟡 Количество для обмена равно нулю. Показан только баланс.")
            return

        # --- Логика обмена (если количество > 0) ---
        logger.info(f"▶️ Подготовка к операции: {SIDE.upper()} {AMOUNT} {SYMBOL}")
        
        # Проверка достаточности средств для сделки
        if SIDE == 'sell':
            if amount_dec > base_balance:
                logger.error(f"❌ Недостаточно средств. Нужно: {amount_dec} {base_currency}, доступно: {base_balance}")
                return
        else:  # buy
            ticker = await connector.fetch_ticker(SYMBOL)
            current_price = Decimal(str(ticker['last']))
            required_quote_amount = amount_dec * current_price

            if required_quote_amount > quote_balance:
                logger.error(f"❌ Недостаточно средств. Нужно ~{required_quote_amount:.4f} {quote_currency}, доступно: {quote_balance:.4f}")
                return

        # Создание ордера
        logger.info(f"📤 Создание рыночного ({SIDE.upper()}) ордера на {amount_dec} {base_currency}...")
        order_result = await connector.create_order(
            symbol=SYMBOL,
            side=SIDE,
            order_type='market',
            amount=float(amount_dec)
        )
        
        logger.info("🎉 Ордер успешно выполнен!")
        logger.info("--- РЕЗУЛЬТАТ ---")
        logger.info(f"  ID ордера: {order_result.get('id')}")
        logger.info(f"  Статус: {order_result.get('status')}")
        logger.info(f"  Символ: {order_result.get('symbol')}")
        logger.info(f"  Сторона: {order_result.get('side')}")
        logger.info(f"  Количество: {order_result.get('filled')} {base_currency}")
        logger.info(f"  Средняя цена: {order_result.get('average')} {quote_currency}")
        logger.info(f"  Общая стоимость: {order_result.get('cost')} {quote_currency}")
        fee_info = order_result.get('fee', {})
        if fee_info and fee_info.get('cost') is not None:
                logger.info(f"  Комиссия: {fee_info.get('cost')} {fee_info.get('currency')}")
        logger.info("-----------------")

    except Exception as e:
        logger.error(f"❌ Произошла критическая ошибка: {e}", exc_info=True)
    finally:
        if connector:
            await connector.close()
            logger.info("🔌 Соединение с биржей закрыто.")

if __name__ == "__main__":
    try:
        # Используем более надежный метод запуска asyncio для совместимости с отладчиками
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("🛑 Операция прервана пользователем.")
```

### 📄 `sandbox.py`

```python
# sandbox.py (или main.py)
from domain.entities.currency_pair import CurrencyPair
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
import logging

logger = logging.getLogger(__name__)

def main():
    cp = CurrencyPair(base_currency="BTC", quote_currency="USDT")

    # Репозитории
    deals_repo = InMemoryDealsRepository()
    orders_repo = InMemoryOrdersRepository()

    # Фабрика
    deal_factory = DealFactory()

    # 1) Создаём сделку
    deal = deal_factory.create_new_deal(cp)
    logger.info("New Deal: %s", deal)

    # 2) Сохраняем сделку
    deals_repo.save(deal)
    # Также сохраним оба ордера
    if deal.buy_order:
        orders_repo.save(deal.buy_order)
    if deal.sell_order:
        orders_repo.save(deal.sell_order)

    # 3) Проверим get_all_by_deal:
    buy_and_sell = orders_repo.get_all_by_deal(deal.deal_id)
    logger.info("Orders for this deal: %s", buy_and_sell)

    # 4) Закроем сделку
    deal.close()
    deals_repo.save(deal)  # сохраним статус
    logger.info("Closed deal: %s", deal)

if __name__ == "__main__":
    main()

```

### 📄 `sandbox_analysis.py`

```python


import asyncio
import os
import sys
import ccxt.pro
import logging
from pprint import pprint

# --- Настройка путей и логирования ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from config.config_loader import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Функции для анализа API ---

async def analyze_exchange_object(exchange):
    """Анализирует сам объект биржи, его свойства и возможности."""
    print("\n" + "="*40)
    print("--- 1. Анализ объекта биржи ---")
    print("="*40)
    print(f"ID Биржи: {exchange.id}")
    print(f"Название: {exchange.name}")
    print("Поддерживаемые возможности (has):")
    # Выводим только те возможности, которые включены (True)
    enabled_features = {key: value for key, value in exchange.has.items() if value}
    pprint(enabled_features)
    print("\n")

async def analyze_markets(exchange, symbol='ETH/USDT'):
    """Загружает и анализирует рынки (список валютных пар)."""
    print("="*40)
    print("--- 2. Анализ рынков (валютных пар) ---")
    print("="*40)
    try:
        markets = await exchange.load_markets()
        print(f"Всего загружено рынков: {len(markets)}")
        print(f"\nАнализ конкретного рынка: {symbol}")
        market_details = markets.get(symbol)
        if market_details:
            pprint(market_details)
        else:
            print(f"Рынок {symbol} не найден!")
    except Exception as e:
        logger.error(f"Ошибка при загрузке рынков: {e}")
    print("\n")

async def analyze_balance(exchange):
    """Загружает и анализирует баланс в песочнице."""
    print("="*40)
    print("--- 3. Анализ баланса ---")
    print("="*40)
    try:
        balance = await exchange.fetch_balance()
        print("Структура объекта баланса:")
        # Выводим только валюты с ненулевым балансом
        active_balances = {key: value for key, value in balance.items() if isinstance(value, dict) and value.get('total', 0) > 0}
        pprint(active_balances)
        print("\nПримечание: В песочнице балансы могут быть стандартными или нулевыми.")
    except Exception as e:
        logger.error(f"Ошибка при получении баланса: {e}")
    print("\n")

async def analyze_ticker(exchange, symbol='ETH/USDT'):
    """Получает и анализирует тикер для указанной пары."""
    print("="*40)
    print(f"--- 4. Анализ тикера ({symbol}) ---")
    print("="*40)
    try:
        print(f"Ожидание первого тикера для {symbol}...")
        ticker = await exchange.watch_ticker(symbol)
        print("Структура объекта тикера:")
        pprint(ticker)
    except Exception as e:
        logger.error(f"Ошибка при получении тикера: {e}")
    print("\n")

async def analyze_order_book(exchange, symbol='ETH/USDT'):
    """Получает и анализирует стакан ордеров."""
    print("="*40)
    print(f"--- 5. Анализ стакана ордеров ({symbol}) ---")
    print("="*40)
    try:
        print(f"Ожидание первого обновления стакана для {symbol}...")
        order_book = await exchange.watch_order_book(symbol)
        print("Структура объекта стакана:")
        # Выводим только общую структуру и по 2 примера бидов/асков
        pprint({
            'symbol': order_book.get('symbol'),
            'timestamp': order_book.get('timestamp'),
            'datetime': order_book.get('datetime'),
            'nonce': order_book.get('nonce'),
            'bids_count': len(order_book.get('bids', [])),
            'asks_count': len(order_book.get('asks', [])),
            'sample_bids': order_book.get('bids', [])[:2],
            'sample_asks': order_book.get('asks', [])[:2],
        })
    except Exception as e:
        logger.error(f"Ошибка при получении стакана: {e}")
    print("\n")


async def main():
    """Основная функция для инициализации и запуска анализа."""
    # --- Настройка вывода в файл ---
    original_stdout = sys.stdout
    with open('exchange_analysis_report.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f

        logger.info("Загрузка конфигурации для подключения к песочнице Binance...")
        
        try:
            config = load_config()
            sandbox_config = config.get('binance', {}).get('sandbox', {})
            api_key = sandbox_config.get('apiKey')
            secret = sandbox_config.get('secret')

            if not api_key or not secret:
                logger.error("Ключи API для песочницы не найдены в .env или config.json!")
                return

        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации: {e}")
            return

        exchange = ccxt.pro.binance({
            'apiKey': api_key,
            'secret': secret,
            'options': {
                'defaultType': 'spot',
            },
        })

        try:
            exchange.set_sandbox_mode(True)
            logger.info(f"Подключение к песочнице {exchange.name}...")

            # --- Запуск аналитических функций ---
            await analyze_exchange_object(exchange)
            await analyze_markets(exchange)
            await analyze_balance(exchange)
            await analyze_ticker(exchange)
            await analyze_order_book(exchange)

            logger.info("Анализ завершен.")

        except Exception as e:
            logger.error(f"Произошла ошибка во время анализа: {e}", exc_info=True)
        finally:
            logger.info("Закрытие соединения с биржей.")
            await exchange.close()

    # --- Возвращаем стандартный вывод ---
    sys.stdout = original_stdout
    logger.info("Отчет сохранен в exchange_analysis_report.txt")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем.")

```

### 📄 `src\__init__.py`

```python

```

### 📄 `src\application\__init__.py`

```python

```

### 📄 `src\application\use_cases\__init__.py`

```python
"""Use cases for the trading application."""
```

### 📄 `src\application\use_cases\run_realtime_trading.py`

```python
# application/use_cases/run_realtime_trading.py
"""Trading loop using OrderExecutionService and BuyOrderMonitor."""

import asyncio
import time
import logging
from decimal import Decimal

from domain.entities.currency_pair import CurrencyPair
from domain.services.deals.deal_service import DealService
from domain.services.market_data.orderbook_analyzer import OrderBookSignal
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository
from domain.services.market_data.ticker_service import TickerService
from application.utils.performance_logger import PerformanceLogger
from domain.services.trading.signal_cooldown_manager import SignalCooldownManager
from domain.services.utils.orderbook_cache import OrderBookCache
from domain.services.orders.filled_buy_order_handler import FilledBuyOrderHandler
from domain.services.deals.deal_completion_monitor import DealCompletionMonitor

logger = logging.getLogger(__name__)


async def run_realtime_trading(
    pro_exchange_connector_prod: CcxtExchangeConnector,
    pro_exchange_connector_sandbox: CcxtExchangeConnector,
    currency_pair: CurrencyPair,
    deal_service: DealService,
    order_execution_service,
    buy_order_monitor, # Возвращено
    orderbook_analyzer,
    deal_completion_monitor=None,  # Добавлен новый параметр
    stop_loss_monitor=None,  # Добавлен StopLossMonitor
):
    """Simplified trading loop using OrderExecutionService and BuyOrderMonitor."""

    repository = InMemoryTickerRepository(max_size=5000)
    ticker_service = TickerService(repository)
    logger_perf = PerformanceLogger(log_interval_seconds=10)
    cooldown_manager = SignalCooldownManager()
    
    # Создаем кеш для стакана заявок (TTL 30 секунд)
    orderbook_cache = OrderBookCache(ttl_seconds=30)
    
    # Создаем обработчик исполненных BUY ордеров
    filled_buy_order_handler = FilledBuyOrderHandler(
        order_service=order_execution_service.order_service,
        deal_service=deal_service
    )
    
    # Создаем монитор завершения сделок
    deal_completion_monitor = DealCompletionMonitor(
        deal_service=deal_service,
        order_service=order_execution_service.order_service
    )
    
    counter = 0
    last_orderbook_update = 0
    orderbook_update_interval = 10  # Обновляем стакан каждые 10 тиков

    logger.info("🚀 Запуск расширенного торгового цикла с OrderExecutionService + BuyOrderMonitor")

    try:
        while True:
            try:
                ticker_data = await pro_exchange_connector_prod.watch_ticker(currency_pair.symbol)

                start_process = time.time()
                await ticker_service.process_ticker(ticker_data)
                end_process = time.time()

                processing_time = end_process - start_process
                counter += 1

                if len(repository.tickers) < 50:
                    if counter % 100 == 0:
                        logger.info(
                            "🟡 Накоплено %s тиков, нужно 50",
                            len(repository.tickers),
                        )
                    continue

                # Периодически обновляем кеш стакана для стоп-лосса
                if counter - last_orderbook_update >= orderbook_update_interval:
                    try:
                        orderbook_data = await pro_exchange_connector_prod.fetch_order_book(currency_pair.symbol)
                        orderbook_cache.set(currency_pair.symbol, orderbook_data)
                        last_orderbook_update = counter
                        logger.debug(f"📦 Обновлен кеш стакана на тике {counter}")
                    except Exception as e:
                        logger.debug(f"⚠️ Не удалось обновить кеш стакана: {e}")

                ticker_signal = await ticker_service.get_signal()

                if len(repository.tickers) > 0:
                    last_ticker = repository.tickers[-1]
                    signals_count = len(last_ticker.signals) if last_ticker.signals else 0
                    logger_perf.log_tick(
                        price=float(last_ticker.close),
                        processing_time=processing_time,
                        signals_count=signals_count,
                    )

                if ticker_signal == "BUY":
                    # Анализ стакана
                    orderbook_metrics = orderbook_analyzer.analyze_orderbook(
                        await pro_exchange_connector_prod.watch_order_book(currency_pair.symbol)
                    )

                    if orderbook_metrics.signal in [OrderBookSignal.REJECT, OrderBookSignal.WEAK_SELL, OrderBookSignal.STRONG_SELL]:
                        logger.info(f"🚫 Сигнал MACD отклонен анализатором стакана: {orderbook_metrics.signal.value}")
                        continue
                    
                    # Синхронизация ордеров перед принятием решения
                    await order_execution_service.monitor_active_orders()

                    if len(repository.tickers) > 0:
                        last_ticker = repository.tickers[-1]
                        if last_ticker.signals:
                            current_price = float(last_ticker.close)

                            active_deals_count = len(deal_service.get_open_deals())
                            can_buy, reason = cooldown_manager.can_buy(
                                active_deals_count=active_deals_count,
                                max_deals=currency_pair.deal_count,
                            )

                            if not can_buy:
                                if counter % 20 == 0:
                                    logger.info(
                                        "🚫 BUY заблокирован: %s | Цена: %s",
                                        reason,
                                        current_price,
                                    )
                                continue

                            logger.info("\n" + "=" * 80)
                            logger.info(
                                "🟢🔥 MACD СИГНАЛ ПОКУПКИ ОБНАРУЖЕН! ВЫПОЛНЯЕМ ЧЕРЕЗ OrderExecutionService..."
                            )
                            logger.info("=" * 80)

                            macd = last_ticker.signals.get('macd', 0.0)
                            signal = last_ticker.signals.get('signal', 0.0)
                            hist = last_ticker.signals.get('histogram', 0.0)

                            logger.info("   📈 MACD > Signal: %.6f > %.6f", macd, signal)
                            logger.info("   📊 Histogram: %.6f", hist)
                            logger.info("   💰 Текущая цена: %s USDT", current_price)
                            logger.info(
                                "   🎯 Активных сделок: %s/%s",
                                active_deals_count,
                                currency_pair.deal_count,
                            )

                            try:
                                # Используем бюджет из currency_pair
                                budget = currency_pair.deal_quota

                                # Проверка баланса перед выполнением
                                balance_ok, balance_reason = await deal_service.check_balance_before_deal(
                                    quote_currency=currency_pair.quote_currency,
                                    required_amount=budget
                                )
                                if not balance_ok:
                                    logger.error(f"❌ Недостаточно средств: {balance_reason}")
                                    continue

                                strategy_result = ticker_service.calculate_strategy(
                                    buy_price=current_price,
                                    budget=budget,
                                    currency_pair=currency_pair,
                                    profit_percent=currency_pair.profit_markup,
                                )

                                if isinstance(strategy_result, dict) and "comment" in strategy_result:
                                    logger.error(
                                        "❌ Ошибка в калькуляторе: %s",
                                        strategy_result["comment"],
                                    )
                                    continue

                                logger.info("🚀 Выполнение стратегии через OrderExecutionService...")
                                execution_result = await order_execution_service.execute_trading_strategy(
                                    currency_pair=currency_pair,
                                    strategy_result=strategy_result,
                                    metadata={
                                        'trigger': 'macd_signal',
                                        'macd_data': {
                                            'macd': macd,
                                            'signal': signal,
                                            'histogram': hist,
                                        },
                                        'market_price': current_price,
                                        'timestamp': int(time.time() * 1000),
                                    },
                                )

                                if execution_result.success:
                                    logger.info("🎉 СТРАТЕГИЯ ВЫПОЛНЕНА УСПЕШНО!")
                                else:
                                    logger.error(
                                        "❌ СТРАТЕГИЯ НЕ ВЫПОЛНЕНА: %s",
                                        execution_result.error_message,
                                    )

                            except Exception as calc_error:
                                logger.exception(
                                    "❌ Ошибка в стратегии: %s",
                                    calc_error,
                                )

                            logger.info("=" * 80)
                            logger.info("🔄 Продолжаем мониторинг...\n")

                if counter % 50 == 0:  # Изменено с 100 на 50 для более частого вывода
                    # Запускаем обработчик исполненных BUY ордеров
                    await filled_buy_order_handler.check_and_place_sell_orders()
                    # Запускаем монитор завершения сделок
                    await deal_completion_monitor.check_deals_completion()

                    execution_stats = order_execution_service.get_execution_statistics()
                    logger.info("\n📊 СТАТИСТИКА OrderExecutionService (тик %s):", counter)
                    logger.info("   🚀 Всего выполнений: %s", execution_stats["total_executions"])
                    logger.info("   ✅ Успешных: %s", execution_stats["successful_executions"])
                    logger.info("   ❌ Неудачных: %s", execution_stats["failed_executions"])

                    order_stats = order_execution_service.order_service.get_statistics()
                    logger.info("   📦 Всего ордеров: %s", order_stats["total_orders"])
                    logger.info("   🔄 Открытых ордеров: %s", order_stats["open_orders"])

                    all_orders = order_execution_service.order_service.orders_repo.get_all()
                    if all_orders:
                        logger.info("   🔍 ДЕТАЛИ ПО ОРДЕРАМ:")
                        # Динамическое создание строки формата для логов
                        log_format = (
                            "     - ID: {} | DealID: {} | {} | {} | {} | "
                            "Цена: {:g} | Кол-во: {:g} | ExchangeID: {} | Filled: {:g} | AvgPrice: {:g} | Fees: {:g}"
                        )

                        for order in all_orders:
                            logger.info(
                                log_format.format(
                                    order.order_id,
                                    order.deal_id,
                                    order.symbol,
                                    order.side.upper(),
                                    order.status,
                                    float(order.price),
                                    float(order.amount),
                                    order.exchange_id,
                                    float(order.filled_amount),
                                    float(order.average_price),
                                    float(order.fees)
                                )
                            )

                    active_deals = len(deal_service.get_open_deals())
                    logger.info("   💼 Активных сделок: %s", active_deals)

                    # Получение и отображение баланса
                    balance = await pro_exchange_connector_sandbox.fetch_balance()
                    base_currency_balance = balance.get(currency_pair.base_currency, {}).get('free', 0.0)
                    quote_currency_balance = balance.get(currency_pair.quote_currency, {}).get('free', 0.0)
                    logger.info(f"   💰 Баланс: {base_currency_balance:.6f} {currency_pair.base_currency} | {quote_currency_balance:.2f} {currency_pair.quote_currency}")

                    monitor_stats = buy_order_monitor.get_statistics()
                    logger.info("\n🕒 СТАТИСТИКА BuyOrderMonitor:")
                    logger.info("   🔍 Проверок выполнено: %s", monitor_stats["checks_performed"])
                    logger.info("   🚨 Тухляков найдено: %s", monitor_stats["stale_orders_found"])
                    logger.info("   ❌ Ордеров отменено: %s", monitor_stats["orders_cancelled"])
                    logger.info("   🔄 Ордеров пересоздано: %s", monitor_stats["orders_recreated"])
                    
                    # Добавляем статистику для нашего нового DealCompletionMonitor
                    if deal_completion_monitor:
                        try:
                            completion_stats = deal_completion_monitor.get_statistics()
                            logger.info("\n🎯 СТАТИСТИКА DealCompletionMonitor:")
                            logger.info("   🔍 Проверок выполнено: %s", completion_stats["checks_performed"])
                            logger.info("   💼 Сделок отслеживается: %s", completion_stats["deals_monitored"])
                            logger.info("   ✅ Сделок завершено: %s", completion_stats["deals_completed"])
                        except Exception as e:
                            logger.debug("⚠️ DealCompletionMonitor статистика недоступна: %s", e)
                    
                    # Оптимизированная проверка стоп-лосса с кешированными данными
                    if stop_loss_monitor and counter % 50 == 0:  # Проверяем каждые 50 тиков
                        try:
                            current_price = float(ticker_data.get('close', 0))
                            cached_orderbook = orderbook_cache.get(currency_pair.symbol)
                            
                            # Передаем кешированные данные в стоп-лосс
                            await stop_loss_monitor.check_open_deals(
                                current_price=current_price,
                                cached_orderbook=cached_orderbook
                            )
                            
                            if counter % 500 == 0:  # Логируем раз в 500 тиков
                                logger.debug("🛡️ Проверен стоп-лосс с кешированными данными")
                        except Exception as e:
                            logger.debug(f"⚠️ Ошибка в оптимизированном стоп-лоссе: {e}")
                    
                    # Добавляем статистику для StopLossMonitor
                    if stop_loss_monitor:
                        try:
                            stop_loss_stats = stop_loss_monitor.get_statistics()
                            logger.info("\n🛡️ СТАТИСТИКА StopLossMonitor:")
                            logger.info("   🔍 Проверок выполнено: %s", stop_loss_stats["checks_performed"])
                            logger.info("   ⚠️ Предупреждений отправлено: %s", stop_loss_stats["warnings_sent"])
                            logger.info("   🔴 Пробитий поддержки: %s", stop_loss_stats["support_breaks"])
                            logger.info("   🚨 Экстренных ликвидаций: %s", stop_loss_stats["emergency_liquidations"])
                            logger.info("   💥 Стоп-лоссов сработало: %s", stop_loss_stats["stop_loss_triggered"])
                            
                            # Статистика кеша
                            cache_stats = orderbook_cache.get_stats()
                            logger.info("   📦 Кеш стакана: %s валидных записей (TTL: %ss)", cache_stats["valid_entries"], cache_stats["ttl_seconds"])
                        except Exception as e:
                            logger.debug("⚠️ StopLossMonitor статистика недоступна: %s", e)

            except Exception as e:
                logger.exception("❌ Ошибка в торговом цикле: %s", e)
                await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    finally:
        logger.info("🚨 Выполнение экстренной остановки...")
        emergency_result = await order_execution_service.emergency_stop_all_trading()
        logger.info("🚨 Экстренная остановка завершена: %s", emergency_result)

        final_monitor_stats = buy_order_monitor.get_statistics()
        logger.info("🕒 ФИНАЛЬНАЯ СТАТИСТИКА BuyOrderMonitor:")
        logger.info("   🔍 Всего проверок: %s", final_monitor_stats["checks_performed"])
        logger.info("   🚨 Всего тухляков: %s", final_monitor_stats["stale_orders_found"])
        logger.info("   ❌ Всего отменено: %s", final_monitor_stats["orders_cancelled"])
        logger.info("   🔄 Всего пересоздано: %s", final_monitor_stats["orders_recreated"])

        final_stats = order_execution_service.get_execution_statistics()
        logger.info("📊 ФИНАЛЬНАЯ СТАТИСТИКА OrderExecutionService:")
        logger.info("   🚀 Всего выполнений: %s", final_stats["total_executions"])
        logger.info("   ✅ Успешных: %s", final_stats["successful_executions"])
        logger.info("   📈 Процент успеха: %.1f%%", final_stats["success_rate"])
        logger.info("   💰 Общий объем: %.4f USDT", final_stats["total_volume"])
        logger.info("   💸 Общие комиссии: %.4f USDT", final_stats["total_fees"])

```

### 📄 `src\domain\__init__.py`

```python
"""Domain layer containing business logic and entities."""
```

### 📄 `src\domain\entities\__init__.py`

```python
"""Domain entities for the trading system."""
```

### 📄 `src\domain\entities\currency_pair.py`

```python
# my_trading_app/domain/entities/currency_pair.py

class CurrencyPair:
    """
    Упрощённая сущность 'Валютная пара'.
    """

    def __init__(
        self,
        base_currency: str,
        quote_currency: str,
        symbol: str = None,
        order_life_time: int = 1,
        deal_quota: float = 100.0,
        # """
        # profit_markup = 0.5%.
        # """
        profit_markup: float = 0.005,
        deal_count: int = 1
    ):
        """
        symbol, например "BTC/USDT"
        order_life_time - сколько минут живёт ордер до отмены
        deal_quota - размер сделки в quote
        profit_markup - желаемый профит (0.002 = 0.2%)
        deal_count - сколько одновременно может быть открыто сделок
        """
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.symbol = symbol or f"{base_currency}/{quote_currency}"
        self.order_life_time = order_life_time
        self.deal_quota = deal_quota
        self.profit_markup = profit_markup
        self.deal_count = deal_count
        self.precision = {}
        self.limits = {}
        self.taker_fee = 0.001  # Default taker fee
        self.maker_fee = 0.001  # Default maker fee

    def update_exchange_info(self, market_data: dict):
        """
        Обновляет точность, лимиты и комиссии из данных, полученных с биржи.
        """
        if not market_data:
            return
        self.precision = market_data.get('precision', {})
        self.limits = market_data.get('limits', {})
        self.taker_fee = market_data.get('taker', self.taker_fee)
        self.maker_fee = market_data.get('maker', self.maker_fee)
        logging.info(f"Updated currency pair {self.symbol} with exchange data: Precision={self.precision}, Limits={self.limits}, Fees(T/M)={self.taker_fee}/{self.maker_fee}")

    def __repr__(self):
        return (f"<CurrencyPair(symbol={self.symbol}, "
                f"order_life_time={self.order_life_time}, "
                )

```

### 📄 `src\domain\entities\deal.py`

```python
# my_trading_app/domain/entities/deal.py
import time
from .order import Order
from .currency_pair import CurrencyPair

class Deal:
    """
    Базовая сущность "Сделка".
    Содержит ссылки на buy_order и sell_order, статусы и т.д.
    """

    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CANCELED = "CANCELED"

    def __init__(
        self,
        deal_id: int,
        currency_pair: CurrencyPair, # Изменено с ID на объект
        status: str = STATUS_OPEN,
        buy_order: Order = None,
        sell_order: Order = None,
        created_at: int = None,
        closed_at: int = None,
    ):
        self.deal_id = deal_id
        self.currency_pair = currency_pair # Изменено
        self.currency_pair_id = currency_pair.symbol # Оставляем для обратной совместимости
        self.status = status
        self.buy_order = buy_order
        self.sell_order = sell_order
        self.created_at = created_at or int(time.time() * 1000)
        self.closed_at = closed_at

        # Если buy_order или sell_order есть — установим им deal_id
        self._sync_order_deal_id()

    def _sync_order_deal_id(self):
        """Вспомогательный метод, чтобы прописать deal_id в ордера."""
        if self.buy_order:
            self.buy_order.deal_id = self.deal_id
        if self.sell_order:
            self.sell_order.deal_id = self.deal_id

    def attach_orders(self, buy_order: Order, sell_order: Order):
        """
        Если нужно задним числом «подвесить» ордера к сделке.
        """
        self.buy_order = buy_order
        self.sell_order = sell_order
        self._sync_order_deal_id()

    def update_buy_order(self, new_buy_order: Order):
        """Заменяет старый ордер на покупку новым."""
        self.buy_order = new_buy_order
        self._sync_order_deal_id()

    def open(self):
        """Простейший метод: пометить сделку как открытую."""
        self.status = self.STATUS_OPEN

    def close(self):
        """Простейший метод: пометить сделку как закрытую."""
        self.status = self.STATUS_CLOSED
        self.closed_at = int(time.time() * 1000)

    def cancel(self):
        """Простейший метод: пометить сделку как отменённую."""
        self.status = self.STATUS_CANCELED
        self.closed_at = int(time.time() * 1000)

    def is_open(self) -> bool:
        return self.status == self.STATUS_OPEN

    def is_closed(self) -> bool:
        return self.status == self.STATUS_CLOSED

    def __repr__(self):
        return f"<Deal(id={self.deal_id}, status={self.status}, pair={self.currency_pair_id})>"

```

### 📄 `src\domain\entities\order.py`

```python
# domain/entities/order.py.new - ENHANCED для реальной торговли
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

class Order:
    """
    🚀 РАСШИРЕННАЯ сущность "Ордер" для реальной торговли на бирже
    Добавлены критически важные поля для работы с биржевым API
    """

    # Статусы ордера
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CANCELED = "CANCELED"
    STATUS_FAILED = "FAILED"
    STATUS_PENDING = "PENDING"
    STATUS_FILLED = "FILLED"          # 🆕 Полностью исполнен
    STATUS_PARTIALLY_FILLED = "PARTIALLY_FILLED"  # 🆕 Частично исполнен
    STATUS_NOT_FOUND_ON_EXCHANGE = "NOT_FOUND_ON_EXCHANGE" # 🆕 Ордер не найден на бирже

    # Стороны ордера
    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"

    # Типы ордера
    TYPE_LIMIT = "LIMIT"
    TYPE_MARKET = "MARKET"
    TYPE_STOP_LOSS = "STOP_LOSS"      # 🆕 Стоп-лосс
    TYPE_TAKE_PROFIT = "TAKE_PROFIT"  # 🆕 Тейк-профит

    def __init__(
        self,
        order_id: int,
        side: str,
        order_type: str,
        price: float = 0.0,
        amount: float = 0.0,
        status: str = STATUS_PENDING,
        created_at: int = None,
        closed_at: int = None,
        deal_id: int = None,
        # 🆕 КРИТИЧЕСКИЕ ПОЛЯ ДЛЯ БИРЖИ:
        exchange_id: Optional[str] = None,      # ID ордера на бирже
        symbol: Optional[str] = None,           # Торговая пара (BTCUSDT)
        filled_amount: float = 0.0,             # Исполненный объем
        remaining_amount: float = 0.0,          # Оставшийся объем
        average_price: float = 0.0,             # Средняя цена исполнения
        fees: float = 0.0,                      # Комиссии
        fee_currency: str = "USDT",             # Валюта комиссии
        # 🆕 ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ:
        time_in_force: str = "GTC",             # Good Till Cancelled
        client_order_id: Optional[str] = None,  # Клиентский ID
        exchange_timestamp: Optional[int] = None, # Время на бирже
        last_update: Optional[int] = None,      # Последнее обновление
        error_message: Optional[str] = None,    # Сообщение об ошибке
        retries: int = 0,                       # Количество попыток
        # 🆕 МЕТАДАННЫЕ:
        metadata: Optional[Dict[str, Any]] = None,  # Дополнительная информация
        exchange_raw_data: Optional[Dict[str, Any]] = None # Полный ответ от биржи
    ):
        self.order_id = order_id
        self.side = side
        self.order_type = order_type
        self.price = price
        self.amount = amount
        self.status = status
        self.created_at = created_at or int(time.time() * 1000)
        self.closed_at = closed_at
        self.deal_id = deal_id

        # 🆕 Биржевые поля
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.filled_amount = filled_amount
        self.remaining_amount = remaining_amount or amount  # По умолчанию = amount
        self.average_price = average_price
        self.fees = fees
        self.fee_currency = fee_currency

        # 🆕 Дополнительные поля
        self.time_in_force = time_in_force
        self.client_order_id = client_order_id
        self.exchange_timestamp = exchange_timestamp
        self.last_update = last_update or self.created_at
        self.error_message = error_message
        self.retries = retries
        self.metadata = metadata or {}
        self.exchange_raw_data = exchange_raw_data # Сохраняем полный ответ

    # 🆕 РАСШИРЕННЫЕ МЕТОДЫ ПРОВЕРКИ СТАТУСА
    def is_open(self) -> bool:
        """Ордер открыт и ожидает исполнения"""
        return self.status == self.STATUS_OPEN

    def is_closed(self) -> bool:
        """Ордер закрыт (исполнен или отменен)"""
        return self.status in [self.STATUS_CLOSED, self.STATUS_FILLED, self.STATUS_CANCELED, self.STATUS_NOT_FOUND_ON_EXCHANGE]

    def is_filled(self) -> bool:
        """Ордер полностью исполнен"""
        return self.status == self.STATUS_FILLED

    def is_partially_filled(self) -> bool:
        """Ордер частично исполнен"""
        return self.status == self.STATUS_PARTIALLY_FILLED

    def is_pending(self) -> bool:
        """Ордер ожидает размещения на бирже"""
        return self.status == self.STATUS_PENDING

    def is_failed(self) -> bool:
        """Ордер не смог быть размещен"""
        return self.status == self.STATUS_FAILED

    # 🆕 МЕТОДЫ РАБОТЫ С ИСПОЛНЕНИЕМ
    def get_fill_percentage(self) -> float:
        """Возвращает процент исполнения ордера (0.0 - 1.0)"""
        if self.amount == 0:
            return 0.0
        return min(self.filled_amount / self.amount, 1.0)

    def get_remaining_amount(self) -> float:
        """Возвращает оставшийся объем для исполнения"""
        return max(self.amount - self.filled_amount, 0.0)

    def is_fully_filled(self) -> bool:
        """Проверяет, полностью ли исполнен ордер"""
        return self.filled_amount >= self.amount

    # 🆕 МЕТОДЫ ОБНОВЛЕНИЯ СТАТУСА
    def update_from_exchange(self, exchange_data: Dict[str, Any]) -> None:
        """Обновляет ордер данными с биржи, безопасно обрабатывая None."""
        self.exchange_id = exchange_data.get('id', self.exchange_id)
        self.exchange_raw_data = exchange_data # Сохраняем полный ответ от биржи

        # Безопасное обновление числовых полей
        filled = exchange_data.get('filled')
        if filled is not None:
            self.filled_amount = float(filled)

        remaining = exchange_data.get('remaining')
        if remaining is not None:
            self.remaining_amount = float(remaining)

        average = exchange_data.get('average')
        if average is not None:
            self.average_price = float(average)

        if 'fee' in exchange_data and exchange_data['fee'] is not None:
            fee_cost = exchange_data['fee'].get('cost')
            if fee_cost is not None:
                self.fees = float(fee_cost)
        # Обновляем статус на основе данных биржи
        exchange_status = exchange_data.get('status', '').lower()
        if exchange_status == 'closed':
            self.status = self.STATUS_FILLED
        elif exchange_status == 'canceled':
            self.status = self.STATUS_CANCELED
        elif exchange_status == 'open':
            if self.filled_amount > 0:
                self.status = self.STATUS_PARTIALLY_FILLED
            else:
                self.status = self.STATUS_OPEN

        self.last_update = int(time.time() * 1000)
        self.exchange_timestamp = exchange_data.get('timestamp', self.exchange_timestamp)

    def mark_as_placed(self, exchange_id: str, exchange_timestamp: int = None) -> None:
        """Помечает ордер как размещенный на бирже"""
        self.exchange_id = exchange_id
        self.status = self.STATUS_OPEN
        self.exchange_timestamp = exchange_timestamp or int(time.time() * 1000)
        self.last_update = int(time.time() * 1000)

    def mark_as_failed(self, error_message: str) -> None:
        """Помечает ордер как неудачный"""
        self.status = self.STATUS_FAILED
        self.error_message = error_message
        self.closed_at = int(time.time() * 1000)
        self.last_update = self.closed_at

    # 🆕 МЕТОДЫ ДЛЯ ЗАКРЫТИЯ
    def close(self, filled_amount: float = None, average_price: float = None):
        """Закрывает ордер как исполненный"""
        if filled_amount is not None:
            self.filled_amount = filled_amount
        if average_price is not None:
            self.average_price = average_price

        self.status = self.STATUS_FILLED if self.is_fully_filled() else self.STATUS_PARTIALLY_FILLED
        self.closed_at = int(time.time() * 1000)
        self.last_update = self.closed_at

    def cancel(self, reason: str = None):
        """Отменяет ордер"""
        self.status = self.STATUS_CANCELED
        self.closed_at = int(time.time() * 1000)
        self.last_update = self.closed_at
        if reason:
            self.error_message = f"Canceled: {reason}"

    # 🆕 МЕТОДЫ ДЛЯ РАСЧЕТОВ
    def calculate_total_cost(self) -> float:
        """Рассчитывает общую стоимость ордера (без комиссий)"""
        price = self.average_price if self.average_price > 0 else self.price
        return self.filled_amount * price

    def calculate_total_cost_with_fees(self) -> float:
        """Рассчитывает общую стоимость с учетом комиссий"""
        return self.calculate_total_cost() + self.fees

    # 🆕 МЕТОДЫ ДЛЯ ВАЛИДАЦИИ
    def validate_for_exchange(self) -> tuple[bool, str]:
        """Валидирует ордер перед отправкой на биржу"""
        if not self.symbol:
            return False, "Symbol is required"
        if self.amount <= 0:
            return False, "Amount must be positive"
        if self.side not in [self.SIDE_BUY, self.SIDE_SELL]:
            return False, "Invalid side"
        if self.order_type == self.TYPE_LIMIT and self.price <= 0:
            return False, "Price must be positive for limit orders"
        return True, "Valid"

    # 🆕 СЕРИАЛИЗАЦИЯ
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует ордер в словарь для сохранения"""
        return {
            'order_id': self.order_id,
            'side': self.side,
            'order_type': self.order_type,
            'price': self.price,
            'amount': self.amount,
            'status': self.status,
            'created_at': self.created_at,
            'closed_at': self.closed_at,
            'deal_id': self.deal_id,
            'exchange_id': self.exchange_id,
            'symbol': self.symbol,
            'filled_amount': self.filled_amount,
            'remaining_amount': self.remaining_amount,
            'average_price': self.average_price,
            'fees': self.fees,
            'fee_currency': self.fee_currency,
            'time_in_force': self.time_in_force,
            'client_order_id': self.client_order_id,
            'exchange_timestamp': self.exchange_timestamp,
            'last_update': self.last_update,
            'error_message': self.error_message,
            'retries': self.retries,
            'metadata': self.metadata,
            'exchange_raw_data': self.exchange_raw_data # Добавлено в to_dict
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Создает ордер из словаря"""
        return cls(**data)

    def __repr__(self):
        fill_pct = self.get_fill_percentage() * 100
        return (f"<Order(id={self.order_id}, exchange_id={self.exchange_id}, "
                f"deal_id={self.deal_id}, side={self.side}, type={self.order_type}, "
                f"status={self.status}, price={self.price}, amount={self.amount}, "
                f"filled={self.filled_amount} ({fill_pct:.1f}%), fees={self.fees})>")

    def __str__(self):
        """Человеко-читаемое представление"""
        return (f"{self.side} {self.amount} {self.symbol} at {self.price} "
                f"[{self.status}] filled: {self.filled_amount}")


# 🆕 ДОПОЛНИТЕЛЬНЫЕ КЛАССЫ ДЛЯ РАБОТЫ С ОРДЕРАМИ

@dataclass
class OrderValidationResult:
    """Результат валидации ордера"""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass
class OrderExecutionResult:
    """Результат исполнения ордера"""
    success: bool
    order: Optional[Order] = None
    error_message: Optional[str] = None
    exchange_response: Optional[Dict[str, Any]] = None

@dataclass
class ExchangeInfo:
    """Информация о торговой паре с биржи"""
    symbol: str
    min_qty: float
    max_qty: float
    step_size: float
    min_price: float
    max_price: float
    tick_size: float
    min_notional: float
    fees: Dict[str, float]  # maker/taker fees
    precision: Dict[str, float] # ❗️ ДОБАВЛЕНО: полная информация о точности

```

### 📄 `src\domain\entities\ticker.py`

```python
import time
from typing import Dict

class Ticker:
    def __init__(self, data: Dict):
        self.timestamp = data.get("timestamp", int(time.time() * 1000))
        self.symbol = data.get("symbol", "")
        self.price = data.get("last", 0.0)
        self.open = data.get("open", 0.0)
        self.close = data.get("close", 0.0)
        self.volume = data.get("baseVolume", 0.0)
        self.high = data.get("high", 0.0)
        self.low = data.get("low", 0.0)
        self.bid = data.get("bid", 0.0)
        self.ask = data.get("ask", 0.0)
        self.trades_count = 0  # Обновится позже
        self.signals = {}  # Будем дополнять сигналами

    def update_signals(self, signals: Dict):
        """Обновляет сигналы (MACD, RSI, OBV и т. д.)"""
        self.signals.update(signals)

    def to_dict(self) -> Dict:
        """Конвертация тикера в словарь для хранения"""
        return {
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "price": self.price,
            "open": self.open,
            "close": self.close,
            "volume": self.volume,
            "high": self.high,
            "low": self.low,
            "bid": self.bid,
            "ask": self.ask,
            "trades_count": self.trades_count,
            **self.signals  # Добавляем сигналы
        }


    def __repr__(self):
        return f"<Ticker {self.symbol} {self.price} ({self.timestamp})>"
```

### 📄 `src\domain\factories\__init__.py`

```python
"""Factories for creating domain objects."""
```

### 📄 `src\domain\factories\deal_factory.py`

```python
from itertools import count
import time

from domain.entities.currency_pair import CurrencyPair
from domain.entities.deal import Deal
from domain.factories.order_factory import OrderFactory

# 🔧 Генератор уникальных ID на основе счетчика + timestamp
_id_gen = count(int(time.time()*1e6))

def _next_id():
    """🔧 Генерация следующего уникального ID"""
    return next(_id_gen)

class DealFactory:
    """
    Фабрика для создания сущностей Deal.
    """
    def __init__(self, order_factory: OrderFactory):
        self.order_factory = order_factory

    def create_new_deal(self, currency_pair: CurrencyPair, status: str = Deal.STATUS_OPEN) -> Deal:
        """
        Создает новую сделку с уникальным ID.
        """
        deal_id = _next_id()
        return Deal(
            deal_id=deal_id,
            currency_pair=currency_pair,
            status=status
        )
```

### 📄 `src\domain\factories\order_factory.py`

```python
# domain/factories/order_factory.py.new - ENHANCED для реальной торговли
import time
import uuid
import math
from itertools import count
from typing import Optional, Dict, Any
from domain.entities.order import Order, ExchangeInfo

# 🔧 Генератор уникальных ID на основе счетчика + timestamp
_id_gen = count(int(time.time()*1e6))

def _next_id():
    """🔧 Генерация следующего уникального ID"""
    return next(_id_gen)

def _generate_client_order_id(prefix: str = "auto") -> str:
    """🆕 Генерация уникального клиентского ID"""
    timestamp = int(time.time() * 1000)
    short_uuid = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{short_uuid}"

class OrderFactory:
    """
    🚀 РАСШИРЕННАЯ фабрика для создания ордеров с валидацией и поддержкой биржевых параметров
    """

    def __init__(self, exchange_info_cache: Optional[Dict[str, ExchangeInfo]] = None):
        """
        Инициализация фабрики

        Args:
            exchange_info_cache: Кеш информации о торговых парах с биржи
        """
        self.exchange_info_cache = exchange_info_cache or {}

    def _create_base_order(
        self,
        side: str,
        order_type: str,
        symbol: str,
        amount: float,
        price: float = 0.0,
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
        time_in_force: str = "GTC",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        🆕 Базовый метод создания ордера с полной валидацией

        Args:
            side: BUY или SELL
            order_type: LIMIT, MARKET, STOP_LOSS, etc.
            symbol: Торговая пара (например, BTCUSDT)
            amount: Количество для торговли
            price: Цена (для лимитных ордеров)
            deal_id: ID связанной сделки
            client_order_id: Клиентский ID (генерируется автоматически если None)
            time_in_force: Время жизни ордера
            metadata: Дополнительная информация
        """

        # Генерируем ID если не предоставлен
        if client_order_id is None:
            client_order_id = _generate_client_order_id(f"{side.lower()}_{symbol.lower()}")

        # Создаем ордер с расширенными параметрами
        order = Order(
            order_id=_next_id(),
            side=side,
            order_type=order_type,
            price=price,
            amount=amount,
            status=Order.STATUS_PENDING,  # Начинаем с PENDING
            deal_id=deal_id,
            symbol=symbol,
            remaining_amount=amount,  # Изначально весь объем остается
            client_order_id=client_order_id,
            time_in_force=time_in_force,
            metadata=metadata or {}
        )

        return order

    def create_buy_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: Optional[int] = None,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        🛒 Создание BUY ордера с валидацией

        Args:
            symbol: Торговая пара (BTCUSDT)
            amount: Количество для покупки
            price: Цена покупки
            deal_id: ID связанной сделки
            order_type: Тип ордера (по умолчанию LIMIT)
            client_order_id: Клиентский ID
            metadata: Дополнительная информация
        """

        # Добавляем метаданные для buy ордера
        buy_metadata = metadata or {}
        buy_metadata.update({
            'order_direction': 'entry',  # Вход в позицию
            'created_by': 'order_factory',
            'creation_timestamp': int(time.time() * 1000)
        })

        return self._create_base_order(
            side=Order.SIDE_BUY,
            order_type=order_type,
            symbol=symbol,
            amount=amount,
            price=price,
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=buy_metadata
        )

    def create_sell_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: Optional[int] = None,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        🏷️ Создание SELL ордера с валидацией

        Args:
            symbol: Торговая пара (BTCUSDT)
            amount: Количество для продажи
            price: Цена продажи
            deal_id: ID связанной сделки
            order_type: Тип ордера (по умолчанию LIMIT)
            client_order_id: Клиентский ID
            metadata: Дополнительная информация
        """

        # Добавляем метаданные для sell ордера
        sell_metadata = metadata or {}
        sell_metadata.update({
            'order_direction': 'exit',  # Выход из позиции
            'created_by': 'order_factory',
            'creation_timestamp': int(time.time() * 1000)
        })

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=order_type,
            symbol=symbol,
            amount=amount,
            price=price,
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=sell_metadata
        )

    def create_market_buy_order(
        self,
        symbol: str,
        amount: float,
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        🛒 Создание MARKET BUY ордера (покупка по рынку)
        """
        metadata = {
            'order_direction': 'entry',
            'order_urgency': 'immediate',
            'market_order': True
        }

        return self._create_base_order(
            side=Order.SIDE_BUY,
            order_type=Order.TYPE_MARKET,
            symbol=symbol,
            amount=amount,
            price=0.0,  # Для market ордеров цена не нужна
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    def create_market_sell_order(
        self,
        symbol: str,
        amount: float,
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        🏷️ Создание MARKET SELL ордера (продажа по рынку)
        """
        metadata = {
            'order_direction': 'exit',
            'order_urgency': 'immediate',
            'market_order': True
        }

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=Order.TYPE_MARKET,
            symbol=symbol,
            amount=amount,
            price=0.0,  # Для market ордеров цена не нужна
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    def create_stop_loss_order(
        self,
        symbol: str,
        amount: float,
        stop_price: float,
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        🛡️ Создание STOP LOSS ордера для защиты от убытков

        Args:
            symbol: Торговая пара
            amount: Количество для продажи
            stop_price: Цена срабатывания стоп-лосса
            deal_id: ID связанной сделки
            client_order_id: Клиентский ID
        """
        metadata = {
            'order_direction': 'exit',
            'order_purpose': 'stop_loss',
            'risk_management': True,
            'stop_price': stop_price
        }

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=Order.TYPE_STOP_LOSS,
            symbol=symbol,
            amount=amount,
            price=stop_price,
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    def create_take_profit_order(
        self,
        symbol: str,
        amount: float,
        target_price: float,
        deal_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """
        💰 Создание TAKE PROFIT ордера для фиксации прибыли

        Args:
            symbol: Торговая пара
            amount: Количество для продажи
            target_price: Целевая цена прибыли
            deal_id: ID связанной сделки
            client_order_id: Клиентский ID
        """
        metadata = {
            'order_direction': 'exit',
            'order_purpose': 'take_profit',
            'profit_taking': True,
            'target_price': target_price
        }

        return self._create_base_order(
            side=Order.SIDE_SELL,
            order_type=Order.TYPE_TAKE_PROFIT,
            symbol=symbol,
            amount=amount,
            price=target_price,
            deal_id=deal_id,
            client_order_id=client_order_id,
            metadata=metadata
        )

    # 🆕 МЕТОДЫ ВАЛИДАЦИИ

    def validate_order_params(
        self,
        symbol: str,
        amount: float,
        price: float = None,
        side: str = None
    ) -> tuple[bool, list[str]]:
        """
        🔍 Валидация параметров ордера перед созданием

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []

        # Проверяем основные параметры
        if not symbol:
            errors.append("Symbol is required")
        if amount <= 0:
            errors.append("Amount must be positive")
        if price is not None and price <= 0:
            errors.append("Price must be positive")
        if side and side not in [Order.SIDE_BUY, Order.SIDE_SELL]:
            errors.append("Side must be BUY or SELL")

        # Проверяем против exchange info если доступно
        if symbol in self.exchange_info_cache:
            exchange_info = self.exchange_info_cache[symbol]

            if amount < exchange_info.min_qty:
                errors.append(f"Amount {amount} below minimum {exchange_info.min_qty}")
            if amount > exchange_info.max_qty:
                errors.append(f"Amount {amount} above maximum {exchange_info.max_qty}")

            if price is not None:
                if price < exchange_info.min_price:
                    errors.append(f"Price {price} below minimum {exchange_info.min_price}")
                if price > exchange_info.max_price:
                    errors.append(f"Price {price} above maximum {exchange_info.max_price}")

                # Проверяем минимальную стоимость ордера
                notional_value = amount * price
                if notional_value < exchange_info.min_notional:
                    errors.append(f"Order value {notional_value} below minimum {exchange_info.min_notional}")

        return len(errors) == 0, errors

    def adjust_amount_precision(self, symbol: str, amount: float, round_up: bool = False) -> float:
        """🔧 Корректирует количество согласно ``step_size`` биржи.

        Если ``round_up`` установлено в ``True``, то количество округляется
        вверх до ближайшего допустимого шага. Это полезно при создании BUY
        ордеров, чтобы избежать ситуации, когда биржа округляет значение в
        меньшую сторону и фактически покупается меньшее количество.
        """
        if symbol not in self.exchange_info_cache:
            return amount

        exchange_info = self.exchange_info_cache[symbol]
        step_size = exchange_info.step_size

        if step_size > 0:
            precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
            steps = amount / step_size
            steps = math.ceil(steps) if round_up else math.floor(steps)
            adjusted = round(steps * step_size, precision)
            adjusted = min(max(adjusted, exchange_info.min_qty), exchange_info.max_qty)
            return adjusted

        return amount

    def adjust_price_precision(self, symbol: str, price: float) -> float:
        """
        🔧 Корректирует цену согласно tick_size биржи
        """
        if symbol not in self.exchange_info_cache:
            return price

        exchange_info = self.exchange_info_cache[symbol]
        tick_size = exchange_info.tick_size

        if tick_size > 0:
            # Округляем до ближайшего tick_size
            precision = len(str(tick_size).split('.')[-1]) if '.' in str(tick_size) else 0
            adjusted = round(price // tick_size * tick_size, precision)
            return max(adjusted, exchange_info.min_price)

        return price

    def update_exchange_info(self, symbol: str, exchange_info: ExchangeInfo) -> None:
        """
        🔄 Обновляет информацию о торговой паре
        """
        self.exchange_info_cache[symbol] = exchange_info

    def get_exchange_info(self, symbol: str) -> Optional[ExchangeInfo]:
        """
        📊 Возвращает информацию о торговой паре
        """
        return self.exchange_info_cache.get(symbol)

```

### 📄 `src\domain\services\__init__.py`

```python
"""Domain services for business logic."""
```

### 📄 `src\domain\services\deals\__init__.py`

```python

```

### 📄 `src\domain\services\deals\deal_completion_monitor.py`

```python
# src/domain/services/deals/deal_completion_monitor.py
import asyncio
import logging
from typing import List

from domain.services.deals.deal_service import DealService
from domain.services.orders.order_service import OrderService
from domain.entities.deal import Deal
from domain.entities.order import Order

logger = logging.getLogger(__name__)

class DealCompletionMonitor:
    """
    Сервис для мониторинга завершения сделок.
    Проверяет, исполнены ли оба ордера (BUY и SELL) в рамках открытой сделки,
    логирует их статус и закрывает сделку в случае полного исполнения.
    """

    def __init__(self, deal_service: DealService, order_service: OrderService, check_interval_seconds: int = 30):
        self.deal_service = deal_service
        self.order_service = order_service
        self.check_interval_seconds = check_interval_seconds
        self.stats = {
            "checks_performed": 0,
            "deals_monitored": 0,
            "deals_completed": 0,
        }
        self._is_running = False

    async def start_monitoring(self):
        """Запускает мониторинг в фоновом режиме."""
        self._is_running = True
        logger.info(f"🚀 DealCompletionMonitor запущен (проверка каждые {self.check_interval_seconds}с)")
        while self._is_running:
            await self.check_deals_completion()
            await asyncio.sleep(self.check_interval_seconds)

    def stop_monitoring(self):
        """Останавливает мониторинг."""
        self._is_running = False
        logger.info("🔴 DealCompletionMonitor остановлен.")

    async def check_deals_completion(self):
        """
        Основной метод, проверяющий все открытые сделки на предмет завершения.
        """
        self.stats["checks_performed"] += 1
        open_deals = self.deal_service.get_open_deals()
        self.stats["deals_monitored"] = len(open_deals)

        if not open_deals:
            return

        logger.debug(f"Мониторинг завершения {len(open_deals)} открытых сделок...")

        for deal in open_deals:
            try:
                await self._check_single_deal(deal)
            except Exception as e:
                logger.error(f"Ошибка при проверке сделки {deal.deal_id}: {e}", exc_info=True)

    async def _check_single_deal(self, deal: Deal):
        """Проверяет и обрабатывает одну сделку."""
        buy_order = self.order_service.get_order_by_id(deal.buy_order.order_id)
        sell_order = self.order_service.get_order_by_id(deal.sell_order.order_id)

        if not buy_order or not sell_order:
            logger.warning(f"Не найден один из ордеров для сделки {deal.deal_id}. Пропускаем.")
            return

        # Логируем текущий статус ордеров в сделке
        logger.info(
            f"DEAL_STATUS | DealID: {deal.deal_id} | "
            f"BUY: {buy_order.order_id} [{buy_order.status}, {buy_order.get_fill_percentage():.0%}] | "
            f"SELL: {sell_order.order_id} [{sell_order.status}, {sell_order.get_fill_percentage():.0%}]"
        )

        # Условие для закрытия сделки: оба ордера полностью исполнены
        if buy_order.is_filled() and sell_order.is_filled():
            logger.info(f"🎉 Сделка {deal.deal_id} полностью исполнена! Закрываем...")
            self.deal_service.close_deal(deal.deal_id)
            self.stats["deals_completed"] += 1
            logger.info(f"✅ Сделка {deal.deal_id} успешно закрыта.")

    def get_statistics(self) -> dict:
        """Возвращает статистику работы монитора."""
        return self.stats

```

### 📄 `src\domain\services\deals\deal_service.py`

```python
# domain/services/deal_service.py

from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from domain.factories.deal_factory import DealFactory
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from infrastructure.repositories.deals_repository import DealsRepository
from domain.services.orders.order_service import OrderService
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class DealService:
    """
    Сервис для управления сделками:
    - Создание сделок через DealFactory,
    - Обновление и управление статусами сделок,
    - Взаимодействие с OrderService для управления ордерами.
    """

    def __init__(self, deals_repo: DealsRepository, order_service: OrderService, deal_factory: DealFactory, exchange_connector: CcxtExchangeConnector):
        self.deals_repo = deals_repo
        self.order_service = order_service
        self.deal_factory = deal_factory
        self.exchange_connector = exchange_connector

    async def check_balance_before_deal(self, quote_currency: str, required_amount: float) -> (bool, str):
        """Проверяет, достаточно ли средств на балансе."""
        try:
            balance = await self.exchange_connector.get_balance(quote_currency)
            if balance >= required_amount:
                return True, f"Баланс {quote_currency} достаточен: {balance:.2f}"
            else:
                return False, f"Недостаточно средств. Требуется: {required_amount:.2f}, доступно: {balance:.2f}"
        except Exception as e:
            return False, f"Ошибка при проверке баланса: {e}"

    def create_new_deal(self, currency_pair: CurrencyPair) -> Deal:
        """
        Создает новую сделку для указанной валютной пары.
        """
        deal = self.deal_factory.create_new_deal(currency_pair)
        self.deals_repo.save(deal)
        logger.info(f"Created new deal: {deal}")
        return deal

    def open_buy_order(self, price, amount, deal_id):
        """
        Проверяет и обрабатывает все открытые сделки.
        """
        buy_order = self.order_service.create_buy_order(
            price, amount
        )
        buy_order.deal_id = deal_id
        logger.info(f"Create BUY Order: {buy_order}")
        return buy_order


    def open_sell_order(self, price, amount, deal_id):
        """
        Проверяет и обрабатывает все открытые сделки.
        """
        sell_order = self.order_service.create_sell_order(
            price, amount
        )
        sell_order.deal_id = deal_id
        logger.info(f"Create SELL Order: {sell_order}")
        return sell_order

    def process_open_deals(self):
        """
        Проверяет и обрабатывает все открытые сделки.
        """
        open_deals = self.deals_repo.get_open_deals()
        for deal in open_deals:
            if self.should_close_deal(deal):
                self.close_deal(deal)

    def close_deal(self, deal_id: int):
        """
        Закрывает сделку, меняя ее статус на CLOSED.
        """
        deal = self.get_deal_by_id(deal_id)
        if deal and deal.is_open():
            deal.close()
            self.deals_repo.save(deal)
            logger.info(f"Closed deal: {deal}")
        elif not deal:
            logger.warning(f"Попытка закрыть несуществующую сделку: {deal_id}")
        else:
            logger.info(f"Сделка {deal_id} уже закрыта, статус: {deal.status}")

    async def close_deal_if_completed(self, deal: Deal) -> bool:
        """
        Закрывает сделку если оба ордера исполнены.
        Возвращает True если сделка была закрыта.
        """
        # Проверяем статус ордеров
        if deal.buy_order:
            deal.buy_order = await self.order_service.get_order_status(deal.buy_order)
        if deal.sell_order:
            deal.sell_order = await self.order_service.get_order_status(deal.sell_order)
        
        # Если оба ордера исполнены - закрываем сделку естественно
        if (deal.buy_order and deal.buy_order.is_filled() and 
            deal.sell_order and deal.sell_order.is_filled()):
            
            # Рассчитываем прибыль
            buy_cost = deal.buy_order.calculate_total_cost_with_fees()
            sell_revenue = deal.sell_order.calculate_total_cost()
            profit = sell_revenue - buy_cost
            
            deal.close()
            self.deals_repo.save(deal)
            logger.info(f"✅ Deal completed naturally: {deal.deal_id}, profit: {profit:.4f} USDT")
            return True
        
        return False

    def should_close_deal(self, deal: Deal) -> bool:
        """
        Определяет, нужно ли закрывать сделку на основе бизнес-логики.
        """
        # Здесь может быть сложная логика с проверкой условий: времени, цен, индикаторов и т.п.
        return False  # Пример: возвращаем False, не закрываем автоматически

    def get_open_deals(self) -> List[Deal]:
        """
        Возвращает список всех открытых сделок.
        """
        return self.deals_repo.get_open_deals()

    def get_deal_by_id(self, deal_id: int) -> Optional[Deal]:
        """
        Возвращает сделку по идентификатору.
        """
        return self.deals_repo.get_by_id(deal_id)

    def force_close_all(self):
        """
        Принудительное закрытие всех открытых сделок.
        """
        for deal in self.get_open_deals():
            self.close_deal(deal)

```

### 📄 `src\domain\services\indicators\__init__.py`

```python

```

### 📄 `src\domain\services\indicators\cached_indicator_service.py`

```python
import time
from typing import Dict, List
import numpy as np
import talib
from talib import MA_Type
import logging

logger = logging.getLogger(__name__)

class CachedIndicatorService:
    def __init__(self):
        # Кеши разных уровней
        self.fast_cache = {}      # Каждый тик
        self.medium_cache = {}    # Каждые 10 тиков
        self.heavy_cache = {}     # Каждые 50 тиков

        # Счетчики обновлений
        self.last_medium_update = 0
        self.last_heavy_update = 0
        self.tick_count = 0

        # Буферы для инкрементальных вычислений
        self.sma_7_buffer = []
        self.sma_25_buffer = []
        self.price_sum_7 = 0
        self.price_sum_25 = 0

    def update_fast_indicators(self, price: float) -> Dict:
        """Быстрые индикаторы каждый тик (без TALIB)"""

        if not isinstance(price, (int, float)) or np.isnan(price):
            return self.fast_cache  # Вернуть предыдущие значения

        self.tick_count += 1

        # SMA-7 инкрементально
        self.sma_7_buffer.append(price)
        self.price_sum_7 += price

        if len(self.sma_7_buffer) > 7:
            removed = self.sma_7_buffer.pop(0)
            self.price_sum_7 -= removed

        sma_7 = self.price_sum_7 / len(self.sma_7_buffer) if self.sma_7_buffer else 0

        # SMA-25 инкрементально
        self.sma_25_buffer.append(price)
        self.price_sum_25 += price

        if len(self.sma_25_buffer) > 25:
            removed = self.sma_25_buffer.pop(0)
            self.price_sum_25 -= removed

        sma_25 = self.price_sum_25 / len(self.sma_25_buffer) if len(self.sma_25_buffer) >= 25 else 0

        self.fast_cache = {
            "price": price,
            "sma_7": round(sma_7, 8),
            "sma_25": round(sma_25, 8) if sma_25 > 0 else 0,
            "timestamp": int(time.time() * 1000)
        }

        return self.fast_cache

    def should_update_medium(self) -> bool:
        return self.tick_count - self.last_medium_update >= 10

    def should_update_heavy(self) -> bool:
        return self.tick_count - self.last_heavy_update >= 50

    def update_medium_indicators(self, price_history: List[float]) -> Dict:
        """Средние индикаторы каждые 10 тиков"""
        if len(price_history) < 30:
            return {}

        closes = np.array(price_history[-30:])  # Только последние 30

        try:
            rsi_5 = talib.RSI(closes, timeperiod=5)
            rsi_15 = talib.RSI(closes, timeperiod=15)

            self.medium_cache = {
                "rsi_5": round(float(rsi_5[-1]), 8) if len(rsi_5) > 0 and not np.isnan(rsi_5[-1]) else 0,
                "rsi_15": round(float(rsi_15[-1]), 8) if len(rsi_15) > 0 and not np.isnan(rsi_15[-1]) else 0,
            }

            self.last_medium_update = self.tick_count
            logger.info(
                f"🔄 Обновлен средний кеш на тике {self.tick_count}"
            )

        except Exception as e:
            logger.warning(f"⚠️ Ошибка в medium_indicators: {e}")

        return self.medium_cache

    def update_heavy_indicators(self, price_history: List[float]) -> Dict:
        """Тяжелые индикаторы каждые 50 тиков"""
        if len(price_history) < 50:
            return {}

        closes = np.array(price_history[-100:])  # Только последние 100

        try:
            # MACD
            macd, macdsignal, macdhist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)

            # SMA-99
            sma_75 = talib.MA(closes, timeperiod=75, matype=MA_Type.SMA)

            # Bollinger Bands
            upperband, middleband, lowerband = talib.BBANDS(closes, timeperiod=20, nbdevup=2, nbdevdn=2)

            self.heavy_cache = {
                "macd": round(float(macd[-1]), 8) if len(macd) > 0 and not np.isnan(macd[-1]) else 0,
                "signal": round(float(macdsignal[-1]), 8) if len(macdsignal) > 0 and not np.isnan(macdsignal[-1]) else 0,
                "histogram": round(float(macdhist[-1]), 8) if len(macdhist) > 0 and not np.isnan(macdhist[-1]) else 0,
                "sma_99": round(float(sma_75[-1]), 8) if len(sma_75) > 0 and not np.isnan(sma_75[-1]) else 0,
                "bb_upper": round(float(upperband[-1]), 8) if len(upperband) > 0 and not np.isnan(upperband[-1]) else 0,
                "bb_middle": round(float(middleband[-1]), 8) if len(middleband) > 0 and not np.isnan(middleband[-1]) else 0,
                "bb_lower": round(float(lowerband[-1]), 8) if len(lowerband) > 0 and not np.isnan(lowerband[-1]) else 0,
            }

            self.last_heavy_update = self.tick_count
            logger.info(
                f"🔥 Обновлен тяжелый кеш на тике {self.tick_count}"
            )

        except Exception as e:
            logger.warning(f"⚠️ Ошибка в heavy_indicators: {e}")

        return self.heavy_cache

    def get_all_cached_signals(self) -> Dict:
        """Возвращает все кешированные сигналы"""
        return {
            **self.fast_cache,
            **self.medium_cache,
            **self.heavy_cache
        }
```

### 📄 `src\domain\services\market_data\__init__.py`

```python

```

### 📄 `src\domain\services\market_data\market_analysis_service.py`

```python
from typing import List, Dict
import statistics


class MarketAnalysisService:
    """🔍 Сервис для анализа рыночных условий"""

    def __init__(self):
        self.analysis_window = 20

    def analyze_volatility(self, prices: List[float]) -> Dict:
        """Подробный анализ волатильности"""
        if len(prices) < self.analysis_window:
            return {"status": "insufficient_data", "message": "Недостаточно данных"}

        recent_prices = prices[-self.analysis_window:]

        # Вычисляем различные метрики волатильности
        price_changes = []
        for i in range(1, len(recent_prices)):
            change = (recent_prices[i] - recent_prices[i - 1]) / recent_prices[i - 1]
            price_changes.append(abs(change))

        avg_volatility = statistics.mean(price_changes) * 100
        max_volatility = max(price_changes) * 100
        volatility_std = statistics.stdev(price_changes) * 100 if len(price_changes) > 1 else 0

        # Классификация
        risk_level = self._classify_risk(avg_volatility)
        trading_recommendation = self._get_trading_recommendation(avg_volatility)

        return {
            "avg_volatility": round(avg_volatility, 3),
            "max_volatility": round(max_volatility, 3),
            "volatility_std": round(volatility_std, 3),
            "risk_level": risk_level,
            "trading_recommendation": trading_recommendation,
            "should_trade": 0.03 <= avg_volatility <= 0.12
        }

    def _classify_risk(self, volatility: float) -> str:
        """Классифицирует уровень риска"""
        if volatility > 0.15:
            return "🔥 ЭКСТРЕМАЛЬНЫЙ"
        elif volatility > 0.08:
            return "⚡ ВЫСОКИЙ"
        elif volatility > 0.03:
            return "📊 СРЕДНИЙ"
        else:
            return "😴 НИЗКИЙ"

    def _get_trading_recommendation(self, volatility: float) -> str:
        """Дает рекомендации по торговле"""
        if volatility > 0.15:
            return "❌ НЕ ТОРГОВАТЬ - слишком рискованно"
        elif volatility > 0.12:
            return "⚠️ ОСТОРОЖНО - высокий риск"
        elif volatility > 0.03:
            return "✅ МОЖНО ТОРГОВАТЬ"
        else:
            return "🟡 НИЗКАЯ АКТИВНОСТЬ - мало возможностей"

    def analyze_trend(self, prices: List[float], window: int = 10) -> Dict:
        """Анализ тренда"""
        if len(prices) < window:
            return {"status": "insufficient_data"}

        recent_prices = prices[-window:]
        first_price = recent_prices[0]
        last_price = recent_prices[-1]

        change_percent = (last_price - first_price) / first_price * 100

        # Считаем наклон тренда (линейная регрессия упрощенно)
        x_values = list(range(len(recent_prices)))
        slope = self._calculate_slope(x_values, recent_prices)

        trend_direction = "📈 ВОСХОДЯЩИЙ" if slope > 0 else "📉 НИСХОДЯЩИЙ" if slope < 0 else "➡️ БОКОВОЙ"

        return {
            "change_percent": round(change_percent, 2),
            "slope": round(slope, 6),
            "trend_direction": trend_direction,
            "strength": self._classify_trend_strength(abs(change_percent))
        }

    def _calculate_slope(self, x_values: List, y_values: List[float]) -> float:
        """Простой расчет наклона тренда"""
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope

    def _classify_trend_strength(self, change_percent: float) -> str:
        """Классифицирует силу тренда"""
        if change_percent > 2.0:
            return "🔥 СИЛЬНЫЙ"
        elif change_percent > 0.5:
            return "📊 УМЕРЕННЫЙ"
        else:
            return "😴 СЛАБЫЙ"

```

### 📄 `src\domain\services\market_data\orderbook_analyzer.py`

```python
# domain/services/orderbook_analyzer.py
import asyncio
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class OrderBookSignal(Enum):
    """Сигналы от анализа стакана"""
    STRONG_BUY = "strong_buy"
    WEAK_BUY = "weak_buy" 
    NEUTRAL = "neutral"
    WEAK_SELL = "weak_sell"
    STRONG_SELL = "strong_sell"
    REJECT = "reject"  # Отклонить сделку

@dataclass
class OrderBookMetrics:
    """Метрики стакана"""
    bid_ask_spread: float
    bid_volume: float
    ask_volume: float
    volume_imbalance: float  # % покупателей - продавцов
    liquidity_depth: float
    support_level: Optional[float]
    resistance_level: Optional[float]
    slippage_buy: float
    slippage_sell: float
    big_walls: List[Dict]
    signal: OrderBookSignal
    confidence: float  # 0-1

class OrderBookAnalyzer:
    """Анализатор биржевого стакана"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.min_volume_threshold = config.get('min_volume_threshold', 1000)
        self.big_wall_threshold = config.get('big_wall_threshold', 5000)
        self.max_spread_percent = config.get('max_spread_percent', 0.5)
        self.min_liquidity_depth = config.get('min_liquidity_depth', 10)
        self.typical_order_size = config.get('typical_order_size', 10)  # USDT
        
    async def get_orderbook_stream(self, exchange, symbol: str):
        """Получение потока данных стакана через вебсокет"""
        try:
            while True:
                orderbook = await exchange.watch_order_book(symbol)
                metrics = self.analyze_orderbook(orderbook)
                yield metrics
                await asyncio.sleep(0.1)  # Небольшая задержка
                
        except Exception as e:
            logger.error(f"Ошибка получения стакана: {e}")
            
    def analyze_orderbook(self, orderbook: Dict) -> OrderBookMetrics:
        """Полный анализ стакана"""
        bids = orderbook['bids']
        asks = orderbook['asks']
        
        if not bids or not asks:
            return self._create_reject_metrics("Пустой стакан")
            
        # Базовые метрики
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        spread = best_ask - best_bid
        spread_percent = (spread / best_bid) * 100
        
        # Объемы
        bid_volume = sum([bid[1] for bid in bids[:self.min_liquidity_depth]])
        ask_volume = sum([ask[1] for ask in asks[:self.min_liquidity_depth]])
        total_volume = bid_volume + ask_volume
        volume_imbalance = ((bid_volume - ask_volume) / total_volume) * 100 if total_volume > 0 else 0
        
        # Анализ ликвидности
        liquidity_depth = self._calculate_liquidity_depth(bids, asks, best_bid)
        
        # 🔧 FIX: Поддержка и сопротивление с проверкой дистанции
        support_level = self._find_support_level(bids, best_bid)
        resistance_level = self._find_resistance_level(asks, best_ask)
        
        # Слиппедж
        slippage_buy = self._calculate_slippage(asks, 'buy')
        slippage_sell = self._calculate_slippage(bids, 'sell')
        
        # Большие стены
        big_walls = self._find_big_walls(bids, asks)
        
        # Генерация сигнала
        signal, confidence = self._generate_signal(
            spread_percent, volume_imbalance, liquidity_depth,
            slippage_buy, slippage_sell, big_walls
        )
        
        return OrderBookMetrics(
            bid_ask_spread=spread_percent,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            volume_imbalance=volume_imbalance,
            liquidity_depth=liquidity_depth,
            support_level=support_level,
            resistance_level=resistance_level,
            slippage_buy=slippage_buy,
            slippage_sell=slippage_sell,
            big_walls=big_walls,
            signal=signal,
            confidence=confidence
        )
    
    def _calculate_liquidity_depth(self, bids: List, asks: List, mid_price: float) -> float:
        """Расчет глубины ликвидности в % от цены"""
        total_volume = 0
        price_range = 0
        
        # Анализ бидов
        for bid in bids:
            if bid[0] > mid_price * 0.95:  # В пределах 5% от цены
                total_volume += bid[1]
                price_range = max(price_range, abs(bid[0] - mid_price))
                
        # Анализ асков
        for ask in asks:
            if ask[0] < mid_price * 1.05:  # В пределах 5% от цены
                total_volume += ask[1]
                price_range = max(price_range, abs(ask[0] - mid_price))
                
        return total_volume / max(price_range, 0.001)
    
    def _find_support_level(self, bids: List, mid_price: float, max_pct: float = 2.0) -> Optional[float]:
        """🔧 FIX: Поиск уровня поддержки с фильтром расстояния"""
        if len(bids) < 5:
            return None
            
        # Ищем самый большой объем в бидах
        support = max(bids[:20], key=lambda b: b[1])[0]  # самая толстая стена
        
        # 🔧 FIX: Проверяем что стена не слишком далеко
        if abs(support - mid_price) / mid_price * 100 > max_pct:
            return None  # стена слишком далеко

        return support
    
    def _find_resistance_level(self, asks: List, mid_price: float, max_pct: float = 2.0) -> Optional[float]:
        """🔧 FIX: Поиск уровня сопротивления с фильтром расстояния"""
        if len(asks) < 5:
            return None
            
        # Ищем самый большой объем в асках
        resistance = max(asks[:20], key=lambda a: a[1])[0]  # самая толстая стена
        
        # 🔧 FIX: Проверяем что стена не слишком далеко
        if abs(resistance - mid_price) / mid_price * 100 > max_pct:
            return None  # стена слишком далеко

        return resistance
    
    def _calculate_slippage(self, orders: List, side: str) -> float:
        """Расчет слиппеджа для объема сделки.

        В исходной версии метода средняя цена вычислялась неверно: при
        суммировании использовалось ``price * order_value`` (где
        ``order_value = price * volume``), что приводило к квадрированию цены и
        некорректному результату. Теперь мы правильно учитываем объём в монете
        и стоимость в USDT, рассчитывая средневзвешенную цену покупки/продажи.
        """

        volume_to_execute = self.typical_order_size  # Объём в USDT

        cumulative_value = 0.0       # Сколько USDT уже исполнено
        total_volume_coin = 0.0      # Сколько монет куплено/продано
        weighted_sum_price = 0.0     # Σ(price * volume_coin)

        for price, volume in orders:
            order_value = price * volume  # Стоимость ордера в USDT

            if cumulative_value + order_value >= volume_to_execute:
                # Частичное исполнение последнего уровня стакана
                remaining_value = volume_to_execute - cumulative_value
                executed_volume = remaining_value / price
                weighted_sum_price += price * executed_volume
                total_volume_coin += executed_volume
                cumulative_value += remaining_value
                break
            else:
                # Полное исполнение уровня стакана
                weighted_sum_price += price * volume
                total_volume_coin += volume
                cumulative_value += order_value

        if total_volume_coin > 0:
            avg_price = weighted_sum_price / total_volume_coin
            best_price = orders[0][0]
            return abs((avg_price - best_price) / best_price) * 100

        # Недостаточно ликвидности для исполнения объёма
        return 999
    
    def _find_big_walls(self, bids: List, asks: List) -> List[Dict]:
        """Поиск больших стен в стакане"""
        big_walls = []
        
        # Анализ бидов
        for bid in bids:
            if bid[1] > self.big_wall_threshold:
                big_walls.append({
                    'side': 'bid',
                    'price': bid[0],
                    'volume': bid[1],
                    'type': 'support'
                })
                
        # Анализ асков
        for ask in asks:
            if ask[1] > self.big_wall_threshold:
                big_walls.append({
                    'side': 'ask',
                    'price': ask[0],
                    'volume': ask[1],
                    'type': 'resistance'
                })
                
        return big_walls
    
    def _generate_signal(self, spread_percent: float, volume_imbalance: float, 
                        liquidity_depth: float, slippage_buy: float, 
                        slippage_sell: float, big_walls: List) -> Tuple[OrderBookSignal, float]:
        """Генерация сигнала на основе всех метрик"""
        
        # Проверки на отклонение сделки
        if spread_percent > self.max_spread_percent:
            return OrderBookSignal.REJECT, 0.9
            
        if slippage_buy > 2.0 or slippage_sell > 2.0:
            return OrderBookSignal.REJECT, 0.8
            
        if liquidity_depth < self.min_liquidity_depth:
            return OrderBookSignal.REJECT, 0.7
        
        # Подсчет очков для сигнала
        score = 0
        confidence = 0.5
        
        # Дисбаланс объемов
        if volume_imbalance > 20:  # Больше покупателей
            score += 2
            confidence += 0.2
        elif volume_imbalance > 10:
            score += 1
            confidence += 0.1
        elif volume_imbalance < -20:  # Больше продавцов
            score -= 2
            confidence += 0.2
        elif volume_imbalance < -10:
            score -= 1
            confidence += 0.1
            
        # Анализ больших стен
        resistance_walls = [w for w in big_walls if w['type'] == 'resistance']
        support_walls = [w for w in big_walls if w['type'] == 'support']
        
        if len(support_walls) > len(resistance_walls):
            score += 1
            confidence += 0.1
        elif len(resistance_walls) > len(support_walls):
            score -= 1
            confidence += 0.1
            
        # Ликвидность
        if liquidity_depth > self.min_liquidity_depth * 2:
            score += 1
            confidence += 0.1
            
        # Слиппедж
        if slippage_buy < 0.1 and slippage_sell < 0.1:
            score += 1
            confidence += 0.1
            
        # Преобразование в сигнал
        if score >= 3:
            return OrderBookSignal.STRONG_BUY, min(confidence, 0.95)
        elif score >= 1:
            return OrderBookSignal.WEAK_BUY, min(confidence, 0.8)
        elif score <= -3:
            return OrderBookSignal.STRONG_SELL, min(confidence, 0.95)
        elif score <= -1:
            return OrderBookSignal.WEAK_SELL, min(confidence, 0.8)
        else:
            return OrderBookSignal.NEUTRAL, confidence
    
    def _create_reject_metrics(self, reason: str) -> OrderBookMetrics:
        """Создание метрик с сигналом отклонения"""
        return OrderBookMetrics(
            bid_ask_spread=999,
            bid_volume=0,
            ask_volume=0,
            volume_imbalance=0,
            liquidity_depth=0,
            support_level=None,
            resistance_level=None,
            slippage_buy=999,
            slippage_sell=999,
            big_walls=[],
            signal=OrderBookSignal.REJECT,
            confidence=0.9
        )

```

### 📄 `src\domain\services\market_data\orderbook_service.py`

```python
# domain/services/orderbook_service.py
import asyncio
import logging
from typing import Optional
from .orderbook_analyzer import OrderBookAnalyzer, OrderBookMetrics, OrderBookSignal

logger = logging.getLogger(__name__)

class OrderBookService:
    """Сервис для мониторинга стакана в фоновом режиме"""

    def __init__(self, orderbook_analyzer: OrderBookAnalyzer):
        self.orderbook_analyzer = orderbook_analyzer
        self.latest_metrics: Optional[OrderBookMetrics] = None
        self.is_monitoring = False
        self._monitoring_task = None

    async def start_monitoring(self, exchange, symbol: str):
        """Запуск мониторинга стакана в фоновом режиме"""
        if self.is_monitoring:
            logger.warning("Мониторинг стакана уже запущен")
            return

        self.is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitor_orderbook(exchange, symbol))
        logger.info(f"🔍 Запущен мониторинг стакана для {symbol}")

    async def stop_monitoring(self):
        """Остановка мониторинга стакана"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Мониторинг стакана остановлен")

    async def _monitor_orderbook(self, exchange, symbol: str):
        """Фоновый мониторинг стакана"""
        try:
            async for metrics in self.orderbook_analyzer.get_orderbook_stream(exchange, symbol):
                if not self.is_monitoring:
                    break

                self.latest_metrics = metrics
                await asyncio.sleep(0.1)  # Небольшая пауза

        except asyncio.CancelledError:
            logger.info("Мониторинг стакана отменен")
        except Exception as e:
            logger.error(f"Ошибка в мониторинге стакана: {e}")
            self.is_monitoring = False

    def get_latest_metrics(self) -> Optional[OrderBookMetrics]:
        """Получение последних метрик стакана"""
        return self.latest_metrics

    async def get_current_metrics(self, exchange, symbol: str) -> Optional[OrderBookMetrics]:
        """Получение текущих метрик стакана (разовый запрос)"""
        try:
            orderbook = await exchange.fetch_order_book(symbol)
            return self.orderbook_analyzer.analyze_orderbook(orderbook)
        except Exception as e:
            logger.error(f"Ошибка получения стакана: {e}")
            return None

    def is_orderbook_healthy(self) -> bool:
        """Проверка здоровья стакана"""
        if not self.latest_metrics:
            return False

        return (
                self.latest_metrics.signal != OrderBookSignal.REJECT and
                self.latest_metrics.bid_ask_spread < self.orderbook_analyzer.max_spread_percent and
                self.latest_metrics.slippage_buy < 2.0
        )

```

### 📄 `src\domain\services\market_data\ticker_service.py`

```python
import math
from decimal import Decimal, ROUND_DOWN, ROUND_UP, ROUND_HALF_UP
from typing import Dict, List, Optional

from domain.entities.currency_pair import CurrencyPair
from domain.entities.ticker import Ticker
from domain.services.indicators.cached_indicator_service import CachedIndicatorService
from domain.services.utils.decimal_rounding_service import DecimalRoundingService
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository


class TickerService:
    def __init__(self, repository: InMemoryTickerRepository):
        self.repository = repository
        self.cached_indicators = CachedIndicatorService()
        self.price_history_cache = []
        self.volatility_window = 20

    async def process_ticker(self, data: Dict):
        ticker = Ticker(data)
        current_price = float(data.get('close', 0))
        self.price_history_cache.append(current_price)
        if len(self.price_history_cache) > 200:
            self.price_history_cache.pop(0)

        self.cached_indicators.update_fast_indicators(current_price)

        if self.cached_indicators.should_update_medium():
            self.cached_indicators.update_medium_indicators(self.price_history_cache)

        if self.cached_indicators.should_update_heavy():
            self.cached_indicators.update_heavy_indicators(self.price_history_cache)
        
        all_signals = self.cached_indicators.get_all_cached_signals()
        ticker.update_signals(all_signals)
        self.repository.save(ticker)

    async def get_signal(self) -> str:
        if len(self.repository.tickers) < 50:
            return "HOLD"
        last_ticker = self.repository.tickers[-1]
        if not last_ticker.signals:
            return "HOLD"

        macd = last_ticker.signals.get('macd', 0)
        signal = last_ticker.signals.get('signal', 0)
        hist = last_ticker.signals.get('histogram', 0)
        sma_7 = last_ticker.signals.get('sma_7', 0)
        sma_25 = last_ticker.signals.get('sma_25', 0)

        if macd > signal and hist > 0 and sma_7 > sma_25:
            return "BUY"
        else:
            return "HOLD"

    def calculate_strategy(
            self,
            buy_price: float,
            budget: float,
            currency_pair: CurrencyPair,
            profit_percent: float
    ):
        """
        Рассчитывает сделку, используя `DecimalRoundingService` и данные о
        лимитах и точности из объекта `currency_pair`.
        """
        # 1. Получаем правила с биржи (из объекта currency_pair)
        # Получаем шаг цены и количества (tick size / step size)
        price_step = Decimal(str(currency_pair.precision.get('price', '0.000001')))
        amount_step = Decimal(str(currency_pair.precision.get('amount', '0.0001')))

        # ВЫЧИСЛЯЕМ КОЛИЧЕСТВО ЗНАКОВ ПОСЛЕ ЗАПЯТОЙ ИЗ ШАГА
        # Это ключевое исправление: мы не используем 0.01 как количество знаков, а вычисляем его.
        price_precision = int(price_step.normalize().as_tuple().exponent * -1)
        amount_precision = int(amount_step.normalize().as_tuple().exponent * -1)

        min_notional = Decimal(str(currency_pair.limits.get('cost', {}).get('min', 10.0)))

        # 2. Конвертируем все в Decimal для точности
        buy_price_dec = Decimal(str(buy_price))
        budget_dec = Decimal(str(budget))
        # Используем комиссии тейкера, так как мы исполняем ордера по рынку
        buy_fee_rate = Decimal(str(currency_pair.taker_fee))
        sell_fee_rate = Decimal(str(currency_pair.taker_fee))
        profit_dec = Decimal(str(profit_percent))

        # 3. Проверка на минимальную сумму ордера
        if budget_dec < min_notional:
            return {"comment": f"❌ Бюджет ({budget_dec}) меньше минимально допустимого ({min_notional})"}

        # 4. Расчеты с использованием DecimalRoundingService
        # Сколько монет мы можем купить на наш бюджет
        coins_to_buy_raw = budget_dec / buy_price_dec
        # КРИТИЧЕСКИ ВАЖНО: округляем ВВЕРХ чтобы не потерять монеты из-за комиссий!
        coins_to_buy = DecimalRoundingService.ceil_to_precision(coins_to_buy_raw, amount_precision)

        # Комиссия вычитается из ПОЛУЧЕННОГО количества монет
        coins_after_buy_fee = coins_to_buy * (1 - buy_fee_rate)

        # Цена продажи, которая покрывает обе комиссии и дает желаемую прибыль
        # (Цена покупки * (1 + %профита)) / (1 - %комиссии_продажи)
        sell_price_raw = buy_price_dec * (1 + profit_dec) / (1 - sell_fee_rate)
        sell_price = DecimalRoundingService.round_to_precision(sell_price_raw, price_precision)
        
        # Что останется для продажи после уплаты комиссии (которая берется в том же активе)
        coins_to_sell = DecimalRoundingService.floor_to_precision(
            coins_after_buy_fee,
            amount_precision
        )

        # 5. Финальные проверки
        total_cost = coins_to_buy * buy_price_dec
        if total_cost < min_notional:
             return {"comment": f"❌ Итоговая сумма ордера ({total_cost:.2f}) меньше минимально допустимой ({min_notional})"}

        final_revenue = coins_to_sell * sell_price
        net_profit = final_revenue - total_cost

        # 10) Возвращаем результат
        return (
            buy_price_dec,
            coins_to_buy,
            sell_price,
            coins_to_sell,
            {
                "comment": "✅ Сделка возможна.",
                "net_profit": f"{net_profit:.4f} USDT"
            }
        )
```

### 📄 `src\domain\services\orders\__init__.py`

```python

```

### 📄 `src\domain\services\orders\buy_order_monitor.py`

```python
# domain/services/buy_order_monitor.py.new
import asyncio
import logging
import time
from typing import List, Optional
from domain.entities.order import Order
from domain.services.orders.order_service import OrderService
from domain.services.deals.deal_service import DealService
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

logger = logging.getLogger(__name__)

class BuyOrderMonitor:
    """
    🕒 Простой мониторинг протухших BUY ордеров
    
    Проверяет только BUY ордера на:
    - Время жизни (по умолчанию 15 минут)
    - Отклонение цены от рынка (по умолчанию 3%)
    
    При превышении лимитов - отменяет и пересоздает ордер по новой цене
    """

    def __init__(
        self,
        order_service: OrderService,
        deal_service: DealService, # ❗️ ДОБАВЛЕНО
        exchange_connector: CcxtExchangeConnector,
        max_age_minutes: float = 15.0,
        max_price_deviation_percent: float = 3.0,
        check_interval_seconds: int = 60
    ):
        self.order_service = order_service
        self.deal_service = deal_service # ❗️ ДОБАВЛЕНО
        self.exchange = exchange_connector
        self.max_age_minutes = max_age_minutes
        self.max_price_deviation_percent = max_price_deviation_percent
        self.check_interval_seconds = check_interval_seconds
        
        self.running = False
        self.stats = {
            'checks_performed': 0,
            'stale_orders_found': 0,
            'orders_cancelled': 0,
            'orders_recreated': 0
        }

    async def start_monitoring(self):
        """Запуск мониторинга в фоне"""
        if self.running:
            logger.warning("⚠️ BuyOrderMonitor already running")
            return
            
        self.running = True
        logger.info(f"🕒 Запуск мониторинга BUY ордеров (проверка каждые {self.check_interval_seconds}с)")
        
        while self.running:
            try:
                await self.check_stale_buy_orders()
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                logger.error(f"❌ Ошибка в мониторинге BUY ордеров: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке

    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("🔴 Мониторинг BUY ордеров остановлен")

    async def check_stale_buy_orders(self):
        """Проверка всех открытых BUY ордеров на протухание"""
        try:
            # Получаем все открытые ордера
            open_orders = self.order_service.get_open_orders()
            
            # Фильтруем только BUY ордера
            buy_orders = [order for order in open_orders if order.side == Order.SIDE_BUY]
            
            if not buy_orders:
                return
                
            self.stats['checks_performed'] += 1
            
            logger.debug(f"🔍 Проверяем {len(buy_orders)} открытых BUY ордеров")
            
            for order in buy_orders:
                is_stale = await self._is_order_stale(order)
                if is_stale:
                    await self._handle_stale_buy_order(order)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка проверки BUY ордеров: {e}")

    async def _is_order_stale(self, order: Order) -> bool:
        """Проверяет протух ли BUY ордер"""
        try:
            # 1. Проверка возраста
            current_time = int(time.time() * 1000)
            age_minutes = (current_time - order.created_at) / 1000 / 60
            
            if age_minutes > self.max_age_minutes:
                logger.info(f"🕒 BUY ордер {order.order_id} протух по времени: {age_minutes:.1f} мин")
                return True
            
            # 2. Проверка отклонения цены
            ticker = await self.exchange.fetch_ticker(order.symbol)
            current_price = float(ticker['last'])
            
            # Для BUY: если рынок ушел выше нашей цены
            price_deviation = ((current_price - order.price) / order.price) * 100
            
            if price_deviation > self.max_price_deviation_percent:
                logger.info(f"📈 BUY ордер {order.order_id} протух по цене: рынок {current_price}, ордер {order.price} (+{price_deviation:.1f}%)")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки ордера {order.order_id}: {e}")
            return False

    async def _handle_stale_buy_order(self, order: Order):
        """Обработка протухшего BUY ордера: отмена + пересоздание + обновление связанного SELL."""
        try:
            self.stats['stale_orders_found'] += 1
            logger.warning(f"🚨 Обрабатываем протухший BUY ордер {order.order_id} для сделки {order.deal_id}")

            # 1. Отменяем старый BUY ордер
            cancel_success = await self.order_service.cancel_order(order)
            if not cancel_success:
                logger.error(f"❌ Не удалось отменить BUY ордер {order.order_id}")
                return
            self.stats['orders_cancelled'] += 1
            logger.info(f"✅ BUY ордер {order.order_id} отменен")

            # 2. Пересоздаем BUY ордер по новой цене
            new_buy_order = await self._recreate_buy_order(order)
            if not new_buy_order:
                logger.error(f"❌ Не удалось пересоздать BUY ордер для сделки {order.deal_id}")
                return
            self.stats['orders_recreated'] += 1
            logger.info(f"✅ BUY ордер пересоздан: {order.order_id} -> {new_buy_order.order_id} (Exchange ID: {new_buy_order.exchange_id})")

            # 3. Обновляем сделку, привязывая к ней новый BUY ордер
            deal = self.deal_service.get_deal_by_id(order.deal_id)
            if not deal:
                logger.error(f"Критическая ошибка: не найдена сделка {order.deal_id} для обновления!")
                return
            
            deal.update_buy_order(new_buy_order)
            self.deal_service.deals_repo.save(deal)
            logger.info(f"✅ Сделка {deal.deal_id} обновлена новым BUY ордером {new_buy_order.order_id}")

            # 4. Находим и обновляем связанный PENDING SELL ордер
            await self._update_related_sell_order(deal, new_buy_order)

        except Exception as e:
            logger.error(f"❌ Ошибка обработки протухшего BUY ордера {order.order_id}: {e}", exc_info=True)

    async def _recreate_buy_order(self, old_order: Order) -> Optional[Order]:
        """Пересоздание BUY ордера по текущей рыночной цене"""
        try:
            ticker = await self.exchange.fetch_ticker(old_order.symbol)
            current_price = float(ticker['last'])
            new_price = current_price * 0.999

            logger.info(f"🔄 Пересоздаем BUY ордер: старая цена {old_order.price}, новая цена {new_price}")

            execution_result = await self.order_service.create_and_place_buy_order(
                symbol=old_order.symbol,
                amount=old_order.amount,
                price=new_price,
                deal_id=old_order.deal_id,
                order_type=old_order.order_type
            )
            
            return execution_result.order if execution_result.success else None
        except Exception as e:
            logger.error(f"❌ Ошибка пересоздания BUY ордера: {e}", exc_info=True)
            return None

    async def _update_related_sell_order(self, deal, new_buy_order: Order):
        """Находит связанный PENDING SELL и обновляет его параметры."""
        try:
            pending_sell = self.order_service.get_order_by_id(deal.sell_order.order_id)
            
            if not pending_sell or not pending_sell.is_pending():
                logger.warning(f"Не найден PENDING SELL для сделки {deal.deal_id}. Нечего обновлять.")
                return

            # Пересчитываем цену и количество для SELL на основе нового BUY
            # (Эта логика должна быть идентична той, что в TickerService/Strategy)
            profit_markup = deal.currency_pair.profit_markup
            new_sell_price = new_buy_order.price * (1 + profit_markup)
            
            # TODO: Пересчет количества, если есть комиссия в базовой валюте
            new_sell_amount = new_buy_order.amount 

            logger.info(f"🔄 Обновляем PENDING SELL ордер {pending_sell.order_id}: цена {pending_sell.price} -> {new_sell_price}, кол-во {pending_sell.amount} -> {new_sell_amount}")

            pending_sell.price = new_sell_price
            pending_sell.amount = new_sell_amount
            
            self.order_service.orders_repo.save(pending_sell)
            logger.info(f"✅ PENDING SELL ордер {pending_sell.order_id} обновлен.")

        except Exception as e:
            logger.error(f"❌ Ошибка обновления связанного SELL ордера для сделки {deal.deal_id}: {e}", exc_info=True)

    def get_statistics(self) -> dict:
        """Получение статистики работы мониторинга"""
        return {
            'running': self.running,
            'max_age_minutes': self.max_age_minutes,
            'max_price_deviation_percent': self.max_price_deviation_percent,
            'check_interval_seconds': self.check_interval_seconds,
            **self.stats
        }

    def configure(
        self,
        max_age_minutes: float = None,
        max_price_deviation_percent: float = None,
        check_interval_seconds: int = None
    ):
        """Изменение настроек мониторинга"""
        if max_age_minutes is not None:
            self.max_age_minutes = max_age_minutes
        if max_price_deviation_percent is not None:
            self.max_price_deviation_percent = max_price_deviation_percent
        if check_interval_seconds is not None:
            self.check_interval_seconds = check_interval_seconds
            
        logger.info(f"⚙️ Настройки мониторинга обновлены: {self.get_statistics()}")

```

### 📄 `src\domain\services\orders\filled_buy_order_handler.py`

```python
# src/domain/services/orders/filled_buy_order_handler.py
import asyncio
import logging
from typing import List

from domain.entities.order import Order
from domain.services.orders.order_service import OrderService
from domain.services.deals.deal_service import DealService

logger = logging.getLogger(__name__)

class FilledBuyOrderHandler:
    """
    Сервис, который отслеживает исполненные BUY ордера и размещает
    соответствующие им PENDING SELL ордера на биржу.
    """

    def __init__(self, order_service: OrderService, deal_service: DealService):
        self.order_service = order_service
        self.deal_service = deal_service
        self.processed_buy_orders = set()

    async def check_and_place_sell_orders(self):
        """
        Основной метод, который ищет исполненные BUY ордера и размещает
        связанные с ними SELL ордера.
        """
        try:
            all_orders = self.order_service.orders_repo.get_all()
            filled_buy_orders = [
                order for order in all_orders
                if order.side == Order.SIDE_BUY
                and order.is_filled()
                and order.order_id not in self.processed_buy_orders
            ]

            if not filled_buy_orders:
                return

            logger.info(f"Обнаружено {len(filled_buy_orders)} новых исполненных BUY ордеров. Обработка...")

            for buy_order in filled_buy_orders:
                await self._process_filled_buy_order(buy_order)

        except Exception as e:
            logger.error(f"Ошибка в FilledBuyOrderHandler: {e}", exc_info=True)

    async def _process_filled_buy_order(self, buy_order: Order):
        """Обрабатывает один исполненный BUY ордер."""
        try:
            deal = self.deal_service.get_deal_by_id(buy_order.deal_id)
            if not deal:
                logger.warning(f"Не найдена сделка для исполненного BUY ордера {buy_order.order_id}")
                self.processed_buy_orders.add(buy_order.order_id)
                return

            # Ищем связанный PENDING SELL ордер
            sell_order = self.order_service.get_order_by_id(deal.sell_order.order_id)
            
            if not sell_order or not sell_order.is_pending():
                logger.warning(f"Не найден PENDING SELL ордер для сделки {deal.deal_id}. Возможно, уже размещен.")
                self.processed_buy_orders.add(buy_order.order_id)
                return

            logger.info(f"Найден PENDING SELL ордер {sell_order.order_id} для сделки {deal.deal_id}. Размещаем на бирже...")

            # Размещаем SELL ордер на бирже
            execution_result = await self.order_service.place_existing_order(sell_order)

            if execution_result.success:
                logger.info(f"SELL ордер {sell_order.order_id} успешно размещен на бирже. Exchange ID: {execution_result.order.exchange_id}")
            else:
                logger.error(f"Не удалось разместить SELL ордер {sell_order.order_id}: {execution_result.error_message}")

            # Помечаем BUY ордер как обработанный, чтобы не трогать его снова
            self.processed_buy_orders.add(buy_order.order_id)

        except Exception as e:
            logger.error(f"Ошибка при обработке исполненного BUY ордера {buy_order.order_id}: {e}", exc_info=True)
            # Не добавляем в processed, чтобы повторить попытку

```

### 📄 `src\domain\services\orders\order_execution_service.py`

```python
# domain/services/order_execution_service.py.new - ГЛАВНЫЙ сервис Issue #7
import asyncio
import logging
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from domain.entities.order import Order, OrderExecutionResult
from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from domain.services.orders.order_service import OrderService
from domain.services.deals.deal_service import DealService
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

logger = logging.getLogger(__name__)

@dataclass
class TradingContext:
    """Контекст для выполнения торговых операций"""
    currency_pair: CurrencyPair
    current_price: float
    budget: float
    strategy_result: Any  # Результат расчета стратегии
    deal: Optional[Deal] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ExecutionReport:
    """Отчет о выполнении торговой операции"""
    success: bool
    deal_id: Optional[int] = None
    buy_order: Optional[Order] = None
    sell_order: Optional[Order] = None
    total_cost: float = 0.0
    expected_profit: float = 0.0
    fees: float = 0.0
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = None

class OrderExecutionService:
    """
    🚀 ГЛАВНЫЙ сервис для выполнения торговых операций (Issue #7)
    
    Это высокоуровневый сервис, который:
    - Координирует создание сделок и ордеров
    - Выполняет полные торговые стратегии
    - Управляет рисками и валидацией
    - Обеспечивает реальное размещение ордеров на бирже
    - Мониторит исполнение и состояние ордеров
    """

    def __init__(
        self,
        order_service: OrderService,
        deal_service: DealService,
        exchange_connector: CcxtExchangeConnector
    ):
        self.order_service = order_service
        self.deal_service = deal_service
        self.exchange_connector = exchange_connector
        
        # Статистика
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_volume': 0.0,
            'total_fees': 0.0,
            'average_execution_time_ms': 0.0
        }
        
        # Настройки выполнения
        self.max_execution_time_sec = 30.0  # Максимальное время выполнения
        self.enable_risk_checks = True
        self.enable_balance_checks = True
        self.enable_slippage_protection = True

    # 🚀 ГЛАВНЫЙ МЕТОД ВЫПОЛНЕНИЯ ТОРГОВОЙ СТРАТЕГИИ

    async def execute_trading_strategy(
        self,
        currency_pair: CurrencyPair,
        strategy_result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutionReport:
        """
        🎯 ГЛАВНЫЙ метод выполнения торговой стратегии
        
        Принимает результат расчета стратегии и выполняет полную торговую операцию:
        1. Создает сделку
        2. Размещает BUY ордер на бирже
        3. Размещает SELL ордер на бирже
        4. Связывает все компоненты
        5. Возвращает детальный отчет
        
        Args:
            currency_pair: Торговая пара
            strategy_result: Результат расчета стратегии (из ticker_service)
            metadata: Дополнительная информация
            
        Returns:
            ExecutionReport с результатами выполнения
        """
        start_time = datetime.now()
        execution_id = f"exec_{int(start_time.timestamp() * 1000)}"
        
        logger.info(f"🚀 [{execution_id}] Starting strategy execution for {currency_pair.symbol}")
        
        try:
            # 1. Валидация входных данных
            validation_result = self._validate_strategy_input(currency_pair, strategy_result)
            if not validation_result[0]:
                return ExecutionReport(
                    success=False,
                    error_message=f"Input validation failed: {validation_result[1]}"
                )
            
            # 2. Парсинг результатов стратегии
            strategy_data = self._parse_strategy_result(strategy_result)
            if not strategy_data:
                return ExecutionReport(
                    success=False,
                    error_message="Failed to parse strategy result"
                )
            
            # 3. Создание контекста торговли
            context = TradingContext(
                currency_pair=currency_pair,
                current_price=strategy_data['buy_price'],
                budget=currency_pair.deal_quota,
                strategy_result=strategy_result,
                metadata=metadata or {}
            )
            
            # 4. Pre-execution проверки
            pre_check_result = await self._perform_pre_execution_checks(context, strategy_data)
            if not pre_check_result[0]:
                return ExecutionReport(
                    success=False,
                    error_message=f"Pre-execution checks failed: {pre_check_result[1]}",
                    warnings=pre_check_result[2] if len(pre_check_result) > 2 else []
                )
            
            # 5. Создание сделки
            deal = self.deal_service.create_new_deal(currency_pair)
            context.deal = deal
            
            logger.info(f"✅ [{execution_id}] Deal #{deal.deal_id} created")
            
            # 6. Выполнение BUY ордера
            buy_result = await self._execute_buy_order(context, strategy_data)
            if not buy_result.success:
                return ExecutionReport(
                    success=False,
                    deal_id=deal.deal_id,
                    error_message=f"BUY order failed: {buy_result.error_message}"
                )
            
            buy_order = buy_result.order
            logger.info(f"✅ [{execution_id}] BUY order placed: {buy_order.exchange_id}")
            
            # 7. Создание ЛОКАЛЬНОГО SELL ордера (без размещения на бирже)
            sell_result = await self._create_local_sell_order(context, strategy_data)
            if not sell_result.success:
                # Если не удалось даже локально создать SELL, отменяем BUY
                await self._emergency_cancel_buy_order(buy_order)
                return ExecutionReport(
                    success=False,
                    deal_id=deal.deal_id,
                    buy_order=buy_order,
                    error_message=f"Local SELL order creation failed: {sell_result.error_message}"
                )
            
            sell_order = sell_result.order
            logger.info(f"✅ [{execution_id}] Local SELL order created with status PENDING.")
            
            # 8. Связывание ордеров со сделкой
            deal.attach_orders(buy_order, sell_order)
            self.deal_service.deals_repo.save(deal)

            # 9. Расчет финансовых пока��ателей (на основе ожидаемых данных)
            total_cost = buy_order.amount * buy_order.price
            expected_profit = (sell_order.amount * sell_order.price) - total_cost
            
            # 10. Обновление статистики
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_execution_stats(True, total_cost, 0, execution_time)
            
            # 11. Формирование отчета
            report = ExecutionReport(
                success=True,
                deal_id=deal.deal_id,
                buy_order=buy_order,
                sell_order=sell_order,
                total_cost=total_cost,
                expected_profit=expected_profit,
                fees=0, # Комиссии будут известны после исполнения
                execution_time_ms=execution_time
            )
            
            logger.info(f"🎉 [{execution_id}] Strategy executed successfully! BUY order placed, SELL order is PENDING.")
            logger.info(f"   💰 Cost: {total_cost:.4f} USDT")
            logger.info(f"   📈 Expected profit: {expected_profit:.4f} USDT")
            logger.info(f"   ⏱️ Execution time: {execution_time:.1f}ms")
            
            return report
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_execution_stats(False, 0.0, 0.0, execution_time)
            
            logger.error(f"❌ [{execution_id}] Strategy execution failed: {e}")
            return ExecutionReport(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                execution_time_ms=execution_time
            )

    # 🔧 ВНУТРЕННИЕ МЕТОДЫ ВЫПОЛНЕНИЯ

    def _validate_strategy_input(
        self, 
        currency_pair: CurrencyPair, 
        strategy_result: Any
    ) -> Tuple[bool, str]:
        """Валидация входных данных для стратегии"""
        try:
            if not currency_pair:
                return False, "Currency pair is required"
            
            if not currency_pair.symbol:
                return False, "Currency pair symbol is required"
            
            if currency_pair.deal_quota <= 0:
                return False, "Deal quota must be positive"
            
            if not strategy_result:
                return False, "Strategy result is required"
            
            # Проверяем формат strategy_result
            if isinstance(strategy_result, dict) and "comment" in strategy_result:
                return False, f"Strategy calculation error: {strategy_result['comment']}"
            
            if not isinstance(strategy_result, (tuple, list)) or len(strategy_result) < 5:
                return False, "Invalid strategy result format"
            
            return True, "Valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _parse_strategy_result(self, strategy_result: Any) -> Optional[Dict[str, Any]]:
        """Парсинг результата стратегии в удобный формат"""
        try:
            if isinstance(strategy_result, dict) and "comment" in strategy_result:
                return None  # Ошибка в стратегии
            
            # Распаковываем tuple результат
            if isinstance(strategy_result, (tuple, list)) and len(strategy_result) >= 5:
                buy_price, buy_amount, sell_price, sell_amount, info_dict = strategy_result[:5]
                
                return {
                    'buy_price': float(buy_price),
                    'buy_amount': float(buy_amount),
                    'sell_price': float(sell_price),
                    'sell_amount': float(sell_amount),
                    'info': info_dict if isinstance(info_dict, dict) else {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error parsing strategy result: {e}")
            return None

    async def _perform_pre_execution_checks(
        self, 
        context: TradingContext, 
        strategy_data: Dict[str, Any]
    ) -> Tuple[bool, str, List[str]]:
        """Предварительные проверки перед выполнением"""
        warnings = []
        
        try:
            # 1. Проверка баланса
            if self.enable_balance_checks:
                balance_check = await self.exchange_connector.check_sufficient_balance(
                    context.currency_pair.symbol,
                    'buy',
                    strategy_data['buy_amount'],
                    strategy_data['buy_price']
                )
                
                if not balance_check[0]:
                    return False, f"Insufficient balance: need {strategy_data['buy_amount'] * strategy_data['buy_price']:.4f} {balance_check[1]}, have {balance_check[2]:.4f}", warnings
                
                # Предупреждение если баланс близок к лимиту
                required = strategy_data['buy_amount'] * strategy_data['buy_price']
                if balance_check[2] < required * 1.1:
                    warnings.append("Balance is close to required amount")
            
            # 2. Проверка цен на разумность
            ticker = await self.exchange_connector.fetch_ticker(context.currency_pair.symbol)
            current_market_price = ticker['last']
            
            buy_price_diff = abs(strategy_data['buy_price'] - current_market_price) / current_market_price
            if buy_price_diff > 0.05:  # 5% отклонение
                warnings.append(f"BUY price differs from market by {buy_price_diff*100:.1f}%")
            
            sell_price_diff = abs(strategy_data['sell_price'] - current_market_price) / current_market_price  
            if sell_price_diff > 0.10:  # 10% отклонение
                warnings.append(f"SELL price differs from market by {sell_price_diff*100:.1f}%")
            
            # 3. Проверка объемов
            symbol_info = await self.exchange_connector.get_symbol_info(context.currency_pair.symbol)
            if strategy_data['buy_amount'] < symbol_info.min_qty:
                return False, f"BUY amount {strategy_data['buy_amount']} below minimum {symbol_info.min_qty}", warnings
            
            if strategy_data['sell_amount'] < symbol_info.min_qty:
                return False, f"SELL amount {strategy_data['sell_amount']} below minimum {symbol_info.min_qty}", warnings
            
            return True, "Checks passed", warnings
            
        except Exception as e:
            return False, f"Pre-execution check error: {str(e)}", warnings

    async def _execute_buy_order(
        self, 
        context: TradingContext, 
        strategy_data: Dict[str, Any]
    ) -> OrderExecutionResult:
        """Выполнение BUY ордера"""
        try:
            return await self.order_service.create_and_place_buy_order(
                symbol=context.currency_pair.symbol,
                amount=strategy_data['buy_amount'],
                price=strategy_data['buy_price'],
                deal_id=context.deal.deal_id,
                order_type=Order.TYPE_LIMIT # Возвращено на LIMIT
            )
        except Exception as e:
            logger.error(f"❌ Error executing BUY order: {e}")
            return OrderExecutionResult(
                success=False,
                error_message=f"BUY execution error: {str(e)}"
            )

    async def _create_local_sell_order(
        self,
        context: TradingContext,
        strategy_data: Dict[str, Any]
    ) -> OrderExecutionResult:
        """Выполнение SELL ордера"""
        try:
            return await self.order_service.create_local_sell_order(
                symbol=context.currency_pair.symbol,
                amount=strategy_data['sell_amount'],
                price=strategy_data['sell_price'],
                deal_id=context.deal.deal_id,
                order_type=Order.TYPE_LIMIT
            )
        except Exception as e:
            logger.error(f"❌ Error creating local SELL order: {e}")
            return OrderExecutionResult(
                success=False,
                error_message=f"SELL local creation error: {str(e)}"
            )

    async def _emergency_cancel_buy_order(self, buy_order: Order) -> bool:
        """Экстренная отмена BUY ордера при неудаче SELL"""
        try:
            logger.warning(f"🚨 Emergency cancelling BUY order {buy_order.order_id}")
            return await self.order_service.cancel_order(buy_order)
        except Exception as e:
            logger.error(f"❌ Failed to emergency cancel BUY order: {e}")
            return False

    def _update_execution_stats(
        self, 
        success: bool, 
        volume: float, 
        fees: float, 
        execution_time_ms: float
    ):
        """Обновление статистики выполнения"""
        self.execution_stats['total_executions'] += 1
        
        if success:
            self.execution_stats['successful_executions'] += 1
            self.execution_stats['total_volume'] += volume
            self.execution_stats['total_fees'] += fees
        else:
            self.execution_stats['failed_executions'] += 1
        
        # Обновляем среднее время выполнения
        total_time = (self.execution_stats['average_execution_time_ms'] * 
                     (self.execution_stats['total_executions'] - 1) + execution_time_ms)
        self.execution_stats['average_execution_time_ms'] = total_time / self.execution_stats['total_executions']

    # 📊 МЕТОДЫ МОНИТОРИНГА И УПРАВЛЕНИЯ

    async def monitor_active_orders(self) -> Dict[str, Any]:
        """
        📊 Мониторинг всех активных ордеров
        """
        try:
            # Синхронизируем ордера с биржей
            updated_orders = await self.order_service.sync_orders_with_exchange()
            
            # Группируем по статусам
            open_orders = []
            partially_filled = []
            filled_orders = []
            
            for order in updated_orders:
                if order.is_open():
                    open_orders.append(order)
                elif order.is_partially_filled():
                    partially_filled.append(order)
                elif order.is_filled():
                    filled_orders.append(order)
            
            return {
                'open_orders': len(open_orders),
                'partially_filled': len(partially_filled),
                'filled_orders': len(filled_orders),
                'total_monitored': len(updated_orders),
                'orders': {
                    'open': [order.to_dict() for order in open_orders],
                    'partially_filled': [order.to_dict() for order in partially_filled],
                    'filled': [order.to_dict() for order in filled_orders]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error monitoring orders: {e}")
            return {'error': str(e)}

    async def emergency_stop_all_trading(self, symbol: str = None) -> Dict[str, Any]:
        """
        🚨 Экстренная остановка всей торговли
        """
        logger.warning("🚨 EMERGENCY STOP - Cancelling all orders")
        
        try:
            # Отменяем все ордера через order_service
            cancelled_count = await self.order_service.emergency_cancel_all_orders(symbol)
            
            # Получаем статистику
            open_orders = self.order_service.get_open_orders()
            open_deals = self.deal_service.get_open_deals()
            
            return {
                'cancelled_orders': cancelled_count,
                'remaining_open_orders': len(open_orders),
                'open_deals': len(open_deals),
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol or 'ALL'
            }
            
        except Exception as e:
            logger.error(f"❌ Error during emergency stop: {e}")
            return {'error': str(e), 'cancelled_orders': 0}

    def get_execution_statistics(self) -> Dict[str, Any]:
        """📊 Получение статистики выполнения"""
        stats = self.execution_stats.copy()
        
        if stats['total_executions'] > 0:
            stats['success_rate'] = (stats['successful_executions'] / stats['total_executions']) * 100
            stats['average_volume_per_execution'] = stats['total_volume'] / stats['successful_executions'] if stats['successful_executions'] > 0 else 0
            stats['average_fees_per_execution'] = stats['total_fees'] / stats['successful_executions'] if stats['successful_executions'] > 0 else 0
        else:
            stats['success_rate'] = 0
            stats['average_volume_per_execution'] = 0
            stats['average_fees_per_execution'] = 0
        
        return stats

    def reset_statistics(self):
        """🔄 Сброс статистики"""
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_volume': 0.0,
            'total_fees': 0.0,
            'average_execution_time_ms': 0.0
        }

    # ⚙️ НАСТРОЙКИ

    def configure_execution_settings(
        self,
        max_execution_time_sec: float = None,
        enable_risk_checks: bool = None,
        enable_balance_checks: bool = None,
        enable_slippage_protection: bool = None
    ):
        """⚙️ Настройка параметров выполнения"""
        if max_execution_time_sec is not None:
            self.max_execution_time_sec = max_execution_time_sec
        if enable_risk_checks is not None:
            self.enable_risk_checks = enable_risk_checks
        if enable_balance_checks is not None:
            self.enable_balance_checks = enable_balance_checks
        if enable_slippage_protection is not None:
            self.enable_slippage_protection = enable_slippage_protection
        
        logger.info(f"⚙️ Execution settings updated")

    def get_current_settings(self) -> Dict[str, Any]:
        """⚙️ Получение текущих настроек"""
        return {
            'max_execution_time_sec': self.max_execution_time_sec,
            'enable_risk_checks': self.enable_risk_checks,
            'enable_balance_checks': self.enable_balance_checks,
            'enable_slippage_protection': self.enable_slippage_protection
        }

    # 🚨 РИСК-МЕНЕДЖМЕНТ МЕТОДЫ

    async def create_market_sell_order(
        self, 
        currency_pair_id: str, 
        amount: float, 
        deal_id: int
    ) -> Optional[Order]:
        """🚨 Создание маркет-ордера на продажу для стоп-лосса"""
        try:
            logger.info(f"🚨 Создание маркет SELL ордера для ликвидации позиции:")
            logger.info(f"   Пара: {currency_pair_id}")
            logger.info(f"   Количество: {amount}")
            logger.info(f"   Deal ID: {deal_id}")
            
            # Получаем текущую цену для логирования
            ticker = await self.exchange_connector.fetch_ticker(currency_pair_id)
            current_price = ticker['last']
            logger.info(f"   Текущая цена: {current_price}")
            
            # Создаем маркет-ордер на продажу
            order_result = await self.exchange_connector.create_market_sell_order(
                currency_pair_id, 
                amount
            )
            
            if order_result and order_result.success:
                # Создаем объект Order
                order = Order(
                    order_id=self.order_service.generate_order_id(),
                    deal_id=deal_id,
                    currency_pair_id=currency_pair_id,
                    side="SELL",
                    order_type="MARKET",
                    price=current_price,  # Для маркет-ордера цена примерная
                    amount=amount,
                    exchange_order_id=order_result.exchange_order_id,
                    filled_amount=order_result.filled_amount or amount,
                    average_price=order_result.average_price or current_price,
                    fees=order_result.fees or 0.0,
                    status="FILLED" if order_result.filled_amount else "OPEN"
                )
                
                # Сохраняем в репозиторий
                self.order_service.save_order(order)
                
                logger.info(f"✅ Маркет SELL ордер #{order.order_id} создан успешно")
                logger.info(f"   Exchange ID: {order_result.exchange_order_id}")
                logger.info(f"   Исполнено: {order_result.filled_amount or 'N/A'}")
                logger.info(f"   Средняя цена: {order_result.average_price or 'N/A'}")
                
                return order
                
            else:
                logger.error(f"❌ Не удалось создать маркет SELL ордер: {order_result.error_message if order_result else 'Unknown error'}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка при создании маркет SELL ордера: {e}")
            return None

    async def cancel_order(self, order: Order) -> bool:
        """🚫 Отмена ордера"""
        try:
            if order.exchange_order_id:
                result = await self.exchange_connector.cancel_order(
                    order.exchange_order_id, 
                    order.currency_pair_id
                )
                
                if result:
                    order.status = "CANCELED"
                    self.order_service.save_order(order)
                    logger.info(f"✅ Ордер #{order.order_id} отменен")
                    return True
                else:
                    logger.error(f"❌ Не удалось отменить ордер #{order.order_id}")
                    return False
            else:
                logger.warning(f"⚠️ Нет exchange_order_id для отмены ордера #{order.order_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при отмене ордера #{order.order_id}: {e}")
            return False

```

### 📄 `src\domain\services\orders\order_service.py`

```python
# domain/services/order_service.py.new - РЕАЛЬНАЯ торговля с API
import asyncio
import logging
from typing import Optional, Dict, List, Any, Tuple
from decimal import ROUND_DOWN, ROUND_UP
from domain.entities.order import Order, OrderValidationResult, OrderExecutionResult
from domain.factories.order_factory import OrderFactory
from domain.services.utils.decimal_rounding_service import DecimalRoundingService
from infrastructure.repositories.orders_repository import OrdersRepository
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
import ccxt

logger = logging.getLogger(__name__)

class OrderService:
    """
    🚀 ПОЛНОЦЕННЫЙ сервис для реальной торговли на бирже:
    - Создание и размещение ордеров на РЕАЛЬНОЙ бирже
    - Отслеживание статусов ордеров через API
    - Отмена и управление ордерами
    - Проверка балансов и валидация
    - Обработка ошибок и retry механизмы
    """

    def __init__(
        self,
        orders_repo: OrdersRepository,
        order_factory: OrderFactory,
        exchange_connector: CcxtExchangeConnector = None,
        currency_pair_symbol: str = None
    ):
        self.orders_repo = orders_repo
        self.order_factory = order_factory
        self.exchange_connector = exchange_connector
        self.currency_pair_symbol = currency_pair_symbol

        # Retry parameters
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.retry_backoff = 2.0  # exponential backoff multiplier

        # Statistics
        self.stats = {
            'orders_created': 0,
            'orders_executed': 0,
            'orders_failed': 0,
            'orders_cancelled': 0,
            'total_fees': 0.0
        }

    # 🚀 ОСНОВНЫЕ МЕТОДЫ СОЗДАНИЯ И РАЗМЕЩЕНИЯ ОРДЕРОВ

    async def create_and_place_buy_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: int,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        🛒 РЕАЛЬНОЕ создание и размещение BUY ордера на бирже

        Args:
            symbol: Торговая пара (BTCUSDT)
            amount: Количество для покупки
            price: Цена покупки
            deal_id: ID связанной сделки
            order_type: Тип ордера (LIMIT, MARKET)
            client_order_id: Клиентский ID ордера

        Returns:
            OrderExecutionResult с информацией о результате
        """
        try:
            # Корректируем количество согласно правилам биржи
            amount = self.order_factory.adjust_amount_precision(symbol, amount, round_up=True)

            # === ИСПРАВЛЕНИЕ v4: Корректируем цену согласно precision с биржи ===
            market_info = await self.exchange_connector.get_symbol_info(symbol)
            price_precision = market_info.precision.get('price')
            if price_precision:
                 price = float(DecimalRoundingService.round_by_tick_size(price, str(price_precision), rounding_mode=ROUND_DOWN))
            # =================================================================

            logger.info(f"🛒 Creating BUY order: {amount} {symbol} @ {price}")

            # 1. Валидация параметров
            validation_result = await self._validate_order_params(
                symbol, Order.SIDE_BUY, amount, price, order_type
            )
            if not validation_result.is_valid:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Validation failed: {', '.join(validation_result.errors)}"
                )

            # 2. Проверка баланса
            balance_check = await self._check_balance_for_order(symbol, Order.SIDE_BUY, amount, price)
            if not balance_check[0]:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Insufficient balance: need {amount * price:.4f} {balance_check[1]}, have {balance_check[2]:.4f}"
                )

            # 3. Создание ордера через фабрику
            order = self.order_factory.create_buy_order(
                symbol=symbol,
                amount=amount,
                price=price,
                deal_id=deal_id,
                order_type=order_type,
                client_order_id=client_order_id
            )

            # 4. Сохранение в репозиторий
            self.orders_repo.save(order)

            # 5. РЕАЛЬНОЕ размещение на бирже
            if self.exchange_connector:
                execution_result = await self._execute_order_on_exchange(order)
                if execution_result.success:
                    self.stats['orders_executed'] += 1
                    logger.info(f"✅ BUY order executed: {order.exchange_id}")
                else:
                    self.stats['orders_failed'] += 1
                    logger.error(f"❌ BUY order failed: {execution_result.error_message}")

                return execution_result
            else:
                # Fallback без коннектора
                order.status = Order.STATUS_PENDING
                self.orders_repo.save(order)
                logger.warning(f"⚠️ BUY order created locally (no exchange connector)")

                return OrderExecutionResult(
                    success=True,
                    order=order,
                    error_message="Created locally - no exchange connector"
                )

        except Exception as e:
            logger.error(f"❌ Error creating BUY order: {e}")
            self.stats['orders_failed'] += 1
            return OrderExecutionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )

    async def create_and_place_sell_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: int,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        🏷️ РЕАЛЬНОЕ создание и размещение SELL ордера на бирже
        """
        try:
            # Корректируем количество согласно правилам биржи (округляем вниз)
            amount = self.order_factory.adjust_amount_precision(symbol, amount)

            # === ИСПРАВЛЕНИЕ v4: Корректируем цену согласно precision с биржи ===
            market_info = await self.exchange_connector.get_symbol_info(symbol)
            price_precision = market_info.precision.get('price')
            if price_precision:
                 price = float(DecimalRoundingService.round_by_tick_size(price, str(price_precision), rounding_mode=ROUND_UP))
            # =================================================================

            logger.info(f"🏷️ Creating SELL order: {amount} {symbol} @ {price}")

            # 1. Валидация параметров
            validation_result = await self._validate_order_params(
                symbol, Order.SIDE_SELL, amount, price, order_type
            )
            if not validation_result.is_valid:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Validation failed: {', '.join(validation_result.errors)}"
                )

            # 2. Проверка баланса
            balance_check = await self._check_balance_for_order(symbol, Order.SIDE_SELL, amount, price)
            if not balance_check[0]:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Insufficient balance: need {amount:.4f} {balance_check[1]}, have {balance_check[2]:.4f}"
                )

            # 3. Создание ордера через фабрику
            order = self.order_factory.create_sell_order(
                symbol=symbol,
                amount=amount,
                price=price,
                deal_id=deal_id,
                order_type=order_type,
                client_order_id=client_order_id
            )

            # 4. Сохранение в репозиторий
            self.orders_repo.save(order)

            # 5. РЕАЛЬНОЕ размещение на бирже
            if self.exchange_connector:
                execution_result = await self._execute_order_on_exchange(order)
                if execution_result.success:
                    self.stats['orders_executed'] += 1
                    logger.info(f"✅ SELL order executed: {order.exchange_id}")
                else:
                    self.stats['orders_failed'] += 1
                    logger.error(f"❌ SELL order failed: {execution_result.error_message}")

                return execution_result

                return execution_result
            else:
                # Fallback без коннектора
                order.status = Order.STATUS_PENDING
                self.orders_repo.save(order)
                logger.warning(f"⚠️ SELL order created locally (no exchange connector)")

                return OrderExecutionResult(
                    success=True,
                    order=order,
                    error_message="Created locally - no exchange connector"
                )

        except Exception as e:
            logger.error(f"❌ Error creating SELL order: {e}")
            self.stats['orders_failed'] += 1
            return OrderExecutionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )

    async def create_local_sell_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: int,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        📝 Создание ЛОКАЛЬНОГО SELL ордера без размещения на бирже.
        Ордер сохраняется в репозиторий со стату��ом PENDING.
        """
        try:
            # Корректируем количество и цену
            amount = self.order_factory.adjust_amount_precision(symbol, amount)
            market_info = await self.exchange_connector.get_symbol_info(symbol)
            price_precision = market_info.precision.get('price')
            if price_precision:
                price = float(DecimalRoundingService.round_by_tick_size(price, str(price_precision), rounding_mode=ROUND_UP))

            logger.info(f"📝 Creating LOCAL SELL order: {amount} {symbol} @ {price}")

            # Валидация параметров (локальная)
            validation_result = await self._validate_order_params(
                symbol, Order.SIDE_SELL, amount, price, order_type
            )
            if not validation_result.is_valid:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Validation failed: {', '.join(validation_result.errors)}"
                )

            # Создание ордера через фабрику
            order = self.order_factory.create_sell_order(
                symbol=symbol,
                amount=amount,
                price=price,
                deal_id=deal_id,
                order_type=order_type,
                client_order_id=client_order_id
            )
            
            # Устанавливаем статус PENDING, так как ордер не размещается
            order.status = Order.STATUS_PENDING
            
            # Сохранение в репозиторий
            self.orders_repo.save(order)
            self.stats['orders_created'] += 1
            
            logger.info(f"✅ LOCAL SELL order {order.order_id} created and saved with status PENDING.")

            return OrderExecutionResult(
                success=True,
                order=order,
                error_message="Created locally with PENDING status"
            )

        except Exception as e:
            logger.error(f"❌ Error creating LOCAL SELL order: {e}")
            self.stats['orders_failed'] += 1
            return OrderExecutionResult(
                success=False,
                error_message=f"Unexpected error in local creation: {str(e)}"
            )

    async def place_existing_order(self, order: Order) -> OrderExecutionResult:
        """
        📤 Размещает на бирже уже существующий локальный ордер (в статусе PENDING).
        """
        if not order.is_pending():
            return OrderExecutionResult(success=False, error_message=f"Order {order.order_id} is not in PENDING state.")

        logger.info(f"📤 Размещаем существующий ордер {order.order_id} ({order.side} {order.amount} {order.symbol}) на бирже.")

        # Проверка баланса перед размещением
        balance_check = await self._check_balance_for_order(order.symbol, order.side, order.amount, order.price)
        if not balance_check[0]:
            return OrderExecutionResult(
                success=False,
                error_message=f"Insufficient balance for pending order: need {order.amount * order.price:.4f} {balance_check[1]}, have {balance_check[2]:.4f}"
            )

        if self.exchange_connector:
            execution_result = await self._execute_order_on_exchange(order)
            if execution_result.success:
                self.stats['orders_executed'] += 1
                logger.info(f"✅ Existing order {order.order_id} placed successfully: {order.exchange_id}")
            else:
                self.stats['orders_failed'] += 1
                logger.error(f"❌ Failed to place existing order {order.order_id}: {execution_result.error_message}")
            return execution_result
        else:
            return OrderExecutionResult(success=False, error_message="No exchange connector available.")

    # 🔧 ВНУТРЕННИЕ МЕТОДЫ

    async def _execute_order_on_exchange(self, order: Order) -> OrderExecutionResult:
        """
        🚀 РЕАЛЬНОЕ размещение ордера на бирже с retry механизмом
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.info(f"📤 Placing order on exchange (attempt {attempt + 1}/{self.max_retries})")

                # Вызов API биржи
                exchange_response = await self.exchange_connector.create_order(
                    symbol=order.symbol,
                    side=order.side.lower(),
                    order_type=order.order_type.lower(),
                    amount=order.amount,
                    price=order.price if order.order_type == Order.TYPE_LIMIT else None
                )

                # Обновляем ордер данными с биржи
                order.mark_as_placed(
                    exchange_id=exchange_response['id'],
                    exchange_timestamp=exchange_response.get('timestamp')
                )
                # Дополнительный запрос для получения полных данных об исполнении
                if hasattr(self.exchange_connector, 'fetch_order'):
                    full_order_data = await self.exchange_connector.fetch_order(
                        order.exchange_id,
                        order.symbol
                    )
                    order.update_from_exchange(full_order_data)

                # Сохраняем обновленный ордер
                self.orders_repo.save(order)

                logger.info(f"✅ Order placed successfully: {order.exchange_id}")
                return OrderExecutionResult(
                    success=True,
                    order=order,
                    exchange_response=exchange_response
                )

            except Exception as e:
                last_error = e
                order.retries += 1
                logger.warning(f"⚠️ Order placement failed (attempt {attempt + 1}): {e}")

                # Exponential backoff для retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (self.retry_backoff ** attempt))

        # Все попытки неудачны
        order.mark_as_failed(f"Failed after {self.max_retries} attempts: {last_error}")
        self.orders_repo.save(order)

        return OrderExecutionResult(
            success=False,
            order=order,
            error_message=f"Failed after {self.max_retries} attempts: {last_error}"
        )

    async def _validate_order_params(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        order_type: str
    ) -> OrderValidationResult:
        """
        🔍 Валидация параметров ордера
        """
        errors = []
        warnings = []

        # Основная валидация
        if not symbol:
            errors.append("Symbol is required")
        if amount <= 0:
            errors.append("Amount must be positive")
        if order_type == Order.TYPE_LIMIT and price <= 0:
            errors.append("Price must be positive for limit orders")
        if side not in [Order.SIDE_BUY, Order.SIDE_SELL]:
            errors.append("Side must be BUY or SELL")

        # Валидация через exchange info если доступно
        if self.exchange_connector:
            try:
                symbol_info = await self.exchange_connector.get_symbol_info(symbol)

                if amount < symbol_info.min_qty:
                    errors.append(f"Amount {amount} below minimum {symbol_info.min_qty}")
                if amount > symbol_info.max_qty:
                    errors.append(f"Amount {amount} above maximum {symbol_info.max_qty}")

                if order_type == Order.TYPE_LIMIT:
                    if price < symbol_info.min_price:
                        errors.append(f"Price {price} below minimum {symbol_info.min_price}")
                    if price > symbol_info.max_price:
                        errors.append(f"Price {price} above maximum {symbol_info.max_price}")

                    # Проверяем минимальную стоимость
                    notional_value = amount * price
                    if notional_value < symbol_info.min_notional:
                        errors.append(f"Order value {notional_value} below minimum {symbol_info.min_notional}")

                    # Предупреждения
                    if notional_value < symbol_info.min_notional * 1.1:
                        warnings.append(f"Order value close to minimum notional")

            except Exception as e:
                warnings.append(f"Could not validate against exchange info: {e}")

        return OrderValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def _check_balance_for_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float
    ) -> Tuple[bool, str, float]:
        """
        💰 Проверка баланса для ордера
        """
        if not self.exchange_connector:
            return True, "UNKNOWN", 0.0  # Пропускаем проверку без коннектора

        try:
            return await self.exchange_connector.check_sufficient_balance(
                symbol, side, amount, price
            )
        except Exception as e:
            logger.error(f"❌ Error checking balance: {e}")
            return False, "ERROR", 0.0

    # 📊 МЕТОДЫ ОТСЛЕЖИВАНИЯ И УПРАВЛЕНИЯ ОРДЕРАМИ

    async def get_order_status(self, order: Order) -> Optional[Order]:
        """
        📊 РЕАЛЬНАЯ проверка статуса ордера на бирже
        """
        if not order.exchange_id or not self.exchange_connector:
            return order

        try:
            logger.debug(f"📊 Checking status for order {order.exchange_id}")

            # РЕАЛЬНЫЙ запрос к бирже
            exchange_order = await self.exchange_connector.fetch_order(
                order.exchange_id,
                order.symbol
            )

            # Обновляем локальный ордер данными с биржи
            order.update_from_exchange(exchange_order)

            # Сохраняем обновления
            self.orders_repo.save(order)

            logger.debug(f"📊 Order {order.order_id} status updated: {order.status}")
            return order

        except Exception as e:
            logger.error(f"❌ Error checking order status {order.order_id}: {e}")
            return order

    async def cancel_order(self, order: Order) -> bool:
        """
        ❌ РЕАЛЬНАЯ отмена ордера на бирже
        """
        if not order.is_open():
            logger.warning(f"⚠️ Order {order.order_id} is not open ({order.status})")
            return False

        if not self.exchange_connector or not order.exchange_id:
            # Локальная отмена без биржи
            order.cancel("No exchange connector or exchange_id")
            self.orders_repo.save(order)
            logger.warning(f"⚠️ Order {order.order_id} cancelled locally")
            return True

        try:
            logger.info(f"❌ Cancelling order {order.exchange_id} on exchange")

            # РЕАЛЬНАЯ отмена на бирже
            exchange_response = await self.exchange_connector.cancel_order(
                order.exchange_id,
                order.symbol
            )

            # Обновляем статус
            order.cancel("Cancelled by user")
            if exchange_response:
                order.update_from_exchange(exchange_response)

            self.orders_repo.save(order)
            self.stats['orders_cancelled'] += 1

            logger.info(f"✅ Order {order.order_id} cancelled successfully")
            return True

        except ccxt.OrderNotFound:
            # Ордер не найден на бирже, значит, его уже нет или он исполнен
            logger.warning(f"⚠️ Order {order.order_id} (exchange_id: {order.exchange_id}) not found on exchange. Assuming it's already gone.")
            order.status = Order.STATUS_NOT_FOUND_ON_EXCHANGE # Новый статус
            order.closed_at = int(time.time() * 1000)
            self.orders_repo.save(order)
            return True # Считаем, что цель достигнута: ордера на бирже нет

        except Exception as e:
            logger.error(f"❌ Error cancelling order {order.order_id}: {e}")
            order.status = Order.STATUS_FAILED # Или новый статус FAILED_TO_CANCEL
            order.error_message = str(e)
            self.orders_repo.save(order)
            return False # Отмена не удалась

    async def sync_orders_with_exchange(self) -> List[Order]:
        """
        🔄 Синхронизация всех открытых ордеров с биржей
        """
        if not self.exchange_connector:
            logger.warning("⚠️ No exchange connector for sync")
            return []

        updated_orders = []

        try:
            # Получаем все локальные открытые ордера
            local_orders = self.get_open_orders()

            # Получаем открытые ордера с биржи
            # Используем self.currency_pair_symbol для fetchOpenOrders
            symbol_to_fetch = self.currency_pair_symbol if self.currency_pair_symbol else (local_orders[0].symbol if local_orders else None)
            if not symbol_to_fetch:
                logger.warning("⚠️ No symbol available to fetch open orders. Skipping sync.")
                return []

            exchange_open_orders = await self.exchange_connector.fetch_open_orders(symbol=symbol_to_fetch)
            exchange_open_orders_map = {order['id']: order for order in exchange_open_orders}

            for order in local_orders:
                if order.exchange_id:
                    if order.exchange_id in exchange_open_orders_map:
                        # Ордер есть на бирже и открыт - обновляем статус
                        exchange_data = exchange_open_orders_map[order.exchange_id]
                        order.update_from_exchange(exchange_data)
                        self.orders_repo.save(order)
                        updated_orders.append(order)
                    else:
                        # Ордера нет среди ОТКРЫТЫХ на бирже.
                        # Нужно запросить его полный статус, чтобы понять, что с ним произошло.
                        try:
                            full_exchange_order = await self.exchange_connector.fetch_order(
                                order.exchange_id,
                                order.symbol
                            )
                            order.update_from_exchange(full_exchange_order)
                            self.orders_repo.save(order)
                            updated_orders.append(order)
                            logger.info(f"🔄 Synced order {order.order_id} (exchange_id: {order.exchange_id}) status: {order.status}")
                        except ccxt.OrderNotFound:
                            # Ордер не найден на бирже вообще (ни открытый, ни закрытый)
                            logger.warning(f"⚠️ Order {order.order_id} (exchange_id: {order.exchange_id}) not found on exchange during sync. Marking as NOT_FOUND_ON_EXCHANGE.")
                            order.status = Order.STATUS_NOT_FOUND_ON_EXCHANGE
                            order.closed_at = int(time.time() * 1000)
                            self.orders_repo.save(order)
                            updated_orders.append(order)
                        except Exception as e:
                            logger.error(f"❌ Error fetching status for order {order.order_id} (exchange_id: {order.exchange_id}) during sync: {e}")
                            # Оставляем ордер в текущем состоянии, но логируем ошибку
                else:
                    # Локальный ордер без exchange_id - возможно, не был размещен
                    logger.warning(f"⚠️ Local order {order.order_id} has no exchange_id. Skipping sync for this order.")

            # logger.info(f"🔄 Synced {len(updated_orders)} orders with exchange")
            return updated_orders

        except Exception as e:
            logger.error(f"❌ Error syncing orders: {e}")
            return []

    # 📋 МЕТОДЫ ПОЛУЧЕНИЯ ОРДЕРОВ

    def get_orders_by_deal(self, deal_id: int) -> List[Order]:
        """📋 Получает все ордера по ID сделки"""
        return self.orders_repo.get_all_by_deal(deal_id)

    def get_open_orders(self) -> List[Order]:
        """📋 Получает все открытые ордера"""
        all_orders = self.orders_repo.get_all()
        return [order for order in all_orders if order.is_open() or order.is_partially_filled()]

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """📋 Получает ордер по ID"""
        return self.orders_repo.get_by_id(order_id)

    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """📋 Получает все ордера по символу"""
        all_orders = self.orders_repo.get_all()
        return [order for order in all_orders if order.symbol == symbol]

    # 🚨 ЭКСТРЕННЫЕ МЕТОДЫ

    async def emergency_cancel_all_orders(self, symbol: str = None) -> int:
        """
        🚨 Экстренная отмена всех открытых ордеров
        """
        logger.warning("🚨 Emergency cancellation of all orders")

        open_orders = self.get_open_orders()
        if symbol:
            open_orders = [order for order in open_orders if order.symbol == symbol]

        cancelled_count = 0
        for order in open_orders:
            try:
                if await self.cancel_order(order):
                    cancelled_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to cancel order {order.order_id}: {e}")

        logger.warning(f"🚨 Emergency cancelled {cancelled_count}/{len(open_orders)} orders")
        return cancelled_count

    # 📊 СТАТИСТИКА И МОНИТОРИНГ

    def get_statistics(self) -> Dict[str, Any]:
        """📊 Получение статистики работы сервиса"""
        all_orders = self.orders_repo.get_all()

        stats = self.stats.copy()
        stats.update({
            'total_orders': len(all_orders),
            'open_orders': len(self.get_open_orders()),
            'success_rate': (self.stats['orders_executed'] / max(self.stats['orders_created'], 1)) * 100
        })

        return stats

    def reset_statistics(self):
        """🔄 Сброс статистики"""
        self.stats = {
            'orders_created': 0,
            'orders_executed': 0,
            'orders_failed': 0,
            'orders_cancelled': 0,
            'total_fees': 0.0
        }

    def save_order(self, order: Order):
        """Сохранение ордера в репозиторий"""
        self.orders_repo.save(order)
        self.stats['orders_created'] += 1

```

### 📄 `src\domain\services\orders\order_timeout_service.py`

```python
# domain/services/order_timeout_service.py.new - Система проверки протухших BUY ордеров
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from domain.entities.order import Order
from domain.entities.currency_pair import CurrencyPair
from domain.services.orders.order_service import OrderService
from domain.services.deals.deal_service import DealService
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

logger = logging.getLogger(__name__)

class OrderTimeoutService:
    """
    🕒 Сервис для автоматического отслеживания и управления протухшими BUY ордерами
    
    Отслеживает только ордера на ПОКУПКУ (BUY) которые могут "протухнуть" если:
    - Ордер висит слишком долго без исполнения
    - Рыночная цена ушла слишком далеко вверх от цены ордера
    - Ордер потерял актуальность из-за изменения трендов
    
    SELL ордерами займется RiskManagementService позже
    """

    def __init__(
        self, 
        order_service: OrderService,
        deal_service: DealService,
        exchange_connector: CcxtExchangeConnector,
        config: Dict[str, Any] = None
    ):
        self.order_service = order_service
        self.deal_service = deal_service
        self.exchange = exchange_connector
        
        # Конфигурация таймаутов (по умолчанию)
        default_config = {
            'max_order_age_minutes': 15,           # Максимальный возраст ордера (15 минут)
            'max_price_deviation_percent': 3.0,    # Максимальное отклонение цены (3%)
            'check_interval_seconds': 30,          # Интервал проверки (30 секунд)
            'auto_recreate_orders': True,          # Автоматически пересоздавать ордера
            'max_recreations_per_deal': 3,         # Максимум пересозданий на сделку
            'min_time_between_recreations_minutes': 2,  # Минимум времени между пересозданиями
            'trend_validation_enabled': True       # Проверять тренд перед пересозданием
        }
        
        self.config = {**default_config, **(config or {})}
        
        # Состояние сервиса
        self.is_monitoring = False
        self.monitoring_task = None
        
        # Статистика
        self.stats = {
            'total_checks': 0,
            'stale_orders_found': 0,
            'orders_cancelled': 0,
            'orders_recreated': 0,
            'recreation_failures': 0,
            'reasons': {
                'age_timeout': 0,
                'price_deviation': 0,
                'trend_changed': 0
            }
        }
        
        # Отслеживание пересозданий для каждой сделки
        self.deal_recreations = {}  # deal_id -> count

    # 🚀 ОСНОВНЫЕ МЕТОДЫ ЗАПУСКА/ОСТАНОВКИ

    async def start_monitoring(self):
        """Запуск фонового мониторинга протухших BUY ордеров"""
        if self.is_monitoring:
            logger.warning("⚠️ Order timeout monitoring already started")
            return
            
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info(f"🕒 Order timeout monitoring started")
        logger.info(f"   ⏰ Check interval: {self.config['check_interval_seconds']}s")
        logger.info(f"   📅 Max age: {self.config['max_order_age_minutes']} minutes")
        logger.info(f"   📊 Max price deviation: {self.config['max_price_deviation_percent']}%")
        logger.info(f"   🔄 Auto recreate: {'✅' if self.config['auto_recreate_orders'] else '❌'}")

    async def stop_monitoring(self):
        """Остановка мониторинга"""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
                
        logger.info("🔴 Order timeout monitoring stopped")

    async def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        logger.info("🔄 Starting order timeout monitoring loop")
        
        while self.is_monitoring:
            try:
                await self._check_stale_buy_orders()
                self.stats['total_checks'] += 1
                
                # Очистка старых записей пересозданий (старше 1 часа)
                self._cleanup_old_recreation_records()
                
                await asyncio.sleep(self.config['check_interval_seconds'])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in order timeout monitoring loop: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке

    # 🔍 ОСНОВНАЯ ЛОГИКА ПРОВЕРКИ

    async def _check_stale_buy_orders(self):
        """Проверяет все открытые BUY ордера на 'протухание'"""
        try:
            # Получаем все открытые ордера
            open_orders = self.order_service.get_open_orders()
            
            # Фильтруем только BUY ордера
            buy_orders = [order for order in open_orders if order.side == Order.SIDE_BUY]
            
            if not buy_orders:
                return
                
            logger.debug(f"🔍 Checking {len(buy_orders)} open BUY orders for staleness")
            
            for order in buy_orders:
                await self._check_single_buy_order(order)
                
        except Exception as e:
            logger.error(f"❌ Error checking stale BUY orders: {e}")

    async def _check_single_buy_order(self, order: Order):
        """Проверяет конкретный BUY ордер на протухание"""
        try:
            # Проверка по времени
            is_too_old, age_minutes = await self._check_order_age(order)
            
            # Проверка по отклонению цены
            is_price_too_far, price_deviation = await self._check_price_deviation(order)
            
            # Определяем причину протухания
            stale_reasons = []
            if is_too_old:
                stale_reasons.append(f"age_timeout (age: {age_minutes:.1f}min)")
                self.stats['reasons']['age_timeout'] += 1
                
            if is_price_too_far:
                stale_reasons.append(f"price_deviation (deviation: {price_deviation:.2f}%)")
                self.stats['reasons']['price_deviation'] += 1
            
            # Если ордер протух
            if stale_reasons:
                self.stats['stale_orders_found'] += 1
                
                logger.warning(f"🕒 STALE BUY ORDER detected: {order.order_id}")
                logger.warning(f"   📋 Reasons: {', '.join(stale_reasons)}")
                logger.warning(f"   💰 Order: {order.amount} {order.symbol} @ {order.price}")
                logger.warning(f"   🔗 Deal ID: {order.deal_id}")
                
                await self._handle_stale_buy_order(order, stale_reasons)
                
        except Exception as e:
            logger.error(f"❌ Error checking BUY order {order.order_id}: {e}")

    async def _check_order_age(self, order: Order) -> Tuple[bool, float]:
        """Проверка превышения времени жизни BUY ордера"""
        current_time = int(time.time() * 1000)
        order_age_ms = current_time - order.created_at
        order_age_minutes = order_age_ms / 1000 / 60
        
        max_age = self.config['max_order_age_minutes']
        is_too_old = order_age_minutes > max_age
        
        if is_too_old:
            logger.debug(f"⏰ Order {order.order_id} age: {order_age_minutes:.1f}min > {max_age}min")
            
        return is_too_old, order_age_minutes

    async def _check_price_deviation(self, order: Order) -> Tuple[bool, float]:
        """Проверка отклонения цены BUY ордера от рыночной"""
        try:
            ticker = await self.exchange.fetch_ticker(order.symbol)
            current_price = ticker['last']
            
            # Для BUY ордера: если рынок ушел значительно выше нашей цены покупки
            # Это означает что никто не продаст нам по нашей низкой цене
            deviation_percent = ((current_price - order.price) / order.price) * 100
            
            max_deviation = self.config['max_price_deviation_percent']
            is_too_far = deviation_percent > max_deviation
            
            if is_too_far:
                logger.debug(f"📈 Order {order.order_id} price deviation: "
                           f"{order.price} vs market {current_price} = {deviation_percent:.2f}%")
                           
            return is_too_far, deviation_percent
            
        except Exception as e:
            logger.error(f"❌ Error checking price deviation for order {order.order_id}: {e}")
            return False, 0.0

    # 🛠️ ОБРАБОТКА ПРОТУХШИХ ОРДЕРОВ

    async def _handle_stale_buy_order(self, order: Order, reasons: List[str]):
        """Обработка протухшего BUY ордера"""
        logger.info(f"🛠️ Handling stale BUY order {order.order_id}")
        logger.info(f"   📋 Reasons: {', '.join(reasons)}")
        
        try:
            # 1. Отменяем старый BUY ордер
            cancel_success = await self._cancel_stale_order(order)
            
            if not cancel_success:
                logger.error(f"❌ Failed to cancel stale BUY order {order.order_id}")
                return
                
            self.stats['orders_cancelled'] += 1
            
            # 2. Определяем нужно ли пересоздавать ордер
            if self.config['auto_recreate_orders']:
                should_recreate = await self._should_recreate_buy_order(order, reasons)
                
                if should_recreate:
                    # 3. Пересоздаем BUY ордер по новой цене
                    new_order = await self._recreate_buy_order(order)
                    
                    if new_order:
                        self.stats['orders_recreated'] += 1
                        logger.info(f"✅ BUY order recreated: {order.order_id} -> {new_order.order_id}")
                    else:
                        self.stats['recreation_failures'] += 1
                        logger.error(f"❌ Failed to recreate BUY order {order.order_id}")
                else:
                    logger.info(f"❌ BUY order {order.order_id} cancelled without recreation")
            else:
                logger.info(f"❌ BUY order {order.order_id} cancelled (auto-recreation disabled)")
                
        except Exception as e:
            logger.error(f"❌ Error handling stale BUY order {order.order_id}: {e}")

    async def _cancel_stale_order(self, order: Order) -> bool:
        """Отменяет протухший ордер"""
        try:
            logger.info(f"❌ Cancelling stale BUY order {order.order_id}")
            
            success = await self.order_service.cancel_order(order)
            
            if success:
                logger.info(f"✅ Stale BUY order {order.order_id} cancelled successfully")
            else:
                logger.error(f"❌ Failed to cancel stale BUY order {order.order_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error cancelling stale BUY order {order.order_id}: {e}")
            return False

    async def _should_recreate_buy_order(self, order: Order, reasons: List[str]) -> bool:
        """Определяет нужно ли пересоздавать BUY ордер"""
        
        # Проверяем лимит пересозданий для этой сделки
        deal_id = order.deal_id
        recreations_count = self.deal_recreations.get(deal_id, 0)
        max_recreations = self.config['max_recreations_per_deal']
        
        if recreations_count >= max_recreations:
            logger.warning(f"⚠️ Deal {deal_id} reached max recreations limit: {recreations_count}/{max_recreations}")
            return False
            
        # Проверяем минимальное время между пересозданиями
        last_recreation_time = getattr(order, 'last_recreation_time', None)
        if last_recreation_time:
            min_interval_ms = self.config['min_time_between_recreations_minutes'] * 60 * 1000
            time_since_last = int(time.time() * 1000) - last_recreation_time
            
            if time_since_last < min_interval_ms:
                logger.warning(f"⚠️ Too soon to recreate order {order.order_id}, wait {min_interval_ms - time_since_last}ms")
                return False
        
        # Не пересоздаем если только возраст проблема (возможно сделка уже не актуальна)
        age_only = len(reasons) == 1 and 'age_timeout' in reasons[0]
        if age_only:
            logger.info(f"💭 Not recreating order {order.order_id} - age timeout only, deal may be stale")
            return False
            
        # Пересоздаем если цена ушла (основная причина)
        price_deviation = any('price_deviation' in reason for reason in reasons)
        if price_deviation:
            logger.info(f"💭 Will recreate order {order.order_id} - price deviation detected")
            return True
            
        return False

    async def _recreate_buy_order(self, old_order: Order) -> Optional[Order]:
        """Пересоздает BUY ордер по текущей рыночной цене"""
        
        try:
            logger.info(f"🔄 Recreating BUY order {old_order.order_id} with current market price")
            
            # Получаем текущую цену
            ticker = await self.exchange.fetch_ticker(old_order.symbol)
            current_price = ticker['last']
            
            # Для BUY ордера: ставим цену немного ниже текущей рыночной
            # чтобы увеличить вероятность исполнения
            price_adjustment = 0.001  # -0.1%
            new_price = current_price * (1 - price_adjustment)
            
            logger.info(f"💰 New BUY price calculation:")
            logger.info(f"   📊 Market price: {current_price}")
            logger.info(f"   🎯 Old order price: {old_order.price}")
            logger.info(f"   🆕 New order price: {new_price} (-{price_adjustment*100:.1f}%)")
            
            # Создаем новый BUY ордер
            execution_result = await self.order_service.create_and_place_buy_order(
                symbol=old_order.symbol,
                amount=old_order.amount,
                price=new_price,
                deal_id=old_order.deal_id,
                order_type=old_order.order_type,
                client_order_id=f"recreated_{old_order.order_id}_{int(time.time())}"
            )
            
            if execution_result.success:
                new_order = execution_result.order
                
                # Отмечаем время пересоздания
                new_order.last_recreation_time = int(time.time() * 1000)
                
                # Увеличиваем счетчик пересозданий для сделки
                deal_id = old_order.deal_id
                self.deal_recreations[deal_id] = self.deal_recreations.get(deal_id, 0) + 1
                
                logger.info(f"✅ BUY order recreated successfully:")
                logger.info(f"   🆔 New order ID: {new_order.order_id}")
                logger.info(f"   🏷️ Exchange ID: {new_order.exchange_id}")
                logger.info(f"   💰 Price: {old_order.price} -> {new_order.price}")
                logger.info(f"   🔄 Deal recreations: {self.deal_recreations[deal_id]}")
                
                return new_order
            else:
                logger.error(f"❌ Failed to recreate BUY order: {execution_result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error recreating BUY order {old_order.order_id}: {e}")
            return None

    # 🧹 УТИЛИТНЫЕ МЕТОДЫ

    def _cleanup_old_recreation_records(self):
        """Очистка старых записей пересозданий (старше 1 часа)"""
        try:
            # Получаем все открытые сделки
            open_deals = self.deal_service.get_open_deals()
            open_deal_ids = {deal.deal_id for deal in open_deals}
            
            # Удаляем записи для закрытых сделок
            closed_deal_ids = []
            for deal_id in self.deal_recreations:
                if deal_id not in open_deal_ids:
                    closed_deal_ids.append(deal_id)
                    
            for deal_id in closed_deal_ids:
                del self.deal_recreations[deal_id]
                
            if closed_deal_ids:
                logger.debug(f"🧹 Cleaned up recreation records for {len(closed_deal_ids)} closed deals")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up recreation records: {e}")

    # 📊 СТАТИСТИКА И МОНИТОРИНГ

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики работы сервиса"""
        stats = self.stats.copy()
        
        # Дополнительные метрики
        if stats['total_checks'] > 0:
            stats['stale_rate'] = (stats['stale_orders_found'] / stats['total_checks']) * 100
        else:
            stats['stale_rate'] = 0.0
            
        if stats['orders_cancelled'] > 0:
            stats['recreation_success_rate'] = (stats['orders_recreated'] / stats['orders_cancelled']) * 100
        else:
            stats['recreation_success_rate'] = 0.0
            
        stats['active_deal_recreations'] = len(self.deal_recreations)
        stats['monitoring_status'] = 'RUNNING' if self.is_monitoring else 'STOPPED'
        
        return stats

    def get_configuration(self) -> Dict[str, Any]:
        """Получение текущей конфигурации"""
        return self.config.copy()

    def update_configuration(self, new_config: Dict[str, Any]):
        """Обновление конфигурации"""
        self.config.update(new_config)
        logger.info(f"⚙️ Order timeout configuration updated: {new_config}")

    def reset_statistics(self):
        """Сброс статистики"""
        self.stats = {
            'total_checks': 0,
            'stale_orders_found': 0,
            'orders_cancelled': 0,
            'orders_recreated': 0,
            'recreation_failures': 0,
            'reasons': {
                'age_timeout': 0,
                'price_deviation': 0,
                'trend_changed': 0
            }
        }
        self.deal_recreations.clear()
        logger.info("📊 Order timeout statistics reset")

    # 🚨 ЭКСТРЕННЫЕ МЕТОДЫ

    async def emergency_cancel_all_stale_orders(self) -> Dict[str, Any]:
        """Экстренная отмена всех протухших BUY ордеров"""
        logger.warning("🚨 EMERGENCY: Cancelling all stale BUY orders")
        
        result = {
            'cancelled_orders': 0,
            'failed_cancellations': 0,
            'errors': []
        }
        
        try:
            open_orders = self.order_service.get_open_orders()
            buy_orders = [order for order in open_orders if order.side == Order.SIDE_BUY]
            
            for order in buy_orders:
                try:
                    # Проверяем на протухание
                    is_old, _ = await self._check_order_age(order)
                    is_far, _ = await self._check_price_deviation(order)
                    
                    if is_old or is_far:
                        success = await self.order_service.cancel_order(order)
                        if success:
                            result['cancelled_orders'] += 1
                        else:
                            result['failed_cancellations'] += 1
                            
                except Exception as e:
                    result['failed_cancellations'] += 1
                    result['errors'].append(f"Order {order.order_id}: {str(e)}")
                    
            logger.warning(f"🚨 Emergency cancellation completed: "
                         f"{result['cancelled_orders']} cancelled, "
                         f"{result['failed_cancellations']} failed")
                         
        except Exception as e:
            logger.error(f"❌ Error in emergency cancellation: {e}")
            result['errors'].append(f"Emergency cancellation error: {str(e)}")
            
        return result

    def __repr__(self):
        status = "RUNNING" if self.is_monitoring else "STOPPED"
        return (f"<OrderTimeoutService(status={status}, "
                f"stale_found={self.stats['stale_orders_found']}, "
                f"recreated={self.stats['orders_recreated']})>")

```

### 📄 `src\domain\services\risk\stop_loss_monitor.py`

```python
# domain/services/risk/stop_loss_monitor.py
import asyncio
import logging
from typing import Dict, Optional

from src.domain.services.deals.deal_service import DealService
from src.domain.services.orders.order_execution_service import OrderExecutionService
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from src.domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer, OrderBookSignal

logger = logging.getLogger(__name__)


class StopLossMonitor:
    """
    Мониторит открытые сделки и инициирует stop-loss при падении цены.
    """

    def __init__(
        self,
        deal_service: DealService,
        order_execution_service: OrderExecutionService,
        exchange_connector: CcxtExchangeConnector,
        orderbook_analyzer: OrderBookAnalyzer,
        stop_loss_percent: float,
        check_interval_seconds: int,
        warning_percent: float = 5.0,
        critical_percent: float = 10.0,
        emergency_percent: float = 15.0,
    ):
        self.deal_service = deal_service
        self.order_execution_service = order_execution_service
        self.exchange_connector = exchange_connector
        self.orderbook_analyzer = orderbook_analyzer
        self.stop_loss_percent = stop_loss_percent
        self.warning_percent = warning_percent
        self.critical_percent = critical_percent
        self.emergency_percent = emergency_percent
        self.check_interval_seconds = check_interval_seconds
        self._is_running = False
        self._warned_deals = set()  # Отслеживаем уже предупрежденные сделки
        self._stats = {
            "checks_performed": 0,
            "warnings_sent": 0,
            "support_breaks": 0,
            "emergency_liquidations": 0,
            "stop_loss_triggered": 0,
        }

    async def start_monitoring(self):
        """Запускает мониторинг в фоновом режиме."""
        self._is_running = True
        logger.info(f"🚀 StopLossMonitor запущен с умным анализом стакана:")
        logger.info(f"   - {self.warning_percent}% предупреждение + проверка поддержки")
        logger.info(f"   - {self.critical_percent}% маркет-ордер при пробитии support_level")
        logger.info(f"   - {self.emergency_percent}% принудительная ликвидация")
        logger.info(f"   - Интервал проверки: {self.check_interval_seconds} сек.")
        while self._is_running:
            await self.check_open_deals()
            await asyncio.sleep(self.check_interval_seconds)

    def stop_monitoring(self):
        """Останавливает мониторинг."""
        self._is_running = False
        logger.info("🔴 StopLossMonitor остановлен.")

    async def check_open_deals(self, current_price: float = None, cached_orderbook: dict = None):
        """Проверяет все открытые сделки на предмет срабатывания stop-loss с анализом стакана."""
        self._stats["checks_performed"] += 1
        open_deals = self.deal_service.get_open_deals()

        for deal in open_deals:
            if not deal.buy_order or not deal.buy_order.is_filled():
                continue

            try:
                # Используем переданную цену или получаем с биржи
                if current_price is None:
                    ticker = await self.exchange_connector.fetch_ticker(deal.currency_pair_id)
                    price = ticker['last']
                else:
                    price = current_price
                    
                entry_price = deal.buy_order.price
                
                # Используем кешированный стакан или получаем новый
                if cached_orderbook is not None:
                    orderbook_metrics = self.orderbook_analyzer.analyze_orderbook(cached_orderbook)
                else:
                    orderbook = await self.exchange_connector.fetch_order_book(deal.currency_pair_id)
                    orderbook_metrics = self.orderbook_analyzer.analyze_orderbook(orderbook)

                price_drop_percent = ((entry_price - price) / entry_price) * 100

                # Уровень 1: -5% предупреждение + проверка поддержки
                if price_drop_percent >= self.warning_percent:
                    await self._handle_warning_level(deal, price_drop_percent, orderbook_metrics)
                
                # Уровень 2: -10% маркет-ордер при пробитии support_level
                if price_drop_percent >= self.critical_percent:
                    await self._handle_critical_level(deal, price_drop_percent, price, orderbook_metrics)
                
                # Уровень 3: -15% принудительная ликвидация
                if price_drop_percent >= self.emergency_percent:
                    await self._handle_emergency_level(deal, price_drop_percent, orderbook_metrics)

            except Exception as e:
                logger.error(f"Ошибка при проверке stop-loss для сделки #{deal.deal_id}: {e}")

    async def _handle_warning_level(self, deal, price_drop_percent: float, orderbook_metrics):
        """Уровень 1: -5% предупреждение + проверка поддержки"""
        if deal.deal_id not in self._warned_deals:
            support_info = ""
            if orderbook_metrics.support_level:
                support_info = f" | Поддержка: {orderbook_metrics.support_level:.6f}"
            
            logger.warning(f"⚠️  ПРЕДУПРЕЖДЕНИЕ: Просадка {price_drop_percent:.2f}% для сделки #{deal.deal_id}{support_info}")
            logger.warning(f"   Дисбаланс объемов: {orderbook_metrics.volume_imbalance:.1f}%")
            
            self._warned_deals.add(deal.deal_id)
            self._stats["warnings_sent"] += 1

    async def _handle_critical_level(self, deal, price_drop_percent: float, current_price: float, orderbook_metrics):
        """Уровень 2: -10% маркет-ордер при пробитии support_level"""
        support_broken = False
        
        if orderbook_metrics.support_level and current_price <= orderbook_metrics.support_level:
            support_broken = True
            logger.error(f"🔴 ПРОБИТИЕ ПОДДЕРЖКИ! Цена {current_price:.6f} <= поддержка {orderbook_metrics.support_level:.6f}")
            self._stats["support_breaks"] += 1
        
        # Дополнительные критерии для маркет-ордера
        critical_conditions = [
            support_broken,
            orderbook_metrics.volume_imbalance < -20,  # Сильный дисбаланс в сторону продаж
            orderbook_metrics.signal == OrderBookSignal.STRONG_SELL,
            orderbook_metrics.slippage_sell > 2.0  # Высокий слиппедж
        ]
        
        if any(critical_conditions):
            logger.error(f"🚨 КРИТИЧЕСКИЙ УРОВЕНЬ! Сделка #{deal.deal_id} - просадка {price_drop_percent:.2f}%")
            logger.error(f"   Условия: support_broken={support_broken}, imbalance={orderbook_metrics.volume_imbalance:.1f}%")
            await self._create_market_sell_order(deal)
            self._stats["stop_loss_triggered"] += 1

    async def _handle_emergency_level(self, deal, price_drop_percent: float, orderbook_metrics):
        """Уровень 3: -15% принудительная ликвидация"""
        logger.critical(f"🆘 ЭКСТРЕННАЯ ЛИКВИДАЦИЯ! Сделка #{deal.deal_id} - просадка {price_drop_percent:.2f}%")
        logger.critical(f"   Принудительная продажа по рынку!")
        
        await self._create_market_sell_order(deal, force=True)
        self._stats["emergency_liquidations"] += 1
        self._stats["stop_loss_triggered"] += 1

    async def _create_market_sell_order(self, deal, force: bool = False):
        """Создает маркет-ордер на продажу для ликвидации позиции"""
        try:
            if deal.buy_order and deal.buy_order.is_filled():
                # Отменяем существующий лимитный sell-ордер если есть
                if deal.sell_order and not deal.sell_order.is_filled():
                    await self.order_execution_service.cancel_order(deal.sell_order)
                    logger.info(f"Отменен лимитный SELL ордер для сделки #{deal.deal_id}")
                
                # Создаем маркет-ордер на продажу
                filled_amount = deal.buy_order.filled_amount
                
                market_sell_order = await self.order_execution_service.create_market_sell_order(
                    deal.currency_pair_id,
                    filled_amount,
                    deal.deal_id
                )
                
                if market_sell_order:
                    deal.sell_order = market_sell_order
                    logger.info(f"✅ Создан маркет SELL ордер #{market_sell_order.order_id} для сделки #{deal.deal_id}")
                    
                    # Закрываем сделку
                    await self.deal_service.close_deal(deal.deal_id)
                    logger.info(f"Сделка #{deal.deal_id} закрыта {'принудительно' if force else 'по стоп-лоссу'}")
                else:
                    logger.error(f"Не удалось создать маркет-ордер для сделки #{deal.deal_id}")
                    
        except Exception as e:
            logger.error(f"Ошибка при создании маркет-ордера для сделки #{deal.deal_id}: {e}")
            # В крайнем случае просто закрываем сделку
            await self.deal_service.close_deal(deal.deal_id)

    async def trigger_stop_loss(self, deal):
        """Старый метод для обратной совместимости"""
        logger.warning(f"🚨 Вызван старый метод trigger_stop_loss для сделки #{deal.deal_id}")
        await self._create_market_sell_order(deal)

    def get_statistics(self) -> Dict:
        """Возвращает статистику работы монитора."""
        return self._stats

```

### 📄 `src\domain\services\trading\__init__.py`

```python

```

### 📄 `src\domain\services\trading\signal_cooldown_manager.py`

```python
# domain/services/signal_cooldown_manager.py
from typing import Tuple

class SignalCooldownManager:
    """
    Защита от повторных сигналов BUY:
    - Только лимит активных сделок (без проверки цены)
    """
    
    def __init__(self):
        pass  # Убираем все переменные связанные с ценой
        
    def can_buy(self, active_deals_count: int, max_deals: int) -> Tuple[bool, str]:
        """
        Проверяет, можно ли выдать сигнал BUY
        
        Args:
            active_deals_count: Количество активных сделок
            max_deals: Максимальное количество сделок (deal_count)
            
        Returns:
            (can_buy: bool, reason: str)
        """
        
        # Проверка лимита сделок
        if active_deals_count >= max_deals:
            return False, f"🎯 Лимит сделок: {active_deals_count}/{max_deals}"

        return True, "✅ Можно покупать"
    
    def get_status(self, active_deals_count: int, max_deals: int) -> str:
        """
        Возвращает текущий статус менеджера
        """
        return f"🎯 Активных сделок: {active_deals_count}/{max_deals}"

```

### 📄 `src\domain\services\trading\trading_decision_engine.py`

```python
# domain/services/trading_decision_engine.py
from typing import Dict, Optional

from src.domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer, OrderBookMetrics, OrderBookSignal
from src.infrastructure.connectors.exchange_connector import ExchangeConnector


class TradingDecisionEngine:
    """Движок принятия торговых решений с учетом MACD + стакана"""

    def __init__(self, orderbook_analyzer: OrderBookAnalyzer, exchange_connector: ExchangeConnector):
        self.orderbook_analyzer = orderbook_analyzer
        self.exchange_connector = exchange_connector

    def check_balance(self, quote_currency: str, required_amount: float) -> (bool, str):
        """Проверяет, достаточно ли средств на балансе."""
        try:
            balance = self.exchange_connector.get_balance(quote_currency)
            if balance >= required_amount:
                return True, f"Баланс {quote_currency} достаточен: {balance:.2f}"
            else:
                return False, f"Недостаточно средств. Требуется: {required_amount:.2f}, доступно: {balance:.2f}"
        except Exception as e:
            return False, f"Ошибка при проверке баланса: {e}"

    def should_execute_trade(self, macd_signal: bool, orderbook_metrics: OrderBookMetrics,
                             quote_currency: str, required_amount: float) -> Dict:
        """Принятие решения о выполнении сделки"""
        
        result = {
            'execute': False,
            'reason': '',
            'confidence': 0,
            'modifications': {}
        }
        
        # Проверка баланса
        has_enough_balance, balance_reason = self.check_balance(quote_currency, required_amount)
        if not has_enough_balance:
            result['reason'] = f"❌ БАЛАНС: {balance_reason}"
            return result

        # Проверка сигнала стакана
        if orderbook_metrics.signal == OrderBookSignal.REJECT:
            result['reason'] = f"❌ СТАКАН: Отклонено (спред: {orderbook_metrics.bid_ask_spread:.3f}%, слиппедж: {orderbook_metrics.slippage_buy:.2f}%)"
            return result
            
        # Базовый MACD сигнал
        if not macd_signal:
            result['reason'] = "❌ MACD: Нет сигнала"
            return result
            
        # Анализ комбинированного сигнала
        if orderbook_metrics.signal in [OrderBookSignal.STRONG_BUY, OrderBookSignal.WEAK_BUY]:
            result['execute'] = True
            result['confidence'] = orderbook_metrics.confidence
            
            # Модификации на основе стакана
            modifications = {}
            
            # Корректировка цены входа по поддержке
            if orderbook_metrics.support_level:
                modifications['entry_price_hint'] = orderbook_metrics.support_level
                
            # Корректировка цены выхода по сопротивлению  
            if orderbook_metrics.resistance_level:
                modifications['exit_price_hint'] = orderbook_metrics.resistance_level
                
            # Корректировка размера позиции при высоком слиппедже
            if orderbook_metrics.slippage_buy > 0.5:
                modifications['reduce_position_size'] = 0.7  # Уменьшить на 30%
                
            result['modifications'] = modifications
            
            # Формирование описания
            signal_emoji = "🟢🔥" if orderbook_metrics.signal == OrderBookSignal.STRONG_BUY else "🟡"
            result['reason'] = f"{signal_emoji} СТАКАН ПОДДЕРЖИВАЕТ: {orderbook_metrics.signal.value} (доверие: {orderbook_metrics.confidence:.1%})"
            
        elif orderbook_metrics.signal == OrderBookSignal.NEUTRAL:
            result['execute'] = True  # Нейтральный стакан не мешает MACD
            result['confidence'] = 0.6
            result['reason'] = "🟡 СТАКАН НЕЙТРАЛЕН: MACD решает"
            
        else:  # WEAK_SELL, STRONG_SELL
            result['reason'] = f"❌ СТАКАН ПРОТИВ: {orderbook_metrics.signal.value} (дисбаланс: {orderbook_metrics.volume_imbalance:.1f}%)"
            
        return result
    
    def format_orderbook_info(self, metrics: OrderBookMetrics) -> str:
        """Форматирование информации о стакане"""
        info = []
        info.append(f"📊 АНАЛИЗ СТАКАНА:")
        info.append(f"   💱 Спред: {metrics.bid_ask_spread:.3f}%")
        info.append(f"   ⚖️ Дисбаланс: {metrics.volume_imbalance:+.1f}% {'(покупатели)' if metrics.volume_imbalance > 0 else '(продавцы)'}")
        info.append(f"   💧 Ликвидность: {metrics.liquidity_depth:.1f}")
        info.append(f"   📉 Слиппедж покупки: {metrics.slippage_buy:.2f}%")
        info.append(f"   📈 Слиппедж продажи: {metrics.slippage_sell:.2f}%")
        
        if metrics.support_level:
            info.append(f"   🛡️ Поддержка: {metrics.support_level:.4f}")
        if metrics.resistance_level:
            info.append(f"   🚧 Сопротивление: {metrics.resistance_level:.4f}")
            
        if metrics.big_walls:
            info.append(f"   🧱 Больших стен: {len(metrics.big_walls)}")
            
        return "\n".join(info)
    
    def apply_orderbook_modifications(self, current_price: float, budget: float, modifications: Dict) -> Dict:
        """🔧 FIX: Применение модификаций от анализа стакана с проверкой дистанции"""
        
        result = {
            'entry_price': current_price,
            'budget_multiplier': 1.0,
            'exit_price_hint': None,
            'modifications_applied': []
        }
        
        # 🔧 FIX: Применение entry_price_hint с проверкой дистанции
        if 'entry_price_hint' in modifications:
            hint = modifications['entry_price_hint']
            # Проверяем что хинт ниже текущей цены И не дальше 2%
            if hint < current_price and abs(hint/current_price - 1) < 0.02:
                result['entry_price'] = hint
                result['modifications_applied'].append(f"💡 Используем цену поддержки: {hint:.4f} вместо {current_price:.4f}")
        
        # 🔧 FIX: Применение exit_price_hint с проверкой дистанции
        if 'exit_price_hint' in modifications:
            hint = modifications['exit_price_hint']
            # Проверяем что хинт выше текущей цены И не дальше 2%
            if hint > current_price and abs(hint/current_price - 1) < 0.02:
                result['exit_price_hint'] = hint
                result['modifications_applied'].append(f"💡 Целевая цена сопротивления: {hint:.4f}")

        # Корректировка размера позиции
        if 'reduce_position_size' in modifications:
            result['budget_multiplier'] = modifications['reduce_position_size']
            result['modifications_applied'].append(f"⚠️ Уменьшаем размер позиции до {result['budget_multiplier']:.1%}")

        return result

```

### 📄 `src\domain\services\trading\trading_service.py`

```python
# domain/services/trading_service.py
from typing import Dict, Optional
from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.deals_repository import DealsRepository
from domain.services.orders.order_service import OrderService
import logging

logger = logging.getLogger(__name__)

class TradingService:
    """
    🎯 Главный сервис для управления торговыми операциями (TradingOrchestrator):
    - Координирует создание сделок и ордеров
    - Управляет жизненным циклом торговых операций
    - Связывает все торговые сервисы воедино

    Переписанный с учетом архитектурных принципов оркестратора.
    """

    def __init__(
        self,
        deals_repo: DealsRepository,
        order_service: OrderService,
        deal_factory: DealFactory
    ):
        self.deals_repo = deals_repo
        self.order_service = order_service
        self.deal_factory = deal_factory

    async def execute_buy_strategy(
        self,
        currency_pair: CurrencyPair,
        strategy_result: tuple
    ) -> Deal:
        """
        🛒 Исполняет стратегию покупки:
        1. Создает новую сделку
        2. Создает buy/sell ордера через OrderService
        3. Привязывает ордера к сделке
        """
        # Распаковываем результат калькулятора
        buy_price_calc, total_coins_needed, sell_price_calc, coins_to_sell, info_dict = strategy_result

        # 1. Создаем новую сделку
        new_deal = self.deal_factory.create_new_deal(currency_pair)
        self.deals_repo.save(new_deal)

        # 2. Создаем BUY ордер через OrderService
        buy_order = await self.order_service.create_and_place_buy_order(
            price=float(buy_price_calc),
            amount=float(total_coins_needed),
            deal_id=new_deal.deal_id,
            symbol=currency_pair.symbol
        )

        # 3. Создаем SELL ордер через OrderService
        sell_order = await self.order_service.create_and_place_sell_order(
            price=float(sell_price_calc),
            amount=float(coins_to_sell),
            deal_id=new_deal.deal_id,
            symbol=currency_pair.symbol
        )

        # 4. Привязываем ордера к сделке
        new_deal.attach_orders(buy_order, sell_order)
        self.deals_repo.save(new_deal)

        logger.info(f"\n🆕 Создана сделка #{new_deal.deal_id}")
        logger.info(f"   🛒 BUY: {buy_order}")
        logger.info(f"   🏷️ SELL: {sell_order}")

        return new_deal

    def process_open_deals(self):
        """
        📊 Обработка всех открытых сделок:
        - Проверка статусов ордеров
        - Закрытие завершенных сделок
        """
        open_deals = self.deals_repo.get_open_deals()
        for deal in open_deals:
            # Проверяем статусы ордеров через OrderService
            if deal.buy_order:
                updated_buy_order = self.order_service.get_order_status(deal.buy_order)
                if updated_buy_order and updated_buy_order.is_filled():
                    logger.info(
                        f"✅ BUY ордер #{deal.buy_order.order_id} исполнен"
                    )

            if deal.sell_order:
                updated_sell_order = self.order_service.get_order_status(deal.sell_order)
                if updated_sell_order and updated_sell_order.is_filled():
                    logger.info(
                        f"✅ SELL ордер #{deal.sell_order.order_id} исполнен"
                    )
                    self.close_deal(deal)

    def close_deal(self, deal: Deal):
        """
        🔒 Закрытие сделки с отменой незавершенных ордеров
        """
        if deal.is_open():
            # Отменяем открытые ордера через OrderService
            if deal.buy_order and deal.buy_order.is_open():
                self.order_service.cancel_order(deal.buy_order)
            if deal.sell_order and deal.sell_order.is_open():
                self.order_service.cancel_order(deal.sell_order)

            # Закрываем саму сделку
            deal.close()
            self.deals_repo.save(deal)
            logger.info(f"🔒 Закрыта сделка #{deal.deal_id}")

    def cancel_deal(self, deal: Deal):
        """
        ❌ Отменяет сделку и все связанные ордера
        """
        if deal.is_open():
            if deal.buy_order and deal.buy_order.is_open():
                self.order_service.cancel_order(deal.buy_order)
            if deal.sell_order and deal.sell_order.is_open():
                self.order_service.cancel_order(deal.sell_order)

            deal.cancel()
            self.deals_repo.save(deal)
            logger.warning(f"❌ Отменена сделка #{deal.deal_id}")

    def force_close_all_deals(self):
        """
        🚨 Экстренное закрытие всех открытых сделок
        """
        open_deals = self.deals_repo.get_open_deals()
        for deal in open_deals:
            self.close_deal(deal)
        logger.warning(f"🚨 Принудительно закрыто {len(open_deals)} сделок")

    def get_trading_statistics(self) -> Dict:
        """
        📈 Получение статистики торговли
        """
        open_deals = self.deals_repo.get_open_deals()
        all_deals = self.deals_repo.get_all()

        return {
            "open_deals_count": len(open_deals),
            "total_deals_count": len(all_deals),
            "can_create_new_deal": len(open_deals) < 10  # Примерный лимит
        }

    # === СТАРЫЕ МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ ===

    def create_new_deal(self, currency_pair: CurrencyPair) -> Deal:
        """
        Создаём сделку (совместимость со старым API)
        """
        deal = self.deal_factory.create_new_deal(currency_pair)
        self.deals_repo.save(deal)
        logger.info(f"[TradingService] Created new deal: {deal}")
        return deal

    def force_close_all(self):
        """
        Утилитарный метод: закрыть все открытые сделки (совместимость)
        """
        self.force_close_all_deals()

```

### 📄 `src\infrastructure\__init__.py`

```python
"""Infrastructure layer for external integrations."""
```

### 📄 `src\infrastructure\connectors\__init__.py`

```python
"""Exchange connectors for external API integrations."""
```

### 📄 `src\infrastructure\connectors\exchange_connector.py`

```python
# src/infrastructure/connectors/exchange_connector.py - УНИВЕРСАЛЬНАЯ ВЕРСИЯ
import asyncio
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path
import ccxt.pro as ccxtpro
import ccxt
from config.config_loader import load_config
from domain.entities.order import ExchangeInfo

logger = logging.getLogger(__name__)

class CcxtExchangeConnector:
    """
    УНИВЕРСАЛЬНЫЙ коннектор для биржи, использующий ccxt.pro.
    Поддерживает как RESTful-запросы (создание ордеров, баланс),
    так и WebSocket-стримы (watch_ticker, watch_order_book).
    """

    def __init__(self, exchange_name="binance", use_sandbox=False):
        self.exchange_name = exchange_name
        self.use_sandbox = use_sandbox
        self.config = None
        self.client = None  # Это будет ccxt.pro клиент

        self.exchange_info_cache = {}
        self._load_config()
        self._init_exchange_client()

    def _load_config(self):
        """Загружает конфигурацию API ключей"""
        try:
            full_config = load_config()
            env_key = 'sandbox' if self.use_sandbox else 'production'
            self.config = full_config.get('binance', {}).get(env_key, {})

            private_key_path = self.config.get('privateKeyPath')
            if private_key_path and Path(private_key_path).exists():
                with open(private_key_path, 'r') as f:
                    private_key = f.read()
                self.config['secret'] = private_key
                self.config['privateKey'] = private_key

            logger.info(f"✅ Config loaded for {self.exchange_name} ({'sandbox' if self.use_sandbox else 'production'})")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            raise

    def _init_exchange_client(self):
        """Инициализирует ccxt.pro клиент"""
        try:
            exchange_class = getattr(ccxtpro, self.exchange_name)
            settings = {
                'apiKey': self.config.get('apiKey'),
                'secret': self.config.get('secret'),
                'enableRateLimit': True,
                'newUpdates': True,
                'options': {'defaultType': 'spot'}
            }
            self.client = exchange_class(settings)

            if self.use_sandbox:
                self.client.set_sandbox_mode(True)
                logger.info("🧪 Sandbox mode enabled")

            logger.info(f"✅ CCXT.pro client initialized for {self.exchange_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ccxt.pro client: {e}")
            raise

    def _normalize_symbol(self, symbol: str) -> str:
        """Преобразует 'ETHUSDT' -> 'ETH/USDT'"""
        if not symbol: return None
        if '/' in symbol: return symbol
        if symbol.endswith('USDT'): return f"{symbol[:-4]}/USDT"
        if symbol.endswith('USDC'): return f"{symbol[:-4]}/USDC"
        return symbol

    async def watch_order_book(self, symbol: str):
        return await self.client.watch_order_book(self._normalize_symbol(symbol))

    async def fetch_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Получение стакана заявок (разовый запрос)"""
        normalized_symbol = self._normalize_symbol(symbol)
        return await self.client.fetch_order_book(normalized_symbol, limit)

    async def watch_ticker(self, symbol: str):
        return await self.client.watch_ticker(self._normalize_symbol(symbol))

    async def watch_trades(self, symbol: str):
        return await self.client.watch_trades(self._normalize_symbol(symbol))

    async def watch_ohlcv(self, symbol: str, timeframe='1m'):
        return await self.client.watch_ohlcv(self._normalize_symbol(symbol), timeframe)

    async def load_markets(self, reload=False):
        return await self.client.load_markets(reload)

    async def create_order(self, symbol: str, side: str, order_type: str, amount: float, price: float = None, params: Dict[str, Any] = None):
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"📤 Creating {side.upper()} {order_type} order: {amount} {normalized_symbol} @ {price}")
            result = await self.client.create_order(normalized_symbol, order_type, side, amount, price, params or {})
            logger.info(f"✅ Order created successfully: {result.get('id', 'N/A')}")
            return result
        except ccxt.InsufficientFunds as e:
            logger.error(f"💸 Insufficient funds: {e}")
            raise
        except ccxt.InvalidOrder as e:
            logger.error(f"❌ Invalid order: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error creating order: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"❌ Cancelling order {order_id} for {normalized_symbol}")
            result = await self.client.cancel_order(order_id, normalized_symbol)
            logger.info(f"✅ Order cancelled successfully: {order_id}")
            return result
        except ccxt.OrderNotFound:
            logger.warning(f"⚠️ Order not found on exchange: {order_id}")
            raise  # Пробрасываем исключение дальше
        except Exception as e:
            logger.error(f"❌ Error cancelling order {order_id}: {e}")
            raise

    async def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        result = await self.client.fetch_order(order_id, self._normalize_symbol(symbol))
        return result

    async def fetch_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        return await self.client.fetch_open_orders(self._normalize_symbol(symbol))

    async def fetch_balance(self) -> Dict[str, Any]:
        return await self.client.fetch_balance()

    async def get_available_balance(self, currency: str) -> float:
        balance = await self.fetch_balance()
        return balance.get(currency, {}).get('free', 0.0)

    async def get_balance(self, currency: str) -> float:
        """Для совместимости со старым кодом"""
        return await self.get_available_balance(currency)

    async def check_sufficient_balance(self, symbol: str, side: str, amount: float, price: float = None) -> Tuple[bool, str, float]:
        """Проверка достаточности баланса для ордера"""
        try:
            base_currency, quote_currency = self._normalize_symbol(symbol).split('/')

            if side.lower() == 'buy':
                required_amount = amount * (price or 0)
                available = await self.get_available_balance(quote_currency)
                return available >= required_amount, quote_currency, available
            else:
                available = await self.get_available_balance(base_currency)
                return available >= amount, base_currency, available

        except Exception as e:
            logger.error(f"❌ Error checking balance: {e}")
            return False, "UNKNOWN", 0.0

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        return await self.client.fetch_ticker(self._normalize_symbol(symbol))

    async def get_symbol_info(self, symbol: str) -> ExchangeInfo:
        normalized_symbol = self._normalize_symbol(symbol)
        if normalized_symbol in self.exchange_info_cache:
            return self.exchange_info_cache[normalized_symbol]

        markets = await self.load_markets()
        market_info = markets.get(normalized_symbol)
        if not market_info:
            raise ValueError(f"Symbol {normalized_symbol} not found in markets")

        limits = market_info.get('limits', {})
        precision = market_info.get('precision', {})
        exchange_info = ExchangeInfo(
            symbol=normalized_symbol,
            min_qty=limits.get('amount', {}).get('min'),
            max_qty=limits.get('amount', {}).get('max'),
            step_size=precision.get('amount'),
            min_price=limits.get('price', {}).get('min'),
            max_price=limits.get('price', {}).get('max'),
            tick_size=precision.get('price'),
            min_notional=limits.get('cost', {}).get('min'),
            fees={'maker': market_info.get('maker', 0.001), 'taker': market_info.get('taker', 0.001)},
            precision=precision # ❗️ ДОБАВЛЕНО: сохраняем весь словарь
        )
        self.exchange_info_cache[normalized_symbol] = exchange_info
        return exchange_info

    async def create_market_sell_order(self, symbol: str, amount: float):
        """🚨 Создание маркет-ордера на продажу для стоп-лосса"""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"🚨 Creating MARKET SELL order: {amount} {normalized_symbol}")
            
            # Создаем маркет-ордер на продажу
            result = await self.client.create_market_sell_order(normalized_symbol, amount)
            
            if result:
                logger.info(f"✅ Market SELL order created successfully: {result.get('id', 'N/A')}")
                # Возвращаем результат в стандартном формате
                from domain.entities.order import OrderExecutionResult
                return OrderExecutionResult(
                    success=True,
                    exchange_order_id=result.get('id'),
                    filled_amount=result.get('filled', amount),
                    average_price=result.get('average'),
                    fees=result.get('fee', {}).get('cost', 0.0),
                    timestamp=result.get('timestamp')
                )
            else:
                logger.error("❌ Failed to create market sell order - no result")
                return None
                
        except ccxt.InsufficientFunds as e:
            logger.error(f"💸 Insufficient funds for market sell: {e}")
            return None
        except ccxt.InvalidOrder as e:
            logger.error(f"❌ Invalid market sell order: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error creating market sell order: {e}")
            return None

    async def test_connection(self) -> bool:
        try:
            await self.fetch_balance()
            logger.info(f"✅ Connection test successful for {self.exchange_name} ({'sandbox' if self.use_sandbox else 'production'})")
            return True
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    async def close(self):
        logger.info(f"🔌 Closing connection for {self.exchange_name} ({'sandbox' if self.use_sandbox else 'production'})")
        await self.client.close()
```

### 📄 `src\infrastructure\repositories\__init__.py`

```python
"""Data repositories for persistence layer."""
```

### 📄 `src\infrastructure\repositories\deals_repository.py`

```python
# my_trading_app/infrastructure/repositories/deals_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.deal import Deal

class DealsRepository(ABC):
    """
    Интерфейс (абстрактный класс) для хранения и извлечения сделок (Deal).
    """

    @abstractmethod
    def save(self, deal: Deal) -> None:
        pass

    @abstractmethod
    def get_by_id(self, deal_id: int) -> Optional[Deal]:
        pass

    @abstractmethod
    def get_open_deals(self) -> List[Deal]:
        pass

    @abstractmethod
    def get_all(self) -> List[Deal]:
        pass


class InMemoryDealsRepository(DealsRepository):
    """
    Простейшая InMemory-реализация.
    Хранит Deal в словаре {deal_id: Deal}.
    """

    def __init__(self):
        self._storage = {}

    def save(self, deal: Deal) -> None:
        self._storage[deal.deal_id] = deal

    def get_by_id(self, deal_id: int) -> Optional[Deal]:
        return self._storage.get(deal_id)

    def get_open_deals(self) -> List[Deal]:
        return [d for d in self._storage.values() if d.is_open()]

    def get_all(self) -> List[Deal]:
        """Возвращает все сделки (открытые, закрытые, отмененные)"""
        return list(self._storage.values())

```

### 📄 `src\infrastructure\repositories\orders_repository.py`

```python
# infrastructure/repositories/orders_repository.py.new - ENHANCED для реальной торговли
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from domain.entities.order import Order
import json
import logging

logger = logging.getLogger(__name__)

class OrdersRepository(ABC):
    """
    🚀 РАСШИРЕННЫЙ интерфейс репозитория для ордеров с поддержкой биржевых операций
    """

    @abstractmethod
    def save(self, order: Order) -> None:
        """Сохранить ордер"""
        pass

    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Получить ордер по локальному ID"""
        pass

    @abstractmethod
    def get_by_exchange_id(self, exchange_id: str) -> Optional[Order]:
        """🆕 Получить ордер по ID биржи"""
        pass

    @abstractmethod
    def get_all_by_deal(self, deal_id: int) -> List[Order]:
        """Получить все ордера сделки"""
        pass

    @abstractmethod
    def get_all(self) -> List[Order]:
        """Получить все ордера"""
        pass

    @abstractmethod
    def get_open_orders(self) -> List[Order]:
        """🆕 Получить только открытые ордера"""
        pass

    @abstractmethod
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """🆕 Получить ордера по торговой паре"""
        pass

    @abstractmethod
    def get_orders_by_status(self, status: str) -> List[Order]:
        """🆕 Получить ордера по статусу"""
        pass

    @abstractmethod
    def get_pending_orders(self) -> List[Order]:
        """🆕 Получить ордера в ожидании размещения"""
        pass

    @abstractmethod
    def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """🆕 Получить ордера за период"""
        pass

    @abstractmethod
    def bulk_update_status(self, order_ids: List[int], status: str) -> int:
        """🆕 Массовое обновление статуса"""
        pass

    @abstractmethod
    def delete_old_orders(self, older_than_days: int) -> int:
        """🆕 Удаление старых ордеров"""
        pass


class InMemoryOrdersRepository(OrdersRepository):
    """
    🚀 РАСШИРЕННАЯ InMemory реализация с поддержкой всех новых методов
    Подходит для MVP, но в production нужна БД
    """

    def __init__(self, max_orders: int = 10000):
        self._storage: Dict[int, Order] = {}
        self._exchange_id_index: Dict[str, int] = {}  # exchange_id -> order_id
        self._symbol_index: Dict[str, List[int]] = {}  # symbol -> [order_ids]
        self._deal_index: Dict[int, List[int]] = {}    # deal_id -> [order_ids]
        self._status_index: Dict[str, List[int]] = {}  # status -> [order_ids]
        self.max_orders = max_orders

        # Статистика
        self.stats = {
            'total_saves': 0,
            'total_queries': 0,
            'index_rebuilds': 0
        }

    def save(self, order: Order) -> None:
        """Сохранить ордер с обновлением индексов"""
        try:
            # Проверяем лимит
            if len(self._storage) >= self.max_orders and order.order_id not in self._storage:
                self._cleanup_old_orders()

            # Удаляем старые индексы если ордер уже существует
            if order.order_id in self._storage:
                self._remove_from_indexes(self._storage[order.order_id])

            # Сохраняем ордер
            self._storage[order.order_id] = order

            # Обновляем индексы
            self._add_to_indexes(order)

            self.stats['total_saves'] += 1
            logger.debug(f"💾 Order {order.order_id} saved successfully")

        except Exception as e:
            logger.error(f"❌ Error saving order {order.order_id}: {e}")
            raise

    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Получить ордер по локальному ID"""
        self.stats['total_queries'] += 1
        return self._storage.get(order_id)

    def get_by_exchange_id(self, exchange_id: str) -> Optional[Order]:
        """🆕 Получить ордер по ID биржи"""
        self.stats['total_queries'] += 1
        order_id = self._exchange_id_index.get(exchange_id)
        if order_id:
            return self._storage.get(order_id)
        return None

    def get_all_by_deal(self, deal_id: int) -> List[Order]:
        """Получить все ордера сделки"""
        self.stats['total_queries'] += 1
        order_ids = self._deal_index.get(deal_id, [])
        return [self._storage[oid] for oid in order_ids if oid in self._storage]

    def get_all(self) -> List[Order]:
        """Получить все ордера"""
        self.stats['total_queries'] += 1
        return list(self._storage.values())

    def get_open_orders(self) -> List[Order]:
        """🆕 Получить только открытые ордера"""
        self.stats['total_queries'] += 1
        open_statuses = [Order.STATUS_OPEN, Order.STATUS_PARTIALLY_FILLED]
        orders = []
        for status in open_statuses:
            order_ids = self._status_index.get(status, [])
            orders.extend([self._storage[oid] for oid in order_ids if oid in self._storage])
        return orders

    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """🆕 Получить ордера по торговой паре"""
        self.stats['total_queries'] += 1
        order_ids = self._symbol_index.get(symbol, [])
        return [self._storage[oid] for oid in order_ids if oid in self._storage]

    def get_orders_by_status(self, status: str) -> List[Order]:
        """🆕 Получить ордера по статусу"""
        self.stats['total_queries'] += 1
        order_ids = self._status_index.get(status, [])
        return [self._storage[oid] for oid in order_ids if oid in self._storage]

    def get_pending_orders(self) -> List[Order]:
        """🆕 Получить ордера в ожидании размещения"""
        return self.get_orders_by_status(Order.STATUS_PENDING)

    def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """🆕 Получить ордера за период"""
        self.stats['total_queries'] += 1
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)

        orders = []
        for order in self._storage.values():
            if start_timestamp <= order.created_at <= end_timestamp:
                orders.append(order)

        return sorted(orders, key=lambda x: x.created_at, reverse=True)

    def bulk_update_status(self, order_ids: List[int], status: str) -> int:
        """🆕 Массовое обновление статуса"""
        updated_count = 0

        for order_id in order_ids:
            if order_id in self._storage:
                order = self._storage[order_id]
                old_status = order.status

                # Обновляем статус
                order.status = status
                order.last_update = int(datetime.now().timestamp() * 1000)

                # Обновляем индексы
                self._update_status_index(order, old_status, status)
                updated_count += 1

        logger.info(f"📊 Bulk updated {updated_count} orders to status {status}")
        return updated_count

    def delete_old_orders(self, older_than_days: int) -> int:
        """🆕 Удаление старых ордеров"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        cutoff_timestamp = int(cutoff_date.timestamp() * 1000)

        to_delete = []
        for order_id, order in self._storage.items():
            # Удаляем только закрытые старые ордера
            if (order.closed_at and order.closed_at < cutoff_timestamp) or \
               (not order.closed_at and order.created_at < cutoff_timestamp and order.is_closed()):
                to_delete.append(order_id)

        deleted_count = 0
        for order_id in to_delete:
            order = self._storage[order_id]
            self._remove_from_indexes(order)
            del self._storage[order_id]
            deleted_count += 1

        logger.info(f"🗑️ Deleted {deleted_count} old orders (older than {older_than_days} days)")
        return deleted_count

    # 🔧 МЕТОДЫ УПРАВЛЕНИЯ ИНДЕКСАМИ

    def _add_to_indexes(self, order: Order):
        """Добавляет ордер во все индексы"""
        # Exchange ID index
        if order.exchange_id:
            self._exchange_id_index[order.exchange_id] = order.order_id

        # Symbol index
        if order.symbol:
            if order.symbol not in self._symbol_index:
                self._symbol_index[order.symbol] = []
            if order.order_id not in self._symbol_index[order.symbol]:
                self._symbol_index[order.symbol].append(order.order_id)

        # Deal index
        if order.deal_id:
            if order.deal_id not in self._deal_index:
                self._deal_index[order.deal_id] = []
            if order.order_id not in self._deal_index[order.deal_id]:
                self._deal_index[order.deal_id].append(order.order_id)

        # Status index
        if order.status not in self._status_index:
            self._status_index[order.status] = []
        if order.order_id not in self._status_index[order.status]:
            self._status_index[order.status].append(order.order_id)

    def _remove_from_indexes(self, order: Order):
        """Удаляет ордер из всех индексов"""
        # Exchange ID index
        if order.exchange_id and order.exchange_id in self._exchange_id_index:
            del self._exchange_id_index[order.exchange_id]

        # Symbol index
        if order.symbol and order.symbol in self._symbol_index:
            if order.order_id in self._symbol_index[order.symbol]:
                self._symbol_index[order.symbol].remove(order.order_id)
            if not self._symbol_index[order.symbol]:
                del self._symbol_index[order.symbol]

        # Deal index
        if order.deal_id and order.deal_id in self._deal_index:
            if order.order_id in self._deal_index[order.deal_id]:
                self._deal_index[order.deal_id].remove(order.order_id)
            if not self._deal_index[order.deal_id]:
                del self._deal_index[order.deal_id]

        # Status index
        if order.status in self._status_index:
            if order.order_id in self._status_index[order.status]:
                self._status_index[order.status].remove(order.order_id)
            if not self._status_index[order.status]:
                del self._status_index[order.status]

    def _update_status_index(self, order: Order, old_status: str, new_status: str):
        """Обновляет индекс статусов при изменении статуса"""
        # Удаляем из старого статуса
        if old_status in self._status_index and order.order_id in self._status_index[old_status]:
            self._status_index[old_status].remove(order.order_id)
            if not self._status_index[old_status]:
                del self._status_index[old_status]

        # Добавляем в новый статус
        if new_status not in self._status_index:
            self._status_index[new_status] = []
        if order.order_id not in self._status_index[new_status]:
            self._status_index[new_status].append(order.order_id)

    def _cleanup_old_orders(self):
        """Очистка старых ордеров при достижении лимита"""
        if len(self._storage) < self.max_orders:
            return

        # Удаляем 10% самых старых закрытых ордеров
        closed_orders = []
        for order in self._storage.values():
            if order.is_closed():
                closed_orders.append((order.order_id, order.closed_at or order.created_at))

        # Сортируем по времени закрытия
        closed_orders.sort(key=lambda x: x[1])

        # Удаляем самые старые
        to_delete_count = max(1, len(closed_orders) // 10)
        for i in range(min(to_delete_count, len(closed_orders))):
            order_id = closed_orders[i][0]
            order = self._storage[order_id]
            self._remove_from_indexes(order)
            del self._storage[order_id]

        logger.info(f"🧹 Cleaned up {to_delete_count} old orders")

    def rebuild_indexes(self):
        """🔧 Перестроение всех индексов"""
        logger.info("🔧 Rebuilding orders indexes...")

        # Очищаем индексы
        self._exchange_id_index.clear()
        self._symbol_index.clear()
        self._deal_index.clear()
        self._status_index.clear()

        # Перестраиваем
        for order in self._storage.values():
            self._add_to_indexes(order)

        self.stats['index_rebuilds'] += 1
        logger.info("✅ Orders indexes rebuilt successfully")

    # 📊 СТАТИСТИКА И МОНИТОРИНГ

    def get_statistics(self) -> Dict[str, Any]:
        """📊 Получение статистики репозитория"""
        total_orders = len(self._storage)

        # Группировка по статусам
        status_counts = {}
        for status, order_ids in self._status_index.items():
            status_counts[status] = len(order_ids)

        # Группировка по символам
        symbol_counts = {}
        for symbol, order_ids in self._symbol_index.items():
            symbol_counts[symbol] = len(order_ids)

        return {
            'total_orders': total_orders,
            'max_orders': self.max_orders,
            'usage_percent': (total_orders / self.max_orders) * 100,
            'status_distribution': status_counts,
            'symbol_distribution': symbol_counts,
            'total_deals': len(self._deal_index),
            'orders_with_exchange_id': len(self._exchange_id_index),
            'performance_stats': self.stats.copy()
        }

    def export_to_json(self, file_path: str = None) -> str:
        """💾 Экспорт всех ордеров в JSON"""
        orders_data = []
        for order in self._storage.values():
            orders_data.append(order.to_dict())

        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_orders': len(orders_data),
            'orders': orders_data,
            'statistics': self.get_statistics()
        }

        json_data = json.dumps(export_data, indent=2, default=str)

        if file_path:
            with open(file_path, 'w') as f:
                f.write(json_data)
            logger.info(f"📁 Orders exported to {file_path}")

        return json_data

    def import_from_json(self, json_data: str = None, file_path: str = None) -> int:
        """📥 Импорт ордеров из JSON"""
        try:
            if file_path:
                with open(file_path, 'r') as f:
                    json_data = f.read()

            if not json_data:
                raise ValueError("No JSON data provided")

            data = json.loads(json_data)
            orders_data = data.get('orders', [])

            imported_count = 0
            for order_dict in orders_data:
                try:
                    order = Order.from_dict(order_dict)
                    self.save(order)
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Failed to import order: {e}")

            logger.info(f"📥 Imported {imported_count} orders")
            return imported_count

        except Exception as e:
            logger.error(f"❌ Error importing orders: {e}")
            return 0

    # 🔍 РАСШИРЕННЫЕ ПОИСКОВЫЕ МЕТОДЫ

    def search_orders(
        self,
        symbol: str = None,
        status: str = None,
        deal_id: int = None,
        exchange_id: str = None,
        side: str = None,
        order_type: str = None,
        min_amount: float = None,
        max_amount: float = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = None
    ) -> List[Order]:
        """🔍 Комплексный поиск ордеров по множественным критериям"""
        self.stats['total_queries'] += 1

        # Начинаем со всех ордеров
        candidates = list(self._storage.values())

        # Применяем фильтры
        if symbol:
            candidates = [o for o in candidates if o.symbol == symbol]
        if status:
            candidates = [o for o in candidates if o.status == status]
        if deal_id:
            candidates = [o for o in candidates if o.deal_id == deal_id]
        if exchange_id:
            candidates = [o for o in candidates if o.exchange_id == exchange_id]
        if side:
            candidates = [o for o in candidates if o.side == side]
        if order_type:
            candidates = [o for o in candidates if o.order_type == order_type]
        if min_amount:
            candidates = [o for o in candidates if o.amount >= min_amount]
        if max_amount:
            candidates = [o for o in candidates if o.amount <= max_amount]

        # Фильтр по дате
        if date_from:
            from_timestamp = int(date_from.timestamp() * 1000)
            candidates = [o for o in candidates if o.created_at >= from_timestamp]
        if date_to:
            to_timestamp = int(date_to.timestamp() * 1000)
            candidates = [o for o in candidates if o.created_at <= to_timestamp]

        # Сортируем по времени создания (новые первые)
        candidates.sort(key=lambda x: x.created_at, reverse=True)

        # Применяем лимит
        if limit:
            candidates = candidates[:limit]

        return candidates

    def get_orders_with_errors(self) -> List[Order]:
        """⚠️ Получить ордера с ошибками"""
        orders_with_errors = []
        for order in self._storage.values():
            if order.error_message or order.status == Order.STATUS_FAILED:
                orders_with_errors.append(order)
        return orders_with_errors

    def get_orders_requiring_sync(self) -> List[Order]:
        """🔄 Получить ордера требующие синхронизации с биржей"""
        sync_required = []
        current_time = int(datetime.now().timestamp() * 1000)

        for order in self._storage.values():
            # Ордера открытые более 5 минут без обновлений
            if (order.is_open() and
                order.exchange_id and
                current_time - order.last_update > 5 * 60 * 1000):
                sync_required.append(order)

        return sync_required

```

### 📄 `src\infrastructure\repositories\tickers_repository.py`

```python
import json
import os
import pandas as pd
from typing import List, Dict
from domain.entities.ticker import Ticker


class InMemoryTickerRepository:
    def __init__(self, max_size: int = 1000, dump_file: str = "tickers_dump.json"):
        self.tickers = []
        self.max_size = max_size
        self.dump_file = dump_file

        # 🆕 Кеши для оптимизации
        self._last_n_cache = {}  # Кеш для get_last_n
        self._cache_valid_size = 0  # Размер когда кеш был создан

    def save(self, ticker: Ticker):
        """Оптимизированное сохранение"""
        self.tickers.append(ticker)

        # Очищаем кеш при изменении размера
        if len(self.tickers) != self._cache_valid_size:
            self._last_n_cache.clear()
            self._cache_valid_size = len(self.tickers)

        # Ограничиваем размер
        if len(self.tickers) > self.max_size:
            # Удаляем старые записи батчами для производительности
            remove_count = self.max_size // 10  # Удаляем 10%
            self.tickers = self.tickers[remove_count:]

    def get_last_n(self, n: int) -> List[Ticker]:
        """🚀 КЕШИРОВАННОЕ получение последних N тикеров"""

        # Проверяем кеш
        cache_key = f"last_{n}"
        current_size = len(self.tickers)

        if cache_key in self._last_n_cache and current_size == self._cache_valid_size:
            return self._last_n_cache[cache_key]

        # Создаем результат и кешируем
        result = self.tickers[-n:] if len(self.tickers) >= n else self.tickers.copy()
        self._last_n_cache[cache_key] = result
        self._cache_valid_size = current_size

        return result
```

## 📄 TXT файлы

### 📄 `exchange_analysis_report.txt`

```text

========================================
--- 1. Анализ объекта биржи ---
========================================
ID Биржи: binance
Название: Binance
Поддерживаемые возможности (has):
{'addMargin': True,
 'borrowCrossMargin': True,
 'borrowIsolatedMargin': True,
 'cancelAllOrders': True,
 'cancelAllOrdersWs': True,
 'cancelOrder': True,
 'cancelOrderWs': True,
 'cancelOrders': True,
 'createConvertTrade': True,
 'createLimitBuyOrder': True,
 'createLimitOrder': True,
 'createLimitSellOrder': True,
 'createMarketBuyOrder': True,
 'createMarketBuyOrderWithCost': True,
 'createMarketOrder': True,
 'createMarketOrderWithCost': True,
 'createMarketOrderWs': True,
 'createMarketSellOrder': True,
 'createMarketSellOrderWithCost': True,
 'createOrder': True,
 'createOrderWs': True,
 'createOrders': True,
 'createPostOnlyOrder': True,
 'createReduceOnlyOrder': True,
 'createStopLimitOrder': True,
 'createStopLossOrder': True,
 'createStopOrder': True,
 'createTakeProfitOrder': True,
 'createTrailingPercentOrder': True,
 'createTriggerOrder': True,
 'editOrder': True,
 'editOrderWs': True,
 'editOrders': True,
 'fetchAllGreeks': True,
 'fetchBalance': True,
 'fetchBalanceWs': True,
 'fetchBidsAsks': True,
 'fetchBorrowInterest': True,
 'fetchBorrowRateHistory': True,
 'fetchCanceledAndClosedOrders': 'emulated',
 'fetchCanceledOrders': 'emulated',
 'fetchClosedOrders': 'emulated',
 'fetchConvertCurrencies': True,
 'fetchConvertQuote': True,
 'fetchConvertTrade': True,
 'fetchConvertTradeHistory': True,
 'fetchCrossBorrowRate': True,
 'fetchCurrencies': True,
 'fetchCurrenciesWs': 'emulated',
 'fetchDepositAddress': True,
 'fetchDepositWithdrawFee': 'emulated',
 'fetchDepositWithdrawFees': True,
 'fetchDeposits': True,
 'fetchFundingHistory': True,
 'fetchFundingInterval': 'emulated',
 'fetchFundingIntervals': True,
 'fetchFundingRate': True,
 'fetchFundingRateHistory': True,
 'fetchFundingRates': True,
 'fetchGreeks': True,
 'fetchIndexOHLCV': True,
 'fetchIsolatedBorrowRate': 'emulated',
 'fetchIsolatedBorrowRates': True,
 'fetchL2OrderBook': True,
 'fetchLastPrices': True,
 'fetchLedger': True,
 'fetchLedgerEntry': True,
 'fetchLeverage': 'emulated',
 'fetchLeverageTiers': True,
 'fetchLeverages': True,
 'fetchLongShortRatioHistory': True,
 'fetchMarginAdjustmentHistory': True,
 'fetchMarginMode': True,
 'fetchMarginModes': True,
 'fetchMarkOHLCV': True,
 'fetchMarkPrice': True,
 'fetchMarkPrices': True,
 'fetchMarketLeverageTiers': 'emulated',
 'fetchMarkets': True,
 'fetchMyLiquidations': True,
 'fetchMySettlementHistory': True,
 'fetchMyTrades': True,
 'fetchMyTradesWs': True,
 'fetchOHLCV': True,
 'fetchOHLCVWs': True,
 'fetchOpenInterest': True,
 'fetchOpenInterestHistory': True,
 'fetchOpenOrder': True,
 'fetchOpenOrders': True,
 'fetchOpenOrdersWs': True,
 'fetchOption': True,
 'fetchOrder': True,
 'fetchOrderBook': True,
 'fetchOrderBookWs': True,
 'fetchOrderTrades': True,
 'fetchOrderWs': True,
 'fetchOrders': True,
 'fetchOrdersWs': True,
 'fetchPosition': True,
 'fetchPositionForSymbolWs': True,
 'fetchPositionMode': True,
 'fetchPositionWs': True,
 'fetchPositions': True,
 'fetchPositionsRisk': True,
 'fetchPositionsWs': True,
 'fetchPremiumIndexOHLCV': True,
 'fetchSettlementHistory': True,
 'fetchStatus': True,
 'fetchTicker': True,
 'fetchTickerWs': True,
 'fetchTickers': True,
 'fetchTime': True,
 'fetchTrades': True,
 'fetchTradesWs': True,
 'fetchTradingFee': True,
 'fetchTradingFees': True,
 'fetchTradingLimits': 'emulated',
 'fetchTransactionFee': 'emulated',
 'fetchTransactionFees': True,
 'fetchTransfers': True,
 'fetchWithdrawals': True,
 'future': True,
 'margin': True,
 'option': True,
 'privateAPI': True,
 'publicAPI': True,
 'reduceMargin': True,
 'repayCrossMargin': True,
 'repayIsolatedMargin': True,
 'sandbox': True,
 'setLeverage': True,
 'setMarginMode': True,
 'setPositionMode': True,
 'spot': True,
 'swap': True,
 'transfer': True,
 'watchBalance': True,
 'watchBidsAsks': True,
 'watchLiquidations': True,
 'watchLiquidationsForSymbols': True,
 'watchMarkPrice': True,
 'watchMarkPrices': True,
 'watchMyLiquidations': True,
 'watchMyLiquidationsForSymbols': True,
 'watchMyTrades': True,
 'watchOHLCV': True,
 'watchOHLCVForSymbols': True,
 'watchOrderBook': True,
 'watchOrderBookForSymbols': True,
 'watchOrders': True,
 'watchOrdersForSymbols': True,
 'watchPositions': True,
 'watchTicker': True,
 'watchTickers': True,
 'watchTrades': True,
 'watchTradesForSymbols': True,
 'withdraw': True,
 'ws': True}


========================================
--- 2. Анализ рынков (валютных пар) ---
========================================
Всего загружено рынков: 2047

Анализ конкретного рынка: ETH/USDT
{
  'active': True,
  'base': 'ETH',
  'baseId': 'ETH',
  'contract': False,
  'contractSize': None,
  'created': None,
  'expiry': None,
  'expiryDatetime': None,
  'feeSide': 'get',
  'future': False,
  'id': 'ETHUSDT',
  'index': None,
  'info': {
    'allowTrailingStop': True,
    'allowedSelfTradePreventionModes': [
      'NONE',
      'EXPIRE_TAKER',
      'EXPIRE_MAKER',
      'EXPIRE_BOTH',
      'DECREMENT'
    ],
    'amendAllowed': True,
    'baseAsset': 'ETH',
    'baseAssetPrecision': '8',
    'baseCommissionPrecision': '8',
    'cancelReplaceAllowed': True,
    'defaultSelfTradePreventionMode': 'EXPIRE_MAKER',
    'filters': [
      {
        'filterType': 'PRICE_FILTER',
        'maxPrice': '1000000.00000000',
        'minPrice': '0.01000000',
        'tickSize': '0.01000000'
      },
      {
        'filterType': 'LOT_SIZE',
        'maxQty': '9000.00000000',
        'minQty': '0.00010000',
        'stepSize': '0.00010000'
      },
      {
        'filterType': 'ICEBERG_PARTS',
        'limit': '10'
      },
      {
        'filterType': 'MARKET_LOT_SIZE',
        'maxQty': '3730.93834769',
        'minQty': '0.00000000',
        'stepSize': '0.00000000'
      },
      {
        'filterType': 'TRAILING_DELTA',
        'maxTrailingAboveDelta': '2000',
        'maxTrailingBelowDelta': '2000',
        'minTrailingAboveDelta': '10',
        'minTrailingBelowDelta': '10'
      },
      {
        'askMultiplierDown': '0.2',
        'askMultiplierUp': '5',
        'avgPriceMins': '5',
        'bidMultiplierDown': '0.2',
        'bidMultiplierUp': '5',
        'filterType': 'PERCENT_PRICE_BY_SIDE'
      },
      {
        'applyMaxToMarket': False,
        'applyMinToMarket': True,
        'avgPriceMins': '5',
        'filterType': 'NOTIONAL',
        'maxNotional': '9000000.00000000',
        'minNotional': '5.00000000'
      },
      {
        'filterType': 'MAX_NUM_ORDERS',
        'maxNumOrders': '200'
      },
      {
        'filterType': 'MAX_NUM_ALGO_ORDERS',
        'maxNumAlgoOrders': '5'
      }
    ],
    'icebergAllowed': True,
    'isMarginTradingAllowed': False,
    'isSpotTradingAllowed': True,
    'ocoAllowed': True,
    'orderTypes': [
      'LIMIT',
      'LIMIT_MAKER',
      'MARKET',
      'STOP_LOSS',
      'STOP_LOSS_LIMIT',
      'TAKE_PROFIT',
      'TAKE_PROFIT_LIMIT'
    ],
    'otoAllowed': True,
    'permissionSets': [
      [
        'SPOT'
      ]
    ],
    'permissions': [],
    'quoteAsset': 'USDT',
    'quoteAssetPrecision': '8',
    'quoteCommissionPrecision': '8',
    'quoteOrderQtyMarketAllowed': True,
    'quotePrecision': '8',
    'status': 'TRADING',
    'symbol': 'ETHUSDT'
  },
  'inverse': None,
  'limits': {
    'amount': {
      'max': 9000.0,
      'min': 0.0001
    },
    'cost': {
      'max': 9000000.0,
      'min': 5.0
    },
    'leverage': {
      'max': None,
      'min': None
    },
    'market': {
      'max': 3730.93834769,
      'min': 0.0
    },
    'price': {
      'max': 1000000.0,
      'min': 0.01
    }
  },
  'linear': None,
  'lowercaseId': 'ethusdt',
  'maker': 0.001,
  'margin': False,
  'marginModes': {
    'cross': False,
    'isolated': False
  },
  'option': False,
  'optionType': None,
  'percentage': True,
  'precision': {
    'amount': 0.0001,
    'base': 1e-08,
    'cost': None,
    'price': 0.01,
    'quote': 1e-08
  },
  'quote': 'USDT',
  'quoteId': 'USDT',
  'settle': None,
  'settleId': None,
  'spot': True,
  'strike': None,
  'subType': None,
  'swap': False,
  'symbol': 'ETH/USDT',
  'taker': 0.001,
  'tierBased': False,
  'type': 'spot'
}


========================================
--- 3. Анализ баланса ---
========================================
Структура объекта баланса:
{'1000CAT': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 '1000CHEEMS': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 '1000SATS': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 '1INCH': {'free': 2911.0, 'total': 2911.0, 'used': 0.0},
 '1MBABYDOGE': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'A': {'free': 1037.0, 'total': 1037.0, 'used': 0.0},
 'AAVE': {'free': 1.0, 'total': 1.0, 'used': 0.0},
 'ACA': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ACE': {'free': 994.0, 'total': 994.0, 'used': 0.0},
 'ACH': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ACM': {'free': 655.0, 'total': 655.0, 'used': 0.0},
 'ACT': {'free': 12690.0, 'total': 12690.0, 'used': 0.0},
 'ACX': {'free': 3775.0, 'total': 3775.0, 'used': 0.0},
 'ADA': {'free': 893.0, 'total': 893.0, 'used': 0.0},
 'ADX': {'free': 6560.0, 'total': 6560.0, 'used': 0.0},
 'AEUR': {'free': 440.0, 'total': 440.0, 'used': 0.0},
 'AEVO': {'free': 6104.0, 'total': 6104.0, 'used': 0.0},
 'AGLD': {'free': 745.0, 'total': 745.0, 'used': 0.0},
 'AI': {'free': 4623.0, 'total': 4623.0, 'used': 0.0},
 'AIXBT': {'free': 3897.0, 'total': 3897.0, 'used': 0.0},
 'ALCX': {'free': 68.0, 'total': 68.0, 'used': 0.0},
 'ALGO': {'free': 2852.0, 'total': 2852.0, 'used': 0.0},
 'ALICE': {'free': 1331.0, 'total': 1331.0, 'used': 0.0},
 'ALPHA': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ALPINE': {'free': 737.0, 'total': 737.0, 'used': 0.0},
 'ALT': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'AMP': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ANIME': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ANKR': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'APE': {'free': 826.0, 'total': 826.0, 'used': 0.0},
 'API3': {'free': 825.0, 'total': 825.0, 'used': 0.0},
 'APT': {'free': 109.0, 'total': 109.0, 'used': 0.0},
 'AR': {'free': 96.0, 'total': 96.0, 'used': 0.0},
 'ARB': {'free': 1466.0, 'total': 1466.0, 'used': 0.0},
 'ARDR': {'free': 6439.0, 'total': 6439.0, 'used': 0.0},
 'ARK': {'free': 1390.0, 'total': 1390.0, 'used': 0.0},
 'ARKM': {'free': 1102.0, 'total': 1102.0, 'used': 0.0},
 'ARPA': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ARS': {'free': 18466.0, 'total': 18466.0, 'used': 0.0},
 'ASR': {'free': 218.0, 'total': 218.0, 'used': 0.0},
 'ASTR': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ATA': {'free': 11907.0, 'total': 11907.0, 'used': 0.0},
 'ATM': {'free': 499.0, 'total': 499.0, 'used': 0.0},
 'ATOM': {'free': 124.0, 'total': 124.0, 'used': 0.0},
 'AUCTION': {'free': 57.0, 'total': 57.0, 'used': 0.0},
 'AUDIO': {'free': 9021.0, 'total': 9021.0, 'used': 0.0},
 'AVA': {'free': 1008.0, 'total': 1008.0, 'used': 0.0},
 'AVAX': {'free': 28.0, 'total': 28.0, 'used': 0.0},
 'AWE': {'free': 8766.0, 'total': 8766.0, 'used': 0.0},
 'AXL': {'free': 1566.0, 'total': 1566.0, 'used': 0.0},
 'AXS': {'free': 228.0, 'total': 228.0, 'used': 0.0},
 'BABY': {'free': 10689.0, 'total': 10689.0, 'used': 0.0},
 'BAKE': {'free': 5002.0, 'total': 5002.0, 'used': 0.0},
 'BANANA': {'free': 29.0, 'total': 29.0, 'used': 0.0},
 'BANANAS31': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'BAND': {'free': 892.0, 'total': 892.0, 'used': 0.0},
 'BAR': {'free': 486.0, 'total': 486.0, 'used': 0.0},
 'BAT': {'free': 4035.0, 'total': 4035.0, 'used': 0.0},
 'BB': {'free': 6188.0, 'total': 6188.0, 'used': 0.0},
 'BCH': {'free': 1.0, 'total': 1.0, 'used': 0.0},
 'BEAMX': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'BEL': {'free': 2240.0, 'total': 2240.0, 'used': 0.0},
 'BERA': {'free': 296.0, 'total': 296.0, 'used': 0.0},
 'BICO': {'free': 5506.0, 'total': 5506.0, 'used': 0.0},
 'BIFI': {'free': 3.0, 'total': 3.0, 'used': 0.0},
 'BIGTIME': {'free': 9865.0, 'total': 9865.0, 'used': 0.0},
 'BIO': {'free': 9799.0, 'total': 9799.0, 'used': 0.0},
 'BLUR': {'free': 7124.0, 'total': 7124.0, 'used': 0.0},
 'BMT': {'free': 3640.0, 'total': 3640.0, 'used': 0.0},
 'BNB': {'free': 1.0, 'total': 1.0, 'used': 0.0},
 'BNSOL': {'free': 3.0, 'total': 3.0, 'used': 0.0},
 'BNT': {'free': 858.0, 'total': 858.0, 'used': 0.0},
 'BOME': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'BONK': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'BRL': {'free': 97.0, 'total': 97.0, 'used': 0.0},
 'BROCCOLI714': {'free': 11845.0, 'total': 11845.0, 'used': 0.0},
 'BSW': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'BTC': {'free': 1.003, 'total': 1.003, 'used': 0.0},
 'BTTC': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'C98': {'free': 11900.0, 'total': 11900.0, 'used': 0.0},
 'CAKE': {'free': 218.0, 'total': 218.0, 'used': 0.0},
 'CATI': {'free': 6421.0, 'total': 6421.0, 'used': 0.0},
 'CELO': {'free': 1914.0, 'total': 1914.0, 'used': 0.0},
 'CELR': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'CETUS': {'free': 5609.0, 'total': 5609.0, 'used': 0.0},
 'CFX': {'free': 6605.0, 'total': 6605.0, 'used': 0.0},
 'CGPT': {'free': 5444.0, 'total': 5444.0, 'used': 0.0},
 'CHESS': {'free': 6254.0, 'total': 6254.0, 'used': 0.0},
 'CHR': {'free': 6441.0, 'total': 6441.0, 'used': 0.0},
 'CHZ': {'free': 14444.0, 'total': 14444.0, 'used': 0.0},
 'CITY': {'free': 606.0, 'total': 606.0, 'used': 0.0},
 'CKB': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'COMP': {'free': 11.0, 'total': 11.0, 'used': 0.0},
 'COOKIE': {'free': 3081.0, 'total': 3081.0, 'used': 0.0},
 'COP': {'free': 18466.0, 'total': 18466.0, 'used': 0.0},
 'COS': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'COTI': {'free': 9775.0, 'total': 9775.0, 'used': 0.0},
 'COW': {'free': 1832.0, 'total': 1832.0, 'used': 0.0},
 'CRV': {'free': 973.0, 'total': 973.0, 'used': 0.0},
 'CTK': {'free': 1593.0, 'total': 1593.0, 'used': 0.0},
 'CTSI': {'free': 8840.0, 'total': 8840.0, 'used': 0.0},
 'CVC': {'free': 5755.0, 'total': 5755.0, 'used': 0.0},
 'CVX': {'free': 222.0, 'total': 222.0, 'used': 0.0},
 'CYBER': {'free': 418.0, 'total': 418.0, 'used': 0.0},
 'CZK': {'free': 18466.0, 'total': 18466.0, 'used': 0.0},
 'D': {'free': 16359.0, 'total': 16359.0, 'used': 0.0},
 'DAI': {'free': 10000.0, 'total': 10000.0, 'used': 0.0},
 'DASH': {'free': 25.0, 'total': 25.0, 'used': 0.0},
 'DATA': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'DCR': {'free': 32.0, 'total': 32.0, 'used': 0.0},
 'DEGO': {'free': 497.0, 'total': 497.0, 'used': 0.0},
 'DENT': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'DEXE': {'free': 67.0, 'total': 67.0, 'used': 0.0},
 'DF': {'free': 17362.0, 'total': 17362.0, 'used': 0.0},
 'DGB': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'DIA': {'free': 1332.0, 'total': 1332.0, 'used': 0.0},
 'DODO': {'free': 13404.0, 'total': 13404.0, 'used': 0.0},
 'DOGE': {'free': 3092.0, 'total': 3092.0, 'used': 0.0},
 'DOGS': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'DOT': {'free': 150.0, 'total': 150.0, 'used': 0.0},
 'DUSK': {'free': 9495.0, 'total': 9495.0, 'used': 0.0},
 'DYDX': {'free': 969.0, 'total': 969.0, 'used': 0.0},
 'DYM': {'free': 2222.0, 'total': 2222.0, 'used': 0.0},
 'EDU': {'free': 3825.0, 'total': 3825.0, 'used': 0.0},
 'EGLD': {'free': 37.0, 'total': 37.0, 'used': 0.0},
 'EIGEN': {'free': 454.0, 'total': 454.0, 'used': 0.0},
 'ENA': {'free': 1911.0, 'total': 1911.0, 'used': 0.0},
 'ENJ': {'free': 7633.0, 'total': 7633.0, 'used': 0.0},
 'ENS': {'free': 27.0, 'total': 27.0, 'used': 0.0},
 'EPIC': {'free': 586.0, 'total': 586.0, 'used': 0.0},
 'ETC': {'free': 30.0, 'total': 30.0, 'used': 0.0},
 'ETH': {'free': 1.0, 'total': 1.0, 'used': 0.0},
 'ETHFI': {'free': 528.0, 'total': 528.0, 'used': 0.0},
 'EUR': {'free': 425.0, 'total': 425.0, 'used': 0.0},
 'EURI': {'free': 425.0, 'total': 425.0, 'used': 0.0},
 'FARM': {'free': 19.0, 'total': 19.0, 'used': 0.0},
 'FDUSD': {'free': 10000.0, 'total': 10000.0, 'used': 0.0},
 'FET': {'free': 723.0, 'total': 723.0, 'used': 0.0},
 'FIDA': {'free': 6302.0, 'total': 6302.0, 'used': 0.0},
 'FIL': {'free': 222.0, 'total': 222.0, 'used': 0.0},
 'FIO': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'FIS': {'free': 6206.0, 'total': 6206.0, 'used': 0.0},
 'FLM': {'free': 15050.0, 'total': 15050.0, 'used': 0.0},
 'FLOKI': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'FLOW': {'free': 1552.0, 'total': 1552.0, 'used': 0.0},
 'FLUX': {'free': 2536.0, 'total': 2536.0, 'used': 0.0},
 'FORM': {'free': 171.0, 'total': 171.0, 'used': 0.0},
 'FORTH': {'free': 213.0, 'total': 213.0, 'used': 0.0},
 'FTT': {'free': 615.0, 'total': 615.0, 'used': 0.0},
 'FUN': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'FXS': {'free': 252.0, 'total': 252.0, 'used': 0.0},
 'G': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'GALA': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'GAS': {'free': 179.0, 'total': 179.0, 'used': 0.0},
 'GHST': {'free': 1388.0, 'total': 1388.0, 'used': 0.0},
 'GLM': {'free': 2259.0, 'total': 2259.0, 'used': 0.0},
 'GLMR': {'free': 8051.0, 'total': 8051.0, 'used': 0.0},
 'GMT': {'free': 11600.0, 'total': 11600.0, 'used': 0.0},
 'GMX': {'free': 36.0, 'total': 36.0, 'used': 0.0},
 'GNO': {'free': 4.0, 'total': 4.0, 'used': 0.0},
 'GNS': {'free': 308.0, 'total': 308.0, 'used': 0.0},
 'GPS': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'GRT': {'free': 6047.0, 'total': 6047.0, 'used': 0.0},
 'GTC': {'free': 2173.0, 'total': 2173.0, 'used': 0.0},
 'GUN': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'HAEDAL': {'free': 4201.0, 'total': 4201.0, 'used': 0.0},
 'HBAR': {'free': 3387.0, 'total': 3387.0, 'used': 0.0},
 'HEI': {'free': 1827.0, 'total': 1827.0, 'used': 0.0},
 'HFT': {'free': 3618.0, 'total': 3618.0, 'used': 0.0},
 'HIFI': {'free': 3781.0, 'total': 3781.0, 'used': 0.0},
 'HIGH': {'free': 980.0, 'total': 980.0, 'used': 0.0},
 'HIVE': {'free': 2463.0, 'total': 2463.0, 'used': 0.0},
 'HMSTR': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'HOME': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'HOOK': {'free': 5363.0, 'total': 5363.0, 'used': 0.0},
 'HOT': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'HUMA': {'free': 15115.0, 'total': 15115.0, 'used': 0.0},
 'HYPER': {'free': 4856.0, 'total': 4856.0, 'used': 0.0},
 'ICP': {'free': 103.0, 'total': 103.0, 'used': 0.0},
 'ICX': {'free': 4036.0, 'total': 4036.0, 'used': 0.0},
 'ID': {'free': 3266.0, 'total': 3266.0, 'used': 0.0},
 'IDEX': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ILV': {'free': 47.0, 'total': 47.0, 'used': 0.0},
 'IMX': {'free': 1146.0, 'total': 1146.0, 'used': 0.0},
 'INIT': {'free': 1219.0, 'total': 1219.0, 'used': 0.0},
 'INJ': {'free': 47.0, 'total': 47.0, 'used': 0.0},
 'IO': {'free': 705.0, 'total': 705.0, 'used': 0.0},
 'IOST': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'IOTA': {'free': 3197.0, 'total': 3197.0, 'used': 0.0},
 'IOTX': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'IQ': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'JASMY': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'JOE': {'free': 3508.0, 'total': 3508.0, 'used': 0.0},
 'JPY': {'free': 18466.0, 'total': 18466.0, 'used': 0.0},
 'JST': {'free': 14604.0, 'total': 14604.0, 'used': 0.0},
 'JTO': {'free': 239.0, 'total': 239.0, 'used': 0.0},
 'JUP': {'free': 1137.0, 'total': 1137.0, 'used': 0.0},
 'JUV': {'free': 552.0, 'total': 552.0, 'used': 0.0},
 'KAIA': {'free': 3124.0, 'total': 3124.0, 'used': 0.0},
 'KAITO': {'free': 323.0, 'total': 323.0, 'used': 0.0},
 'KAVA': {'free': 1253.0, 'total': 1253.0, 'used': 0.0},
 'KDA': {'free': 1296.0, 'total': 1296.0, 'used': 0.0},
 'KERNEL': {'free': 4553.0, 'total': 4553.0, 'used': 0.0},
 'KMD': {'free': 16758.0, 'total': 16758.0, 'used': 0.0},
 'KMNO': {'free': 8451.0, 'total': 8451.0, 'used': 0.0},
 'KNC': {'free': 1778.0, 'total': 1778.0, 'used': 0.0},
 'KSM': {'free': 39.0, 'total': 39.0, 'used': 0.0},
 'LAYER': {'free': 792.0, 'total': 792.0, 'used': 0.0},
 'LAZIO': {'free': 691.0, 'total': 691.0, 'used': 0.0},
 'LDO': {'free': 693.0, 'total': 693.0, 'used': 0.0},
 'LEVER': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'LINK': {'free': 38.0, 'total': 38.0, 'used': 0.0},
 'LISTA': {'free': 2136.0, 'total': 2136.0, 'used': 0.0},
 'LOKA': {'free': 10618.0, 'total': 10618.0, 'used': 0.0},
 'LPT': {'free': 82.0, 'total': 82.0, 'used': 0.0},
 'LQTY': {'free': 381.0, 'total': 381.0, 'used': 0.0},
 'LRC': {'free': 6693.0, 'total': 6693.0, 'used': 0.0},
 'LSK': {'free': 1351.0, 'total': 1351.0, 'used': 0.0},
 'LTC': {'free': 5.0, 'total': 5.0, 'used': 0.0},
 'LTO': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'LUMIA': {'free': 2154.0, 'total': 2154.0, 'used': 0.0},
 'LUNA': {'free': 3466.0, 'total': 3466.0, 'used': 0.0},
 'LUNC': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'MAGIC': {'free': 4017.0, 'total': 4017.0, 'used': 0.0},
 'MANA': {'free': 2011.0, 'total': 2011.0, 'used': 0.0},
 'MANTA': {'free': 2717.0, 'total': 2717.0, 'used': 0.0},
 'MASK': {'free': 424.0, 'total': 424.0, 'used': 0.0},
 'MAV': {'free': 9992.0, 'total': 9992.0, 'used': 0.0},
 'MBL': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'MBOX': {'free': 10443.0, 'total': 10443.0, 'used': 0.0},
 'MDT': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ME': {'free': 694.0, 'total': 694.0, 'used': 0.0},
 'MEME': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'METIS': {'free': 32.0, 'total': 32.0, 'used': 0.0},
 'MINA': {'free': 2945.0, 'total': 2945.0, 'used': 0.0},
 'MKR': {'free': 1.0, 'total': 1.0, 'used': 0.0},
 'MLN': {'free': 71.0, 'total': 71.0, 'used': 0.0},
 'MOVE': {'free': 2962.0, 'total': 2962.0, 'used': 0.0},
 'MOVR': {'free': 93.0, 'total': 93.0, 'used': 0.0},
 'MTL': {'free': 755.0, 'total': 755.0, 'used': 0.0},
 'MUBARAK': {'free': 13228.0, 'total': 13228.0, 'used': 0.0},
 'MXN': {'free': 18466.0, 'total': 18466.0, 'used': 0.0},
 'NEAR': {'free': 233.0, 'total': 233.0, 'used': 0.0},
 'NEIRO': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'NEO': {'free': 92.0, 'total': 92.0, 'used': 0.0},
 'NEWT': {'free': 1486.0, 'total': 1486.0, 'used': 0.0},
 'NEXO': {'free': 416.0, 'total': 416.0, 'used': 0.0},
 'NFP': {'free': 9058.0, 'total': 9058.0, 'used': 0.0},
 'NIL': {'free': 1751.0, 'total': 1751.0, 'used': 0.0},
 'NKN': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'NMR': {'free': 66.0, 'total': 66.0, 'used': 0.0},
 'NOT': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'NTRN': {'free': 5868.0, 'total': 5868.0, 'used': 0.0},
 'NXPC': {'free': 538.0, 'total': 538.0, 'used': 0.0},
 'OG': {'free': 124.0, 'total': 124.0, 'used': 0.0},
 'OGN': {'free': 9633.0, 'total': 9633.0, 'used': 0.0},
 'OM': {'free': 2466.0, 'total': 2466.0, 'used': 0.0},
 'OMNI': {'free': 352.77, 'total': 352.77, 'used': 0.0},
 'ONDO': {'free': 652.0, 'total': 652.0, 'used': 0.0},
 'ONE': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ONG': {'free': 3056.0, 'total': 3056.0, 'used': 0.0},
 'ONT': {'free': 4255.0, 'total': 4255.0, 'used': 0.0},
 'OP': {'free': 923.0, 'total': 923.0, 'used': 0.0},
 'ORCA': {'free': 261.0, 'total': 261.0, 'used': 0.0},
 'ORDI': {'free': 68.0, 'total': 68.0, 'used': 0.0},
 'OSMO': {'free': 3544.0, 'total': 3544.0, 'used': 0.0},
 'OXT': {'free': 9504.0, 'total': 9504.0, 'used': 0.0},
 'PARTI': {'free': 2389.0, 'total': 2389.0, 'used': 0.0},
 'PAXG': {'free': 1.0, 'total': 1.0, 'used': 0.0},
 'PENDLE': {'free': 146.0, 'total': 146.0, 'used': 0.0},
 'PENGU': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'PEOPLE': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'PEPE': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'PERP': {'free': 2234.0, 'total': 2234.0, 'used': 0.0},
 'PHA': {'free': 5186.0, 'total': 5186.0, 'used': 0.0},
 'PHB': {'free': 1188.0, 'total': 1188.0, 'used': 0.0},
 'PIVX': {'free': 3937.0, 'total': 3937.0, 'used': 0.0},
 'PIXEL': {'free': 15685.0, 'total': 15685.0, 'used': 0.0},
 'PLN': {'free': 18466.0, 'total': 18466.0, 'used': 0.0},
 'PNUT': {'free': 2283.0, 'total': 2283.0, 'used': 0.0},
 'POL': {'free': 2761.0, 'total': 2761.0, 'used': 0.0},
 'POLYX': {'free': 4098.0, 'total': 4098.0, 'used': 0.0},
 'POND': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'PORTAL': {'free': 13621.0, 'total': 13621.0, 'used': 0.0},
 'PORTO': {'free': 680.0, 'total': 680.0, 'used': 0.0},
 'POWR': {'free': 3344.0, 'total': 3344.0, 'used': 0.0},
 'PROM': {'free': 77.0, 'total': 77.0, 'used': 0.0},
 'PSG': {'free': 347.0, 'total': 347.0, 'used': 0.0},
 'PUNDIX': {'free': 1815.0, 'total': 1815.0, 'used': 0.0},
 'PYR': {'free': 557.0, 'total': 557.0, 'used': 0.0},
 'PYTH': {'free': 4873.0, 'total': 4873.0, 'used': 0.0},
 'QI': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'QKC': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'QNT': {'free': 4.0, 'total': 4.0, 'used': 0.0},
 'QTUM': {'free': 260.0, 'total': 260.0, 'used': 0.0},
 'QUICK': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'RAD': {'free': 807.0, 'total': 807.0, 'used': 0.0},
 'RARE': {'free': 9999.0, 'total': 9999.0, 'used': 0.0},
 'RAY': {'free': 244.0, 'total': 244.0, 'used': 0.0},
 'RDNT': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'RED': {'free': 1694.0, 'total': 1694.0, 'used': 0.0},
 'REI': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'RENDER': {'free': 158.0, 'total': 158.0, 'used': 0.0},
 'REQ': {'free': 3688.0, 'total': 3688.0, 'used': 0.0},
 'RESOLV': {'free': 3634.0, 'total': 3634.0, 'used': 0.0},
 'REZ': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'RIF': {'free': 9523.0, 'total': 9523.0, 'used': 0.0},
 'RLC': {'free': 549.0, 'total': 549.0, 'used': 0.0},
 'RON': {'free': 18466.0, 'total': 18466.0, 'used': 0.0},
 'RONIN': {'free': 1136.0, 'total': 1136.0, 'used': 0.0},
 'ROSE': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'RPL': {'free': 100.0, 'total': 100.0, 'used': 0.0},
 'RSR': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'RUNE': {'free': 376.0, 'total': 376.0, 'used': 0.0},
 'RVN': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'S': {'free': 1585.0, 'total': 1585.0, 'used': 0.0},
 'SAGA': {'free': 2429.0, 'total': 2429.0, 'used': 0.0},
 'SAHARA': {'free': 6582.0, 'total': 6582.0, 'used': 0.0},
 'SAND': {'free': 2097.0, 'total': 2097.0, 'used': 0.0},
 'SANTOS': {'free': 269.0, 'total': 269.0, 'used': 0.0},
 'SC': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'SCR': {'free': 2016.0, 'total': 2016.0, 'used': 0.0},
 'SCRT': {'free': 3211.0, 'total': 3211.0, 'used': 0.0},
 'SEI': {'free': 1789.0, 'total': 1789.0, 'used': 0.0},
 'SFP': {'free': 1126.0, 'total': 1126.0, 'used': 0.0},
 'SHELL': {'free': 3440.0, 'total': 3440.0, 'used': 0.0},
 'SHIB': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'SIGN': {'free': 7507.0, 'total': 7507.0, 'used': 0.0},
 'SKL': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'SLF': {'free': 6134.0, 'total': 6134.0, 'used': 0.0},
 'SLP': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'SNX': {'free': 881.0, 'total': 881.0, 'used': 0.0},
 'SOL': {'free': 3.0, 'total': 3.0, 'used': 0.0},
 'SOLV': {'free': 11136.0, 'total': 11136.0, 'used': 0.0},
 'SOPH': {'free': 16098.0, 'total': 16098.0, 'used': 0.0},
 'SPELL': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'SPK': {'free': 14060.0, 'total': 14060.0, 'used': 0.0},
 'SSV': {'free': 69.0, 'total': 69.0, 'used': 0.0},
 'STEEM': {'free': 3920.0, 'total': 3920.0, 'used': 0.0},
 'STG': {'free': 3335.0, 'total': 3335.0, 'used': 0.0},
 'STO': {'free': 7201.0, 'total': 7201.0, 'used': 0.0},
 'STORJ': {'free': 2101.0, 'total': 2101.0, 'used': 0.0},
 'STRAX': {'free': 11018.0, 'total': 11018.0, 'used': 0.0},
 'STRK': {'free': 4382.0, 'total': 4382.0, 'used': 0.0},
 'STX': {'free': 758.0, 'total': 758.0, 'used': 0.0},
 'SUI': {'free': 180.0, 'total': 180.0, 'used': 0.0},
 'SUN': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'SUPER': {'free': 765.0, 'total': 765.0, 'used': 0.0},
 'SUSHI': {'free': 844.0, 'total': 844.0, 'used': 0.0},
 'SXP': {'free': 2943.0, 'total': 2943.0, 'used': 0.0},
 'SXT': {'free': 6754.0, 'total': 6754.0, 'used': 0.0},
 'SYN': {'free': 5413.0, 'total': 5413.0, 'used': 0.0},
 'SYRUP': {'free': 907.0, 'total': 907.0, 'used': 0.0},
 'SYS': {'free': 14921.0, 'total': 14921.0, 'used': 0.0},
 'T': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'TAO': {'free': 1.0, 'total': 1.0, 'used': 0.0},
 'TFUEL': {'free': 15484.0, 'total': 15484.0, 'used': 0.0},
 'THE': {'free': 1932.0, 'total': 1932.0, 'used': 0.0},
 'THETA': {'free': 736.0, 'total': 736.0, 'used': 0.0},
 'TIA': {'free': 345.0, 'total': 345.0, 'used': 0.0},
 'TKO': {'free': 3851.0, 'total': 3851.0, 'used': 0.0},
 'TLM': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'TNSR': {'free': 4371.0, 'total': 4371.0, 'used': 0.0},
 'TON': {'free': 177.0, 'total': 177.0, 'used': 0.0},
 'TRB': {'free': 13.0, 'total': 13.0, 'used': 0.0},
 'TRU': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'TRUMP': {'free': 57.0, 'total': 57.0, 'used': 0.0},
 'TRX': {'free': 1778.0, 'total': 1778.0, 'used': 0.0},
 'TRY': {'free': 18466.0, 'total': 18466.0, 'used': 0.0},
 'TST': {'free': 12018.0, 'total': 12018.0, 'used': 0.0},
 'TURBO': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'TUSD': {'free': 10000.0, 'total': 10000.0, 'used': 0.0},
 'TUT': {'free': 8069.0, 'total': 8069.0, 'used': 0.0},
 'TWT': {'free': 731.0, 'total': 731.0, 'used': 0.0},
 'UAH': {'free': 18466.0, 'total': 18466.0, 'used': 0.0},
 'UMA': {'free': 459.0, 'total': 459.0, 'used': 0.0},
 'UNI': {'free': 70.0, 'total': 70.0, 'used': 0.0},
 'USD1': {'free': 500.0, 'total': 500.0, 'used': 0.0},
 'USDC': {'free': 10000.0, 'total': 10000.0, 'used': 0.0},
 'USDP': {'free': 500.0, 'total': 500.0, 'used': 0.0},
 'USDT': {'free': 9560.927045, 'total': 9560.927045, 'used': 0.0},
 'USTC': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'USUAL': {'free': 7928.0, 'total': 7928.0, 'used': 0.0},
 'UTK': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'VANA': {'free': 115.0, 'total': 115.0, 'used': 0.0},
 'VANRY': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'VELODROME': {'free': 11169.0, 'total': 11169.0, 'used': 0.0},
 'VET': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'VIC': {'free': 3152.0, 'total': 3152.0, 'used': 0.0},
 'VIRTUAL': {'free': 337.0, 'total': 337.0, 'used': 0.0},
 'VOXEL': {'free': 11063.0, 'total': 11063.0, 'used': 0.0},
 'VTHO': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'W': {'free': 7028.0, 'total': 7028.0, 'used': 0.0},
 'WAN': {'free': 4678.0, 'total': 4678.0, 'used': 0.0},
 'WAXP': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'WBETH': {'free': 1.0, 'total': 1.0, 'used': 0.0},
 'WBTC': {'free': 1.0, 'total': 1.0, 'used': 0.0},
 'WCT': {'free': 1635.0, 'total': 1635.0, 'used': 0.0},
 'WIF': {'free': 618.0, 'total': 618.0, 'used': 0.0},
 'WIN': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'WLD': {'free': 562.0, 'total': 562.0, 'used': 0.0},
 'WOO': {'free': 7552.0, 'total': 7552.0, 'used': 0.0},
 'XAI': {'free': 10036.0, 'total': 10036.0, 'used': 0.0},
 'XEC': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'XLM': {'free': 2162.0, 'total': 2162.0, 'used': 0.0},
 'XNO': {'free': 581.0, 'total': 581.0, 'used': 0.0},
 'XRP': {'free': 228.0, 'total': 228.0, 'used': 0.0},
 'XTZ': {'free': 946.0, 'total': 946.0, 'used': 0.0},
 'XUSD': {'free': 500.0, 'total': 500.0, 'used': 0.0},
 'XVG': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'XVS': {'free': 87.0, 'total': 87.0, 'used': 0.0},
 'YFI': {'free': 1.0, 'total': 1.0, 'used': 0.0},
 'YGG': {'free': 3431.0, 'total': 3431.0, 'used': 0.0},
 'ZAR': {'free': 18466.0, 'total': 18466.0, 'used': 0.0},
 'ZEC': {'free': 13.0, 'total': 13.0, 'used': 0.0},
 'ZEN': {'free': 70.0, 'total': 70.0, 'used': 0.0},
 'ZIL': {'free': 18446.0, 'total': 18446.0, 'used': 0.0},
 'ZK': {'free': 10960.0, 'total': 10960.0, 'used': 0.0},
 'ZRO': {'free': 260.0, 'total': 260.0, 'used': 0.0},
 'ZRX': {'free': 2325.0, 'total': 2325.0, 'used': 0.0}}

Примечание: В песочнице балансы могут быть стандартными или нулевыми.

========================================
--- 4. Анализ тикера (ETH/USDT) ---
========================================
Ожидание первого тикера для ETH/USDT...
Структура объекта тикера:
{
  'ask': 2993.89,
  'askVolume': 3.1682,
  'average': 2966.37,
  'baseVolume': 60101.529,
  'bid': 2993.88,
  'bidVolume': 2.9678,
  'change': 55.28,
  'close': 2994.01,
  'datetime': '2025-07-13T17:44:01.597Z',
  'high': 3044.83,
  'indexPrice': None,
  'info': {
    'A': '3.16820000',
    'B': '2.96780000',
    'C': 1752428641597,
    'E': 1752428642006,
    'F': 569112,
    'L': 615980,
    'O': 1752342241597,
    'P': '1.881',
    'Q': '1.24260000',
    'a': '2993.89000000',
    'b': '2993.88000000',
    'c': '2994.01000000',
    'e': '24hrTicker',
    'h': '3044.83000000',
    'l': '2916.54000000',
    'n': 46869,
    'o': '2938.73000000',
    'p': '55.28000000',
    'q': '177833162.42208800',
    's': 'ETHUSDT',
    'v': '60101.52900000',
    'w': '2958.87917298',
    'x': '2938.73000000'
  },
  'last': 2994.01,
  'low': 2916.54,
  'markPrice': None,
  'open': 2938.73,
  'percentage': 1.881,
  'previousClose': 2938.73,
  'quoteVolume': 177833162.422088,
  'symbol': 'ETH/USDT',
  'timestamp': 1752428641597,
  'vwap': 2958.87917298
}


========================================
--- 5. Анализ стакана ордеров (ETH/USDT) ---
========================================
Ожидание первого обновления стакана для ETH/USDT...
Структура объекта стакана:
{
  'asks_count': 129,
  'bids_count': 19,
  'datetime': None,
  'nonce': 5920183,
  'sample_asks': [
    [
      2993.89,
      3.1682
    ],
    [
      2993.9,
      3.2634
    ]
  ],
  'sample_bids': [
    [
      2993.88,
      2.9678
    ],
    [
      2993.87,
      2.9327
    ]
  ],
  'symbol': 'ETH/USDT',
  'timestamp': None
}

```

### 📄 `requirements.txt`

```text
ccxt>=4.4.93
ccxtpro>=1.0.1
pandas>=2.3.1  # required for tests
ta-lib>=0.6.4
numpy>=2.2.2
termcolor>=3.0.1
pytz>=2025.2
requests>=2.32.4
pywin32>=310; sys_platform == "win32"
pytest>=8.4.1
pytest-asyncio>=1.0.0
pytest-cov>=5.0.0
cryptography>=45.0.5
python-dotenv>=1.0.0


```

## 📋 YAML файлы

### 📄 `.github\workflows\auto-sync-branches.yml`

```yaml
name: Auto Sync Branches

on:
  push:
    branches: [main]

jobs:
  sync-branches:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Configure Git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Create sync PR for stage
        run: |
          # Check if stage needs sync
          COMMITS_BEHIND=$(git rev-list --count stage..main)
          
          if [ "$COMMITS_BEHIND" -gt 0 ]; then
            # Create branch for PR
            BRANCH_NAME="auto-sync/main-to-stage-$(date +%Y%m%d-%H%M%S)"
            git checkout -b $BRANCH_NAME main
            git push origin $BRANCH_NAME
            
            # Create PR
            gh pr create \
              --title "🔄 Auto-sync main → stage" \
              --body "Automatically syncing changes from maтоеin to stage branch.

            **Changes included:**
            $(git log stage..main --oneline --max-count=10)

            This PR was created automatically after changes were merged to main." \
              --base stage \
              --head $BRANCH_NAME \
              --label "auto-sync"
          else
            echo "Stage is up to date with main"
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Create sync PR for dev
        run: |
          # Check if dev needs sync
          COMMITS_BEHIND=$(git rev-list --count dev..stage 2>/dev/null || echo "0")
          
          if [ "$COMMITS_BEHIND" -gt 0 ]; then
            # Create branch for PR
            BRANCH_NAME="auto-sync/stage-to-dev-$(date +%Y%m%d-%H%M%S)"
            git checkout -b $BRANCH_NAME stage
            git push origin $BRANCH_NAME
            
            # Create PR
            gh pr create \
              --title "🔄 Auto-sync stage → dev" \
              --body "Automatically syncing changes from stage to dev branch.

            **Changes included:**
            $(git log dev..stage --oneline --max-count=10 2>/dev/null || echo 'No commits to sync')

            This PR was created automatically after stage was updated." \
              --base dev \
              --head $BRANCH_NAME \
              --label "auto-sync"
          else
            echo "Dev is up to date with stage"
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 📄 `.github\workflows\python-tests.yml`

```yaml
name: 🧪 Python Tests

on:
  pull_request:
    branches: [ "dev", "stage", "release/*", "main" ]
  push:
    branches: [ "dev", "stage", "release/*", "main" ]

jobs:
  test:
    name: 🔍 Run Pytest inside Docker CI image
    runs-on: ubuntu-latest

    container:
      image: sni10per/new_autotrade-ci:latest

    steps:
      - name: ⬇️ Checkout repository
        uses: actions/checkout@v4

      - name: 🧪 Run tests with Pytest
        run: pytest tests/

      - name: 📦 Archive test results (optional)
        if: always()
        run: |
          mkdir -p artifacts
          cp -r .pytest_cache artifacts/ || true
          cp -r tests/__pycache__ artifacts/ || true

      - name: 📤 Upload artifacts (optional)
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pytest-artifacts
          path: artifacts

```

### 📄 `.github\workflows\versioning.yml`

```yaml
name: Auto Versioning

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      increment_type:
        description: 'Version increment type'
        required: true
        default: 'patch'
        type: choice
        options:
          - patch
          - minor
          - major

env:
  MAJOR_VERSION: 3

jobs:
  versioning:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Get latest tag
        id: latest_tag
        run: |
          LATEST_TAG=$(git tag -l "v*" --sort=-version:refname | head -n1)
          if [[ -z "$LATEST_TAG" ]]; then
            LATEST_TAG="v${MAJOR_VERSION}.0.0"
          fi
          echo "tag=$LATEST_TAG" >> $GITHUB_OUTPUT

      - name: Calculate version
        id: version
        run: |
          LATEST_TAG="${{ steps.latest_tag.outputs.tag }}"
          CURRENT_VERSION=${LATEST_TAG#v}
          
          IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
          MAJOR=${VERSION_PARTS[0]:-$MAJOR_VERSION}
          MINOR=${VERSION_PARTS[1]:-0}
          PATCH=${VERSION_PARTS[2]:-0}
          
          if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            INCREMENT_TYPE="${{ github.event.inputs.increment_type }}"
          else
            COMMITS_SINCE_TAG=$(git rev-list --count ${LATEST_TAG}..HEAD)
            if [[ $COMMITS_SINCE_TAG -eq 0 ]]; then
              echo "skip=true" >> $GITHUB_OUTPUT
              exit 0
            fi
          
            BREAKING_CHANGES=$(git log ${LATEST_TAG}..HEAD --grep="BREAKING CHANGE" --oneline | wc -l)
            FEATURES=$(git log ${LATEST_TAG}..HEAD --grep="feat:" --oneline | wc -l)
          
            if [[ $BREAKING_CHANGES -gt 0 ]]; then
              INCREMENT_TYPE="major"
            elif [[ $FEATURES -gt 0 ]]; then
              INCREMENT_TYPE="minor"
            else
              INCREMENT_TYPE="patch"
            fi
          fi
          
          case $INCREMENT_TYPE in
            major)
              MAJOR=$((MAJOR + 1))
              MINOR=0
              PATCH=0
              ;;
            minor)
              MINOR=$((MINOR + 1))
              PATCH=0
              ;;
            patch)
              PATCH=$((PATCH + 1))
              ;;
          esac
          
          NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
          NEW_TAG="v${NEW_VERSION}"
          
          if git tag -l "$NEW_TAG" | grep -q "$NEW_TAG"; then
            echo "Tag $NEW_TAG already exists!"
            exit 1
          fi
          
          echo "version=$NEW_VERSION" >> $GITHUB_OUTPUT
          echo "tag=$NEW_TAG" >> $GITHUB_OUTPUT
          echo "increment_type=$INCREMENT_TYPE" >> $GITHUB_OUTPUT
          echo "skip=false" >> $GITHUB_OUTPUT

      - name: Generate changelog
        if: steps.version.outputs.skip != 'true'
        id: changelog
        run: |
          LATEST_TAG="${{ steps.latest_tag.outputs.tag }}"
          NEW_TAG="${{ steps.version.outputs.tag }}"
          
          CHANGELOG=$(git log ${LATEST_TAG}..HEAD --pretty=format:"- %s (%h)" --no-merges)
          TOTAL_COMMITS=$(git rev-list --count ${LATEST_TAG}..HEAD)
          CONTRIBUTORS=$(git log ${LATEST_TAG}..HEAD --format='%an' | sort -u | wc -l)
          
          RELEASE_BODY="## Changes in ${NEW_TAG}
          
          ### Statistics
          - **Commits**: ${TOTAL_COMMITS}
          - **Contributors**: ${CONTRIBUTORS}
          - **Type**: ${{ steps.version.outputs.increment_type }}
          
          ### Changelog
          ${CHANGELOG}
          
          ### Links
          - **Full diff**: [\`${LATEST_TAG}...${NEW_TAG}\`](https://github.com/${{ github.repository }}/compare/${LATEST_TAG}...${NEW_TAG})
          - **Commit**: ${{ github.sha }}"
          
          {
            echo "body<<EOF"
            echo "$RELEASE_BODY"
            echo "EOF"
          } >> $GITHUB_OUTPUT

      - name: Create tag
        if: steps.version.outputs.skip != 'true'
        run: |
          NEW_TAG="${{ steps.version.outputs.tag }}"
          
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          
          git tag -a "$NEW_TAG" -m "Release $NEW_TAG
          
          Auto-generated by GitHub Actions
          Commit: ${{ github.sha }}
          Increment: ${{ steps.version.outputs.increment_type }}
          Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
          
          git push origin "$NEW_TAG"

      - name: Create GitHub Release
        if: steps.version.outputs.skip != 'true'
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.version.outputs.tag }}
          name: Release ${{ steps.version.outputs.tag }}
          body: ${{ steps.changelog.outputs.body }}
          draft: false
          prerelease: false
          generate_release_notes: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Summary
        if: always()
        run: |
          if [[ "${{ steps.version.outputs.skip }}" == "true" ]]; then
            echo "## Versioning skipped" >> $GITHUB_STEP_SUMMARY
            echo "No new commits for release" >> $GITHUB_STEP_SUMMARY
          else
            echo "## Release created successfully" >> $GITHUB_STEP_SUMMARY
            echo "| Parameter | Value |" >> $GITHUB_STEP_SUMMARY
            echo "|----------|-------|" >> $GITHUB_STEP_SUMMARY
            echo "| **Version** | ${{ steps.version.outputs.version }} |" >> $GITHUB_STEP_SUMMARY
            echo "| **Tag** | ${{ steps.version.outputs.tag }} |" >> $GITHUB_STEP_SUMMARY
            echo "| **Type** | ${{ steps.version.outputs.increment_type }} |" >> $GITHUB_STEP_SUMMARY
            echo "| **Branch** | ${{ github.ref_name }} |" >> $GITHUB_STEP_SUMMARY
          fi
```
