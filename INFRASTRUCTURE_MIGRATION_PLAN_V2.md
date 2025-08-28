# 🚀 AutoTrade v3.0: План Миграции на Двухуровневую Архитектуру Хранения

**Версия:** 2.0 (Исправленная и Оптимизированная)  
**Статус:** Готов к реализации  
**Автор:** Архитектурная команда AutoTrade  

---

## 🎯 Цель и Философия

### Проблема текущей системы:
- ❌ Данные в памяти теряются при перезапуске
- ❌ Нет возможности анализа исторических данных  
- ❌ Невозможно восстановить состояние сделок после сбоя
- ❌ JSON файлы медленные и ненадежные

### Решение - "Двухуровневая архитектура":
- ✅ **Уровень 1 (RAM):** Все операции со скоростью памяти через Pandas DataFrame
- ✅ **Уровень 2 (Диск):** Надежное хранение PostgreSQL + эффективные Parquet дампы
- ✅ **Изоляция слоев:** Сервисы работают только с памятью, персистентность - фоновая
- ✅ **Умная стратегия:** Критические данные сразу в БД, потоковые - пачками в дампы

---

## 🏗️ Архитектура: Два Независимых Уровня

```
┌─────────────────────────────────────────────────────────────┐
│                    СЕРВИСНЫЙ СЛОЙ                           │
│  (DealService, OrderService, TickerService, etc.)          │
│                        ↓ ↑                                  │
│                  Работает ТОЛЬКО с                          │
│                 DataFrame в памяти                          │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                 УРОВЕНЬ 1: ОПЕРАТИВНАЯ ПАМЯТЬ               │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   АТОМАРНЫЕ     │    │         ПОТОКОВЫЕ               │ │
│  │                 │    │                                 │ │
│  │ deals_df        │    │ tickers_df (10M записей)       │ │
│  │ orders_df       │    │ orderbooks_df (5M записей)     │ │
│  │ pairs_df        │    │ indicators_df (1M записей)     │ │
│  │                 │    │                                 │ │
│  │ ↓ мгновенно     │    │ ↓ накопление до лимита         │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                УРОВЕНЬ 2: ПЕРСИСТЕНТНОЕ ХРАНЕНИЕ            │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   PostgreSQL    │    │         Parquet Files           │ │
│  │                 │    │                                 │ │
│  │ deals ──────────│    │ /dumps/tickers_20240801.parquet│ │
│  │ orders          │    │ /dumps/books_20240801.parquet  │ │
│  │ currency_pairs  │    │ /dumps/signals_20240801.parquet│ │
│  │                 │    │                                 │ │
│  │ ↑ Write-Through │    │ ↑ Batch Dump (раз в период)    │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Ключевые Принципы

### 1. **Скорость торговли превыше всего**
- Все сервисы работают с DataFrame в памяти (наносекунды)
- Персистентность НЕ блокирует торговый цикл
- Критический путь остается таким же быстрым

### 2. **Умное разделение данных**
- **Атомарные** (Deal, Order) → мгновенно в PostgreSQL
- **Потоковые** (Ticker, OrderBook) → накопление + пачечный дамп

### 3. **Полная изоляция слоев**
- Сервисы не знают о существовании PostgreSQL/Parquet
- Можно легко переключать backend (SQLite, Redis, etc.)
- Тестирование проще - mock'и только для интерфейсов

---

## 🔧 Реализация: Пошаговый План

### **ШАГ 1: Создание Базовых Абстракций**

**Файл:** `src/domain/repositories/base_repository.py`

```python
"""
Базовые интерфейсы для двухуровневой архитектуры хранения.
Каждый репозиторий предоставляет единый интерфейс работы с данными,
скрывая детали персистентности от бизнес-логики.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
import pandas as pd
from datetime import datetime

# Универсальные типы для любых сущностей
T_Entity = TypeVar('T_Entity')      # Deal, Order, Ticker, etc.
T_EntityID = TypeVar('T_EntityID')  # int, str, UUID

class IMemoryFirstRepository(Generic[T_Entity, T_EntityID], ABC):
    """
    Базовый интерфейс для всех репозиториев с приоритетом памяти.
    
    ПРИНЦИП: Все операции чтения/записи выполняются с DataFrame в памяти.
    Персистентность происходит асинхронно в фоне.
    """
    
    @abstractmethod
    async def save(self, entity: T_Entity) -> T_Entity:
        """
        Сохраняет сущность в DataFrame (мгновенно).
        Персистентность запускается автоматически в фоне.
        
        Returns: Сохраненная сущность с присвоенным ID
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, entity_id: T_EntityID) -> Optional[T_Entity]:
        """Поиск по ID в DataFrame (наносекунды)."""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[T_Entity]:
        """Возвращает все записи из DataFrame."""
        pass
    
    @abstractmethod
    async def get_dataframe(self) -> pd.DataFrame:
        """
        Прямой доступ к DataFrame для сложных запросов и аналитики.
        Это основное преимущество новой архитектуры!
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: T_EntityID) -> bool:
        """Удаление из DataFrame + персистентного слоя."""
        pass

class IAtomicRepository(IMemoryFirstRepository[T_Entity, T_EntityID]):
    """
    Интерфейс для атомарных сущностей (Deal, Order, CurrencyPair).
    
    СТРАТЕГИЯ: Write-Through - каждое изменение немедленно идет в PostgreSQL.
    """
    
    @abstractmethod
    async def sync_to_persistent(self) -> None:
        """Принудительная синхронизация с PostgreSQL."""
        pass

class IStreamRepository(IMemoryFirstRepository[T_Entity, T_EntityID]):
    """
    Интерфейс для потоковых данных (Ticker, OrderBook, Indicators).
    
    СТРАТЕГИЯ: Batch Dump - накапливаем в памяти, периодически сбрасываем дампы.
    """
    
    @abstractmethod
    async def append_batch(self, entities: List[T_Entity]) -> None:
        """Эффективное добавление пачки записей."""
        pass
    
    @abstractmethod
    async def get_last_n(self, n: int) -> List[T_Entity]:
        """Получить последние N записей (для индикаторов)."""
        pass
    
    @abstractmethod
    async def force_dump(self) -> str:
        """
        Принудительный дамп в Parquet + очистка памяти.
        Returns: Путь к файлу дампа.
        """
        pass
    
    @abstractmethod
    def get_memory_usage(self) -> Dict[str, Any]:
        """Статистика использования памяти."""
        pass
```

---

### **ШАГ 2: Конкретные Интерфейсы**

**Файл:** `src/domain/repositories/repository_interfaces.py`

```python
"""
Конкретные интерфейсы для каждой сущности AutoTrade.
Эти интерфейсы импортируют сервисы.
"""

from .base_repository import IAtomicRepository, IStreamRepository
from src.domain.entities.deal import Deal
from src.domain.entities.order import Order
from src.domain.entities.currency_pair import CurrencyPair
from src.domain.entities.ticker import Ticker
from src.domain.entities.order_book import OrderBook
from src.domain.entities.indicator_data import IndicatorData

# ═══════════════════════════════════════════════════════════════
#                    АТОМАРНЫЕ РЕПОЗИТОРИИ
# ═══════════════════════════════════════════════════════════════

class IDealsRepository(IAtomicRepository[Deal, int]):
    """
    Репозиторий сделок - самая критичная сущность системы.
    
    ОСОБЕННОСТИ:
    - Каждое изменение немедленно в PostgreSQL
    - Поддержка сложных запросов (поиск активных сделок)
    - История изменений статусов
    """
    
    async def get_open_deals(self) -> List[Deal]:
        """Только активные сделки (используется в торговом цикле)."""
        pass
        
    async def get_deals_by_symbol(self, symbol: str) -> List[Deal]:
        """Сделки по валютной паре."""
        pass

class IOrdersRepository(IAtomicRepository[Order, int]):
    """
    Репозиторий ордеров с расширенными возможностями поиска.
    """
    
    async def get_open_orders(self) -> List[Order]:
        """Активные ордера (критично для мониторинга)."""
        pass
        
    async def get_orders_by_deal_id(self, deal_id: int) -> List[Order]:
        """Ордера по сделке."""
        pass
        
    async def get_orders_by_exchange_id(self, exchange_id: str) -> Optional[Order]:
        """Поиск по ID биржи (для синхронизации)."""
        pass

class ICurrencyPairRepository(IAtomicRepository[CurrencyPair, str]):
    """
    Репозиторий валютных пар.
    ID = symbol (например, "ETH/USDT")
    """
    pass

# ═══════════════════════════════════════════════════════════════
#                    ПОТОКОВЫЕ РЕПОЗИТОРИИ  
# ═══════════════════════════════════════════════════════════════

class ITickersRepository(IStreamRepository[Ticker, int]):
    """
    Репозиторий тиков - самый высокочастотный поток данных.
    
    НАСТРОЙКИ:
    - Лимит памяти: 10M записей (~2GB RAM)
    - Автодамп при достижении лимита
    - Дампы по дням: tickers_YYYYMMDD.parquet
    """
    
    async def get_recent_tickers(self, symbol: str, minutes: int = 60) -> List[Ticker]:
        """Тики за последние N минут (для индикаторов)."""
        pass

class IOrderBooksRepository(IStreamRepository[OrderBook, int]):
    """
    Репозиторий стаканов заявок.
    
    НАСТРОЙКИ:
    - Лимит памяти: 5M записей (~1GB RAM)
    - Дампы каждые 2 часа
    """
    pass

class IIndicatorsRepository(IStreamRepository[IndicatorData, int]):
    """
    Репозиторий рассчитанных индикаторов (MACD, RSI, MA).
    
    НАСТРОЙКИ:
    - Лимит памяти: 1M записей (~500MB RAM)
    - Дампы ежедневно
    """
    
    async def get_latest_macd(self, symbol: str) -> Optional[IndicatorData]:
        """Последний MACD для торгового решения."""
        pass
```

---

### **ШАГ 3: Эталонная Реализация Атомарного Репозитория**

**Файл:** `src/infrastructure/repositories/memory_first_deals_repository.py`

```python
"""
Эталонная реализация атомарного репозитория для сделок.

АРХИТЕКТУРА:
1. Все операции с pandas DataFrame в памяти (быстро)
2. Каждое изменение асинхронно дублируется в PostgreSQL  
3. При старте загружаем данные из PostgreSQL в DataFrame
4. Полная изоляция бизнес-логики от БД
"""

import asyncio
import pandas as pd
import psycopg
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.domain.entities.deal import Deal
from src.domain.repositories.repository_interfaces import IDealsRepository

logger = logging.getLogger(__name__)

class MemoryFirstDealsRepository(IDealsRepository):
    """
    Репозиторий сделок с приоритетом памяти и автосинхронизацией с PostgreSQL.
    """
    
    def __init__(self, postgres_dsn: str):
        self.postgres_dsn = postgres_dsn
        self._df = pd.DataFrame()
        self._next_id = 1
        self._sync_lock = asyncio.Lock()
        
        # Статистика для мониторинга
        self.stats = {
            'saves': 0,
            'sync_operations': 0,
            'last_sync': None,
            'sync_errors': 0
        }
        
    async def initialize(self) -> None:
        """
        Инициализация: создание схемы БД + загрузка данных в DataFrame.
        Вызывается один раз при старте приложения.
        """
        await self._ensure_database_schema()
        await self._load_from_postgres()
        logger.info(f"DealsRepository инициализирован: {len(self._df)} сделок в памяти")
    
    # ═══════════════════════════════════════════════════════════════
    #                    ОСНОВНЫЕ CRUD ОПЕРАЦИИ
    # ═══════════════════════════════════════════════════════════════
    
    async def save(self, deal: Deal) -> Deal:
        """
        Сохраняет сделку в DataFrame + запускает фоновую синхронизацию с PostgreSQL.
        
        ПРОИЗВОДИТЕЛЬНОСТЬ: ~0.1ms (операции с DataFrame)
        """
        # 1. Присваиваем ID если новая сделка
        if deal.id is None:
            deal.id = self._next_id
            self._next_id += 1
        
        # 2. Конвертируем в dict для DataFrame
        deal_dict = self._deal_to_dict(deal)
        
        # 3. Обновляем DataFrame (молниеносно)
        if deal.id in self._df.index:
            # Обновление существующей записи
            for column, value in deal_dict.items():
                self._df.at[deal.id, column] = value
        else:
            # Новая запись
            new_row = pd.DataFrame([deal_dict], index=[deal.id])
            self._df = pd.concat([self._df, new_row])
        
        # 4. Асинхронная синхронизация с PostgreSQL (не блокирует)
        asyncio.create_task(self._sync_deal_to_postgres(deal))
        
        self.stats['saves'] += 1
        logger.debug(f"Deal {deal.id} сохранена в памяти")
        
        return deal
    
    async def find_by_id(self, deal_id: int) -> Optional[Deal]:
        """
        Поиск сделки по ID в DataFrame.
        
        ПРОИЗВОДИТЕЛЬНОСТЬ: ~0.001ms
        """
        if deal_id not in self._df.index:
            return None
            
        row = self._df.loc[deal_id]
        return self._dict_to_deal(row.to_dict())
    
    async def get_all(self) -> List[Deal]:
        """Все сделки из DataFrame."""
        return [self._dict_to_deal(row.to_dict()) 
                for _, row in self._df.iterrows()]
    
    async def get_open_deals(self) -> List[Deal]:
        """
        Активные сделки - критично для торгового цикла.
        
        ОПТИМИЗАЦИЯ: Используем pandas фильтрацию (очень быстро)
        """
        open_deals_df = self._df[self._df['status'].isin(['OPEN', 'BUY_FILLED'])]
        return [self._dict_to_deal(row.to_dict()) 
                for _, row in open_deals_df.iterrows()]
    
    async def get_deals_by_symbol(self, symbol: str) -> List[Deal]:
        """Сделки по валютной паре с использованием pandas фильтрации."""
        symbol_deals_df = self._df[self._df['symbol'] == symbol]
        return [self._dict_to_deal(row.to_dict()) 
                for _, row in symbol_deals_df.iterrows()]
    
    async def get_dataframe(self) -> pd.DataFrame:
        """
        Прямой доступ к DataFrame для аналитики.
        
        МОЩЬ НОВОЙ АРХИТЕКТУРЫ: 
        - df.groupby('status').size()  # Статистика по статусам
        - df[df['profit'] > 0]         # Прибыльные сделки  
        - df.resample('1H').count()    # Сделки по часам
        """
        return self._df.copy()
    
    async def delete(self, deal_id: int) -> bool:
        """Удаление из DataFrame + PostgreSQL."""
        if deal_id not in self._df.index:
            return False
            
        # Удаляем из DataFrame
        self._df.drop(deal_id, inplace=True)
        
        # Асинхронное удаление из PostgreSQL
        asyncio.create_task(self._delete_from_postgres(deal_id))
        
        return True
    
    # ═══════════════════════════════════════════════════════════════
    #                    СИНХРОНИЗАЦИЯ С POSTGRESQL
    # ═══════════════════════════════════════════════════════════════
    
    async def sync_to_persistent(self) -> None:
        """Принудительная полная синхронизация с PostgreSQL."""
        async with self._sync_lock:
            try:
                async with await psycopg.AsyncConnection.connect(self.postgres_dsn) as conn:
                    async with conn.cursor() as cur:
                        # Полная перезапись таблицы
                        await cur.execute("TRUNCATE TABLE deals")
                        
                        for _, row in self._df.iterrows():
                            await cur.execute("""
                                INSERT INTO deals (id, symbol, status, buy_order_id, sell_order_id, 
                                                 profit, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                row.name, row['symbol'], row['status'], 
                                row['buy_order_id'], row['sell_order_id'],
                                row['profit'], row['created_at'], row['updated_at']
                            ))
                        
                        await conn.commit()
                        
                self.stats['sync_operations'] += 1
                self.stats['last_sync'] = datetime.now()
                logger.info(f"Полная синхронизация завершена: {len(self._df)} сделок")
                
            except Exception as e:
                self.stats['sync_errors'] += 1
                logger.error(f"Ошибка синхронизации с PostgreSQL: {e}")
    
    async def _sync_deal_to_postgres(self, deal: Deal) -> None:
        """Фоновая синхронизация одной сделки с PostgreSQL."""
        try:
            async with await psycopg.AsyncConnection.connect(self.postgres_dsn) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        INSERT INTO deals (id, symbol, status, buy_order_id, sell_order_id, 
                                         profit, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            status = EXCLUDED.status,
                            sell_order_id = EXCLUDED.sell_order_id,
                            profit = EXCLUDED.profit,
                            updated_at = EXCLUDED.updated_at
                    """, (
                        deal.id, deal.symbol, deal.status,
                        deal.buy_order.id if deal.buy_order else None,
                        deal.sell_order.id if deal.sell_order else None,
                        deal.profit, deal.created_at, deal.updated_at
                    ))
                    await conn.commit()
                    
        except Exception as e:
            self.stats['sync_errors'] += 1
            logger.error(f"Ошибка синхронизации deal {deal.id}: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    #                    ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ═══════════════════════════════════════════════════════════════
    
    async def _ensure_database_schema(self) -> None:
        """Создание таблицы deals если не существует."""
        async with await psycopg.AsyncConnection.connect(self.postgres_dsn) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS deals (
                        id INTEGER PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        buy_order_id INTEGER,
                        sell_order_id INTEGER,
                        profit DECIMAL(18,8) DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await conn.commit()
    
    async def _load_from_postgres(self) -> None:
        """Загрузка всех сделок из PostgreSQL в DataFrame при старте."""
        try:
            async with await psycopg.AsyncConnection.connect(self.postgres_dsn) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT * FROM deals ORDER BY id")
                    rows = await cur.fetchall()
                    
                    if rows:
                        columns = [desc[0] for desc in cur.description]
                        data = [dict(zip(columns, row)) for row in rows]
                        self._df = pd.DataFrame(data).set_index('id')
                        self._next_id = self._df.index.max() + 1 if len(self._df) > 0 else 1
                    else:
                        self._df = pd.DataFrame(columns=[
                            'symbol', 'status', 'buy_order_id', 'sell_order_id', 
                            'profit', 'created_at', 'updated_at'
                        ])
                        
        except Exception as e:
            logger.warning(f"Не удалось загрузить данные из PostgreSQL: {e}")
            # Инициализируем пустой DataFrame
            self._df = pd.DataFrame(columns=[
                'symbol', 'status', 'buy_order_id', 'sell_order_id', 
                'profit', 'created_at', 'updated_at'
            ])
    
    def _deal_to_dict(self, deal: Deal) -> Dict[str, Any]:
        """Конвертация Deal в dict для DataFrame."""
        return {
            'symbol': deal.symbol,
            'status': deal.status,
            'buy_order_id': deal.buy_order.id if deal.buy_order else None,
            'sell_order_id': deal.sell_order.id if deal.sell_order else None,
            'profit': float(deal.profit) if deal.profit else 0.0,
            'created_at': deal.created_at,
            'updated_at': deal.updated_at or datetime.now()
        }
    
    def _dict_to_deal(self, data: Dict[str, Any]) -> Deal:
        """Конвертация dict в Deal object."""
        # Здесь будет логика восстановления Deal из dict
        # Включая загрузку связанных Order объектов
        deal = Deal(
            id=data.get('id'),
            symbol=data['symbol'],
            status=data['status'],
            profit=data.get('profit', 0.0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
        # TODO: Загрузка buy_order и sell_order по ID
        return deal
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика репозитория для мониторинга."""
        return {
            **self.stats,
            'memory_records': len(self._df),
            'memory_usage_mb': self._df.memory_usage(deep=True).sum() / 1024 / 1024
        }
```

---

### **ШАГ 4: Эталонная Реализация Потокового Репозитория**

**Файл:** `src/infrastructure/repositories/memory_first_tickers_repository.py`

```python
"""
Эталонная реализация потокового репозитория для тиков.

АРХИТЕКТУРА:
1. Накапливаем тики в pandas DataFrame (быстро)
2. При достижении лимита (10M записей) - автодамп в Parquet
3. Очищаем память после дампа  
4. Парquet файлы по дням для эффективной аналитики
"""

import asyncio
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from src.domain.entities.ticker import Ticker
from src.domain.repositories.repository_interfaces import ITickersRepository

logger = logging.getLogger(__name__)

class MemoryFirstTickersRepository(ITickersRepository):
    """
    Потоковый репозиторий тиков с автоматическим дампингом.
    
    НАСТРОЙКИ:
    - Лимит памяти: 10M записей (~2GB RAM)
    - Дампы в /dumps/tickers/
    - Автоочистка старых файлов (30 дней)
    """
    
    def __init__(self, 
                 dump_dir: str = "./dumps/tickers",
                 memory_limit: int = 10_000_000,
                 auto_dump_threshold: int = 8_000_000,
                 retention_days: int = 30):
        
        self.dump_dir = dump_dir
        self.memory_limit = memory_limit
        self.auto_dump_threshold = auto_dump_threshold
        self.retention_days = retention_days
        
        # Основной DataFrame в памяти
        self._df = pd.DataFrame(columns=[
            'timestamp', 'symbol', 'last', 'high', 'low', 'volume', 'bid', 'ask'
        ])
        
        self._next_id = 1
        self._dump_count = 0
        
        # Статистика
        self.stats = {
            'records_saved': 0,
            'dumps_created': 0,
            'last_dump': None,
            'memory_usage_mb': 0,
            'dump_errors': 0
        }
        
        # Создаем директорию дампов
        os.makedirs(self.dump_dir, exist_ok=True)
        
    async def initialize(self) -> None:
        """Инициализация: очистка старых дампов."""
        await self._cleanup_old_dumps()
        logger.info(f"TickersRepository инициализирован. Лимит памяти: {self.memory_limit:,} записей")
    
    # ═══════════════════════════════════════════════════════════════
    #                    ОСНОВНЫЕ ОПЕРАЦИИ С ТИКАМИ
    # ═══════════════════════════════════════════════════════════════
    
    async def save(self, ticker: Ticker) -> Ticker:
        """
        Добавляет тик в DataFrame + проверяет лимиты памяти.
        
        ПРОИЗВОДИТЕЛЬНОСТЬ: ~0.01ms на тик
        """
        if ticker.id is None:
            ticker.id = self._next_id
            self._next_id += 1
        
        # Конвертация в dict для DataFrame
        ticker_dict = self._ticker_to_dict(ticker)
        
        # Добавляем новую строку в DataFrame (эффективно)
        new_row = pd.DataFrame([ticker_dict], index=[ticker.id])
        self._df = pd.concat([self._df, new_row])
        
        self.stats['records_saved'] += 1
        
        # Проверяем лимит памяти (автодамп)
        if len(self._df) >= self.auto_dump_threshold:
            asyncio.create_task(self._auto_dump())
        
        return ticker
    
    async def append_batch(self, tickers: List[Ticker]) -> None:
        """
        Эффективное добавление пачки тиков.
        
        ОПТИМИЗАЦИЯ: Один pd.concat() вместо множества отдельных операций.
        """
        if not tickers:
            return
        
        # Присваиваем ID и конвертируем в list of dicts
        ticker_dicts = []
        for ticker in tickers:
            if ticker.id is None:
                ticker.id = self._next_id
                self._next_id += 1
            ticker_dicts.append(self._ticker_to_dict(ticker))
        
        # Создаем DataFrame из пачки
        if ticker_dicts:
            indices = [t['id'] for t in ticker_dicts]
            batch_df = pd.DataFrame(ticker_dicts, index=indices)
            self._df = pd.concat([self._df, batch_df])
            
            self.stats['records_saved'] += len(tickers)
            
            # Проверяем лимит памяти
            if len(self._df) >= self.auto_dump_threshold:
                asyncio.create_task(self._auto_dump())
    
    async def find_by_id(self, ticker_id: int) -> Optional[Ticker]:
        """Поиск тика по ID (редко используется для потоковых данных)."""
        if ticker_id not in self._df.index:
            return None
        
        row = self._df.loc[ticker_id]
        return self._dict_to_ticker(row.to_dict())
    
    async def get_all(self) -> List[Ticker]:
        """Все тики из памяти (может быть много!)."""
        return [self._dict_to_ticker(row.to_dict()) 
                for _, row in self._df.iterrows()]
    
    async def get_last_n(self, n: int) -> List[Ticker]:
        """
        Последние N тиков - часто используется для индикаторов.
        
        ОПТИМИЗАЦИЯ: pandas tail() очень быстрый.
        """
        tail_df = self._df.tail(n)
        return [self._dict_to_ticker(row.to_dict()) 
                for _, row in tail_df.iterrows()]
    
    async def get_recent_tickers(self, symbol: str, minutes: int = 60) -> List[Ticker]:
        """
        Тики за последние N минут для конкретной валютной пары.
        
        МОЩЬ PANDAS: Комбинированная фильтрация по времени и символу.
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        filtered_df = self._df[
            (self._df['symbol'] == symbol) & 
            (self._df['timestamp'] >= cutoff_time)
        ].sort_values('timestamp')
        
        return [self._dict_to_ticker(row.to_dict()) 
                for _, row in filtered_df.iterrows()]
    
    async def get_dataframe(self) -> pd.DataFrame:
        """
        Прямой доступ к DataFrame для аналитики тиков.
        
        ПРИМЕРЫ МОЩНЫХ ЗАПРОСОВ:
        - df.groupby('symbol')['volume'].sum()           # Объем по парам
        - df.resample('1min', on='timestamp')['last'].ohlc()  # OHLC по минутам  
        - df[df['last'] > df['last'].shift(1)]          # Растущие тики
        """
        return self._df.copy()
    
    async def delete(self, ticker_id: int) -> bool:
        """Удаление тика (редко используется)."""
        if ticker_id not in self._df.index:
            return False
        
        self._df.drop(ticker_id, inplace=True)
        return True
    
    # ═══════════════════════════════════════════════════════════════
    #                    ДАМПИНГ В PARQUET
    # ═══════════════════════════════════════════════════════════════
    
    async def force_dump(self) -> str:
        """
        Принудительный дамп всех данных в Parquet.
        
        Returns: Путь к созданному файлу.
        """
        if self._df.empty:
            logger.warning("Нет данных для дампа")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tickers_{timestamp}.parquet"
        filepath = os.path.join(self.dump_dir, filename)
        
        try:
            # Сохраняем DataFrame в Parquet (сжатие + скорость)
            self._df.to_parquet(filepath, compression='snappy', index=True)
            
            logger.info(f"Дамп создан: {filepath} ({len(self._df):,} записей)")
            
            # Обновляем статистику
            self.stats['dumps_created'] += 1
            self.stats['last_dump'] = datetime.now()
            
            # Очищаем память
            records_dumped = len(self._df)
            self._df = self._df.iloc[0:0]  # Очистка с сохранением структуры
            
            logger.info(f"Память очищена: {records_dumped:,} записей")
            
            return filepath
            
        except Exception as e:
            self.stats['dump_errors'] += 1
            logger.error(f"Ошибка создания дампа: {e}")
            raise
    
    async def _auto_dump(self) -> None:
        """Автоматический дамп при достижении лимита."""
        if len(self._df) >= self.auto_dump_threshold:
            logger.info(f"Автодамп: {len(self._df):,} записей в памяти")
            await self.force_dump()
    
    async def _cleanup_old_dumps(self) -> None:
        """Удаление старых дампов (экономия места)."""
        if not os.path.exists(self.dump_dir):
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0
        
        for filename in os.listdir(self.dump_dir):
            if filename.endswith('.parquet'):
                filepath = os.path.join(self.dump_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)
                    deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Удалено старых дампов: {deleted_count}")
    
    # ═══════════════════════════════════════════════════════════════
    #                    МОНИТОРИНГ И СТАТИСТИКА
    # ═══════════════════════════════════════════════════════════════
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Детальная статистика использования памяти."""
        memory_bytes = self._df.memory_usage(deep=True).sum()
        memory_mb = memory_bytes / 1024 / 1024
        
        return {
            'records_in_memory': len(self._df),
            'memory_usage_mb': round(memory_mb, 2),
            'memory_limit_records': self.memory_limit,
            'memory_usage_percent': round(len(self._df) / self.memory_limit * 100, 1),
            'auto_dump_threshold': self.auto_dump_threshold,
            'next_dump_at': self.auto_dump_threshold - len(self._df)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Полная статистика репозитория."""
        return {
            **self.stats,
            **self.get_memory_usage(),
            'dump_directory': self.dump_dir,
            'retention_days': self.retention_days
        }
    
    # ═══════════════════════════════════════════════════════════════
    #                    ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ═══════════════════════════════════════════════════════════════
    
    def _ticker_to_dict(self, ticker: Ticker) -> Dict[str, Any]:
        """Конвертация Ticker в dict для DataFrame."""
        return {
            'id': ticker.id,
            'timestamp': ticker.timestamp,
            'symbol': ticker.symbol,
            'last': float(ticker.last),
            'high': float(ticker.high) if ticker.high else None,
            'low': float(ticker.low) if ticker.low else None,
            'volume': float(ticker.baseVolume) if ticker.baseVolume else None,
            'bid': float(ticker.bid) if ticker.bid else None,
            'ask': float(ticker.ask) if ticker.ask else None
        }
    
    def _dict_to_ticker(self, data: Dict[str, Any]) -> Ticker:
        """Конвертация dict в Ticker object."""
        return Ticker(
            id=data.get('id'),
            timestamp=data['timestamp'],
            symbol=data['symbol'],
            last=data['last'],
            high=data.get('high'),
            low=data.get('low'),
            baseVolume=data.get('volume'),
            bid=data.get('bid'),
            ask=data.get('ask')
        )
```

---

### **ШАГ 5: Умная Фабрика Репозиториев**

**Файл:** `src/infrastructure/repository_factory.py`

```python
"""
Централизованная фабрика репозиториев с поддержкой разных backend'ов.

ВОЗМОЖНОСТИ:
- Легкое переключение между реализациями через конфиг
- Кеширование инстансов репозиториев  
- Автоинициализация всех репозиториев
- Поддержка fallback стратегий
"""

import asyncio
from typing import Dict, Any, Optional
import logging

from src.domain.repositories.repository_interfaces import (
    IDealsRepository, IOrdersRepository, ICurrencyPairRepository,
    ITickersRepository, IOrderBooksRepository, IIndicatorsRepository
)

# Импорты реализаций
from src.infrastructure.repositories.memory_first_deals_repository import MemoryFirstDealsRepository
from src.infrastructure.repositories.memory_first_orders_repository import MemoryFirstOrdersRepository
from src.infrastructure.repositories.memory_first_tickers_repository import MemoryFirstTickersRepository
# ... другие реализации

# Fallback к старым in-memory репозиториям
from src.infrastructure.repositories.deals_repository import InMemoryDealsRepository
from src.infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from src.infrastructure.repositories.tickers_repository import InMemoryTickerRepository

logger = logging.getLogger(__name__)

class RepositoryFactory:
    """
    Умная фабрика репозиториев с поддержкой конфигурации и fallback'ов.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._repository_cache: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize_all(self) -> None:
        """
        Инициализация всех репозиториев параллельно.
        Вызывается один раз при старте приложения.
        """
        if self._initialized:
            return
        
        logger.info("Инициализация репозиториев...")
        
        # Параллельная инициализация всех репозиториев
        tasks = []
        
        # Атомарные репозитории
        tasks.append(self._init_deals_repository())
        tasks.append(self._init_orders_repository())
        tasks.append(self._init_currency_pairs_repository())
        
        # Потоковые репозитории  
        tasks.append(self._init_tickers_repository())
        tasks.append(self._init_order_books_repository())
        tasks.append(self._init_indicators_repository())
        
        # Ждем инициализации всех
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self._initialized = True
        logger.info("Все репозитории инициализированы")
    
    # ═══════════════════════════════════════════════════════════════
    #                    АТОМАРНЫЕ РЕПОЗИТОРИИ
    # ═══════════════════════════════════════════════════════════════
    
    async def get_deals_repository(self) -> IDealsRepository:
        """Получить репозиторий сделок с умным fallback."""
        if 'deals' in self._repository_cache:
            return self._repository_cache['deals']
        
        return await self._init_deals_repository()
    
    async def _init_deals_repository(self) -> IDealsRepository:
        """Инициализация репозитория сделок."""
        storage_type = self.config.get('storage', {}).get('deals_type', 'memory_first_postgres')
        
        try:
            if storage_type == 'memory_first_postgres':
                postgres_dsn = self.config.get('postgres_dsn')
                if not postgres_dsn:
                    raise ValueError("postgres_dsn не найден в конфигурации")
                
                repo = MemoryFirstDealsRepository(postgres_dsn)
                await repo.initialize()
                
                logger.info("DealsRepository: MemoryFirst + PostgreSQL")
                
            elif storage_type == 'in_memory_legacy':
                repo = InMemoryDealsRepository()
                logger.info("DealsRepository: Legacy InMemory (fallback)")
                
            else:
                raise ValueError(f"Неизвестный тип storage для deals: {storage_type}")
            
            self._repository_cache['deals'] = repo
            return repo
            
        except Exception as e:
            logger.error(f"Ошибка инициализации DealsRepository: {e}")
            
            # Fallback к старой реализации
            logger.warning("Переключение на Legacy InMemory DealsRepository")
            repo = InMemoryDealsRepository()
            self._repository_cache['deals'] = repo
            return repo
    
    async def get_orders_repository(self) -> IOrdersRepository:
        """Получить репозиторий ордеров."""
        if 'orders' in self._repository_cache:
            return self._repository_cache['orders']
        
        return await self._init_orders_repository()
    
    async def _init_orders_repository(self) -> IOrdersRepository:
        """Инициализация репозитория ордеров."""
        storage_type = self.config.get('storage', {}).get('orders_type', 'memory_first_postgres')
        
        try:
            if storage_type == 'memory_first_postgres':
                postgres_dsn = self.config.get('postgres_dsn')
                repo = MemoryFirstOrdersRepository(postgres_dsn)
                await repo.initialize()
                logger.info("OrdersRepository: MemoryFirst + PostgreSQL")
                
            elif storage_type == 'in_memory_legacy':
                max_orders = self.config.get('max_orders', 50000)
                repo = InMemoryOrdersRepository(max_orders=max_orders)
                logger.info(f"OrdersRepository: Legacy InMemory (max: {max_orders})")
                
            else:
                raise ValueError(f"Неизвестный тип storage для orders: {storage_type}")
            
            self._repository_cache['orders'] = repo
            return repo
            
        except Exception as e:
            logger.error(f"Ошибка инициализации OrdersRepository: {e}")
            
            # Fallback
            max_orders = self.config.get('max_orders', 50000)
            repo = InMemoryOrdersRepository(max_orders=max_orders)
            self._repository_cache['orders'] = repo
            return repo
    
    # ═══════════════════════════════════════════════════════════════
    #                    ПОТОКОВЫЕ РЕПОЗИТОРИИ  
    # ═══════════════════════════════════════════════════════════════
    
    async def get_tickers_repository(self) -> ITickersRepository:
        """Получить репозиторий тиков."""
        if 'tickers' in self._repository_cache:
            return self._repository_cache['tickers']
        
        return await self._init_tickers_repository()
    
    async def _init_tickers_repository(self) -> ITickersRepository:
        """Инициализация репозитория тиков."""
        storage_type = self.config.get('storage', {}).get('tickers_type', 'memory_first_parquet')
        
        try:
            if storage_type == 'memory_first_parquet':
                dump_dir = self.config.get('dumps_dir', './dumps/tickers')
                memory_limit = self.config.get('tickers_memory_limit', 10_000_000)
                
                repo = MemoryFirstTickersRepository(
                    dump_dir=dump_dir,
                    memory_limit=memory_limit
                )
                await repo.initialize()
                
                logger.info(f"TickersRepository: MemoryFirst + Parquet (лимит: {memory_limit:,})")
                
            elif storage_type == 'in_memory_legacy':
                max_size = self.config.get('max_tickers', 5000)
                repo = InMemoryTickerRepository(max_size=max_size)
                logger.info(f"TickersRepository: Legacy InMemory (max: {max_size})")
                
            else:
                raise ValueError(f"Неизвестный тип storage для tickers: {storage_type}")
            
            self._repository_cache['tickers'] = repo
            return repo
            
        except Exception as e:
            logger.error(f"Ошибка инициализации TickersRepository: {e}")
            
            # Fallback
            max_size = self.config.get('max_tickers', 5000)
            repo = InMemoryTickerRepository(max_size=max_size)
            self._repository_cache['tickers'] = repo
            return repo
    
    # ═══════════════════════════════════════════════════════════════
    #                    УТИЛИТЫ И МОНИТОРИНГ
    # ═══════════════════════════════════════════════════════════════
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """Статистика всех репозиториев для мониторинга."""
        stats = {}
        
        for repo_name, repo in self._repository_cache.items():
            if hasattr(repo, 'get_stats'):
                stats[repo_name] = repo.get_stats()
            else:
                stats[repo_name] = {'type': 'legacy', 'available': True}
        
        return stats
    
    async def force_sync_all(self) -> None:
        """Принудительная синхронизация всех атомарных репозиториев."""
        tasks = []
        
        for repo_name, repo in self._repository_cache.items():
            if hasattr(repo, 'sync_to_persistent'):
                tasks.append(repo.sync_to_persistent())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Синхронизация завершена для {len(tasks)} репозиториев")
    
    async def force_dump_all(self) -> Dict[str, str]:
        """Принудительный дамп всех потоковых репозиториев."""
        dump_results = {}
        
        for repo_name, repo in self._repository_cache.items():
            if hasattr(repo, 'force_dump'):
                try:
                    filepath = await repo.force_dump()
                    dump_results[repo_name] = filepath
                except Exception as e:
                    dump_results[repo_name] = f"Ошибка: {e}"
        
        return dump_results
    
    def get_config(self) -> Dict[str, Any]:
        """Текущая конфигурация фабрики."""
        return self.config.copy()
```

---

### **ШАГ 6: Обновление Конфигурации**

**Файл:** `src/config/config.json` (дополнения)

```json
{
  "comment": "AutoTrade v3.0 Configuration - Двухуровневое хранение",
  
  "postgres_dsn": "postgresql://autotrade_user:secure_password@localhost:5432/autotrade_db",
  
  "storage": {
    "comment": "Настройки репозиториев - можно легко переключать типы",
    
    "deals_type": "memory_first_postgres",
    "orders_type": "memory_first_postgres", 
    "currency_pairs_type": "memory_first_postgres",
    
    "tickers_type": "memory_first_parquet",
    "order_books_type": "memory_first_parquet",
    "indicators_type": "memory_first_parquet"
  },
  
  "memory_limits": {
    "tickers_memory_limit": 10000000,
    "order_books_memory_limit": 5000000,
    "indicators_memory_limit": 1000000,
    
    "auto_dump_threshold_percent": 80,
    "retention_days": 30
  },
  
  "dumps_dir": "./dumps",
  "max_orders": 50000,
  "max_tickers": 5000,
  
  "currency_pair": {
    "symbol": "ETH/USDT",
    "base_currency": "ETH", 
    "quote_currency": "USDT",
    "deal_quota": 25.0
  },
  
  "existing_config": "все остальные настройки остаются без изменений"
}
```

---

### **ШАГ 7: Интеграция в main.py**

**Файл:** `main.py` (изменения)

```python
"""
Обновленный main.py для AutoTrade v3.0 с двухуровневой архитектурой.

ИЗМЕНЕНИЯ:
- Замена прямого создания репозиториев на RepositoryFactory
- Автоинициализация всех репозиториев при старте  
- Добавление graceful shutdown с принудительной синхронизацией
"""

import asyncio
import sys
import os
import signal
import logging
from datetime import datetime

# Добавляем src в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.config_loader import ConfigLoader
from src.infrastructure.repository_factory import RepositoryFactory  # НОВОЕ!

# Остальные импорты остаются без изменений
from src.domain.factories.order_factory import OrderFactory
from src.domain.factories.deal_factory import DealFactory
from src.domain.services.deals.deal_service import DealService
from src.domain.services.orders.order_service import OrderService
# ... все остальные импорты

logger = logging.getLogger(__name__)

# Глобальная переменная для graceful shutdown
repository_factory: Optional[RepositoryFactory] = None

async def main():
    """
    Основная функция запуска AutoTrade v3.0.
    """
    global repository_factory
    
    try:
        # ════════════════════════════════════════════════════════════════════
        #                          ИНИЦИАЛИЗАЦИЯ
        # ════════════════════════════════════════════════════════════════════
        
        logger.info("🚀 Запуск AutoTrade v3.0 с двухуровневой архитектурой")
        
        # 1. Загрузка конфигурации (без изменений)
        config_loader = ConfigLoader()
        config = config_loader.load_config()
        
        # 2. НОВОЕ: Создание и инициализация фабрики репозиториев
        logger.info("Инициализация репозиториев...")
        repository_factory = RepositoryFactory(config)
        await repository_factory.initialize_all()
        
        # 3. Получение репозиториев из фабрики (вместо прямого создания)
        deals_repo = await repository_factory.get_deals_repository()
        orders_repo = await repository_factory.get_orders_repository()
        # tickers_repo получается локально в run_realtime_trading
        
        logger.info("✅ Репозитории инициализированы:")
        stats = await repository_factory.get_all_stats()
        for repo_name, repo_stats in stats.items():
            logger.info(f"  {repo_name}: {repo_stats}")
        
        # ════════════════════════════════════════════════════════════════════
        #                       ИНИЦИАЛИЗАЦИЯ СЕРВИСОВ  
        #                        (БЕЗ ИЗМЕНЕНИЙ)
        # ════════════════════════════════════════════════════════════════════
        
        # 4. Коннекторы бирж (без изменений)
        pro_exchange_connector_prod = CcxtExchangeConnector(use_sandbox=False)
        pro_exchange_connector_sandbox = CcxtExchangeConnector(use_sandbox=True)
        
        # 5. Фабрики (без изменений)
        order_factory = OrderFactory()
        deal_factory = DealFactory(order_factory)
        
        # 6. Настройка exchange info (без изменений)
        symbol_ccxt = config["currency_pair"]["symbol"].replace("/", "")
        symbol_info = await pro_exchange_connector_prod.get_symbol_info(symbol_ccxt)
        order_factory.update_exchange_info(symbol_ccxt, symbol_info)
        
        # 7. Основные сервисы (используют новые репозитории!)
        order_service = OrderService(
            orders_repo,  # Новый репозиторий из фабрики!
            order_factory, 
            pro_exchange_connector_sandbox, 
            currency_pair_symbol=symbol_ccxt
        )
        
        deal_service = DealService(
            deals_repo,   # Новый репозиторий из фабрики!
            order_service, 
            deal_factory, 
            pro_exchange_connector_sandbox
        )
        
        # 8. Остальные сервисы (без изменений)
        order_execution_service = OrderExecutionService(order_service, deal_service, pro_exchange_connector_sandbox)
        orderbook_analyzer = OrderBookAnalyzer(config.get("orderbook_analyzer", {}))
        
        # 9. Мониторы (без изменений)
        buy_order_monitor = BuyOrderMonitor(
            order_service, deal_service, order_execution_service,
            pro_exchange_connector_sandbox, cooldown_seconds=60
        )
        
        deal_completion_monitor = DealCompletionMonitor(
            deal_service, order_service, pro_exchange_connector_sandbox,
            check_interval_seconds=30
        )
        
        # 10. Проверки (без изменений)
        logger.info("Проверка подключения к sandbox...")
        await pro_exchange_connector_sandbox.test_connection()
        
        balance = await pro_exchange_connector_sandbox.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        logger.info(f"Баланс USDT: {usdt_balance}")
        
        # ════════════════════════════════════════════════════════════════════
        #                        ЗАПУСК ТОРГОВЛИ
        # ════════════════════════════════════════════════════════════════════
        
        # 11. Создание объекта валютной пары (без изменений)
        currency_pair = CurrencyPair(
            config["currency_pair"]["symbol"],
            config["currency_pair"]["base_currency"],
            config["currency_pair"]["quote_currency"],
            config["currency_pair"]["deal_quota"]
        )
        
        # 12. Запуск основного торгового цикла
        logger.info(f"🎯 Начало торговли: {currency_pair.symbol}")
        
        await run_realtime_trading(
            currency_pair=currency_pair,
            pro_exchange_connector_prod=pro_exchange_connector_prod,
            pro_exchange_connector_sandbox=pro_exchange_connector_sandbox,
            order_execution_service=order_execution_service,
            deal_service=deal_service,
            orderbook_analyzer=orderbook_analyzer,
            buy_order_monitor=buy_order_monitor,
            deal_completion_monitor=deal_completion_monitor,
            repository_factory=repository_factory  # НОВОЕ: Передаем фабрику!
        )
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        await graceful_shutdown()

async def graceful_shutdown():
    """
    Корректное завершение работы с сохранением всех данных.
    
    НОВОЕ В v3.0:
    - Принудительная синхронизация атомарных репозиториев
    - Дамп всех потоковых данных
    - Статистика репозиториев
    """
    global repository_factory
    
    logger.info("🛑 Начало graceful shutdown...")
    
    if repository_factory:
        try:
            # 1. Принудительная синхронизация всех атомарных данных
            logger.info("Синхронизация критических данных с PostgreSQL...")
            await repository_factory.force_sync_all()
            
            # 2. Дамп всех потоковых данных
            logger.info("Создание дампов потоковых данных...")
            dump_results = await repository_factory.force_dump_all()
            
            for repo_name, result in dump_results.items():
                if result.startswith("Ошибка"):
                    logger.error(f"{repo_name}: {result}")
                else:
                    logger.info(f"{repo_name}: дамп создан - {result}")
            
            # 3. Финальная статистика
            logger.info("📊 Финальная статистика репозиториев:")
            final_stats = await repository_factory.get_all_stats()
            
            for repo_name, stats in final_stats.items():
                if 'memory_records' in stats:
                    logger.info(f"  {repo_name}: {stats['memory_records']} записей, "
                              f"{stats.get('memory_usage_mb', 0):.1f} MB")
                elif 'records_saved' in stats:
                    logger.info(f"  {repo_name}: {stats['records_saved']} записей сохранено, "
                              f"{stats.get('dumps_created', 0)} дампов")
            
        except Exception as e:
            logger.error(f"Ошибка во время shutdown: {e}")
        
    logger.info("✅ Graceful shutdown завершен")

def setup_signal_handlers():
    """Настройка обработчиков сигналов для graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}")
        # asyncio.create_task не работает в signal handler, используем другой подход
        loop = asyncio.get_event_loop()
        loop.create_task(graceful_shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Настройка политики цикла событий для Windows (без изменений)
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Настройка логирования (без изменений)
    setup_logging()
    
    # НОВОЕ: Настройка обработчиков сигналов
    setup_signal_handlers()
    
    # Запуск основного цикла
    asyncio.run(main())
```

---

### **ШАГ 8: Обновление run_realtime_trading.py**

**Изменения в:** `src/application/use_cases/run_realtime_trading.py`

```python
"""
Основной торговый цикл AutoTrade v3.0 с поддержкой новой архитектуры.

ИЗМЕНЕНИЯ:
- Получение tickers_repository из RepositoryFactory
- Статистика репозиториев в логах производительности
"""

async def run_realtime_trading(
    currency_pair: CurrencyPair,
    pro_exchange_connector_prod: CcxtExchangeConnector,
    pro_exchange_connector_sandbox: CcxtExchangeConnector,
    order_execution_service: OrderExecutionService,
    deal_service: DealService,
    orderbook_analyzer: OrderBookAnalyzer,
    buy_order_monitor: BuyOrderMonitor,
    deal_completion_monitor: DealCompletionMonitor,
    repository_factory: RepositoryFactory,  # НОВОЕ!
    stop_loss_monitor: StopLossMonitor = None
):
    """
    Основной торговый цикл с двухуровневой архитектурой хранения.
    """
    
    # ════════════════════════════════════════════════════════════════════
    #                         ИНИЦИАЛИЗАЦИЯ
    # ════════════════════════════════════════════════════════════════════
    
    # ИЗМЕНЕНИЕ: Получаем репозитории из фабрики
    tickers_repo = await repository_factory.get_tickers_repository()
    indicators_repo = await repository_factory.get_indicators_repository()
    
    # Остальная инициализация без изменений
    ticker_service = TickerService(tickers_repo, indicators_repo)
    logger_perf = PerformanceLogger(log_interval_seconds=10)
    cooldown_manager = SignalCooldownManager()
    orderbook_cache = OrderBookCache(ttl_seconds=30)
    
    filled_buy_order_handler = FilledBuyOrderHandler(
        order_service=deal_service.order_service,
        deal_service=deal_service,
        order_execution_service=order_execution_service,
        exchange_connector=pro_exchange_connector_sandbox
    )
    
    # ════════════════════════════════════════════════════════════════════
    #                       ОСНОВНОЙ ТОРГОВЫЙ ЦИКЛ
    # ════════════════════════════════════════════════════════════════════
    
    tick_count = 0
    
    async for ticker_data in pro_exchange_connector_prod.watch_ticker(currency_pair.symbol):
        try:
            tick_start_time = time.time()
            
            # 1. Обработка тика (теперь использует новый репозиторий!)
            await ticker_service.process_ticker(ticker_data)
            
            # 2. Получение торгового сигнала
            ticker_signal = await ticker_service.get_signal()
            
            # 3. Основная торговая логика (без изменений)
            if ticker_signal == "BUY":
                # ... вся торговая логика остается без изменений
                pass
            
            # ════════════════════════════════════════════════════════════════
            #                    ПЕРИОДИЧЕСКИЕ ПРОВЕРКИ
            # ════════════════════════════════════════════════════════════════
            
            tick_count += 1
            
            if tick_count % 50 == 0:
                # Обработка исполненных BUY ордеров (без изменений)
                await filled_buy_order_handler.check_and_place_sell_orders()
                
                # Проверка завершения сделок (без изменений) 
                await deal_completion_monitor.check_deals_completion()
                
                # НОВОЕ: Статистика репозиториев в логах производительности
                if tick_count % 500 == 0:  # Каждые 500 тиков
                    repo_stats = await repository_factory.get_all_stats()
                    
                    # Логируем использование памяти
                    for repo_name, stats in repo_stats.items():
                        if 'memory_usage_mb' in stats:
                            logger.info(f"📊 {repo_name}: "
                                      f"{stats.get('records_in_memory', 0):,} записей, "
                                      f"{stats['memory_usage_mb']:.1f} MB, "
                                      f"{stats.get('memory_usage_percent', 0):.1f}% лимита")
                
                # Обновление кеша стакана для стоп-лосса
                orderbook_data = await pro_exchange_connector_prod.watch_order_book(currency_pair.symbol, limit=20)
                orderbook_cache.set(currency_pair.symbol, orderbook_data)
                
                # Проверка стоп-лосса
                if stop_loss_monitor:
                    current_price = ticker_data.get('last', 0)
                    cached_orderbook = orderbook_cache.get(currency_pair.symbol)
                    await stop_loss_monitor.check_open_deals(current_price, cached_orderbook)
            
            # Логирование производительности (расширенное)
            tick_process_time = (time.time() - tick_start_time) * 1000
            logger_perf.log_performance(f"tick_processing_ms", tick_process_time)
            
        except Exception as e:
            logger.error(f"Ошибка в торговом цикле: {e}", exc_info=True)
            await asyncio.sleep(1)  # Пауза при ошибке
```

---

## 🎯 Преимущества Новой Архитектуры

### **1. Производительность**
- ✅ **Скорость RAM** для всех торговых операций
- ✅ **Pandas мощь** для сложных запросов и аналитики
- ✅ **Параллельная персистентность** не блокирует торговлю

### **2. Надежность** 
- ✅ **Атомарные данные** (сделки/ордера) сразу в PostgreSQL
- ✅ **Автоматические дампы** потоковых данных
- ✅ **Graceful shutdown** с сохранением всех данных

### **3. Масштабируемость**
- ✅ **10M+ тиков** в памяти без деградации
- ✅ **Автоочистка памяти** при достижении лимитов
- ✅ **Сжатые Parquet дампы** для долгосрочного хранения

### **4. Гибкость**
- ✅ **Легкое переключение** backend'ов через конфиг
- ✅ **Fallback стратегии** при проблемах с БД
- ✅ **Полная изоляция** сервисного слоя

### **5. Аналитические возможности**
```python
# Примеры мощных запросов с новой архитектурой:

# Получаем DataFrame тиков для анализа
df = await tickers_repo.get_dataframe()

# Объемы торгов по часам
hourly_volume = df.groupby(df['timestamp'].dt.hour)['volume'].sum()

# OHLC данные по минутам
ohlc = df.set_index('timestamp').resample('1min')['last'].ohlc()

# Корреляция между тиками разных пар
correlation = df.pivot_table(values='last', index='timestamp', columns='symbol').corr()

# Статистика прибыльности сделок
deals_df = await deals_repo.get_dataframe()
profit_stats = deals_df.groupby('status')['profit'].agg(['count', 'sum', 'mean'])
```

---

## 🚀 План Внедрения

### **Этап 1: Подготовка (1-2 дня)**
1. Создание базовых абстракций и интерфейсов
2. Настройка PostgreSQL и схемы БД
3. Написание тестов для новых репозиториев

### **Этап 2: Реализация (3-5 дней)**
1. Эталонные реализации Deal и Ticker репозиториев
2. Умная фабрика репозиториев с fallback
3. Интеграция в main.py и торговый цикл

### **Этап 3: Тестирование (2-3 дня)**
1. Тестирование в sandbox режиме
2. Нагрузочное тестирование памяти и дампов
3. Проверка graceful shutdown

### **Этап 4: Постепенное внедрение (1-2 дня)**
1. Запуск с fallback на старые репозитории
2. Мониторинг производительности и памяти
3. Полное переключение на новую архитектуру

---

## 📝 Заключение

Данный план представляет **полную трансформацию** системы хранения AutoTrade с сохранением **скорости торговли** и добавлением **надежности персистентности**.

**Ключевые особенности:**
- 🚀 **Скорость торговли не снижается** - все операции с DataFrame в памяти
- 🛡️ **Надежность критических данных** - атомарная запись в PostgreSQL  
- 📊 **Мощная аналитика** - прямой доступ к pandas DataFrame
- 🔧 **Простота внедрения** - полная обратная совместимость
- 🎯 **Производственная готовность** - fallback стратегии и мониторинг

Данная архитектура превращает AutoTrade в **профессиональную торговую систему** промышленного уровня с сохранением всех преимуществ текущей высокопроизводительной реализации.