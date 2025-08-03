# src/infrastructure/repositories/factory/repository_factory.py
import asyncio
from typing import Dict, Any
from config.config_loader import load_config
from infrastructure.database.postgres_provider import PostgresPersistenceProvider

# Импорты интерфейсов
from ..interfaces.deals_repository_interface import IDealsRepository
from ..interfaces.orders_repository_interface import IOrdersRepository
from ..interfaces.tickers_repository_interface import ITickersRepository
from ..interfaces.order_books_repository_interface import IOrderBooksRepository

# Импорты MemoryFirst реализаций
from ..memory_first.memory_first_deals_repository import MemoryFirstDealsRepository
from ..memory_first.memory_first_orders_repository import MemoryFirstOrdersRepository
from ..memory_first.memory_first_tickers_repository import MemoryFirstTickersRepository
from ..memory_first.memory_first_order_books_repository import MemoryFirstOrderBooksRepository

# Импорты Legacy реализаций (для fallback)
from ..deals_repository import InMemoryDealsRepository
from ..orders_repository import InMemoryOrdersRepository
from ..tickers_repository import InMemoryTickerRepository

import logging

logger = logging.getLogger(__name__)

class RepositoryFactory:
    """
    Фабрика для создания репозиториев с двухуровневой архитектурой:
    
    АТОМАРНЫЕ ДАННЫЕ (Deal, Order):
    - Уровень 1: DataFrame в памяти (скорость наносекунд)
    - Уровень 2: PostgreSQL (мгновенная синхронизация)
    
    ПОТОКОВЫЕ ДАННЫЕ (Ticker, OrderBook):
    - Уровень 1: DataFrame в памяти (накопление)
    - Уровень 2: Parquet файлы (периодические дампы)
    
    Принципы:
    - Конфигурационное переключение backend'ов
    - Fallback на legacy репозитории
    - Автоматическая инициализация PostgreSQL
    - Graceful degradation при сбоях
    """
    
    def __init__(self):
        self.config = load_config()
        self.persistent_provider = None
        self._initialized = False
        
    async def initialize(self):
        """Инициализация фабрики и подключений"""
        if self._initialized:
            return
            
        try:
            # Инициализация PostgreSQL провайдера для атомарных данных
            if self.config.get("database"):
                self.persistent_provider = PostgresPersistenceProvider(
                    self.config["database"]
                )
                await self.persistent_provider.connect()
                logger.info("✅ PostgreSQL provider initialized")
                
                # Создание таблиц если их нет
                await self._create_database_schema()
                
            self._initialized = True
            logger.info("🚀 RepositoryFactory initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RepositoryFactory: {e}")
            # Продолжаем работу без PostgreSQL (fallback режим)
            self.persistent_provider = None
    
    async def _create_database_schema(self):
        """Создание схемы БД для атомарных данных"""
        if not self.persistent_provider:
            return
            
        schema_sql = """
        -- Таблица для сделок (АТОМАРНЫЕ ДАННЫЕ)
        CREATE TABLE IF NOT EXISTS deals (
            deal_id SERIAL PRIMARY KEY,
            currency_pair VARCHAR(20) NOT NULL,
            base_currency VARCHAR(10) NOT NULL,
            quote_currency VARCHAR(10) NOT NULL,
            deal_quota DECIMAL(18,8) NOT NULL,
            status VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            closed_at TIMESTAMP,
            buy_order_id INTEGER,
            sell_order_id INTEGER,
            profit DECIMAL(18,8) DEFAULT 0,
            UNIQUE(deal_id)
        );
        
        -- Индексы для быстрого поиска сделок
        CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
        CREATE INDEX IF NOT EXISTS idx_deals_currency_pair ON deals(currency_pair);
        CREATE INDEX IF NOT EXISTS idx_deals_created_at ON deals(created_at);
        
        -- Таблица для ордеров (АТОМАРНЫЕ ДАННЫЕ)
        CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY,
            exchange_order_id VARCHAR(100),
            deal_id INTEGER,
            order_type VARCHAR(10) NOT NULL,
            side VARCHAR(10) NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            amount DECIMAL(18,8) NOT NULL,
            price DECIMAL(18,8) NOT NULL,
            status VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            filled_amount DECIMAL(18,8) DEFAULT 0,
            fees DECIMAL(18,8) DEFAULT 0,
            commission DECIMAL(18,8) DEFAULT 0,
            UNIQUE(order_id)
        );
        
        -- Индексы для быстрого поиска ордеров
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_orders_deal_id ON orders(deal_id);
        CREATE INDEX IF NOT EXISTS idx_orders_exchange_id ON orders(exchange_order_id);
        CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
        
        -- Таблица для истории тикеров (ПОТОКОВЫЕ ДАННЫЕ - только для аналитики)
        CREATE TABLE IF NOT EXISTS tickers_history (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timestamp BIGINT NOT NULL,
            last_price DECIMAL(18,8) NOT NULL,
            bid_price DECIMAL(18,8),
            ask_price DECIMAL(18,8),
            volume DECIMAL(18,8),
            data JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(symbol, timestamp)
        );
        
        -- Индексы для аналитики тикеров
        CREATE INDEX IF NOT EXISTS idx_tickers_symbol_timestamp ON tickers_history(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_tickers_created_at ON tickers_history(created_at);
        
        -- Таблица для истории стаканов (ПОТОКОВЫЕ ДАННЫЕ - только для аналитики)
        CREATE TABLE IF NOT EXISTS order_books_history (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timestamp BIGINT NOT NULL,
            best_bid DECIMAL(18,8),
            best_ask DECIMAL(18,8),
            spread DECIMAL(18,8),
            data JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(symbol, timestamp)
        );
        
        -- Индексы для аналитики стаканов
        CREATE INDEX IF NOT EXISTS idx_order_books_symbol_timestamp ON order_books_history(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_order_books_created_at ON order_books_history(created_at);
        """
        
        try:
            async with self.persistent_provider._pool.acquire() as conn:
                await conn.execute(schema_sql)
            logger.info("✅ Database schema created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create database schema: {e}")
    
    async def get_deals_repository(self) -> IDealsRepository:
        """Создает репозиторий сделок (АТОМАРНЫЕ ДАННЫЕ)"""
        storage_type = self.config.get("storage", {}).get("deals_type", "memory_first_postgres")
        
        try:
            if storage_type == "memory_first_postgres":
                if not self._initialized:
                    await self.initialize()
                
                repo = MemoryFirstDealsRepository(self.persistent_provider)
                logger.info("✅ Created MemoryFirstDealsRepository")
                return repo
                
            elif storage_type == "in_memory_legacy":
                repo = InMemoryDealsRepository()
                logger.info("✅ Created InMemoryDealsRepository (legacy)")
                return repo
                
            else:
                raise ValueError(f"Unknown deals storage type: {storage_type}")
                
        except Exception as e:
            logger.error(f"❌ Failed to create deals repository: {e}")
            # Fallback на legacy репозиторий
            logger.warning("🔄 Falling back to InMemoryDealsRepository")
            return InMemoryDealsRepository()
    
    async def get_orders_repository(self) -> IOrdersRepository:
        """Создает репозиторий ордеров (АТОМАРНЫЕ ДАННЫЕ)"""
        storage_type = self.config.get("storage", {}).get("orders_type", "memory_first_postgres")
        
        try:
            if storage_type == "memory_first_postgres":
                if not self._initialized:
                    await self.initialize()
                
                repo = MemoryFirstOrdersRepository(self.persistent_provider)
                logger.info("✅ Created MemoryFirstOrdersRepository")
                return repo
                
            elif storage_type == "in_memory_legacy":
                repo = InMemoryOrdersRepository(max_orders=50000)
                logger.info("✅ Created InMemoryOrdersRepository (legacy)")
                return repo
                
            else:
                raise ValueError(f"Unknown orders storage type: {storage_type}")
                
        except Exception as e:
            logger.error(f"❌ Failed to create orders repository: {e}")
            # Fallback на legacy репозиторий
            logger.warning("🔄 Falling back to InMemoryOrdersRepository")
            return InMemoryOrdersRepository(max_orders=50000)
    
    async def get_tickers_repository(self) -> ITickersRepository:
        """Создает репозиторий тикеров (ПОТОКОВЫЕ ДАННЫЕ)"""
        storage_type = self.config.get("storage", {}).get("tickers_type", "memory_first_parquet")
        storage_config = self.config.get("storage", {})
        
        try:
            if storage_type == "memory_first_parquet":
                repo = MemoryFirstTickersRepository(
                    persistent_provider=self.persistent_provider,  # Для аналитики в PostgreSQL
                    batch_size=storage_config.get("batch_size", 10000),
                    dump_interval_minutes=storage_config.get("dump_interval_minutes", 5),
                    keep_last_n=100000
                )
                logger.info("✅ Created MemoryFirstTickersRepository")
                return repo
                
            elif storage_type == "in_memory_legacy":
                repo = InMemoryTickerRepository(max_size=100000)
                logger.info("✅ Created InMemoryTickerRepository (legacy)")
                return repo
                
            else:
                raise ValueError(f"Unknown tickers storage type: {storage_type}")
                
        except Exception as e:
            logger.error(f"❌ Failed to create tickers repository: {e}")
            # Fallback на legacy репозиторий
            logger.warning("🔄 Falling back to InMemoryTickerRepository")
            return InMemoryTickerRepository(max_size=100000)
    
    async def get_order_books_repository(self) -> IOrderBooksRepository:
        """Создает репозиторий стаканов ордеров (ПОТОКОВЫЕ ДАННЫЕ)"""
        storage_type = self.config.get("storage", {}).get("orderbooks_type", "memory_first_parquet")
        storage_config = self.config.get("storage", {})
        
        try:
            if storage_type == "memory_first_parquet":
                repo = MemoryFirstOrderBooksRepository(
                    persistent_provider=self.persistent_provider,  # Для аналитики в PostgreSQL
                    batch_size=storage_config.get("batch_size", 5000),
                    dump_interval_minutes=storage_config.get("dump_interval_minutes", 3),
                    keep_last_n=50000
                )
                logger.info("✅ Created MemoryFirstOrderBooksRepository")
                return repo
                
            else:
                raise ValueError(f"Unknown order books storage type: {storage_type}")
                
        except Exception as e:
            logger.error(f"❌ Failed to create order books repository: {e}")
            # Для OrderBooks нет legacy fallback, создаем простую заглушку
            logger.warning("🔄 Creating minimal OrderBooksRepository fallback")
            return MemoryFirstOrderBooksRepository(
                persistent_provider=None,
                batch_size=1000,
                dump_interval_minutes=10,
                keep_last_n=10000
            )
    
    async def close(self):
        """Закрытие всех подключений"""
        try:
            if self.persistent_provider:
                await self.persistent_provider.close()
                logger.info("✅ PostgreSQL provider closed")
                
            self._initialized = False
            logger.info("🔒 RepositoryFactory closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing RepositoryFactory: {e}")
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Получить информацию о текущей конфигурации хранилища"""
        storage_config = self.config.get("storage", {})
        
        return {
            "deals_type": storage_config.get("deals_type", "memory_first_postgres"),
            "orders_type": storage_config.get("orders_type", "memory_first_postgres"),
            "tickers_type": storage_config.get("tickers_type", "memory_first_parquet"),
            "orderbooks_type": storage_config.get("orderbooks_type", "memory_first_parquet"),
            "batch_size": storage_config.get("batch_size", 10000),
            "dump_interval_minutes": storage_config.get("dump_interval_minutes", 5),
            "fallback_enabled": storage_config.get("fallback_enabled", True),
            "postgresql_available": self.persistent_provider is not None,
            "initialized": self._initialized
        }