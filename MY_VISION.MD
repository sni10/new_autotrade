Основываясь на анализе структур данных и существующего кода, создаю подробный план миграции с указанием всех файлов, методов и изменений:

# 📋 AutoTrade v3.0: Полный План Миграции на Двухуровневую Архитектуру

## 🎯 Обзор Миграции

### Концепция новой архитектуры:
- **Уровень 1 (RAM)**: Все операции с Pandas DataFrame в памяти
- **Уровень 2 (Диск)**: PostgreSQL для атомарных данных + Parquet для потоковых
- **Конвертация**: Методы `to_dataframe()` и `from_dataframe()` для всех Entity

---

## 🔧 ШАГ 1: Создание Базовых Абстракций

### 📁 `src/domain/repositories/base_repository.py` - НОВЫЙ ФАЙЛ

```python
"""
Базовые интерфейсы для двухуровневой архитектуры хранения.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
import pandas as pd
from datetime import datetime

T_Entity = TypeVar('T_Entity')
T_EntityID = TypeVar('T_EntityID')

class IMemoryFirstRepository(Generic[T_Entity, T_EntityID], ABC):
    """Базовый интерфейс для всех репозиториев с приоритетом памяти."""
    
    @abstractmethod
    async def save(self, entity: T_Entity) -> T_Entity:
        """Сохраняет сущность в DataFrame (мгновенно)."""
        pass
    
    @abstractmethod
    async def find_by_id(self, entity_id: T_EntityID) -> Optional[T_Entity]:
        """Поиск по ID в DataFrame."""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[T_Entity]:
        """Возвращает все записи из DataFrame."""
        pass
    
    @abstractmethod
    async def get_dataframe(self) -> pd.DataFrame:
        """Прямой доступ к DataFrame для аналитики."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: T_EntityID) -> bool:
        """Удаление из DataFrame + персистентного слоя."""
        pass

class IAtomicRepository(IMemoryFirstRepository[T_Entity, T_EntityID]):
    """Интерфейс для атомарных сущностей (Deal, Order)."""
    
    @abstractmethod
    async def sync_to_persistent(self) -> None:
        """Принудительная синхронизация с PostgreSQL."""
        pass

class IStreamRepository(IMemoryFirstRepository[T_Entity, T_EntityID]):
    """Интерфейс для потоковых данных (Ticker, OrderBook)."""
    
    @abstractmethod
    async def append_batch(self, entities: List[T_Entity]) -> None:
        """Эффективное добавление пачки записей."""
        pass
    
    @abstractmethod
    async def dump_to_parquet(self, filepath: str) -> int:
        """Сброс накопленных данных в Parquet файл."""
        pass
    
    @abstractmethod
    async def load_from_parquet(self, filepath: str) -> int:
        """Загрузка данных из Parquet файла."""
        pass
```


---

## 🏗️ ШАГ 2: Создание Data Transfer Objects

### 📁 `src/domain/dto/dataframe_convertible.py` - НОВЫЙ ФАЙЛ

```python
"""
Интерфейс для конвертации сущностей в DataFrame и обратно.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd

class IDataFrameConvertible(ABC):
    """Интерфейс для сущностей, которые могут конвертироваться в DataFrame."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация сущности в словарь для DataFrame."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IDataFrameConvertible':
        """Создание сущности из словаря DataFrame row."""
        pass
    
    @classmethod
    def list_to_dataframe(cls, entities: List['IDataFrameConvertible']) -> pd.DataFrame:
        """Конвертация списка сущностей в DataFrame."""
        if not entities:
            return pd.DataFrame()
        
        data = [entity.to_dict() for entity in entities]
        df = pd.DataFrame(data)
        
        # Установка индекса по ID для быстрого поиска
        if 'id' in df.columns:
            df.set_index('id', inplace=True)
        elif 'deal_id' in df.columns:
            df.set_index('deal_id', inplace=True)
        elif 'order_id' in df.columns:
            df.set_index('order_id', inplace=True)
            
        return df
    
    @classmethod
    def dataframe_to_list(cls, df: pd.DataFrame) -> List['IDataFrameConvertible']:
        """Конвертация DataFrame в список сущностей."""
        entities = []
        for _, row in df.iterrows():
            # Добавляем индекс обратно в данные
            row_dict = row.to_dict()
            if df.index.name and df.index.name not in row_dict:
                row_dict[df.index.name] = row.name
            entities.append(cls.from_dict(row_dict))
        return entities
```


---

## 📦 ШАГ 3: Обновление Существующих Entity

### 📁 `src/domain/entities/deal.py` - ИЗМЕНЕНИЕ

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from domain.dto.dataframe_convertible import IDataFrameConvertible

@dataclass
class Deal(IDataFrameConvertible):
    """Сущность сделки с поддержкой DataFrame конвертации."""
    
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CANCELLED = "CANCELLED"
    
    deal_id: int
    currency_pair: str  # Изменено с объекта на строку для упрощения
    status: str = STATUS_OPEN
    buy_order_id: Optional[int] = None
    sell_order_id: Optional[int] = None
    created_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для DataFrame."""
        return {
            'deal_id': self.deal_id,
            'currency_pair': self.currency_pair,
            'status': self.status,
            'buy_order_id': self.buy_order_id,
            'sell_order_id': self.sell_order_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Deal':
        """Создание из словаря DataFrame row."""
        return cls(
            deal_id=int(data['deal_id']),
            currency_pair=data['currency_pair'],
            status=data.get('status', cls.STATUS_OPEN),
            buy_order_id=int(data['buy_order_id']) if data.get('buy_order_id') else None,
            sell_order_id=int(data['sell_order_id']) if data.get('sell_order_id') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            closed_at=datetime.fromisoformat(data['closed_at']) if data.get('closed_at') else None,
        )
```


### 📁 `src/domain/entities/order.py` - ИЗМЕНЕНИЕ

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from domain.dto.dataframe_convertible import IDataFrameConvertible

@dataclass
class Order(IDataFrameConvertible):
    """Сущность ордера с поддержкой DataFrame конвертации."""
    
    STATUS_PENDING = "PENDING"
    STATUS_PLACED = "PLACED"
    STATUS_FILLED = "FILLED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_FAILED = "FAILED"
    
    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"
    
    order_id: int
    deal_id: int
    symbol: str
    side: str
    order_type: str
    amount: float
    price: float
    status: str = STATUS_PENDING
    exchange_id: Optional[str] = None
    filled_amount: float = 0.0
    average_price: float = 0.0
    fee: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для DataFrame."""
        return {
            'order_id': self.order_id,
            'deal_id': self.deal_id,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type,
            'amount': self.amount,
            'price': self.price,
            'status': self.status,
            'exchange_id': self.exchange_id,
            'filled_amount': self.filled_amount,
            'average_price': self.average_price,
            'fee': self.fee,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'error_message': self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Создание из словаря DataFrame row."""
        return cls(
            order_id=int(data['order_id']),
            deal_id=int(data['deal_id']),
            symbol=data['symbol'],
            side=data['side'],
            order_type=data['order_type'],
            amount=float(data['amount']),
            price=float(data['price']),
            status=data.get('status', cls.STATUS_PENDING),
            exchange_id=data.get('exchange_id'),
            filled_amount=float(data.get('filled_amount', 0.0)),
            average_price=float(data.get('average_price', 0.0)),
            fee=float(data.get('fee', 0.0)),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            error_message=data.get('error_message'),
        )
```


### 📁 `src/domain/entities/ticker.py` - ИЗМЕНЕНИЕ

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from domain.dto.dataframe_convertible import IDataFrameConvertible

@dataclass
class Ticker(IDataFrameConvertible):
    """Сущность тикера с поддержкой DataFrame конвертации."""
    
    symbol: str
    timestamp: int
    datetime: str
    high: float
    low: float
    bid: float
    ask: float
    last: float
    close: float
    base_volume: float
    quote_volume: float
    signals: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для DataFrame."""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'datetime': self.datetime,
            'high': self.high,
            'low': self.low,
            'bid': self.bid,
            'ask': self.ask,
            'last': self.last,
            'close': self.close,
            'base_volume': self.base_volume,
            'quote_volume': self.quote_volume,
            'signals': str(self.signals) if self.signals else None,  # JSON string
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ticker':
        """Создание из словаря DataFrame row."""
        signals = None
        if data.get('signals'):
            import json
            try:
                signals = json.loads(data['signals'].replace("'", '"'))
            except:
                signals = None
                
        return cls(
            symbol=data['symbol'],
            timestamp=int(data['timestamp']),
            datetime=data['datetime'],
            high=float(data['high']),
            low=float(data['low']),
            bid=float(data['bid']),
            ask=float(data['ask']),
            last=float(data['last']),
            close=float(data['close']),
            base_volume=float(data['base_volume']),
            quote_volume=float(data['quote_volume']),
            signals=signals,
        )
    
    # Существующие методы остаются без изменений
    def update_signals(self, indicators: Dict[str, float]):
        """Обновляет сигналы индикаторов."""
        self.signals = indicators.copy() if indicators else {}
    
    def get_macd_signal(self) -> float:
        return self.signals.get('macd', 0.0) if self.signals else 0.0
    
    def get_macd_signal_line(self) -> float:
        return self.signals.get('signal', 0.0) if self.signals else 0.0
    
    def get_macd_histogram(self) -> float:
        return self.signals.get('histogram', 0.0) if self.signals else 0.0
    
    def get_sma_7(self) -> float:
        return self.signals.get('sma_7', 0.0) if self.signals else 0.0
    
    def get_sma_25(self) -> float:
        return self.signals.get('sma_25', 0.0) if self.signals else 0.0
```


### 📁 `src/domain/entities/indicator_data.py` - ИЗМЕНЕНИЕ

```python
from dataclasses import dataclass
from typing import Dict, Any
from domain.dto.dataframe_convertible import IDataFrameConvertible

@dataclass
class IndicatorData(IDataFrameConvertible):
    """Сущность данных индикаторов с поддержкой DataFrame конвертации."""
    
    symbol: str
    timestamp: int
    values: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для DataFrame."""
        result = {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
        }
        # Разворачиваем значения индикаторов в отдельные колонки
        result.update(self.values)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndicatorData':
        """Создание из словаря DataFrame row."""
        # Извлекаем основные поля
        symbol = data.pop('symbol')
        timestamp = int(data.pop('timestamp'))
        
        # Все остальные поля - это значения индикаторов
        values = {k: float(v) for k, v in data.items() if v is not None}
        
        return cls(
            symbol=symbol,
            timestamp=timestamp,
            values=values
        )

    @classmethod
    def from_dict_original(cls, data: Dict[str, Any]) -> 'IndicatorData':
        """Оригинальный метод для обратной совместимости."""
        return cls(
            symbol=data.get("symbol"),
            timestamp=data.get("timestamp"),
            values=data.get("values", {}),
        )

    def __repr__(self):
        return (f"<IndicatorData(symbol={self.symbol}, timestamp={self.timestamp}, "
                f"values_count={len(self.values)})>")
```


---

## 🏭 ШАГ 4: Создание Новых Репозиториев

### 📁 `src/infrastructure/repositories/deals_repository_v2.py` - НОВЫЙ ФАЙЛ

```python
"""
Новый репозиторий сделок с двухуровневой архитектурой.
"""

import pandas as pd
from typing import List, Optional
import asyncio
from datetime import datetime

from domain.entities.deal import Deal
from domain.repositories.base_repository import IAtomicRepository
from infrastructure.database.postgresql_connection import PostgreSQLConnection

class DealsRepositoryV2(IAtomicRepository[Deal, int]):
    """Репозиторий сделок с приоритетом памяти и персистентностью PostgreSQL."""
    
    def __init__(self, db_connection: PostgreSQLConnection):
        self.db_connection = db_connection
        self._dataframe: pd.DataFrame = pd.DataFrame()
        self._next_id = 1
        self._sync_lock = asyncio.Lock()
        
        # Инициализация при старте
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация репозитория - загрузка данных из БД."""
        await self._load_from_database()
    
    async def _load_from_database(self):
        """Загружает все сделки из PostgreSQL в DataFrame."""
        query = """
        SELECT deal_id, currency_pair, status, buy_order_id, sell_order_id, 
               created_at, closed_at 
        FROM deals 
        ORDER BY deal_id
        """
        
        rows = await self.db_connection.fetch_all(query)
        if rows:
            data = []
            for row in rows:
                data.append({
                    'deal_id': row['deal_id'],
                    'currency_pair': row['currency_pair'],
                    'status': row['status'],
                    'buy_order_id': row['buy_order_id'],
                    'sell_order_id': row['sell_order_id'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'closed_at': row['closed_at'].isoformat() if row['closed_at'] else None,
                })
                self._next_id = max(self._next_id, row['deal_id'] + 1)
            
            self._dataframe = pd.DataFrame(data)
            self._dataframe.set_index('deal_id', inplace=True)
    
    async def save(self, entity: Deal) -> Deal:
        """Сохраняет сделку в DataFrame и PostgreSQL."""
        # Присваиваем ID если его нет
        if entity.deal_id is None or entity.deal_id == 0:
            entity.deal_id = self._next_id
            self._next_id += 1
        
        # Обновляем временные метки
        if entity.created_at is None:
            entity.created_at = datetime.now()
        
        # Сохраняем в DataFrame (мгновенно)
        row_data = entity.to_dict()
        if entity.deal_id in self._dataframe.index:
            # Обновление существующей записи
            for col, value in row_data.items():
                if col != 'deal_id':
                    self._dataframe.loc[entity.deal_id, col] = value
        else:
            # Новая запись
            new_row = pd.DataFrame([row_data])
            new_row.set_index('deal_id', inplace=True)
            self._dataframe = pd.concat([self._dataframe, new_row])
        
        # Асинхронно сохраняем в PostgreSQL
        asyncio.create_task(self._save_to_database(entity))
        
        return entity
    
    async def _save_to_database(self, entity: Deal):
        """Сохраняет сделку в PostgreSQL."""
        async with self._sync_lock:
            query = """
            INSERT INTO deals (deal_id, currency_pair, status, buy_order_id, sell_order_id, created_at, closed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (deal_id) DO UPDATE SET
                status = EXCLUDED.status,
                buy_order_id = EXCLUDED.buy_order_id,
                sell_order_id = EXCLUDED.sell_order_id,
                closed_at = EXCLUDED.closed_at
            """
            
            await self.db_connection.execute(
                query,
                entity.deal_id,
                entity.currency_pair,
                entity.status,
                entity.buy_order_id,
                entity.sell_order_id,
                entity.created_at,
                entity.closed_at
            )
    
    async def find_by_id(self, deal_id: int) -> Optional[Deal]:
        """Поиск сделки по ID в DataFrame."""
        if deal_id in self._dataframe.index:
            row = self._dataframe.loc[deal_id]
            row_dict = row.to_dict()
            row_dict['deal_id'] = deal_id
            return Deal.from_dict(row_dict)
        return None
    
    async def get_all(self) -> List[Deal]:
        """Возвращает все сделки из DataFrame."""
        return Deal.dataframe_to_list(self._dataframe)
    
    async def get_dataframe(self) -> pd.DataFrame:
        """Прямой доступ к DataFrame."""
        return self._dataframe.copy()
    
    async def delete(self, deal_id: int) -> bool:
        """Удаление сделки из DataFrame и PostgreSQL."""
        if deal_id not in self._dataframe.index:
            return False
        
        # Удаляем из DataFrame
        self._dataframe.drop(deal_id, inplace=True)
        
        # Асинхронно удаляем из PostgreSQL
        asyncio.create_task(self._delete_from_database(deal_id))
        
        return True
    
    async def _delete_from_database(self, deal_id: int):
        """Удаляет сделку из PostgreSQL."""
        async with self._sync_lock:
            query = "DELETE FROM deals WHERE deal_id = $1"
            await self.db_connection.execute(query, deal_id)
    
    async def sync_to_persistent(self) -> None:
        """Принудительная синхронизация с PostgreSQL."""
        async with self._sync_lock:
            # Здесь можно добавить логику полной синхронизации если нужно
            pass
    
    # Дополнительные методы для бизнес-логики
    async def get_open_deals(self) -> List[Deal]:
        """Получить все открытые сделки."""
        open_df = self._dataframe[self._dataframe['status'] == Deal.STATUS_OPEN]
        return Deal.dataframe_to_list(open_df)
    
    async def get_deals_by_currency_pair(self, currency_pair: str) -> List[Deal]:
        """Получить сделки по валютной паре."""
        filtered_df = self._dataframe[self._dataframe['currency_pair'] == currency_pair]
        return Deal.dataframe_to_list(filtered_df)
```


### 📁 `src/infrastructure/repositories/orders_repository_v2.py` - НОВЫЙ ФАЙЛ

```python
"""
Новый репозиторий ордеров с двухуровневой архитектурой.
"""

import pandas as pd
from typing import List, Optional
import asyncio
from datetime import datetime

from domain.entities.order import Order
from domain.repositories.base_repository import IAtomicRepository
from infrastructure.database.postgresql_connection import PostgreSQLConnection

class OrdersRepositoryV2(IAtomicRepository[Order, int]):
    """Репозиторий ордеров с приоритетом памяти и персистентностью PostgreSQL."""
    
    def __init__(self, db_connection: PostgreSQLConnection):
        self.db_connection = db_connection
        self._dataframe: pd.DataFrame = pd.DataFrame()
        self._next_id = 1
        self._sync_lock = asyncio.Lock()
        
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация репозитория."""
        await self._load_from_database()
    
    async def _load_from_database(self):
        """Загружает все ордера из PostgreSQL в DataFrame."""
        query = """
        SELECT order_id, deal_id, symbol, side, order_type, amount, price, status,
               exchange_id, filled_amount, average_price, fee, created_at, updated_at, error_message
        FROM orders 
        ORDER BY order_id
        """
        
        rows = await self.db_connection.fetch_all(query)
        if rows:
            data = []
            for row in rows:
                data.append({
                    'order_id': row['order_id'],
                    'deal_id': row['deal_id'],
                    'symbol': row['symbol'],
                    'side': row['side'],
                    'order_type': row['order_type'],
                    'amount': float(row['amount']),
                    'price': float(row['price']),
                    'status': row['status'],
                    'exchange_id': row['exchange_id'],
                    'filled_amount': float(row['filled_amount'] or 0),
                    'average_price': float(row['average_price'] or 0),
                    'fee': float(row['fee'] or 0),
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                    'error_message': row['error_message'],
                })
                self._next_id = max(self._next_id, row['order_id'] + 1)
            
            self._dataframe = pd.DataFrame(data)
            self._dataframe.set_index('order_id', inplace=True)
    
    async def save(self, entity: Order) -> Order:
        """Сохраняет ордер в DataFrame и PostgreSQL."""
        if entity.order_id is None or entity.order_id == 0:
            entity.order_id = self._next_id
            self._next_id += 1
        
        if entity.created_at is None:
            entity.created_at = datetime.now()
        entity.updated_at = datetime.now()
        
        # Сохраняем в DataFrame
        row_data = entity.to_dict()
        if entity.order_id in self._dataframe.index:
            for col, value in row_data.items():
                if col != 'order_id':
                    self._dataframe.loc[entity.order_id, col] = value
        else:
            new_row = pd.DataFrame([row_data])
            new_row.set_index('order_id', inplace=True)
            self._dataframe = pd.concat([self._dataframe, new_row])
        
        # Асинхронно сохраняем в PostgreSQL
        asyncio.create_task(self._save_to_database(entity))
        
        return entity
    
    async def _save_to_database(self, entity: Order):
        """Сохраняет ордер в PostgreSQL."""
        async with self._sync_lock:
            query = """
            INSERT INTO orders (order_id, deal_id, symbol, side, order_type, amount, price, status,
                              exchange_id, filled_amount, average_price, fee, created_at, updated_at, error_message)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (order_id) DO UPDATE SET
                status = EXCLUDED.status,
                exchange_id = EXCLUDED.exchange_id,
                filled_amount = EXCLUDED.filled_amount,
                average_price = EXCLUDED.average_price,
                fee = EXCLUDED.fee,
                updated_at = EXCLUDED.updated_at,
                error_message = EXCLUDED.error_message
            """
            
            await self.db_connection.execute(
                query,
                entity.order_id, entity.deal_id, entity.symbol, entity.side, entity.order_type,
                entity.amount, entity.price, entity.status, entity.exchange_id,
                entity.filled_amount, entity.average_price, entity.fee,
                entity.created_at, entity.updated_at, entity.error_message
            )
    
    async def find_by_id(self, order_id: int) -> Optional[Order]:
        """Поиск ордера по ID в DataFrame."""
        if order_id in self._dataframe.index:
            row = self._dataframe.loc[order_id]
            row_dict = row.to_dict()
            row_dict['order_id'] = order_id
            return Order.from_dict(row_dict)
        return None
    
    async def get_all(self) -> List[Order]:
        """Возвращает все ордера из DataFrame."""
        return Order.dataframe_to_list(self._dataframe)
    
    async def get_dataframe(self) -> pd.DataFrame:
        """Прямой доступ к DataFrame."""
        return self._dataframe.copy()
    
    async def delete(self, order_id: int) -> bool:
        """Удаление ордера."""
        if order_id not in self._dataframe.index:
            return False
        
        self._dataframe.drop(order_id, inplace=True)
        asyncio.create_task(self._delete_from_database(order_id))
        return True
    
    async def _delete_from_database(self, order_id: int):
        """Удаляет ордер из PostgreSQL."""
        async with self._sync_lock:
            query = "DELETE FROM orders WHERE order_id = $1"
            await self.db_connection.execute(query, order_id)
    
    async def sync_to_persistent(self) -> None:
        """Принудительная синхронизация с PostgreSQL."""
        async with self._sync_lock:
            pass
    
    # Бизнес-методы
    async def get_open_orders(self) -> List[Order]:
        """Получить открытые ордера."""
        open_statuses = [Order.STATUS_PENDING, Order.STATUS_PLACED]
        open_df = self._dataframe[self._dataframe['status'].isin(open_statuses)]
        return Order.dataframe_to_list(open_df)
    
    async def get_orders_by_deal(self, deal_id: int) -> List[Order]:
        """Получить ордера по сделке."""
        filtered_df = self._dataframe[self._dataframe['deal_id'] == deal_id]
        return Order.dataframe_to_list(filtered_df)
    
    async def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """Получить ордера по символу."""
        filtered_df = self._dataframe[self._dataframe['symbol'] == symbol]
        return Order.dataframe_to_list(filtered_df)
```


### 📁 `src/infrastructure/repositories/tickers_repository_v2.py` - НОВЫЙ ФАЙЛ

```python
"""
Новый репозиторий тикеров с потоковой архитектурой и Parquet дампами.
"""

import pandas as pd
from typing import List, Optional
import asyncio
import os
from datetime import datetime, date
import json

from domain.entities.ticker import Ticker
from domain.repositories.base_repository import IStreamRepository

class TickersRepositoryV2(IStreamRepository[Ticker, int]):
    """Репозиторий тикеров с накоплением в памяти и дампами в Parquet."""
    
    def __init__(self, dumps_directory: str = "dumps", max_memory_records: int = 10000):
        self.dumps_directory = dumps_directory
        self.max_memory_records = max_memory_records
        self._dataframe: pd.DataFrame = pd.DataFrame()
        self._next_id = 1
        self._dump_lock = asyncio.Lock()
        
        # Создаем директорию для дампов
        os.makedirs(dumps_directory, exist_ok=True)
        
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация - загружаем последние данные из дампов."""
        await self._load_latest_dumps()
    
    async def _load_latest_dumps(self):
        """Загружает последние дампы при старте."""
        today = date.today()
        yesterday = date.fromordinal(today.toordinal() - 1)
        
        # Пробуем загрузить данные за сегодня и вчера
        for target_date in [today, yesterday]:
            parquet_file = os.path.join(
                self.dumps_directory, 
                f"tickers_{target_date.strftime('%Y%m%d')}.parquet"
            )
            if os.path.exists(parquet_file):
                await self.load_from_parquet(parquet_file)
                break
    
    async def save(self, entity: Ticker) -> Ticker:
        """Сохраняет тикер в DataFrame в памяти."""
        if not hasattr(entity, 'id'):
            entity.id = self._next_id
            self._next_id += 1
        
        # Добавляем в DataFrame
        row_data = entity.to_dict()
        row_data['id'] = entity.id
        
        new_row = pd.DataFrame([row_data])
        new_row.set_index('id', inplace=True)
        self._dataframe = pd.concat([self._dataframe, new_row])
        
        # Проверяем лимит записей в памяти
        if len(self._dataframe) >= self.max_memory_records:
            asyncio.create_task(self._auto_dump())
        
        return entity
    
    async def append_batch(self, entities: List[Ticker]) -> None:
        """Эффективное добавление пачки тикеров."""
        if not entities:
            return
        
        data = []
        for entity in entities:
            if not hasattr(entity, 'id'):
                entity.id = self._next_id
                self._next_id += 1
            
            row_data = entity.to_dict()
            row_data['id'] = entity.id
            data.append(row_data)
        
        batch_df = pd.DataFrame(data)
        batch_df.set_index('id', inplace=True)
        self._dataframe = pd.concat([self._dataframe, batch_df])
        
        if len(self._dataframe) >= self.max_memory_records:
            asyncio.create_task(self._auto_dump())
    
    async def _auto_dump(self):
        """Автоматический дамп при превышении лимита."""
        today = date.today()
        dump_file = os.path.join(
            self.dumps_directory,
            f"tickers_{today.strftime('%Y%m%d')}.parquet"
        )
        
        await self.dump_to_parquet(dump_file)
        
        # Очищаем половину старых записей из памяти
        records_to_keep = self.max_memory_records // 2
        self._dataframe = self._dataframe.tail(records_to_keep)
    
    async def dump_to_parquet(self, filepath: str) -> int:
        """Сбрасывает данные в Parquet файл."""
        async with self._dump_lock:
            if self._dataframe.empty:
                return 0
            
            # Подготавливаем данные для записи
            df_to_save = self._dataframe.copy()
            
            # Если файл уже существует, объединяем данные
            if os.path.exists(filepath):
                existing_df = pd.read_parquet(filepath)
                df_to_save = pd.concat([existing_df, df_to_save])
                df_to_save = df_to_save.drop_duplicates(subset=['timestamp', 'symbol'], keep='last')
            
            # Сохраняем в Parquet
            df_to_save.to_parquet(filepath, compression='snappy')
            
            return len(df_to_save)
    
    async def load_from_parquet(self, filepath: str) -> int:
        """Загружает данные из Parquet файла."""
        if not os.path.exists(filepath):
            return 0
        
        loaded_df = pd.read_parquet(filepath)
        
        if not loaded_df.empty:
            # Объединяем с существующими данными
            if not self._dataframe.empty:
                self._dataframe = pd.concat([self._dataframe, loaded_df])
                self._dataframe = self._dataframe.drop_duplicates(subset=['timestamp', 'symbol'], keep='last')
            else:
                self._dataframe = loaded_df
            
            # Обновляем счетчик ID
            if 'id' in self._dataframe.columns or self._dataframe.index.name == 'id':
                max_id = self._dataframe.index.max() if self._dataframe.index.name == 'id' else self._dataframe['id'].max()
                self._next_id = max(self._next_id, max_id + 1)
        
        return len(loaded_df)
    
    async def find_by_id(self, ticker_id: int) -> Optional[Ticker]:
        """Поиск тикера по ID."""
        if ticker_id in self._dataframe.index:
            row = self._dataframe.loc[ticker_id]
            row_dict = row.to_dict()
            row_dict['id'] = ticker_id
            return Ticker.from_dict(row_dict)
        return None
    
    async def get_all(self) -> List[Ticker]:
        """Возвращает все тикеры из памяти."""
        return Ticker.dataframe_to_list(self._dataframe)
    
    async def get_dataframe(self) -> pd.DataFrame:
        """Прямой доступ к DataFrame."""
        return self._dataframe.copy()
    
    async def delete(self, ticker_id: int) -> bool:
        """Удаление тикера (для потоковых данных редко используется)."""
        if ticker_id not in self._dataframe.index:
            return False
        
        self._dataframe.drop(ticker_id, inplace=True)
        return True
    
    async def get_last_n(self, n: int) -> List[Ticker]:
        """Получить последние N тикеров."""
        last_df = self._dataframe.tail(n)
        return Ticker.dataframe_to_list(last_df)
    
    async def get_by_symbol(self, symbol: str, limit: int = 1000) -> List[Ticker]:
        """Получить тикеры по символу."""
        symbol_df = self._dataframe[self._dataframe['symbol'] == symbol].tail(limit)
        return Ticker.dataframe_to_list(symbol_df)
    
    async def get_price_history(self, symbol: str, limit: int = 200) -> List[float]:
        """Получить историю цен для индикаторов."""
        symbol_df = self._dataframe[self._dataframe['symbol'] == symbol].tail(limit)
        return symbol_df['last'].tolist()
    
    # Совместимость со старым интерфейсом
    @property
    def tickers(self) -> List[Ticker]:
        """Свойство для обратной совместимости."""
        return asyncio.run(self.get_all()) if not self._dataframe.empty else []
```


---

## 🔧 ШАГ 5: Обновление Сервисов

### 📁 `src/domain/services/market_data/ticker_service.py` - ИЗМЕНЕНИЕ

```python
# src/domain/services/market_data/ticker_service.py
import time
from decimal import Decimal
from typing import Dict, List, Optional

from domain.entities.currency_pair import CurrencyPair
from domain.entities.ticker import Ticker
from domain.entities.indicator_data import IndicatorData
from domain.services.indicators.indicator_calculator_service import IndicatorCalculatorService
from domain.services.utils.decimal_rounding_service import DecimalRoundingService

# ИЗМЕНЕНИЕ: Новые репозитории
from infrastructure.repositories.tickers_repository_v2 import TickersRepositoryV2
from infrastructure.repositories.indicators_repository_v2 import IndicatorsRepositoryV2

class TickerService:
    def __init__(self, 
                 tickers_repo: TickersRepositoryV2,  # ИЗМЕНЕНО
                 indicators_repo: IndicatorsRepositoryV2):  # ИЗМЕНЕНО
        self.tickers_repo = tickers_repo
        self.indicators_repo = indicators_repo
        self.indicator_calculator = IndicatorCalculatorService()
        
        # Кеш цен для индикаторов
        self.price_history_cache: List[float] = []
        self.tick_count: int = 0
        self.last_medium_update_tick: int = 0
        self.last_heavy_update_tick: int = 0
        
        # ИЗМЕНЕНИЕ: Инициализация кеша из DataFrame
        self._initialize_cache()

    def _initialize_cache(self):
        """Инициализация кеша цен из DataFrame."""
        # Получаем последние 200 тикеров для истории цен
        import asyncio
        try:
            last_tickers = asyncio.run(self.tickers_repo.get_last_n(200))
            if last_tickers:
                self.price_history_cache = [t.last for t in last_tickers]
                self.tick_count = len(self.price_history_cache)
        except:
            self.price_history_cache = []
            self.tick_count = 0

    def _should_update_medium(self) -> bool:
        return self.tick_count - self.last_medium_update_tick >= 10

    def _should_update_heavy(self) -> bool:
        return self.tick_count - self.last_heavy_update_tick >= 50

    async def process_ticker(self, ticker: Ticker):
        """
        ИЗМЕНЕНИЕ: Обрабатывает тикер с использованием новых репозиториев.
        """
        # Обновляем кеш цен
        self.price_history_cache.append(ticker.last)
        if len(self.price_history_cache) > 200:
            self.price_history_cache.pop(0)
        
        self.tick_count += 1

        # Вычисляем индикаторы
        all_indicators = {}
        
        fast_indicators = self.indicator_calculator.calculate_fast_indicators(self.price_history_cache)
        all_indicators.update(fast_indicators.values)
        
        if self._should_update_medium():
            medium_indicators = self.indicator_calculator.calculate_medium_indicators(self.price_history_cache)
            all_indicators.update(medium_indicators.values)
            self.last_medium_update_tick = self.tick_count

        if self._should_update_heavy():
            heavy_indicators = self.indicator_calculator.calculate_heavy_indicators(self.price_history_cache)
            all_indicators.update(heavy_indicators.values)
            self.last_heavy_update_tick = self.tick_count

        # Сохраняем индикаторы
        if all_indicators:
            indicator_data = IndicatorData(
                symbol=ticker.symbol,
                timestamp=ticker.timestamp,
                values=all_indicators
            )
            await self.indicators_repo.save(indicator_data)  # ИЗМЕНЕНО: async

        # Обновляем сигналы тикера и сохраняем
        ticker.update_signals(all_indicators)
        await self.tickers_repo.save(ticker)  # ИЗМЕНЕНО: async

    async def get_signal(self) -> str:
        """ИЗМЕНЕНИЕ: Используем DataFrame для получения сигнала."""
        last_tickers = await self.tickers_repo.get_last_n(50)
        
        if len(last_tickers) < 50:
            return "HOLD"
            
        last_ticker = last_tickers[-1]
        if not last_ticker.signals:
            return "HOLD"

        macd = last_ticker.get_macd_signal()
        signal = last_ticker.get_macd_signal_line()
        hist = last_ticker.get_macd_histogram()
        sma_7 = last_ticker.get_sma_7()
        sma_25 = last_ticker.get_sma_25()

        if macd > signal and hist > 0 and sma_7 > sma_25:
            return "BUY"
        else:
            return "HOLD"

    # НОВЫЙ МЕТОД: Аналитика через DataFrame
    async def get_analytics_dataframe(self) -> Dict[str, any]:
        """Получить аналитику через прямой доступ к DataFrame."""
        df = await self.tickers_repo.get_dataframe()
        
        if df.empty:
            return {"error": "No data available"}
        
        return {
            "total_ticks": len(df),
            "symbols": df['symbol'].unique().tolist(),
            "price_stats": {
                "min": df['last'].min(),
                "max": df['last'].max(),
                "mean": df['last'].mean(),
                "std": df['last'].std()
            },
            "volume_stats": {
                "total_base_volume": df['base_volume'].sum(),
                "total_quote_volume": df['quote_volume'].sum(),
                "avg_base_volume": df['base_volume'].mean()
            },
            "time_range": {
                "from": df['timestamp'].min(),
                "to": df['timestamp'].max(),
                "duration_hours": (df['timestamp'].max() - df['timestamp'].min()) / 3600000
            }
        }

    # Остальные методы остаются без изменений
    def calculate_strategy(self, buy_price: float, budget: float, currency_pair: CurrencyPair, profit_percent: float):
        """Расчет стратегии остается без изменений."""
        price_step = Decimal(str(currency_pair.precision.get('price', '0.000001')))
        amount_step = Decimal(str(currency_pair.precision.get('amount', '0.0001')))
        price_precision = int(price_step.normalize().as_tuple().exponent * -1)
        amount_precision = int(amount_step.normalize().as_tuple().exponent * -1)
        min_notional = Decimal(str(currency_pair.limits.get('cost', {}).get('min', 10.0)))
        buy_price_dec = Decimal(str(buy_price))
        budget_dec = Decimal(str(budget))
        buy_fee_rate = Decimal(str(currency_pair.taker_fee))
        sell_fee_rate = Decimal(str(currency_pair.taker_fee))
        profit_dec = Decimal(str(profit_percent))

        if budget_dec < min_notional:
            return {"comment": f"❌ Бюджет ({budget_dec}) меньше минимально допустимого ({min_notional})"}

        coins_to_buy_raw = budget_dec / buy_price_dec
        coins_to_buy = DecimalRoundingService.ceil_to_precision(coins_to_buy_raw, amount_precision)
        coins_after_buy_fee = coins_to_buy * (1 - buy_fee_rate)
        sell_price_raw = buy_price_dec * (1 + profit_dec) / (1 - sell_fee_rate)
        sell_price = DecimalRoundingService.round_to_precision(sell_price_raw, price_precision)
        coins_to_sell = DecimalRoundingService.floor_to_precision(coins_after_buy_fee, amount_precision)
        total_cost = coins_to_buy * buy_price_dec

        if total_cost < min_notional:
             return {"comment": f"❌ Итоговая сумма ордера ({total_cost:.2f}) меньше минимально допустимой ({min_notional})"}

        final_revenue = coins_to_sell * sell_price
        net_profit = final_revenue - total_cost

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

    async def get_last_price(self) -> Optional[float]:
        """ИЗМЕНЕНИЕ: Используем новый репозиторий."""
        last_tickers = await self.tickers_repo.get_last_n(1)
        return last_tickers[0].last if last_tickers else None
```


### 📁 `src/domain/services/orders/order_service.py` - ИЗМЕНЕНИЕ

```python
# src/domain/services/orders/order_service.py
import logging
from typing import Optional, List
from domain.entities.order import Order, OrderExecutionResult
from domain.factories.order_factory import OrderFactory

# ИЗМЕНЕНИЕ: Новый репозиторий
from infrastructure.repositories.orders_repository_v2 import OrdersRepositoryV2
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
import ccxt

logger = logging.getLogger(__name__)

class OrderService:
    def __init__(self, 
                 orders_repo: OrdersRepositoryV2,  # ИЗМЕНЕНО
                 order_factory: OrderFactory, 
                 exchange_connector: CcxtExchangeConnector):
        self.orders_repo = orders_repo
        self.order_factory = order_factory
        self.exchange_connector = exchange_connector

    async def create_and_place_buy_order(self, symbol: str, amount: float, price: float, deal_id: int, order_type: str = "LIMIT") -> OrderExecutionResult:
        order = self.order_factory.create_buy_order(symbol, amount, price, deal_id, order_type)
        return await self._execute_order_on_exchange(order)

    async def create_local_sell_order(self, symbol: str, amount: float, price: float, deal_id: int, order_type: str = "LIMIT") -> OrderExecutionResult:
        order = self.order_factory.create_sell_order(symbol, amount, price, deal_id, order_type)
        order.status = Order.STATUS_PENDING
        await self.orders_repo.save(order)  # ИЗМЕНЕНО: async
        return OrderExecutionResult(success=True, order=order)

    async def place_existing_order(self, order: Order) -> OrderExecutionResult:
        return await self._execute_order_on_exchange(order)

    async def _execute_order_on_exchange(self, order: Order) -> OrderExecutionResult:
        try:
            placed_order = await self.exchange_connector.create_order(order.symbol, order.side, order.order_type, order.amount, order.price)
            if isinstance(placed_order, Order):
                order.update_from_order(placed_order)
            else:
                order.update_from_exchange(placed_order)
            await self.orders_repo.save(order)  # ИЗМЕНЕНО: async
            return OrderExecutionResult(success=True, order=order)
        except Exception as e:
            order.status = Order.STATUS_FAILED
            order.error_message = str(e)
            await self.orders_repo.save(order)  # ИЗМЕНЕНО: async
            return OrderExecutionResult(success=False, order=order, error_message=str(e))

    async def get_order_status(self, order: Order) -> Order:
        if not order.exchange_id: 
            return order
        try:
            exchange_order = await self.exchange_connector.fetch_order(order.exchange_id, order.symbol)
            if isinstance(exchange_order, Order):
                order.update_from_order(exchange_order)
            else:
                order.update_from_exchange(exchange_order)
            await self.orders_repo.save(order)  # ИЗМЕНЕНО: async
        except Exception as e:
            logger.error(f"Error checking order status for {order.order_id}: {e}")
        return order

    async def cancel_order(self, order: Order) -> bool:
        if not order.exchange_id: 
            return False
        try:
            cancelled_order = await self.exchange_connector.cancel_order(order.exchange_id, order.symbol)
            if isinstance(cancelled_order, Order):
                order.update_from_order(cancelled_order)
            else:
                order.update_from_exchange(cancelled_order)
            await self.orders_repo.save(order)  # ИЗМЕНЕНО: async
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order.order_id}: {e}")
            return False

    # ИЗМЕНЕНИЕ: Новые методы с async
    async def get_open_orders(self) -> List[Order]: 
        return await self.orders_repo.get_open_orders()
    
    async def get_order_by_id(self, order_id: int) -> Optional[Order]: 
        return await self.orders_repo.find_by_id(order_id)
    
    # НОВЫЙ МЕТОД: Аналитика через DataFrame
    async def get_orders_analytics(self) -> Dict[str, any]:
        """Получить аналитику ордеров через DataFrame."""
        df = await self.orders_repo.get_dataframe()
        
        if df.empty:
            return {"error": "No orders data"}
        
        return {
            "total_orders": len(df),
            "status_distribution": df['status'].value_counts().to_dict(),
            "side_distribution": df['side'].value_counts().to_dict(),
            "total_volume": df['amount'].sum(),
            "average_price": df['price'].mean(),
            "fee_total": df['fee'].sum(),
            "symbols": df['symbol'].unique().tolist()
        }
```


---

## 🗄️ ШАГ 6: Создание PostgreSQL Схемы

### 📁 `database/migrations/001_create_tables.sql` - НОВЫЙ ФАЙЛ

```sql
-- Миграция для создания таблиц PostgreSQL

-- Таблица сделок
CREATE TABLE IF NOT EXISTS deals (
    deal_id SERIAL PRIMARY KEY,
    currency_pair VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    buy_order_id INTEGER,
    sell_order_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT deals_status_check CHECK (status IN ('OPEN', 'CLOSED', 'CANCELLED'))
);

-- Таблица ордеров
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    deal_id INTEGER NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    exchange_id VARCHAR(100),
    filled_amount DECIMAL(20, 8) DEFAULT 0,
    average_price DECIMAL(20, 8) DEFAULT 0,
    fee DECIMAL(20, 8) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    
    FOREIGN KEY (deal_id) REFERENCES deals(deal_id) ON DELETE CASCADE,
    CONSTRAINT orders_side_check CHECK (side IN ('BUY', 'SELL')),
    CONSTRAINT orders_status_check CHECK (status IN ('PENDING', 'PLACED', 'FILLED', 'CANCELLED', 'FAILED'))
);

-- Таблица валютных пар
CREATE TABLE IF NOT EXISTS currency_pairs (
    symbol VARCHAR(20) PRIMARY KEY,
    base_currency VARCHAR(10) NOT NULL,
    quote_currency VARCHAR(10) NOT NULL,
    price_precision INTEGER DEFAULT 8,
    amount_precision INTEGER DEFAULT 8,
    min_amount DECIMAL(20, 8),
    max_amount DECIMAL(20, 8),
    min_price DECIMAL(20, 8),
    max_price DECIMAL(20, 8),
    min_notional DECIMAL(20, 8),
    taker_fee DECIMAL(10, 6) DEFAULT 0.001,
    maker_fee DECIMAL(10, 6) DEFAULT 0.001,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_currency_pair ON deals(currency_pair);
CREATE INDEX IF NOT EXISTS idx_deals_created_at ON deals(created_at);

CREATE INDEX IF NOT EXISTS idx_orders_deal_id ON orders(deal_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_exchange_id ON orders(exchange_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- Триггер для обновления updated_at в orders
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_orders_updated_at 
    BEFORE UPDATE ON orders 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_currency_pairs_updated_at 
    BEFORE UPDATE ON currency_pairs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```


### 📁 `src/infrastructure/database/postgresql_connection.py` - НОВЫЙ ФАЙЛ

```python
"""
Менеджер подключений к PostgreSQL с пулом соединений.
"""

import asyncio
import asyncpg
from typing import List, Dict, Any, Optional
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class PostgreSQLConnection:
    """Менеджер подключений к PostgreSQL."""
    
    def __init__(self, connection_string: str, min_size: int = 5, max_size: int = 20):
        self.connection_string = connection_string
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Инициализация пула соединений."""
        async with self._lock:
            if self._pool is None:
                self._pool = await asyncpg.create_pool(
                    self.connection_string,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    command_timeout=60
                )
                logger.info(f"PostgreSQL pool initialized with {self.min_size}-{self.max_size} connections")
    
    async def close(self):
        """Закрытие пула соединений."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager для получения соединения из пула."""
        if not self._pool:
            await self.initialize()
        
        async with self._pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args) -> str:
        """Выполнение INSERT/UPDATE/DELETE запроса."""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Выполнение SELECT запроса с возвратом одной записи."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Выполнение SELECT запроса с возвратом всех записей."""
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def execute_many(self, query: str, args_list: List[tuple]) -> None:
        """Выполнение множественных запросов."""
        async with self.get_connection() as conn:
            await conn.executemany(query, args_list)
    
    async def execute_transaction(self, queries_and_args: List[tuple]):
        """Выполнение нескольких запросов в транзакции."""
        async with self.get_connection() as conn:
            async with conn.transaction():
                for query, args in queries_and_args:
                    await conn.execute(query, *args)
    
    async def run_migrations(self, migrations_dir: str = "database/migrations"):
        """Запуск миграций базы данных."""
        import os
        import glob
        
        if not os.path.exists(migrations_dir):
            logger.warning(f"Migrations directory {migrations_dir} not found")
            return
        
        migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
        
        async with self.get_connection() as conn:
            # Создаем таблицу для отслеживания миграций
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Получаем уже примененные миграции
            applied = await conn.fetch("SELECT filename FROM schema_migrations")
            applied_files = {row['filename'] for row in applied}
            
            # Применяем новые миграции
            for migration_file in migration_files:
                filename = os.path.basename(migration_file)
                
                if filename not in applied_files:
                    logger.info(f"Applying migration: {filename}")
                    
                    with open(migration_file, 'r', encoding='utf-8') as f:
                        migration_sql = f.read()
                    
                    async with conn.transaction():
                        await conn.execute(migration_sql)
                        await conn.execute(
                            "INSERT INTO schema_migrations (filename) VALUES ($1)",
                            filename
                        )
                    
                    logger.info(f"Migration {filename} applied successfully")
                else:
                    logger.debug(f"Migration {filename} already applied")
```


---

## 🔧 ШАG 7: Обновление главного файла приложения

### 📁 `main.py` - ИЗМЕНЕНИЕ

```python
import asyncio
import logging
import os
import time
from datetime import datetime
import win32api
import ccxt

# ИЗМЕНЕНИЕ: Импорты новых репозиториев
from infrastructure.repositories.deals_repository_v2 import DealsRepositoryV2
from infrastructure.repositories.orders_repository_v2 import OrdersRepositoryV2
from infrastructure.repositories.tickers_repository_v2 import TickersRepositoryV2
from infrastructure.repositories.indicators_repository_v2 import IndicatorsRepositoryV2
from infrastructure.database.postgresql_connection import PostgreSQLConnection

# Существующие импорты
from domain.entities.currency_pair import CurrencyPair
from domain.entities.ticker import Ticker
from domain.factories.deal_factory import DealFactory
from domain.factories.order_factory import OrderFactory
from domain.services.market_data.ticker_service import TickerService
from domain.services.deals.deal_service import DealService
from domain.services.orders.order_service import OrderService
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from infrastructure.utils.performance_logger import PerformanceLogger

# Настройка логирования
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_filename = f"autotrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = os.path.join(log_dir, log_filename)

# Настройка логгеров
file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
stream_handler = logging.StreamHandler()

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

def time_sync_windows():
    """Синхронизация времени Windows с сервером времени."""
    try:
        logger.info("🕐 Синхронизация времени с time.windows.com...")
        result = win32api.ShellExecute(0, 'runas', 'w32tm', '/resync /force', None, 0)
        if result > 32:
            logger.info("✅ Время успешно синхронизировано")
        else:
            logger.warning("⚠️ Синхронизация времени завершилась с предупреждением")
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации времени: {e}")

async def main():
    """
    ИЗМЕНЕНИЕ: Главная функция с новой архитектурой репозиториев.
    """
    logger.info("🚀 Запуск AutoTrade v3.0 с двухуровневой архитектурой")
    
    # Синхронизация времени
    time_sync_windows()
    
    # НОВОЕ: Инициализация PostgreSQL подключения
    db_connection_string = os.getenv(
        'DATABASE_URL', 
        'postgresql://autotrade:password@localhost:5432/autotrade'
    )
    
    db_connection = PostgreSQLConnection(db_connection_string)
    
    try:
        # Инициализация БД и применение миграций
        await db_connection.initialize()
        await db_connection.run_migrations()
        logger.info("✅ База данных инициализирована и миграции применены")
        
        # ИЗМЕНЕНИЕ: Создание новых репозиториев
        deals_repo = DealsRepositoryV2(db_connection)
        orders_repo = OrdersRepositoryV2(db_connection)
        tickers_repo = TickersRepositoryV2(dumps_directory="dumps", max_memory_records=10000)
        indicators_repo = IndicatorsRepositoryV2(dumps_directory="dumps", max_memory_records=50000)
        
        logger.info("✅ Все репозитории инициализированы")
        
        # Инициализация биржи
        exchange = ccxt.binance()
        exchange.set_sandbox_mode(True)
        
        # Загрузка рынков
        markets = exchange.load_markets()
        logger.info(f"📈 Загружено {len(markets)} торговых пар")
        
        # Создание валютной пары
        if 'ETH/USDT' not in markets:
            logger.error("❌ Торговая пара ETH/USDT не найдена")
            return
        
        market_info = markets['ETH/USDT']
        currency_pair = CurrencyPair.from_ccxt_market(market_info)
        logger.info(f"💱 Настроена торговая пара: {currency_pair.symbol}")
        
        # ИЗМЕНЕНИЕ: Инициализация сервисов с новыми репозиториями
        exchange_connector = CcxtExchangeConnector(exchange)
        
        # Фабрики
        order_factory = OrderFactory()
        deal_factory = DealFactory(order_factory)
        
        # Сервисы
        ticker_service = TickerService(tickers_repo, indicators_repo)
        order_service = OrderService(orders_repo, order_factory, exchange_connector)
        deal_service = DealService(deals_repo, order_service, deal_factory)
        
        # Система мониторинга производительности
        performance_logger = PerformanceLogger(log_interval_seconds=10)
        
        logger.info("🎯 Все сервисы инициализированы, начинаем торговый цикл")
        
        # ИЗМЕНЕНИЕ: Основной торговый цикл с новой архитектурой
        while True:
            cycle_start_time = time.time()
            
            try:
                # Получение тикера с биржи
                ticker_data = exchange.fetch_ticker('ETH/USDT')
                
                # Создание объекта тикера
                ticker = Ticker(
                    symbol=ticker_data['symbol'],
                    timestamp=ticker_data['timestamp'],
                    datetime=ticker_data['datetime'],
                    high=ticker_data['high'],
                    low=ticker_data['low'],
                    bid=ticker_data['bid'],
                    ask=ticker_data['ask'],
                    last=ticker_data['last'],
                    close=ticker_data['close'],
                    base_volume=ticker_data['baseVolume'],
                    quote_volume=ticker_data['quoteVolume']
                )
                
                # ИЗМЕНЕНИЕ: Обработка тикера через новый сервис
                await ticker_service.process_ticker(ticker)
                
                # Получение торгового сигнала
                signal = await ticker_service.get_signal()
                
                # НОВОЕ: Периодическая аналитика через DataFrame
                if performance_logger.tick_count % 100 == 0:
                    analytics = await ticker_service.get_analytics_dataframe()
                    logger.info(f"📊 Аналитика: {analytics}")
                    
                    orders_analytics = await order_service.get_orders_analytics()
                    logger.info(f"📋 Ордера: {orders_analytics}")
                
                # Логика торговли (упрощенная для примера)
                if signal == "BUY":
                    open_deals = await deal_service.get_open_deals()
                    
                    if len(open_deals) < 3:  # Максимум 3 открытые сделки
                        logger.info("🔥 Сигнал на покупку! Создаем новую сделку...")
                        
                        # Создание новой сделки
                        new_deal = await deal_service.create_new_deal(currency_pair)
                        
                        # Размещение ордера на покупку
                        buy_result = await deal_service.place_buy_order(
                            new_deal, 
                            amount=0.01,  # 0.01 ETH
                            budget=30.0   # $30 USDT
                        )
                        
                        if buy_result.success:
                            logger.info(f"✅ Ордер на покупку размещен: {buy_result.order.order_id}")
                        else:
                            logger.error(f"❌ Ошибка создания ордера: {buy_result.error_message}")
                
                # Обновление статусов открытых ордеров
                open_orders = await order_service.get_open_orders()
                for order in open_orders:
                    await order_service.get_order_status(order)
                
                # Расчет времени обработки
                processing_time = time.time() - cycle_start_time
                
                # Логирование производительности
                signals_count = len(ticker.signals) if ticker.signals else 0
                performance_logger.log_tick(ticker.last, processing_time, signals_count)
                
                # Пауза между циклами (1 секунда)
                await asyncio.sleep(1.0)
                
            except KeyboardInterrupt:
                logger.info("🛑 Получен сигнал остановки")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в торговом цикле: {e}")
                await asyncio.sleep(5.0)  # Пауза при ошибке
    
    except Exception as e:
        logger.error(f"❌ Критическая ошибка инициализации: {e}")
    
    finally:
        # НОВОЕ: Корректное закрытие ресурсов
        logger.info("🔄 Закрытие подключений и сохранение данных...")
        
        # Сохранение накопленных данных в Parquet
        try:
            today_str = datetime.now().strftime('%Y%m%d')
            
            tickers_dump = f"dumps/final_tickers_{today_str}.parquet"
            await tickers_repo.dump_to_parquet(tickers_dump)
            logger.info(f"💾 Тикеры сохранены в {tickers_dump}")
            
            indicators_dump = f"dumps/final_indicators_{today_str}.parquet"
            await indicators_repo.dump_to_parquet(indicators_dump)
            logger.info(f"💾 Индикаторы сохранены в {indicators_dump}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении дампов: {e}")
        
        # Закрытие БД соединения
        await db_connection.close()
        
        logger.info("✅ AutoTrade v3.0 корректно завершен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
```


---

## 🎯 ШАГ 8: Создание конфигурационных файлов

### 📁 `requirements.txt` - ДОБАВЛЕНИЯ

```plain text
# Существующие зависимости остаются
click
coverage
ipython
jinja2
jupyter
numpy
pandas
pip
pytest
pytz
pyyaml
requests
six
tornado
wheel

# НОВЫЕ зависимости для v3.0
asyncpg>=0.28.0          # PostgreSQL async драйвер
pyarrow>=12.0.0          # Поддержка Parquet файлов
fastparquet>=0.8.3       # Альтернативный Parquet движок
sqlalchemy>=2.0.0        # ORM (опционально)
alembic>=1.11.0          # Миграции БД (опционально)
python-dotenv>=1.0.0     # Управление переменными окружения
```


### 📁 `.env.example` - ОБНОВЛЕНИЕ

```shell script
# Существующие переменные
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
EXCHANGE_MODE=sandbox

# НОВЫЕ переменные для v3.0
DATABASE_URL=postgresql://autotrade:password@localhost:5432/autotrade
DATABASE_MIN_POOL_SIZE=5
DATABASE_MAX_POOL_SIZE=20

# Настройки репозиториев
DUMPS_DIRECTORY=dumps
MAX_MEMORY_TICKERS=10000
MAX_MEMORY_INDICATORS=50000

# Настройки автодампов
AUTO_DUMP_INTERVAL=3600          # секунд (1 час)
PARQUET_COMPRESSION=snappy       # snappy, gzip, lz4

# Логирование
LOG_LEVEL=INFO
LOG_DIRECTORY=logs
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5
```


### 📁 `docker-compose.yml` - ОБНОВЛЕНИЕ

```yaml
version: '3.8'

services:
  # НОВОЕ: PostgreSQL сервис
  postgres:
    image: postgres:15-alpine
    container_name: autotrade_postgres
    environment:
      POSTGRES_DB: autotrade
      POSTGRES_USER: autotrade
      POSTGRES_PASSWORD: password
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/migrations:/docker-entrypoint-initdb.d
    networks:
      - autotrade_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U autotrade -d autotrade"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ОБНОВЛЕННЫЙ: AutoTrade приложение
  autotrade:
    build: .
    container_name: autotrade_app
    environment:
      DATABASE_URL: postgresql://autotrade:password@postgres:5432/autotrade
      DUMPS_DIRECTORY: /app/dumps
      LOG_DIRECTORY: /app/logs
    volumes:
      - ./dumps:/app/dumps
      - ./logs:/app/logs
      - ./.env:/app/.env
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - autotrade_network
    restart: unless-stopped

  # НОВОЕ: pgAdmin для управления БД
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: autotrade_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@autotrade.local
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "8080:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      - postgres
    networks:
      - autotrade_network

volumes:
  postgres_data:
  pgadmin_data:

networks:
  autotrade_network:
    driver: bridge
```


---

## 📋 Резюме Плана Миграции

### 🎯 Изменения по файлам:

#### ✅ НОВЫЕ ФАЙЛЫ:
1. `src/domain/repositories/base_repository.py` - Базовые интерфейсы
2. `src/domain/dto/dataframe_convertible.py` - DTO для конвертации
3. `src/infrastructure/repositories/deals_repository_v2.py` - Новый репозиторий сделок
4. `src/infrastructure/repositories/orders_repository_v2.py` - Новый репозиторий ордеров
5. `src/infrastructure/repositories/tickers_repository_v2.py` - Новый репозиторий тикеров
6. `src/infrastructure/repositories/indicators_repository_v2.py` - Новый репозиторий индикаторов
7. `src/infrastructure/database/postgresql_connection.py` - Менеджер БД
8. `database/migrations/001_create_tables.sql` - SQL схема

#### 🔄 ИЗМЕНЕННЫЕ ФАЙЛЫ:
1. `src/domain/entities/deal.py` - Добавлены методы `to_dict()` и `from_dict()`
2. `src/domain/entities/order.py` - Добавлены методы `to_dict()` и `from_dict()`
3. `src/domain/entities/ticker.py` - Добавлены методы `to_dict()` и `from_dict()`
4. `src/domain/entities/indicator_data.py` - Обновлены методы конвертации
5. `src/domain/services/market_data/ticker_service.py` - Переход на новые репозитории
6. `src/domain/services/orders/order_service.py` - Переход на async методы
7. `main.py` - Инициализация новой архитектуры
8. `requirements.txt` - Добавлены новые зависимости
9. `.env.example` - Новые переменные окружения
10. `docker-compose.yml` - Добавлен PostgreSQL

### 🚀 Преимущества новой архитектуры:

1. **⚡ Скорость**: Все операции в памяти через Pandas DataFrame
2. **🔒 Надежность**: Атомарные данные сразу в PostgreSQL
3. **📊 Аналитика**: Прямой доступ к DataFrame для анализа
4. **🗄️ Масштабируемость**: Потоковые данные в эффективных Parquet дампах
5. **🧪 Тестируемость**: Четкое разделение слоев и интерфейсов
6. **🔄 Восстановимость**: Полное восстановление состояния после перезапуска

Этот план обеспечивает плавную миграцию с сохранением всех существующих функций и добавлением новых возможностей для анализа и масштабирования.