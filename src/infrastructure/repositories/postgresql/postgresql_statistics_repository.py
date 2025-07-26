import asyncio
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json

from src.domain.entities.statistics import Statistics, StatisticCategory, StatisticType
from src.domain.repositories.i_statistics_repository import IStatisticsRepository
from src.infrastructure.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PostgreSQLStatisticsRepository(IStatisticsRepository):
    """
    PostgreSQL реализация репозитория статистики
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._ensure_postgresql()
    
    def _ensure_postgresql(self):
        """Проверяем, что используется PostgreSQL"""
        if self.db_manager.db_type != 'postgresql':
            raise ValueError("PostgreSQLStatisticsRepository requires PostgreSQL database")
    
    async def save_statistic(self, statistic: Statistics) -> bool:
        """Сохранить статистику"""
        try:
            query = """
                INSERT INTO statistics (
                    metric_id, metric_name, value, category, metric_type,
                    symbol, timestamp, tags, description
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (metric_id) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    timestamp = EXCLUDED.timestamp,
                    tags = EXCLUDED.tags,
                    description = EXCLUDED.description
            """
            
            params = (
                statistic.metric_id,
                statistic.metric_name,
                str(statistic.value),
                statistic.category.value,
                statistic.metric_type.value,
                statistic.symbol,
                statistic.timestamp,
                json.dumps(statistic.tags or {}),
                statistic.description
            )
            
            await self.db_manager.execute_command(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Error saving statistic: {e}")
            return False
    
    async def update_counter(
        self,
        metric_name: str,
        category: StatisticCategory,
        increment: Union[int, float] = 1,
        symbol: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Обновить счетчик"""
        try:
            metric_id = self._generate_metric_id(metric_name, category, symbol, tags)
            
            # Пытаемся обновить существующий счетчик
            query = """
                UPDATE statistics 
                SET value = (CAST(value AS NUMERIC) + $1)::TEXT,
                    timestamp = $2,
                    tags = $3
                WHERE metric_id = $4
            """
            
            current_timestamp = int(datetime.now().timestamp() * 1000)
            result = await self.db_manager.execute_command(
                query,
                (increment, current_timestamp, json.dumps(tags or {}), metric_id)
            )
            
            # Если строка не была обновлена, создаем новую
            if result == 0:
                new_statistic = Statistics(
                    metric_id=metric_id,
                    metric_name=metric_name,
                    value=increment,
                    category=category,
                    metric_type=StatisticType.COUNTER,
                    symbol=symbol,
                    timestamp=current_timestamp,
                    tags=tags
                )
                return await self.save_statistic(new_statistic)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating counter: {e}")
            return False
    
    async def increment_counter(
        self,
        metric_name: str,
        category: StatisticCategory,
        symbol: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Увеличить счетчик на 1"""
        return await self.update_counter(metric_name, category, 1, symbol, tags)
    
    async def update_gauge(
        self,
        metric_name: str,
        category: StatisticCategory,
        value: Union[int, float],
        symbol: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> bool:
        """Обновить индикатор"""
        try:
            metric_id = self._generate_metric_id(metric_name, category, symbol, tags)
            current_timestamp = int(datetime.now().timestamp() * 1000)
            
            # Обновляем или создаем индикатор
            query = """
                INSERT INTO statistics (
                    metric_id, metric_name, value, category, metric_type,
                    symbol, timestamp, tags, description
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (metric_id) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    timestamp = EXCLUDED.timestamp,
                    tags = EXCLUDED.tags,
                    description = EXCLUDED.description
            """
            
            params = (
                metric_id,
                metric_name,
                str(value),
                category.value,
                StatisticType.GAUGE.value,
                symbol,
                current_timestamp,
                json.dumps(tags or {}),
                description
            )
            
            await self.db_manager.execute_command(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Error updating gauge: {e}")
            return False
    
    async def record_timing(
        self,
        metric_name: str,
        category: StatisticCategory,
        duration_ms: float,
        symbol: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Записать время выполнения"""
        try:
            metric_id = self._generate_metric_id(metric_name, category, symbol, tags)
            current_timestamp = int(datetime.now().timestamp() * 1000)
            
            # Сохраняем время как новую запись (не обновляем)
            timing_id = f"{metric_id}_{current_timestamp}"
            
            statistic = Statistics(
                metric_id=timing_id,
                metric_name=metric_name,
                value=duration_ms,
                category=category,
                metric_type=StatisticType.TIMING,
                symbol=symbol,
                timestamp=current_timestamp,
                tags=tags,
                description=f"Execution time: {duration_ms:.2f}ms"
            )
            
            return await self.save_statistic(statistic)
            
        except Exception as e:
            logger.error(f"Error recording timing: {e}")
            return False
    
    async def get_statistic(
        self,
        metric_name: str,
        category: StatisticCategory,
        symbol: Optional[str] = None
    ) -> Optional[Statistics]:
        """Получить статистику"""
        try:
            query = """
                SELECT metric_id, metric_name, value, category, metric_type,
                       symbol, timestamp, created_at, tags, description
                FROM statistics
                WHERE metric_name = $1 AND category = $2
            """
            params = [metric_name, category.value]
            
            if symbol is not None:
                query += " AND symbol = $3"
                params.append(symbol)
            else:
                query += " AND symbol IS NULL"
            
            query += " ORDER BY timestamp DESC LIMIT 1"
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            if not rows:
                return None
            
            return self._row_to_statistic(rows[0])
            
        except Exception as e:
            logger.error(f"Error getting statistic: {e}")
            return None
    
    async def get_statistics_by_category(
        self,
        category: StatisticCategory,
        symbol: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Statistics]:
        """Получить статистики по категории"""
        try:
            query = """
                SELECT metric_id, metric_name, value, category, metric_type,
                       symbol, timestamp, created_at, tags, description
                FROM statistics
                WHERE category = $1
            """
            params = [category.value]
            param_index = 2
            
            if symbol is not None:
                query += f" AND symbol = ${param_index}"
                params.append(symbol)
                param_index += 1
            
            query += " ORDER BY timestamp DESC"
            
            if limit is not None:
                query += f" LIMIT ${param_index}"
                params.append(limit)
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            return [self._row_to_statistic(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting statistics by category: {e}")
            return []
    
    async def get_statistics_range(
        self,
        start_timestamp: int,
        end_timestamp: int,
        category: Optional[StatisticCategory] = None,
        metric_name: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> List[Statistics]:
        """Получить статистики за период"""
        try:
            query = """
                SELECT metric_id, metric_name, value, category, metric_type,
                       symbol, timestamp, created_at, tags, description
                FROM statistics
                WHERE timestamp >= $1 AND timestamp <= $2
            """
            params = [start_timestamp, end_timestamp]
            param_index = 3
            
            if category is not None:
                query += f" AND category = ${param_index}"
                params.append(category.value)
                param_index += 1
            
            if metric_name is not None:
                query += f" AND metric_name = ${param_index}"
                params.append(metric_name)
                param_index += 1
            
            if symbol is not None:
                query += f" AND symbol = ${param_index}"
                params.append(symbol)
                param_index += 1
            
            query += " ORDER BY timestamp ASC"
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            return [self._row_to_statistic(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting statistics range: {e}")
            return []
    
    async def get_metric_summary(
        self,
        metric_name: str,
        category: StatisticCategory,
        symbol: Optional[str] = None,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """Получить сводку по метрике"""
        try:
            # Вычисляем период
            current_time = int(datetime.now().timestamp() * 1000)
            start_timestamp = current_time - (hours_back * 60 * 60 * 1000)
            
            query = """
                SELECT 
                    COUNT(*) as count,
                    MIN(CAST(value AS NUMERIC)) as min_value,
                    MAX(CAST(value AS NUMERIC)) as max_value,
                    AVG(CAST(value AS NUMERIC)) as avg_value,
                    STDDEV(CAST(value AS NUMERIC)) as stddev_value,
                    SUM(CAST(value AS NUMERIC)) as sum_value
                FROM statistics
                WHERE metric_name = $1 AND category = $2 AND timestamp >= $3
            """
            params = [metric_name, category.value, start_timestamp]
            
            if symbol is not None:
                query += " AND symbol = $4"
                params.append(symbol)
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            if not rows or rows[0]['count'] == 0:
                return {}
            
            row = rows[0]
            return {
                'metric_name': metric_name,
                'category': category.value,
                'symbol': symbol,
                'hours_analyzed': hours_back,
                'count': int(row['count']),
                'min_value': float(row['min_value']) if row['min_value'] is not None else None,
                'max_value': float(row['max_value']) if row['max_value'] is not None else None,
                'avg_value': float(row['avg_value']) if row['avg_value'] is not None else None,
                'stddev_value': float(row['stddev_value']) if row['stddev_value'] is not None else None,
                'sum_value': float(row['sum_value']) if row['sum_value'] is not None else None
            }
            
        except Exception as e:
            logger.error(f"Error getting metric summary: {e}")
            return {}
    
    async def get_all_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Получить все доступные метрики сгруппированные по категориям"""
        try:
            query = """
                SELECT DISTINCT 
                    metric_name,
                    category,
                    metric_type,
                    COUNT(*) as count,
                    MAX(timestamp) as last_updated
                FROM statistics
                GROUP BY metric_name, category, metric_type
                ORDER BY category, metric_name
            """
            
            rows = await self.db_manager.execute_query(query)
            
            # Группируем по категориям
            result = {}
            for row in rows:
                category = row['category']
                if category not in result:
                    result[category] = []
                
                result[category].append({
                    'metric_name': row['metric_name'],
                    'metric_type': row['metric_type'],
                    'count': int(row['count']),
                    'last_updated': int(row['last_updated'])
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all metrics: {e}")
            return {}
    
    async def delete_old_statistics(
        self,
        before_timestamp: int,
        category: Optional[StatisticCategory] = None
    ) -> int:
        """Удалить старую статистику"""
        try:
            query = "DELETE FROM statistics WHERE timestamp < $1"
            params = [before_timestamp]
            
            if category is not None:
                query += " AND category = $2"
                params.append(category.value)
            
            return await self.db_manager.execute_command(query, tuple(params))
            
        except Exception as e:
            logger.error(f"Error deleting old statistics: {e}")
            return 0
    
    async def cleanup_old_statistics(self, days_to_keep: int = 30) -> int:
        """Очистка старой статистики"""
        try:
            # Вычисляем временную метку
            current_time = int(datetime.now().timestamp() * 1000)
            cutoff_timestamp = current_time - (days_to_keep * 24 * 60 * 60 * 1000)
            
            return await self.delete_old_statistics(cutoff_timestamp)
            
        except Exception as e:
            logger.error(f"Error cleaning up old statistics: {e}")
            return 0
    
    async def reset_counter(
        self,
        metric_name: str,
        category: StatisticCategory,
        symbol: Optional[str] = None
    ) -> bool:
        """Сбросить счетчик"""
        return await self.update_gauge(metric_name, category, 0, symbol)
    
    def _generate_metric_id(
        self,
        metric_name: str,
        category: StatisticCategory,
        symbol: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> str:
        """Генерировать уникальный ID метрики"""
        parts = [metric_name, category.value]
        
        if symbol:
            parts.append(symbol)
        
        if tags:
            # Сортируем теги для стабильности ID
            sorted_tags = sorted(tags.items())
            tag_str = "_".join(f"{k}:{v}" for k, v in sorted_tags)
            parts.append(tag_str)
        
        return "_".join(parts)
    
    def _row_to_statistic(self, row: Dict[str, Any]) -> Statistics:
        """Преобразовать строку БД в объект Statistics"""
        try:
            tags = row.get('tags', '{}')
            if isinstance(tags, str):
                tags = json.loads(tags)
            elif tags is None:
                tags = {}
            
            # Пытаемся преобразовать значение в число, если возможно
            value = row['value']
            try:
                if '.' in str(value):
                    value = float(value)
                else:
                    value = int(value)
            except (ValueError, TypeError):
                # Оставляем как строку
                pass
            
            return Statistics(
                metric_id=row['metric_id'],
                metric_name=row['metric_name'],
                value=value,
                category=StatisticCategory(row['category']),
                metric_type=StatisticType(row['metric_type']),
                symbol=row.get('symbol'),
                timestamp=int(row['timestamp']),
                tags=tags,
                description=row.get('description')
            )
            
        except Exception as e:
            logger.error(f"Error converting row to Statistics: {e}")
            logger.debug(f"Row data: {row}")
            raise