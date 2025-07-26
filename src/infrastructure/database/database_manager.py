import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
import aiosqlite
import asyncpg
import json

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Менеджер базы данных для управления подключениями к PostgreSQL и SQLite
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_type = config.get('type', 'sqlite').lower()
        self.connection_pool = None
        self.sqlite_connection = None
        
        # Пути к схемам
        self.schema_dir = Path(__file__).parent / 'schemas'
        self.postgresql_schema = self.schema_dir / 'postgresql_schema.sql'
        self.sqlite_schema = self.schema_dir / 'sqlite_schema.sql'
    
    async def initialize(self) -> bool:
        """Инициализация подключения к базе данных"""
        try:
            if self.db_type == 'postgresql':
                return await self._initialize_postgresql()
            elif self.db_type == 'sqlite':
                return await self._initialize_sqlite()
            else:
                logger.error(f"Unsupported database type: {self.db_type}")
                return False
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    async def _initialize_postgresql(self) -> bool:
        """Инициализация PostgreSQL"""
        try:
            dsn = self._build_postgresql_dsn()
            
            # Создаем пул соединений
            self.connection_pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=self.config.get('min_pool_size', 2),
                max_size=self.config.get('max_pool_size', 10),
                command_timeout=self.config.get('command_timeout', 60)
            )
            
            logger.info("✅ PostgreSQL connection pool created successfully")
            
            # Проверяем подключение
            async with self.connection_pool.acquire() as conn:
                result = await conn.fetchval("SELECT version()")
                logger.info(f"PostgreSQL version: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            return False
    
    async def _initialize_sqlite(self) -> bool:
        """Инициализация SQLite"""
        try:
            db_path = self.config.get('path', 'autotrade.db')
            
            # Создаем директорию если нужно
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Устанавливаем соединение
            self.sqlite_connection = await aiosqlite.connect(db_path)
            
            # Включаем внешние ключи
            await self.sqlite_connection.execute("PRAGMA foreign_keys = ON")
            
            # Настройки производительности
            await self.sqlite_connection.execute("PRAGMA journal_mode = WAL")
            await self.sqlite_connection.execute("PRAGMA synchronous = NORMAL")
            await self.sqlite_connection.execute("PRAGMA cache_size = -64000")  # 64MB cache
            
            await self.sqlite_connection.commit()
            
            logger.info(f"✅ SQLite database initialized: {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}")
            return False
    
    def _build_postgresql_dsn(self) -> str:
        """Построение DSN для PostgreSQL"""
        host = self.config.get('host', 'localhost')
        port = self.config.get('port', 5432)
        database = self.config.get('database', 'autotrade')
        user = self.config.get('user', 'autotrade')
        password = self.config.get('password', '')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    async def create_schema(self) -> bool:
        """Создание схемы базы данных"""
        try:
            if self.db_type == 'postgresql':
                return await self._create_postgresql_schema()
            elif self.db_type == 'sqlite':
                return await self._create_sqlite_schema()
            else:
                logger.error(f"Unsupported database type: {self.db_type}")
                return False
                
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            return False
    
    async def _create_postgresql_schema(self) -> bool:
        """Создание схемы PostgreSQL"""
        try:
            if not self.postgresql_schema.exists():
                logger.error(f"PostgreSQL schema file not found: {self.postgresql_schema}")
                return False
            
            schema_sql = self.postgresql_schema.read_text(encoding='utf-8')
            
            async with self.connection_pool.acquire() as conn:
                # Выполняем скрипт по частям для лучшего контроля ошибок
                statements = schema_sql.split(';')
                
                for statement in statements:
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            await conn.execute(statement)
                        except Exception as e:
                            # Игнорируем ошибки создания уже существующих объектов
                            if "already exists" not in str(e).lower():
                                logger.warning(f"Schema statement failed: {e}")
                                logger.debug(f"Statement: {statement[:100]}...")
            
            logger.info("✅ PostgreSQL schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL schema: {e}")
            return False
    
    async def _create_sqlite_schema(self) -> bool:
        """Создание схемы SQLite"""
        try:
            if not self.sqlite_schema.exists():
                logger.error(f"SQLite schema file not found: {self.sqlite_schema}")
                return False
            
            schema_sql = self.sqlite_schema.read_text(encoding='utf-8')
            
            # Выполняем скрипт
            await self.sqlite_connection.executescript(schema_sql)
            await self.sqlite_connection.commit()
            
            logger.info("✅ SQLite schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create SQLite schema: {e}")
            return False
    
    async def get_connection(self):
        """Получение соединения с базой данных"""
        if self.db_type == 'postgresql':
            if not self.connection_pool:
                raise RuntimeError("PostgreSQL pool not initialized")
            return self.connection_pool.acquire()
        elif self.db_type == 'sqlite':
            if not self.sqlite_connection:
                raise RuntimeError("SQLite connection not initialized")
            return self.sqlite_connection
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Выполнение SELECT запроса"""
        try:
            if self.db_type == 'postgresql':
                async with self.connection_pool.acquire() as conn:
                    if params:
                        rows = await conn.fetch(query, *params)
                    else:
                        rows = await conn.fetch(query)
                    return [dict(row) for row in rows]
            
            elif self.db_type == 'sqlite':
                async with self.sqlite_connection.execute(query, params or ()) as cursor:
                    rows = await cursor.fetchall()
                    columns = [description[0] for description in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise
    
    async def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        """Выполнение INSERT/UPDATE/DELETE команды"""
        try:
            if self.db_type == 'postgresql':
                async with self.connection_pool.acquire() as conn:
                    if params:
                        result = await conn.execute(command, *params)
                    else:
                        result = await conn.execute(command)
                    # Извлекаем количество затронутых строк из результата
                    return int(result.split()[-1]) if result.split() else 0
            
            elif self.db_type == 'sqlite':
                cursor = await self.sqlite_connection.execute(command, params or ())
                await self.sqlite_connection.commit()
                return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            logger.debug(f"Command: {command}")
            logger.debug(f"Params: {params}")
            raise
    
    async def execute_many(self, command: str, params_list: List[tuple]) -> int:
        """Выполнение команды с множественными параметрами"""
        try:
            if self.db_type == 'postgresql':
                async with self.connection_pool.acquire() as conn:
                    await conn.executemany(command, params_list)
                    return len(params_list)
            
            elif self.db_type == 'sqlite':
                await self.sqlite_connection.executemany(command, params_list)
                await self.sqlite_connection.commit()
                return len(params_list)
            
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            logger.debug(f"Command: {command}")
            logger.debug(f"Batch size: {len(params_list)}")
            raise
    
    async def transaction(self):
        """Создание транзакции"""
        if self.db_type == 'postgresql':
            return self.connection_pool.acquire()
        elif self.db_type == 'sqlite':
            # SQLite автоматически использует транзакции
            return self.sqlite_connection
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья базы данных"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            if self.db_type == 'postgresql':
                async with self.connection_pool.acquire() as conn:
                    version = await conn.fetchval("SELECT version()")
                    pool_size = self.connection_pool.get_size()
                    
                end_time = asyncio.get_event_loop().time()
                
                return {
                    "status": "healthy",
                    "type": "postgresql",
                    "version": version,
                    "pool_size": pool_size,
                    "response_time_ms": round((end_time - start_time) * 1000, 2)
                }
            
            elif self.db_type == 'sqlite':
                cursor = await self.sqlite_connection.execute("SELECT sqlite_version()")
                version = (await cursor.fetchone())[0]
                
                end_time = asyncio.get_event_loop().time()
                
                return {
                    "status": "healthy",
                    "type": "sqlite",
                    "version": version,
                    "response_time_ms": round((end_time - start_time) * 1000, 2)
                }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "type": self.db_type,
                "error": str(e)
            }
    
    async def cleanup_old_data(self, days_to_keep: Dict[str, int]) -> Dict[str, int]:
        """Очистка старых данных"""
        try:
            results = {}
            
            # Очистка потоковых данных
            if 'stream_data' in days_to_keep:
                if self.db_type == 'postgresql':
                    count = await self.execute_command(
                        "SELECT cleanup_old_stream_data($1)",
                        (days_to_keep['stream_data'],)
                    )
                else:
                    count = await self.execute_command(
                        "DELETE FROM stream_data WHERE created_at < datetime('now', '-{} days')".format(
                            days_to_keep['stream_data']
                        )
                    )
                results['stream_data'] = count
            
            # Очистка индикаторов
            if 'indicators' in days_to_keep:
                if self.db_type == 'postgresql':
                    count = await self.execute_command(
                        "SELECT cleanup_old_indicators($1)",
                        (days_to_keep['indicators'],)
                    )
                else:
                    count = await self.execute_command(
                        "DELETE FROM indicators WHERE created_at < datetime('now', '-{} days')".format(
                            days_to_keep['indicators']
                        )
                    )
                results['indicators'] = count
            
            # Очистка торговых сигналов
            if 'trading_signals' in days_to_keep:
                if self.db_type == 'postgresql':
                    count = await self.execute_command(
                        "SELECT cleanup_old_trading_signals($1)",
                        (days_to_keep['trading_signals'],)
                    )
                else:
                    count = await self.execute_command(
                        "DELETE FROM trading_signals WHERE created_at < datetime('now', '-{} days')".format(
                            days_to_keep['trading_signals']
                        )
                    )
                results['trading_signals'] = count
            
            # Очистка просроченного кэша
            if self.db_type == 'postgresql':
                cache_count = await self.execute_command("SELECT cleanup_expired_cache()")
            else:
                cache_count = await self.execute_command(
                    "DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at < datetime('now')"
                )
            results['cache'] = cache_count
            
            logger.info(f"Data cleanup completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            return {}
    
    async def close(self) -> None:
        """Закрытие соединений с базой данных"""
        try:
            if self.connection_pool:
                await self.connection_pool.close()
                logger.info("PostgreSQL connection pool closed")
            
            if self.sqlite_connection:
                await self.sqlite_connection.close()
                logger.info("SQLite connection closed")
                
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    def __del__(self):
        """Деструктор для гарантированного закрытия соединений"""
        if self.connection_pool or self.sqlite_connection:
            logger.warning("Database connections not properly closed - forcing cleanup")


# Утилитарные функции для создания менеджера БД

def create_database_manager(config: Dict[str, Any]) -> DatabaseManager:
    """Создание менеджера базы данных из конфигурации"""
    return DatabaseManager(config)


async def init_database_from_config(config_path: str) -> Optional[DatabaseManager]:
    """Инициализация базы данных из файла конфигурации"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        db_config = config.get('database', {})
        if not db_config:
            logger.error("Database configuration not found")
            return None
        
        db_manager = create_database_manager(db_config)
        
        if await db_manager.initialize():
            logger.info("✅ Database initialized from config")
            return db_manager
        else:
            logger.error("❌ Database initialization failed")
            return None
            
    except Exception as e:
        logger.error(f"Failed to initialize database from config: {e}")
        return None