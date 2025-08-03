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

## 🏗️ Работа с MemoryFirst Архитектурой v2.5.0

### Принципы разработки:
1. **Используйте интерфейсы:** Всегда работайте через IDealsRepository, IOrdersRepository
2. **Не блокируйте торговлю:** Персистентность должна быть асинхронной
3. **Тестируйте fallback:** Проверяйте работу с in_memory_legacy режимом
4. **Мониторьте производительность:** Время операций не должно превышать 1ms

### Структура тестов:
```bash
# Тесты архитектуры
pytest tests/test_memory_first_architecture.py -v

# Тесты конкретных репозиториев  
pytest tests/ -k "memory_first" -v

# Интеграционные тесты
pytest tests/test_integration.py -v
```

### PostgreSQL Guidelines:
1. **Схемы в src/infrastructure/database/schemas/** - всегда актуализируйте
2. **Миграции через код** - не используйте внешние инструменты миграций
3. **Fallback готовность** - система должна работать без PostgreSQL
4. **JSON сериализация** - используйте default=str для datetime объектов

### Работа с RepositoryFactory:
**Правильно:** Используйте RepositoryFactory для создания репозиториев
- Фабрика автоматически выберет нужный backend на основе конфигурации
- Поддерживает fallback механизмы при недоступности PostgreSQL
- Обеспечивает единообразную инициализацию всех репозиториев

**Неправильно:** Прямое создание экземпляров MemoryFirst репозиториев
- Обходит систему конфигурации
- Не работают fallback механизмы
- Усложняет тестирование и отладку

### Конфигурационные переключения:
**Новая архитектура (рекомендуется):**
```
"deals_type": "memory_first_postgres"
"orders_type": "memory_first_postgres"
```

**Откат к старой системе (при проблемах):**
```
"deals_type": "in_memory_legacy"  
"orders_type": "in_memory_legacy"
```

Следование этим правилам поможет поддерживать целостность архитектуры и стабильность проекта.
