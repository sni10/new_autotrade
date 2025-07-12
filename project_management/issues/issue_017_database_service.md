# Issue #17: DatabaseService - Система хранения данных
### Статус: запланировано

**🔥 Приоритет:** КРИТИЧЕСКИЙ  
**🏗️ Milestone:** M2 - Персистентность и управление данными  
**🏷️ Labels:** `critical`, `database`, `persistence`, `data-loss-prevention`

## 📝 Описание проблемы

В текущей версии все данные хранятся только в памяти через InMemoryRepositories:
- **Потеря всех данных при перезапуске** - сделки, ордера, конфигурация
- **Невозможность восстановления состояния** после сбоев
- **Отсутствие истории операций** для анализа и аудита  
- **Нет резервного копирования** критических данных
- **Невозможность scale** на несколько инстансов

Это критично недопустимо для production торгового бота с реальными деньгами.

## 🎯 Цель

Реализовать надежную систему постоянного хранения данных с возможностью восстановления состояния, миграций схемы и резервного копирования.

## 🔧 Техническое решение

### 1. Выбор технологии БД

**Этап 1: SQLite** (быстрый старт)
- Простота развертывания
- Нулевая настройка
- Локальные файлы
- Подходит для одного инстанса

**Этап 2: PostgreSQL** (production scale)
- Высокая производительность
- ACID транзакции
- Возможность масштабирования
- Лучшая надежность

### 2. Создать `infrastructure/database/database_service.py`

```python
class DatabaseService:
    def __init__(
        self, 
        connection_string: str,
        pool_size: int = 10
    ):
        self.connection_string = connection_string
        self.pool = None
        self.engine = None
        
    async def initialize(self):
        \"\"\"Инициализация подключения к БД\"\"\"
        
    async def create_tables(self):
        \"\"\"Создание всех необходимых таблиц\"\"\"
        
    async def migrate_schema(self, target_version: str = 'latest'):
        \"\"\"Применение миграций схемы\"\"\"
        
    async def execute_query(
        self, 
        query: str, 
        parameters: Dict = None
    ) -> List[Dict]:
        \"\"\"Выполнение произвольного SQL запроса\"\"\"
        
    async def execute_transaction(
        self, 
        operations: List[DatabaseOperation]
    ) -> bool:
        \"\"\"Выполнение группы операций в транзакции\"\"\"
        
    async def backup_database(self, backup_path: str):
        \"\"\"Создание резервной копии БД\"\"\"
        
    async def restore_database(self, backup_path: str):
        \"\"\"Восстановление из резервной копии\"\"\"
```

### 3. Схема базы данных

```sql
-- Таблица сделок
CREATE TABLE deals (
    id BIGINT PRIMARY KEY,
    currency_pair VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL, -- OPEN, CLOSED, CANCELLED
    buy_order_id BIGINT,
    sell_order_id BIGINT, 
    entry_price DECIMAL(20, 8),
    exit_price DECIMAL(20, 8),
    amount DECIMAL(20, 8),
    profit_loss DECIMAL(20, 8),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP,
    
    INDEX idx_deals_status (status),
    INDEX idx_deals_created_at (created_at),
    INDEX idx_deals_currency_pair (currency_pair)
);

-- Таблица ордеров  
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    deal_id BIGINT,
    exchange_order_id VARCHAR(100),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- BUY, SELL
    type VARCHAR(20) NOT NULL, -- LIMIT, MARKET, STOP_LOSS
    status VARCHAR(20) NOT NULL, -- PENDING, FILLED, CANCELLED, PARTIAL_FILL
    amount DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),
    filled_amount DECIMAL(20, 8) DEFAULT 0,
    average_price DECIMAL(20, 8),
    commission DECIMAL(20, 8) DEFAULT 0,
    commission_asset VARCHAR(10),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    filled_at TIMESTAMP,
    
    FOREIGN KEY (deal_id) REFERENCES deals(id),
    INDEX idx_orders_status (status),
    INDEX idx_orders_deal_id (deal_id),
    INDEX idx_orders_exchange_id (exchange_order_id)
);

-- Таблица рыночных данных (тики)
CREATE TABLE market_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(20, 8),
    high_price DECIMAL(20, 8), 
    low_price DECIMAL(20, 8),
    close_price DECIMAL(20, 8),
    volume DECIMAL(20, 8),
    
    -- Технические индикаторы
    macd DECIMAL(20, 8),
    macd_signal DECIMAL(20, 8),
    macd_histogram DECIMAL(20, 8),
    rsi DECIMAL(8, 4),
    
    INDEX idx_market_data_symbol_timestamp (symbol, timestamp),
    INDEX idx_market_data_timestamp (timestamp)
);

-- Таблица конфигурации
CREATE TABLE configurations (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    data_type VARCHAR(20) NOT NULL, -- string, number, boolean, json
    description TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Таблица событий (для аудита)
CREATE TABLE events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    event_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50), -- deal, order, config  
    entity_id BIGINT,
    event_data JSON,
    severity VARCHAR(20), -- INFO, WARNING, ERROR, CRITICAL
    timestamp TIMESTAMP NOT NULL,
    
    INDEX idx_events_type_timestamp (event_type, timestamp),
    INDEX idx_events_entity (entity_type, entity_id)
);

-- Версионирование схемы
CREATE TABLE schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL,
    checksum VARCHAR(64)
);
```

### 4. Миграции схемы

```python
class MigrationManager:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        self.migrations_dir = 'infrastructure/database/migrations'
        
    async def get_current_version(self) -> str:
        \"\"\"Получение текущей версии схемы\"\"\"
        result = await self.db.execute_query(
            \"SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1\"
        )
        return result[0]['version'] if result else '0.0.0'
        
    async def apply_migrations(self, target_version: str = 'latest'):
        \"\"\"Применение всех необходимых миграций\"\"\"
        current_version = await self.get_current_version()
        pending_migrations = self.get_pending_migrations(current_version, target_version)
        
        for migration in pending_migrations:
            try:
                logger.info(f\"Применение миграции {migration.version}\")
                await self.apply_migration(migration)
                await self.record_migration(migration)
                logger.info(f\"✅ Миграция {migration.version} применена\")
            except Exception as e:
                logger.error(f\"❌ Ошибка применения миграции {migration.version}: {e}\")
                raise MigrationError(f\"Не удалось применить миграцию {migration.version}\")
                
    async def apply_migration(self, migration: Migration):
        \"\"\"Применение конкретной миграции\"\"\"
        operations = []
        for statement in migration.up_statements:
            operations.append(DatabaseOperation('execute', statement))
            
        await self.db.execute_transaction(operations)
```

### 5. Обновленные репозитории

```python
class SqlDealsRepository(DealsRepository):
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        
    async def save(self, deal: Deal):
        if deal.id:
            # UPDATE существующей сделки
            await self.db.execute_query(
                \"\"\"UPDATE deals SET 
                   status = ?, entry_price = ?, exit_price = ?, 
                   profit_loss = ?, updated_at = ?, closed_at = ?
                   WHERE id = ?\"\"\",
                {
                    'status': deal.status,
                    'entry_price': deal.entry_price,
                    'exit_price': deal.exit_price, 
                    'profit_loss': deal.profit_loss,
                    'updated_at': datetime.now(),
                    'closed_at': deal.closed_at,
                    'id': deal.id
                }
            )
        else:
            # INSERT новой сделки
            deal.id = await self.db.execute_query(
                \"\"\"INSERT INTO deals 
                   (currency_pair, status, entry_price, amount, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)\"\"\",
                {
                    'currency_pair': deal.currency_pair,
                    'status': deal.status,
                    'entry_price': deal.entry_price,
                    'amount': deal.amount,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            )
            
    async def get_open_deals(self) -> List[Deal]:
        rows = await self.db.execute_query(
            \"SELECT * FROM deals WHERE status = 'OPEN' ORDER BY created_at\"
        )
        return [self._row_to_deal(row) for row in rows]
        
    async def get_by_id(self, deal_id: int) -> Optional[Deal]:
        rows = await self.db.execute_query(
            \"SELECT * FROM deals WHERE id = ?\", {'id': deal_id}
        )
        return self._row_to_deal(rows[0]) if rows else None
```

## ✅ Критерии готовности

- [ ] SQLite база данных настроена и работает
- [ ] Все таблицы созданы с правильными индексами
- [ ] Система миграций работает корректно
- [ ] SqlDealsRepository заменяет InMemoryDealsRepository
- [ ] SqlOrdersRepository заменяет InMemoryOrdersRepository
- [ ] Сохранение market_data для истории
- [ ] Конфигурация хранится в БД
- [ ] Система backup/restore функционирует
- [ ] Нет потери данных при перезапуске
- [ ] Производительность запросов приемлемая (<10ms для основных операций)

## 🧪 План тестирования

1. **Unit тесты:**
   - Тест каждого метода репозитория
   - Тест миграций в обе стороны
   - Тест backup/restore операций

2. **Integration тесты:**
   - Полный цикл: создание → сохранение → загрузка
   - Тест восстановления после restart
   - Тест performance с большим объемом данных

3. **Stress тесты:**
   - Concurrent access от множественных операций
   - Large dataset operations

## 🔗 Связанные задачи

- **Блокирует:** Issue #16 (StateManagementService) - нужна БД для сохранения состояния
- **Связано с:** Issue #15 (ConfigurationService) - конфигурация в БД
- **Связано с:** Issue #5 (BackupService) - использует БД backup функции

## 📋 Подзадачи

- [ ] Выбрать и настроить SQLite как первую БД
- [ ] Спроектировать полную схему таблиц
- [ ] Создать DatabaseService с connection pooling
- [ ] Реализовать систему миграций
- [ ] Переписать DealsRepository для SQL
- [ ] Переписать OrdersRepository для SQL  
- [ ] Добавить MarketDataRepository для тиков
- [ ] Создать ConfigurationRepository
- [ ] Реализовать backup/restore функциональность
- [ ] Написать comprehensive тесты
- [ ] Performance tuning и оптимизация запросов
- [ ] Подготовка к миграции на PostgreSQL

## ⚠️ Критические моменты

1. **ACID транзакции** - особенно важны для торговых операций
2. **Connection pooling** - избежать exhaustion подключений  
3. **Indexes** - для быстрого поиска по статусам и временным меткам
4. **Data integrity** - foreign keys и constraints
5. **Backup strategy** - автоматические бэкапы каждые 15 минут
6. **Error handling** - graceful degradation при проблемах с БД

## 🚀 План развертывания

### Фаза 1: SQLite Implementation (2 недели)
- Базовая схема и таблицы
- Основные репозитории  
- Система миграций

### Фаза 2: Production Features (1 неделя)
- Backup/restore
- Performance optimization
- Comprehensive testing

### Фаза 3: PostgreSQL Migration (будущее)
- Connection string changes
- Advanced indexing
- Replication setup

## 💡 Дополнительные заметки

- Начать с SQLite для простоты, но архитектуру делать database-agnostic
- Предусмотреть возможность sharding по trading pairs в будущем
- Добавить database health checks в HealthCheckService
- Рассмотреть read replicas для аналитических запросов
- Важно: всегда делать backup перед применением миграций
