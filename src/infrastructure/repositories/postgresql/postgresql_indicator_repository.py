import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from src.domain.entities.indicator_data import IndicatorData, IndicatorType, IndicatorLevel
from src.domain.repositories.i_indicator_repository import IIndicatorRepository
from src.infrastructure.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PostgreSQLIndicatorRepository(IIndicatorRepository):
    """
    PostgreSQL реализация репозитория индикаторов
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._ensure_postgresql()
    
    def _ensure_postgresql(self):
        """Проверяем, что используется PostgreSQL"""
        if self.db_manager.db_type != 'postgresql':
            raise ValueError("PostgreSQLIndicatorRepository requires PostgreSQL database")
    
    async def save_indicator(self, indicator: IndicatorData) -> bool:
        """Сохранить индикатор"""
        try:
            query = """
                INSERT INTO indicators (
                    symbol, indicator_type, value, period, level, 
                    timestamp, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (symbol, indicator_type, period, timestamp) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    level = EXCLUDED.level,
                    metadata = EXCLUDED.metadata
            """
            
            params = (
                indicator.symbol,
                indicator.indicator_type.value,
                float(indicator.value),
                indicator.period,
                indicator.level.value,
                indicator.timestamp,
                json.dumps(indicator.metadata or {})
            )
            
            await self.db_manager.execute_command(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Error saving indicator: {e}")
            return False
    
    async def save_indicators_batch(self, indicators: List[IndicatorData]) -> int:
        """Сохранить пакет индикаторов"""
        if not indicators:
            return 0
        
        try:
            query = """
                INSERT INTO indicators (
                    symbol, indicator_type, value, period, level, 
                    timestamp, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (symbol, indicator_type, period, timestamp) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    level = EXCLUDED.level,
                    metadata = EXCLUDED.metadata
            """
            
            params_list = []
            for indicator in indicators:
                params_list.append((
                    indicator.symbol,
                    indicator.indicator_type.value,
                    float(indicator.value),
                    indicator.period,
                    indicator.level.value,
                    indicator.timestamp,
                    json.dumps(indicator.metadata or {})
                ))
            
            await self.db_manager.execute_many(query, params_list)
            return len(indicators)
            
        except Exception as e:
            logger.error(f"Error saving indicators batch: {e}")
            return 0
    
    async def get_latest_indicator(
        self,
        symbol: str,
        indicator_type: IndicatorType,
        period: Optional[int] = None,
        level: Optional[IndicatorLevel] = None
    ) -> Optional[IndicatorData]:
        """Получить последний индикатор"""
        try:
            query = """
                SELECT symbol, indicator_type, value, period, level, 
                       timestamp, created_at, metadata
                FROM indicators
                WHERE symbol = $1 AND indicator_type = $2
            """
            params = [symbol, indicator_type.value]
            
            if period is not None:
                query += " AND period = $3"
                params.append(period)
            
            if level is not None:
                param_index = len(params) + 1
                query += f" AND level = ${param_index}"
                params.append(level.value)
            
            query += " ORDER BY timestamp DESC LIMIT 1"
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            if not rows:
                return None
            
            return self._row_to_indicator(rows[0])
            
        except Exception as e:
            logger.error(f"Error getting latest indicator: {e}")
            return None
    
    async def get_indicators_range(
        self,
        symbol: str,
        indicator_type: IndicatorType,
        start_timestamp: int,
        end_timestamp: int,
        period: Optional[int] = None,
        level: Optional[IndicatorLevel] = None,
        limit: Optional[int] = None
    ) -> List[IndicatorData]:
        """Получить индикаторы за период"""
        try:
            query = """
                SELECT symbol, indicator_type, value, period, level, 
                       timestamp, created_at, metadata
                FROM indicators
                WHERE symbol = $1 AND indicator_type = $2 
                  AND timestamp >= $3 AND timestamp <= $4
            """
            params = [symbol, indicator_type.value, start_timestamp, end_timestamp]
            param_index = 5
            
            if period is not None:
                query += f" AND period = ${param_index}"
                params.append(period)
                param_index += 1
            
            if level is not None:
                query += f" AND level = ${param_index}"
                params.append(level.value)
                param_index += 1
            
            query += " ORDER BY timestamp ASC"
            
            if limit is not None:
                query += f" LIMIT ${param_index}"
                params.append(limit)
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            return [self._row_to_indicator(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting indicators range: {e}")
            return []
    
    async def get_indicators_by_symbol(
        self,
        symbol: str,
        level: Optional[IndicatorLevel] = None,
        limit: Optional[int] = None
    ) -> List[IndicatorData]:
        """Получить все индикаторы по символу"""
        try:
            query = """
                SELECT symbol, indicator_type, value, period, level, 
                       timestamp, created_at, metadata
                FROM indicators
                WHERE symbol = $1
            """
            params = [symbol]
            param_index = 2
            
            if level is not None:
                query += f" AND level = ${param_index}"
                params.append(level.value)
                param_index += 1
            
            query += " ORDER BY timestamp DESC"
            
            if limit is not None:
                query += f" LIMIT ${param_index}"
                params.append(limit)
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            return [self._row_to_indicator(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting indicators by symbol: {e}")
            return []
    
    async def get_latest_indicators_by_symbol(
        self,
        symbol: str,
        level: Optional[IndicatorLevel] = None
    ) -> Dict[str, IndicatorData]:
        """Получить последние индикаторы каждого типа для символа"""
        try:
            # Используем представление из схемы
            query = """
                SELECT symbol, indicator_type, value, period, level, 
                       timestamp, created_at
                FROM latest_indicators_view
                WHERE symbol = $1
            """
            params = [symbol]
            
            if level is not None:
                query += " AND level = $2"
                params.append(level.value)
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            result = {}
            for row in rows:
                indicator = self._row_to_indicator(row)
                key = f"{indicator.indicator_type.value}_{indicator.period or 0}"
                result[key] = indicator
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting latest indicators by symbol: {e}")
            return {}
    
    async def delete_old_indicators(
        self,
        symbol: str,
        before_timestamp: int,
        level: Optional[IndicatorLevel] = None
    ) -> int:
        """Удалить старые индикаторы"""
        try:
            query = """
                DELETE FROM indicators
                WHERE symbol = $1 AND timestamp < $2
            """
            params = [symbol, before_timestamp]
            
            if level is not None:
                query += " AND level = $3"
                params.append(level.value)
            
            return await self.db_manager.execute_command(query, tuple(params))
            
        except Exception as e:
            logger.error(f"Error deleting old indicators: {e}")
            return 0
    
    async def cleanup_old_indicators(self, days_to_keep: int = 30) -> int:
        """Очистка старых индикаторов"""
        try:
            # Используем функцию из схемы
            result = await self.db_manager.execute_query(
                "SELECT cleanup_old_indicators($1)",
                (days_to_keep,)
            )
            
            return result[0]['cleanup_old_indicators'] if result else 0
            
        except Exception as e:
            logger.error(f"Error cleaning up old indicators: {e}")
            return 0
    
    async def get_indicator_statistics(
        self,
        symbol: str,
        indicator_type: IndicatorType,
        period: Optional[int] = None
    ) -> Dict[str, Any]:
        """Получить статистику по индикатору"""
        try:
            query = """
                SELECT 
                    COUNT(*) as count,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    AVG(value) as avg_value,
                    STDDEV(value) as stddev_value,
                    MIN(timestamp) as first_timestamp,
                    MAX(timestamp) as last_timestamp
                FROM indicators
                WHERE symbol = $1 AND indicator_type = $2
            """
            params = [symbol, indicator_type.value]
            
            if period is not None:
                query += " AND period = $3"
                params.append(period)
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            if not rows or rows[0]['count'] == 0:
                return {}
            
            row = rows[0]
            return {
                'count': int(row['count']),
                'min_value': float(row['min_value']) if row['min_value'] is not None else None,
                'max_value': float(row['max_value']) if row['max_value'] is not None else None,
                'avg_value': float(row['avg_value']) if row['avg_value'] is not None else None,
                'stddev_value': float(row['stddev_value']) if row['stddev_value'] is not None else None,
                'first_timestamp': int(row['first_timestamp']) if row['first_timestamp'] is not None else None,
                'last_timestamp': int(row['last_timestamp']) if row['last_timestamp'] is not None else None,
                'time_range_hours': (
                    (int(row['last_timestamp']) - int(row['first_timestamp'])) / (1000 * 60 * 60)
                    if row['first_timestamp'] and row['last_timestamp'] else 0
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting indicator statistics: {e}")
            return {}
    
    def _row_to_indicator(self, row: Dict[str, Any]) -> IndicatorData:
        """Преобразовать строку БД в объект IndicatorData"""
        try:
            metadata = row.get('metadata', '{}')
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            elif metadata is None:
                metadata = {}
            
            return IndicatorData(
                symbol=row['symbol'],
                timestamp=int(row['timestamp']),
                indicator_type=IndicatorType(row['indicator_type']),
                value=float(row['value']),
                period=row.get('period'),
                level=IndicatorLevel(row.get('level', 'fast')),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error converting row to IndicatorData: {e}")
            logger.debug(f"Row data: {row}")
            raise