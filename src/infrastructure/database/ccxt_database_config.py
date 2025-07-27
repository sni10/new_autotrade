# infrastructure/database/ccxt_database_config.py
import os
import asyncio
import asyncpg
import logging
from typing import Optional, Dict, Any
from asyncpg import Pool

logger = logging.getLogger(__name__)


class CCXTDatabaseConfig:
    """
    🚀 CCXT Database Configuration Manager
    
    Управляет подключением к PostgreSQL с CCXT-совместимой схемой.
    Поддерживает connection pooling и автоматическую миграцию.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "autotrade_ccxt",
        username: str = "autotrade",
        password: str = "autotrade_password",
        pool_min_size: int = 5,
        pool_max_size: int = 20,
        command_timeout: int = 60,
        ssl_mode: str = "prefer"
    ):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.pool_min_size = pool_min_size
        self.pool_max_size = pool_max_size
        self.command_timeout = command_timeout
        self.ssl_mode = ssl_mode
        
        self._pool: Optional[Pool] = None

    @classmethod
    def from_env(cls) -> 'CCXTDatabaseConfig':
        """
        Создает конфигурацию из переменных окружения
        """
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "autotrade_ccxt"),
            username=os.getenv("POSTGRES_USER", "autotrade"),
            password=os.getenv("POSTGRES_PASSWORD", "autotrade_password"),
            pool_min_size=int(os.getenv("POSTGRES_POOL_MIN_SIZE", "5")),
            pool_max_size=int(os.getenv("POSTGRES_POOL_MAX_SIZE", "20")),
            command_timeout=int(os.getenv("POSTGRES_COMMAND_TIMEOUT", "60")),
            ssl_mode=os.getenv("POSTGRES_SSL_MODE", "prefer")
        )

    @classmethod
    def from_config_dict(cls, config: Dict[str, Any]) -> 'CCXTDatabaseConfig':
        """
        Создает конфигурацию из словаря
        """
        db_config = config.get("database", {})
        return cls(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 5432),
            database=db_config.get("database", "autotrade_ccxt"),
            username=db_config.get("username", "autotrade"),
            password=db_config.get("password", "autotrade_password"),
            pool_min_size=db_config.get("pool_min_size", 5),
            pool_max_size=db_config.get("pool_max_size", 20),
            command_timeout=db_config.get("command_timeout", 60),
            ssl_mode=db_config.get("ssl_mode", "prefer")
        )

    def get_connection_dsn(self) -> str:
        """
        Возвращает DSN строку подключения
        """
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.ssl_mode}"
        )

    async def create_connection_pool(self) -> Pool:
        """
        Создает pool соединений с базой данных
        """
        if self._pool is not None:
            logger.warning("Connection pool already exists")
            return self._pool

        try:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                min_size=self.pool_min_size,
                max_size=self.pool_max_size,
                command_timeout=self.command_timeout,
                ssl=self.ssl_mode
            )
            
            logger.info(f"Created PostgreSQL connection pool: {self.host}:{self.port}/{self.database}")
            
            # Проверяем подключение
            await self.health_check()
            
            return self._pool
            
        except Exception as e:
            logger.error(f"Failed to create connection pool: {str(e)}")
            raise

    async def close_connection_pool(self) -> None:
        """
        Закрывает pool соединений
        """
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Closed PostgreSQL connection pool")

    def get_pool(self) -> Optional[Pool]:
        """
        Возвращает текущий pool соединений
        """
        return self._pool

    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья подключения к БД
        """
        if self._pool is None:
            return {"status": "no_pool", "error": "Connection pool not initialized"}

        try:
            async with self._pool.acquire() as conn:
                # Проверяем подключение
                await conn.fetchval("SELECT 1")
                
                # Проверяем версию PostgreSQL
                pg_version = await conn.fetchval("SELECT version()")
                
                # Проверяем наличие CCXT схемы
                ccxt_tables = await conn.fetchval("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name IN ('ccxt_orders', 'ccxt_markets', 'ccxt_tickers')
                """)
                
                # Статистика pool
                pool_stats = {
                    "size": self._pool.get_size(),
                    "free": self._pool.get_size() - self._pool.get_busy_size(),
                    "busy": self._pool.get_busy_size(),
                    "min_size": self.pool_min_size,
                    "max_size": self.pool_max_size
                }
                
                return {
                    "status": "healthy",
                    "postgresql_version": pg_version,
                    "ccxt_tables_count": ccxt_tables,
                    "ccxt_schema_ready": ccxt_tables >= 3,
                    "pool_stats": pool_stats,
                    "connection_info": {
                        "host": self.host,
                        "port": self.port,
                        "database": self.database,
                        "ssl_mode": self.ssl_mode
                    }
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def create_database_if_not_exists(self) -> bool:
        """
        Создает базу данных, если она не существует
        """
        try:
            # Подключаемся к системной БД postgres для создания нашей БД
            system_conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database="postgres",
                user=self.username,
                password=self.password
            )
            
            # Проверяем существование БД
            db_exists = await system_conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", 
                self.database
            )
            
            if not db_exists:
                # Создаем БД
                await system_conn.execute(f'CREATE DATABASE "{self.database}"')
                logger.info(f"Created database: {self.database}")
                
            await system_conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database {self.database}: {str(e)}")
            return False

    async def execute_schema_migration(self, schema_file_path: str) -> bool:
        """
        Выполняет миграцию схемы из SQL файла
        """
        if self._pool is None:
            logger.error("Connection pool not initialized")
            return False

        try:
            # Читаем SQL файл
            with open(schema_file_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            async with self._pool.acquire() as conn:
                await conn.execute(schema_sql)
                logger.info(f"Executed schema migration from: {schema_file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to execute schema migration: {str(e)}")
            return False

    async def check_schema_version(self) -> Optional[str]:
        """
        Проверяет версию схемы в БД
        """
        if self._pool is None:
            return None

        try:
            async with self._pool.acquire() as conn:
                version = await conn.fetchval("""
                    SELECT value FROM configuration 
                    WHERE key = 'schema_version' AND category = 'system'
                """)
                return version
                
        except Exception as e:
            logger.warning(f"Could not check schema version: {str(e)}")
            return None

    async def get_table_statistics(self) -> Dict[str, int]:
        """
        Получает статистику по таблицам
        """
        if self._pool is None:
            return {}

        try:
            async with self._pool.acquire() as conn:
                tables = ['ccxt_orders', 'ccxt_markets', 'ccxt_tickers', 'deals']
                stats = {}
                
                for table in tables:
                    try:
                        count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                        stats[table] = count or 0
                    except:
                        stats[table] = 0
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get table statistics: {str(e)}")
            return {}

    def __repr__(self):
        return (f"CCXTDatabaseConfig(host={self.host}, port={self.port}, "
                f"database={self.database}, pool_size={self.pool_min_size}-{self.pool_max_size})")


# ===== UTILITY FUNCTIONS =====

async def initialize_ccxt_database(config: CCXTDatabaseConfig) -> bool:
    """
    Полная инициализация CCXT базы данных
    """
    logger.info("Initializing CCXT database...")
    
    try:
        # 1. Создаем БД если не существует
        if not await config.create_database_if_not_exists():
            logger.error("Failed to create database")
            return False
        
        # 2. Создаем connection pool
        pool = await config.create_connection_pool()
        if not pool:
            logger.error("Failed to create connection pool")
            return False
        
        # 3. Проверяем схему
        schema_version = await config.check_schema_version()
        logger.info(f"Current schema version: {schema_version}")
        
        # 4. Health check
        health = await config.health_check()
        if health["status"] != "healthy":
            logger.error(f"Database health check failed: {health}")
            return False
        
        logger.info("CCXT database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize CCXT database: {str(e)}")
        return False


async def migrate_to_ccxt_schema(
    config: CCXTDatabaseConfig,
    schema_file: str,
    migration_file: str
) -> bool:
    """
    Выполняет полную миграцию к CCXT схеме
    """
    logger.info("Starting CCXT schema migration...")
    
    try:
        # 1. Выполняем CCXT схему
        if not await config.execute_schema_migration(schema_file):
            logger.error("Failed to execute CCXT schema")
            return False
        
        # 2. Выполняем миграцию данных
        if not await config.execute_schema_migration(migration_file):
            logger.error("Failed to execute data migration")
            return False
        
        # 3. Проверяем результат
        health = await config.health_check()
        if not health.get("ccxt_schema_ready", False):
            logger.error("CCXT schema not ready after migration")
            return False
        
        logger.info("CCXT schema migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"CCXT schema migration failed: {str(e)}")
        return False


# ===== EXAMPLE USAGE =====

if __name__ == "__main__":
    async def example_usage():
        # Создание конфигурации
        config = CCXTDatabaseConfig.from_env()
        
        # Инициализация БД
        success = await initialize_ccxt_database(config)
        if success:
            print("Database initialized successfully!")
            
            # Health check
            health = await config.health_check()
            print(f"Health status: {health}")
            
            # Статистика таблиц
            stats = await config.get_table_statistics()
            print(f"Table statistics: {stats}")
        
        # Закрытие соединений
        await config.close_connection_pool()
    
    asyncio.run(example_usage())