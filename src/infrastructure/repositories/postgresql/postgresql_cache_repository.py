import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

from src.domain.repositories.i_cache_repository import ICacheRepository
from src.infrastructure.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PostgreSQLCacheRepository(ICacheRepository):
    """
    PostgreSQL реализация репозитория кэша
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._ensure_postgresql()
        self._memory_cache = {}  # Дополнительный in-memory кэш для горячих данных
        self._max_memory_cache_size = 1000
    
    def _ensure_postgresql(self):
        """Проверяем, что используется PostgreSQL"""
        if self.db_manager.db_type != 'postgresql':
            raise ValueError("PostgreSQLCacheRepository requires PostgreSQL database")
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Установить значение в кэш"""
        try:
            # Вычисляем время истечения
            expires_at = None
            if ttl_seconds is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
            query = """
                INSERT INTO cache_entries (cache_key, value, ttl_seconds, expires_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (cache_key) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    ttl_seconds = EXCLUDED.ttl_seconds,
                    expires_at = EXCLUDED.expires_at,
                    created_at = CURRENT_TIMESTAMP
            """
            
            # Сериализуем значение в JSON
            json_value = json.dumps(value)
            
            params = (
                key,
                json_value,
                ttl_seconds,
                expires_at
            )
            
            await self.db_manager.execute_command(query, params)
            
            # Обновляем memory cache для горячих данных
            self._update_memory_cache(key, value, expires_at)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache value: {e}")
            return False
    
    async def get(
        self,
        key: str,
        default_value: Any = None
    ) -> Any:
        """Получить значение из кэша"""
        try:
            # Сначала проверяем memory cache
            if key in self._memory_cache:
                cached_item = self._memory_cache[key]
                if self._is_memory_cache_valid(cached_item):
                    return cached_item['value']
                else:
                    # Удаляем просроченное значение
                    del self._memory_cache[key]
            
            # Ищем в базе данных
            query = """
                SELECT value, expires_at
                FROM cache_entries
                WHERE cache_key = $1
            """
            
            rows = await self.db_manager.execute_query(query, (key,))
            
            if not rows:
                return default_value
            
            row = rows[0]
            
            # Проверяем истечение срока
            if row['expires_at'] and datetime.now() > row['expires_at']:
                # Асинхронно удаляем просроченную запись
                asyncio.create_task(self.delete(key))
                return default_value
            
            # Десериализуем значение
            value = json.loads(row['value'])
            
            # Обновляем memory cache
            self._update_memory_cache(key, value, row['expires_at'])
            
            return value
            
        except Exception as e:
            logger.error(f"Error getting cache value: {e}")
            return default_value
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа в кэше"""
        try:
            # Проверяем memory cache
            if key in self._memory_cache:
                cached_item = self._memory_cache[key]
                if self._is_memory_cache_valid(cached_item):
                    return True
                else:
                    del self._memory_cache[key]
            
            query = """
                SELECT 1
                FROM cache_entries
                WHERE cache_key = $1
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """
            
            rows = await self.db_manager.execute_query(query, (key,))
            
            return len(rows) > 0
            
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        try:
            query = "DELETE FROM cache_entries WHERE cache_key = $1"
            
            result = await self.db_manager.execute_command(query, (key,))
            
            # Удаляем из memory cache
            self._memory_cache.pop(key, None)
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting cache value: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Очистить кэш (все или по паттерну)"""
        try:
            if pattern:
                # Используем LIKE для поиска по паттерну
                query = "DELETE FROM cache_entries WHERE cache_key LIKE $1"
                like_pattern = pattern.replace('*', '%')
                result = await self.db_manager.execute_command(query, (like_pattern,))
                
                # Очищаем соответствующие записи из memory cache
                keys_to_remove = [
                    k for k in self._memory_cache.keys() 
                    if self._matches_pattern(k, pattern)
                ]
                for k in keys_to_remove:
                    del self._memory_cache[k]
            else:
                # Очищаем весь кэш
                query = "DELETE FROM cache_entries"
                result = await self.db_manager.execute_command(query)
                
                # Очищаем memory cache
                self._memory_cache.clear()
            
            return result
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    async def cleanup_expired(self) -> int:
        """Очистить просроченные записи"""
        try:
            # Используем функцию из схемы
            result = await self.db_manager.execute_query("SELECT cleanup_expired_cache()")
            
            deleted_count = result[0]['cleanup_expired_cache'] if result else 0
            
            # Очищаем просроченные записи из memory cache
            current_time = datetime.now()
            expired_keys = [
                k for k, v in self._memory_cache.items()
                if v['expires_at'] and current_time > v['expires_at']
            ]
            for k in expired_keys:
                del self._memory_cache[k]
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
            return 0
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Получить время жизни ключа в секундах"""
        try:
            query = """
                SELECT expires_at
                FROM cache_entries
                WHERE cache_key = $1
            """
            
            rows = await self.db_manager.execute_query(query, (key,))
            
            if not rows or not rows[0]['expires_at']:
                return None
            
            expires_at = rows[0]['expires_at']
            current_time = datetime.now()
            
            if expires_at <= current_time:
                return 0  # Уже истекло
            
            delta = expires_at - current_time
            return int(delta.total_seconds())
            
        except Exception as e:
            logger.error(f"Error getting TTL: {e}")
            return None
    
    async def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """Продлить время жизни ключа"""
        try:
            query = """
                UPDATE cache_entries
                SET expires_at = COALESCE(expires_at, CURRENT_TIMESTAMP) + INTERVAL '%s seconds',
                    ttl_seconds = COALESCE(ttl_seconds, 0) + $2
                WHERE cache_key = $1
            """
            
            result = await self.db_manager.execute_command(
                query % additional_seconds,
                (key, additional_seconds)
            )
            
            # Обновляем memory cache
            if key in self._memory_cache:
                item = self._memory_cache[key]
                if item['expires_at']:
                    item['expires_at'] += timedelta(seconds=additional_seconds)
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Error extending TTL: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(CASE WHEN expires_at IS NULL THEN 1 END) as permanent_entries,
                    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at > CURRENT_TIMESTAMP THEN 1 END) as active_entries,
                    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP THEN 1 END) as expired_entries,
                    AVG(LENGTH(value)) as avg_value_size,
                    MAX(LENGTH(value)) as max_value_size,
                    MIN(created_at) as oldest_entry,
                    MAX(created_at) as newest_entry
                FROM cache_entries
            """
            
            rows = await self.db_manager.execute_query(query)
            
            if not rows:
                return {}
            
            row = rows[0]
            
            return {
                'total_entries': int(row['total_entries']),
                'permanent_entries': int(row['permanent_entries']),
                'active_entries': int(row['active_entries']),
                'expired_entries': int(row['expired_entries']),
                'avg_value_size_bytes': float(row['avg_value_size']) if row['avg_value_size'] else 0,
                'max_value_size_bytes': int(row['max_value_size']) if row['max_value_size'] else 0,
                'oldest_entry': row['oldest_entry'].isoformat() if row['oldest_entry'] else None,
                'newest_entry': row['newest_entry'].isoformat() if row['newest_entry'] else None,
                'memory_cache_entries': len(self._memory_cache),
                'memory_cache_max_size': self._max_memory_cache_size
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    async def get_all_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Получить все ключи (опционально по паттерну)"""
        try:
            if pattern:
                query = """
                    SELECT cache_key
                    FROM cache_entries
                    WHERE cache_key LIKE $1
                      AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                    ORDER BY cache_key
                """
                like_pattern = pattern.replace('*', '%')
                rows = await self.db_manager.execute_query(query, (like_pattern,))
            else:
                query = """
                    SELECT cache_key
                    FROM cache_entries
                    WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP
                    ORDER BY cache_key
                """
                rows = await self.db_manager.execute_query(query)
            
            return [row['cache_key'] for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting all keys: {e}")
            return []
    
    async def set_many(self, items: Dict[str, Any], ttl_seconds: Optional[int] = None) -> int:
        """Установить множественные значения"""
        try:
            if not items:
                return 0
            
            # Подготавливаем данные для batch insert
            expires_at = None
            if ttl_seconds is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
            # Используем upsert для каждого элемента
            query = """
                INSERT INTO cache_entries (cache_key, value, ttl_seconds, expires_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (cache_key) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    ttl_seconds = EXCLUDED.ttl_seconds,
                    expires_at = EXCLUDED.expires_at,
                    created_at = CURRENT_TIMESTAMP
            """
            
            params_list = []
            for key, value in items.items():
                json_value = json.dumps(value)
                params_list.append((key, json_value, ttl_seconds, expires_at))
                
                # Обновляем memory cache
                self._update_memory_cache(key, value, expires_at)
            
            await self.db_manager.execute_many(query, params_list)
            
            return len(items)
            
        except Exception as e:
            logger.error(f"Error setting multiple cache values: {e}")
            return 0
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Получить множественные значения"""
        try:
            if not keys:
                return {}
            
            result = {}
            db_keys = []
            
            # Сначала проверяем memory cache
            for key in keys:
                if key in self._memory_cache:
                    cached_item = self._memory_cache[key]
                    if self._is_memory_cache_valid(cached_item):
                        result[key] = cached_item['value']
                    else:
                        del self._memory_cache[key]
                        db_keys.append(key)
                else:
                    db_keys.append(key)
            
            # Запрашиваем оставшиеся ключи из БД
            if db_keys:
                # Создаем плейсхолдеры для IN клаузы
                placeholders = ', '.join(f'${i+1}' for i in range(len(db_keys)))
                
                query = f"""
                    SELECT cache_key, value, expires_at
                    FROM cache_entries
                    WHERE cache_key IN ({placeholders})
                      AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """
                
                rows = await self.db_manager.execute_query(query, tuple(db_keys))
                
                for row in rows:
                    key = row['cache_key']
                    value = json.loads(row['value'])
                    result[key] = value
                    
                    # Обновляем memory cache
                    self._update_memory_cache(key, value, row['expires_at'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting multiple cache values: {e}")
            return {}
    
    def _update_memory_cache(self, key: str, value: Any, expires_at: Optional[datetime]) -> None:
        """Обновить memory cache"""
        try:
            # Проверяем размер кэша
            if len(self._memory_cache) >= self._max_memory_cache_size:
                # Удаляем старые записи (простая стратегия FIFO)
                keys_to_remove = list(self._memory_cache.keys())[:100]
                for k in keys_to_remove:
                    del self._memory_cache[k]
            
            self._memory_cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'accessed_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error updating memory cache: {e}")
    
    def _is_memory_cache_valid(self, cached_item: Dict[str, Any]) -> bool:
        """Проверить валидность записи в memory cache"""
        if cached_item['expires_at'] is None:
            return True
        
        return datetime.now() <= cached_item['expires_at']
    
    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Проверить соответствие текста паттерну"""
        import fnmatch
        return fnmatch.fnmatch(text, pattern)
    
    def clear_memory_cache(self) -> None:
        """Очистить memory cache"""
        self._memory_cache.clear()
    
    def set_memory_cache_size(self, size: int) -> None:
        """Установить максимальный размер memory cache"""
        self._max_memory_cache_size = max(100, size)