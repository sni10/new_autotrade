# Issue #009: DataRepositories - Улучшенные репозитории
### Статус: запланировано

**🏗️ Milestone:** M2  
**📈 Приоритет:** LOW  
**🔗 Зависимости:** Issue #6 (DatabaseService)

---

## 📝 Описание проблемы

Текущие репозитории работают только в памяти и не оптимизированы для работы с реальной БД. После внедрения DatabaseService нужно оптимизировать запросы и добавить индексы.

### 🔍 Текущее состояние:
- `InMemoryDealsRepository`, `InMemoryOrdersRepository`, `InMemoryTickersRepository`
- Простые операции без оптимизации
- Нет индексов и сложных запросов
- Отсутствует пагинация для больших данных

### 🎯 Желаемый результат:
- Оптимизированные SQL репозитории
- Быстрые запросы с индексами
- Поддержка сложных фильтров
- Пагинация и batch операции

---

## 📋 Технические требования

### 🏗️ Архитектура

```python
class SQLDealsRepository(DealsRepository):
    \"\"\"Оптимизированный SQL репозиторий для сделок\"\"\"
    
    async def save(self, deal: Deal) -> Deal:
    async def get_by_id(self, deal_id: int) -> Optional[Deal]:
    async def get_open_deals(self, symbol: Optional[str] = None) -> List[Deal]:
    async def get_deals_by_date_range(self, start: datetime, end: datetime) -> List[Deal]:
    async def get_profitable_deals(self, min_profit: float = 0) -> List[Deal]:
    async def get_deals_statistics(self, symbol: Optional[str] = None) -> DealStatistics:
    async def batch_update_status(self, deal_ids: List[int], status: str) -> int:

class SQLOrdersRepository(OrdersRepository):
    \"\"\"Оптимизированный SQL репозиторий для ордеров\"\"\"
    
    async def save(self, order: Order) -> Order:
    async def get_by_id(self, order_id: int) -> Optional[Order]:
    async def get_by_exchange_id(self, exchange_id: str) -> Optional[Order]:
    async def get_orders_by_deal(self, deal_id: int) -> List[Order]:
    async def get_pending_orders(self, symbol: Optional[str] = None) -> List[Order]:
    async def cancel_expired_orders(self, max_age_minutes: int) -> List[Order]:

class SQLTickersRepository(TickersRepository):
    \"\"\"Оптимизированный SQL репозиторий для тикеров\"\"\"
    
    async def save(self, ticker: Ticker) -> Ticker:
    async def get_latest(self, symbol: str) -> Optional[Ticker]:
    async def get_recent(self, symbol: str, limit: int = 100) -> List[Ticker]:
    async def get_by_time_range(self, symbol: str, start: datetime, end: datetime) -> List[Ticker]:
    async def cleanup_old_data(self, keep_days: int = 30) -> int:
    async def get_price_history(self, symbol: str, interval: str = '1m') -> List[PricePoint]:
```

### 📊 Схема БД с индексами

```sql
-- Сделки
CREATE TABLE deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency_pair_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    buy_order_id INTEGER,
    sell_order_id INTEGER,
    created_at INTEGER NOT NULL,
    closed_at INTEGER,
    profit_amount REAL,
    profit_percent REAL,
    metadata TEXT  -- JSON data
);

-- Индексы для deals
CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_deals_created_at ON deals(created_at);
CREATE INDEX idx_deals_currency_pair ON deals(currency_pair_id);
CREATE INDEX idx_deals_profit ON deals(profit_percent) WHERE profit_percent IS NOT NULL;

-- Ордеры  
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id INTEGER,
    type VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL,
    price REAL NOT NULL,
    amount REAL NOT NULL,
    exchange_id VARCHAR(100),
    created_at INTEGER NOT NULL,
    filled_at INTEGER,
    metadata TEXT  -- JSON data
);

-- Индексы для orders
CREATE INDEX idx_orders_deal_id ON orders(deal_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_exchange_id ON orders(exchange_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Тикеры
CREATE TABLE tickers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    price REAL NOT NULL,
    volume REAL,
    timestamp INTEGER NOT NULL,
    signals TEXT,  -- JSON data
    metadata TEXT  -- JSON data
);

-- Индексы для tickers
CREATE INDEX idx_tickers_symbol_timestamp ON tickers(symbol, timestamp);
CREATE INDEX idx_tickers_timestamp ON tickers(timestamp);
CREATE INDEX idx_tickers_symbol ON tickers(symbol);

-- Партиционирование по времени (для больших объемов данных)
CREATE INDEX idx_tickers_recent ON tickers(symbol, timestamp) 
    WHERE timestamp > strftime('%s', 'now', '-7 days');
```

---

## 🛠️ Детальная реализация

### 1. **Оптимизированный DealsRepository**

**Файл:** `infrastructure/repositories/sql_deals_repository.py`

```python
import json
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass

from domain.entities.deal import Deal
from domain.repositories.deals_repository import DealsRepository
from infrastructure.database.connection import DatabaseConnection

@dataclass
class DealStatistics:
    total_deals: int
    profitable_deals: int
    total_profit: float
    average_profit_percent: float
    win_rate: float
    max_profit: float
    max_loss: float

class SQLDealsRepository(DealsRepository):
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        
    async def save(self, deal: Deal) -> Deal:
        \"\"\"Сохранение или обновление сделки\"\"\"
        
        if deal.id:
            # Update existing deal
            query = \"\"\"
                UPDATE deals SET 
                    status = ?, buy_order_id = ?, sell_order_id = ?,
                    closed_at = ?, profit_amount = ?, profit_percent = ?,
                    metadata = ?
                WHERE id = ?
            \"\"\"
            params = (
                deal.status, deal.buy_order_id, deal.sell_order_id,
                deal.closed_at, deal.profit_amount, deal.profit_percent,
                json.dumps(deal.metadata) if hasattr(deal, 'metadata') else '{}',
                deal.id
            )
        else:
            # Insert new deal
            query = \"\"\"
                INSERT INTO deals (
                    currency_pair_id, status, buy_order_id, sell_order_id,
                    created_at, closed_at, profit_amount, profit_percent, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            \"\"\"
            params = (
                deal.currency_pair_id, deal.status, deal.buy_order_id, deal.sell_order_id,
                deal.created_at, deal.closed_at, deal.profit_amount, deal.profit_percent,
                json.dumps(getattr(deal, 'metadata', {}))
            )
            
        cursor = await self.db.execute(query, params)
        
        if not deal.id:
            deal.id = cursor.lastrowid
            
        return deal
        
    async def get_by_id(self, deal_id: int) -> Optional[Deal]:
        \"\"\"Получение сделки по ID\"\"\"
        query = \"SELECT * FROM deals WHERE id = ?\"
        row = await self.db.fetch_one(query, (deal_id,))
        
        if row:
            return self._row_to_deal(row)
        return None
        
    async def get_open_deals(self, symbol: Optional[str] = None) -> List[Deal]:
        \"\"\"Получение открытых сделок\"\"\"
        
        if symbol:
            # Join with currency_pairs table to filter by symbol
            query = \"\"\"
                SELECT d.* FROM deals d
                JOIN currency_pairs cp ON d.currency_pair_id = cp.id
                WHERE d.status = 'OPEN' AND cp.symbol = ?
                ORDER BY d.created_at DESC
            \"\"\"
            params = (symbol,)
        else:
            query = \"SELECT * FROM deals WHERE status = 'OPEN' ORDER BY created_at DESC\"
            params = ()
            
        rows = await self.db.fetch_all(query, params)
        return [self._row_to_deal(row) for row in rows]
        
    async def get_deals_by_date_range(self, start: datetime, end: datetime) -> List[Deal]:
        \"\"\"Получение сделок за период\"\"\"
        query = \"\"\"
            SELECT * FROM deals 
            WHERE created_at BETWEEN ? AND ?
            ORDER BY created_at DESC
        \"\"\"
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
        
        rows = await self.db.fetch_all(query, (start_ts, end_ts))
        return [self._row_to_deal(row) for row in rows]
        
    async def get_profitable_deals(self, min_profit: float = 0) -> List[Deal]:
        \"\"\"Получение прибыльных сделок\"\"\"
        query = \"\"\"
            SELECT * FROM deals 
            WHERE profit_percent >= ? AND status = 'CLOSED'
            ORDER BY profit_percent DESC
        \"\"\"
        rows = await self.db.fetch_all(query, (min_profit,))
        return [self._row_to_deal(row) for row in rows]
        
    async def get_deals_statistics(self, symbol: Optional[str] = None) -> DealStatistics:
        \"\"\"Получение статистики по сделкам\"\"\"
        
        base_query = \"\"\"
            SELECT 
                COUNT(*) as total_deals,
                COUNT(CASE WHEN profit_percent > 0 THEN 1 END) as profitable_deals,
                COALESCE(SUM(profit_amount), 0) as total_profit,
                COALESCE(AVG(profit_percent), 0) as avg_profit_percent,
                COALESCE(MAX(profit_percent), 0) as max_profit,
                COALESCE(MIN(profit_percent), 0) as max_loss
            FROM deals d
        \"\"\"
        
        if symbol:
            query = base_query + \"\"\"
                JOIN currency_pairs cp ON d.currency_pair_id = cp.id
                WHERE d.status = 'CLOSED' AND cp.symbol = ?
            \"\"\"
            params = (symbol,)
        else:
            query = base_query + \" WHERE d.status = 'CLOSED'\"
            params = ()
            
        row = await self.db.fetch_one(query, params)
        
        total_deals = row['total_deals'] or 0
        profitable_deals = row['profitable_deals'] or 0
        
        return DealStatistics(
            total_deals=total_deals,
            profitable_deals=profitable_deals,
            total_profit=row['total_profit'],
            average_profit_percent=row['avg_profit_percent'],
            win_rate=profitable_deals / total_deals if total_deals > 0 else 0,
            max_profit=row['max_profit'],
            max_loss=row['max_loss']
        )
        
    async def batch_update_status(self, deal_ids: List[int], status: str) -> int:
        \"\"\"Массовое обновление статуса сделок\"\"\"
        if not deal_ids:
            return 0
            
        placeholders = ','.join('?' * len(deal_ids))
        query = f\"UPDATE deals SET status = ? WHERE id IN ({placeholders})\"
        params = [status] + deal_ids
        
        cursor = await self.db.execute(query, params)
        return cursor.rowcount
        
    def _row_to_deal(self, row) -> Deal:
        \"\"\"Конвертация строки БД в объект Deal\"\"\"
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        
        deal = Deal(
            id=row['id'],
            currency_pair_id=row['currency_pair_id'],
            status=row['status'],
            buy_order_id=row['buy_order_id'],
            sell_order_id=row['sell_order_id'],
            created_at=row['created_at'],
            closed_at=row['closed_at']
        )
        
        # Add calculated fields
        if hasattr(deal, 'profit_amount'):
            deal.profit_amount = row['profit_amount']
        if hasattr(deal, 'profit_percent'):
            deal.profit_percent = row['profit_percent']
        if hasattr(deal, 'metadata'):
            deal.metadata = metadata
            
        return deal
```

### 2. **Оптимизированный TickersRepository**

**Файл:** `infrastructure/repositories/sql_tickers_repository.py`

```python
import json
from typing import List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from domain.entities.ticker import Ticker
from domain.repositories.tickers_repository import TickersRepository
from infrastructure.database.connection import DatabaseConnection

@dataclass
class PricePoint:
    timestamp: int
    price: float
    volume: Optional[float] = None

class SQLTickersRepository(TickersRepository):
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        
    async def save(self, ticker: Ticker) -> Ticker:
        \"\"\"Сохранение тикера\"\"\"
        query = \"\"\"
            INSERT INTO tickers (symbol, price, volume, timestamp, signals, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        \"\"\"
        params = (
            ticker.symbol,
            ticker.price,
            getattr(ticker, 'volume', None),
            ticker.timestamp,
            json.dumps(ticker.signals) if ticker.signals else '{}',
            json.dumps(getattr(ticker, 'metadata', {}))
        )
        
        cursor = await self.db.execute(query, params)
        ticker.id = cursor.lastrowid
        return ticker
        
    async def get_latest(self, symbol: str) -> Optional[Ticker]:
        \"\"\"Получение последнего тикера\"\"\"
        query = \"\"\"
            SELECT * FROM tickers 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        \"\"\"
        row = await self.db.fetch_one(query, (symbol,))
        
        if row:
            return self._row_to_ticker(row)
        return None
        
    async def get_recent(self, symbol: str, limit: int = 100) -> List[Ticker]:
        \"\"\"Получение последних тикеров\"\"\"
        query = \"\"\"
            SELECT * FROM tickers 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        \"\"\"
        rows = await self.db.fetch_all(query, (symbol, limit))
        return [self._row_to_ticker(row) for row in rows]
        
    async def get_by_time_range(self, symbol: str, start: datetime, end: datetime) -> List[Ticker]:
        \"\"\"Получение тикеров за период\"\"\"
        query = \"\"\"
            SELECT * FROM tickers 
            WHERE symbol = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        \"\"\"
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
        
        rows = await self.db.fetch_all(query, (symbol, start_ts, end_ts))
        return [self._row_to_ticker(row) for row in rows]
        
    async def cleanup_old_data(self, keep_days: int = 30) -> int:
        \"\"\"Очистка старых данных\"\"\"
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        cutoff_ts = int(cutoff_date.timestamp())
        
        query = \"DELETE FROM tickers WHERE timestamp < ?\"
        cursor = await self.db.execute(query, (cutoff_ts,))
        return cursor.rowcount
        
    async def get_price_history(self, symbol: str, interval: str = '1m') -> List[PricePoint]:
        \"\"\"Получение истории цен с агрегацией\"\"\"
        
        # Интервалы в секундах
        intervals = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        
        interval_seconds = intervals.get(interval, 60)
        
        query = \"\"\"
            SELECT 
                (timestamp / ?) * ? as interval_start,
                AVG(price) as avg_price,
                AVG(volume) as avg_volume
            FROM tickers 
            WHERE symbol = ? 
                AND timestamp > ?
            GROUP BY interval_start
            ORDER BY interval_start ASC
        \"\"\"
        
        # Данные за последние 24 часа
        start_time = int((datetime.now() - timedelta(hours=24)).timestamp())
        
        rows = await self.db.fetch_all(query, (
            interval_seconds, interval_seconds, symbol, start_time
        ))
        
        return [
            PricePoint(
                timestamp=int(row['interval_start']),
                price=row['avg_price'],
                volume=row['avg_volume']
            )
            for row in rows
        ]
        
    def _row_to_ticker(self, row) -> Ticker:
        \"\"\"Конвертация строки БД в объект Ticker\"\"\"
        signals = json.loads(row['signals']) if row['signals'] else {}
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        
        ticker = Ticker(
            symbol=row['symbol'],
            price=row['price'],
            timestamp=row['timestamp'],
            signals=signals
        )
        
        if row['volume']:
            ticker.volume = row['volume']
        if metadata:
            ticker.metadata = metadata
        if hasattr(ticker, 'id'):
            ticker.id = row['id']
            
        return ticker
```

### 3. **Миграции и индексы**

**Файл:** `infrastructure/database/migrations/002_optimize_repositories.sql`

```sql
-- Дополнительные индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_deals_status_created ON deals(status, created_at);
CREATE INDEX IF NOT EXISTS idx_deals_profit_range ON deals(profit_percent) 
    WHERE profit_percent IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_orders_deal_status ON orders(deal_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_pending ON orders(status, created_at) 
    WHERE status IN ('PENDING', 'PARTIALLY_FILLED');

CREATE INDEX IF NOT EXISTS idx_tickers_symbol_recent ON tickers(symbol, timestamp DESC);

-- Оптимизация для аналитических запросов
CREATE INDEX IF NOT EXISTS idx_deals_analytics ON deals(status, created_at, profit_percent)
    WHERE status = 'CLOSED';

-- Партиционирование старых данных (для SQLite эмуляция через VIEW)
CREATE VIEW IF NOT EXISTS recent_tickers AS
SELECT * FROM tickers 
WHERE timestamp > strftime('%s', 'now', '-7 days');
```

---

## ✅ Критерии приемки

### Функциональные требования:
- [ ] Все репозитории работают с реальной БД
- [ ] Оптимизированные запросы с индексами
- [ ] Поддержка сложных фильтров и агрегаций
- [ ] Batch операции для массовых обновлений
- [ ] Автоматическая очистка старых данных

### Производительность:
- [ ] Запрос последних 100 тикеров < 5ms
- [ ] Статистика по сделкам < 10ms
- [ ] Поиск сделок по дате < 15ms
- [ ] Batch операции в 10+ раз быстрее одиночных

### Надежность:
- [ ] Graceful handling больших результатов
- [ ] Правильная обработка JSON полей
- [ ] Откат транзакций при ошибках

---

## 🚧 Риски и митигация

### Риск 1: Медленные запросы при больших объемах
**Митигация:** Тщательное тестирование индексов, мониторинг производительности

### Риск 2: Проблемы с миграциями
**Митигация:** Тестирование миграций на копиях продакшн данных

### Риск 3: Рост размера БД
**Митигация:** Автоматическая очистка старых данных, архивирование

---

## 📚 Связанные материалы

- Issue #6: DatabaseService
- [SQLite Performance Tips](https://www.sqlite.org/optoverview.html)
- [Database Indexing Best Practices](https://use-the-index-luke.com/)
