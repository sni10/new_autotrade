import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from src.domain.entities.order_book import OrderBook, OrderBookLevel
from src.domain.repositories.i_order_book_repository import IOrderBookRepository
from src.infrastructure.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PostgreSQLOrderBookRepository(IOrderBookRepository):
    """
    PostgreSQL реализация репозитория стаканов заявок
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._ensure_postgresql()
    
    def _ensure_postgresql(self):
        """Проверяем, что используется PostgreSQL"""
        if self.db_manager.db_type != 'postgresql':
            raise ValueError("PostgreSQLOrderBookRepository requires PostgreSQL database")
    
    async def save_order_book(self, order_book: OrderBook) -> bool:
        """Сохранить стакан заявок"""
        try:
            query = """
                INSERT INTO order_books (
                    symbol, timestamp, bids, asks, spread, 
                    spread_percent, volume_imbalance
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (symbol, timestamp) 
                DO UPDATE SET 
                    bids = EXCLUDED.bids,
                    asks = EXCLUDED.asks,
                    spread = EXCLUDED.spread,
                    spread_percent = EXCLUDED.spread_percent,
                    volume_imbalance = EXCLUDED.volume_imbalance
            """
            
            # Конвертируем уровни в JSON
            bids_json = json.dumps([
                [level.price, level.volume] for level in order_book.bids
            ])
            asks_json = json.dumps([
                [level.price, level.volume] for level in order_book.asks
            ])
            
            params = (
                order_book.symbol,
                order_book.timestamp,
                bids_json,
                asks_json,
                float(order_book.spread) if order_book.spread else None,
                float(order_book.spread_percent) if order_book.spread_percent else None,
                float(order_book.volume_imbalance) if order_book.volume_imbalance else None
            )
            
            await self.db_manager.execute_command(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Error saving order book: {e}")
            return False
    
    async def save_order_books_batch(self, order_books: List[OrderBook]) -> int:
        """Сохранить пакет стаканов заявок"""
        if not order_books:
            return 0
        
        try:
            query = """
                INSERT INTO order_books (
                    symbol, timestamp, bids, asks, spread, 
                    spread_percent, volume_imbalance
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (symbol, timestamp) 
                DO UPDATE SET 
                    bids = EXCLUDED.bids,
                    asks = EXCLUDED.asks,
                    spread = EXCLUDED.spread,
                    spread_percent = EXCLUDED.spread_percent,
                    volume_imbalance = EXCLUDED.volume_imbalance
            """
            
            params_list = []
            for order_book in order_books:
                # Конвертируем уровни в JSON
                bids_json = json.dumps([
                    [level.price, level.volume] for level in order_book.bids
                ])
                asks_json = json.dumps([
                    [level.price, level.volume] for level in order_book.asks
                ])
                
                params_list.append((
                    order_book.symbol,
                    order_book.timestamp,
                    bids_json,
                    asks_json,
                    float(order_book.spread) if order_book.spread else None,
                    float(order_book.spread_percent) if order_book.spread_percent else None,
                    float(order_book.volume_imbalance) if order_book.volume_imbalance else None
                ))
            
            await self.db_manager.execute_many(query, params_list)
            return len(order_books)
            
        except Exception as e:
            logger.error(f"Error saving order books batch: {e}")
            return 0
    
    async def get_latest_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Получить последний стакан заявок"""
        try:
            query = """
                SELECT symbol, timestamp, bids, asks, spread, 
                       spread_percent, volume_imbalance, created_at
                FROM order_books
                WHERE symbol = $1
                ORDER BY timestamp DESC
                LIMIT 1
            """
            
            rows = await self.db_manager.execute_query(query, (symbol,))
            
            if not rows:
                return None
            
            return self._row_to_order_book(rows[0])
            
        except Exception as e:
            logger.error(f"Error getting latest order book: {e}")
            return None
    
    async def get_order_book_at_time(
        self,
        symbol: str,
        timestamp: int,
        tolerance_ms: int = 5000
    ) -> Optional[OrderBook]:
        """Получить стакан заявок на определенное время"""
        try:
            query = """
                SELECT symbol, timestamp, bids, asks, spread, 
                       spread_percent, volume_imbalance, created_at
                FROM order_books
                WHERE symbol = $1 
                  AND timestamp >= $2 - $3
                  AND timestamp <= $2 + $3
                ORDER BY ABS(timestamp - $2)
                LIMIT 1
            """
            
            rows = await self.db_manager.execute_query(
                query,
                (symbol, timestamp, tolerance_ms)
            )
            
            if not rows:
                return None
            
            return self._row_to_order_book(rows[0])
            
        except Exception as e:
            logger.error(f"Error getting order book at time: {e}")
            return None
    
    async def get_order_books_range(
        self,
        symbol: str,
        start_timestamp: int,
        end_timestamp: int,
        limit: Optional[int] = None
    ) -> List[OrderBook]:
        """Получить стаканы заявок за период"""
        try:
            query = """
                SELECT symbol, timestamp, bids, asks, spread, 
                       spread_percent, volume_imbalance, created_at
                FROM order_books
                WHERE symbol = $1 
                  AND timestamp >= $2 
                  AND timestamp <= $3
                ORDER BY timestamp ASC
            """
            params = [symbol, start_timestamp, end_timestamp]
            
            if limit is not None:
                query += " LIMIT $4"
                params.append(limit)
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            return [self._row_to_order_book(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting order books range: {e}")
            return []
    
    async def get_order_book_spreads(
        self,
        symbol: str,
        start_timestamp: int,
        end_timestamp: int
    ) -> List[Dict[str, Any]]:
        """Получить данные о спредах за период"""
        try:
            query = """
                SELECT timestamp, spread, spread_percent, volume_imbalance
                FROM order_books
                WHERE symbol = $1 
                  AND timestamp >= $2 
                  AND timestamp <= $3
                  AND spread IS NOT NULL
                ORDER BY timestamp ASC
            """
            
            rows = await self.db_manager.execute_query(
                query,
                (symbol, start_timestamp, end_timestamp)
            )
            
            return [
                {
                    'timestamp': int(row['timestamp']),
                    'spread': float(row['spread']),
                    'spread_percent': float(row['spread_percent']) if row['spread_percent'] else None,
                    'volume_imbalance': float(row['volume_imbalance']) if row['volume_imbalance'] else None
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting order book spreads: {e}")
            return []
    
    async def get_spread_statistics(
        self,
        symbol: str,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None
    ) -> Dict[str, Any]:
        """Получить статистику по спредам"""
        try:
            query = """
                SELECT 
                    COUNT(*) as count,
                    MIN(spread) as min_spread,
                    MAX(spread) as max_spread,
                    AVG(spread) as avg_spread,
                    STDDEV(spread) as stddev_spread,
                    MIN(spread_percent) as min_spread_percent,
                    MAX(spread_percent) as max_spread_percent,
                    AVG(spread_percent) as avg_spread_percent,
                    AVG(volume_imbalance) as avg_volume_imbalance
                FROM order_books
                WHERE symbol = $1 AND spread IS NOT NULL
            """
            params = [symbol]
            
            if start_timestamp is not None:
                query += " AND timestamp >= $2"
                params.append(start_timestamp)
                
                if end_timestamp is not None:
                    query += " AND timestamp <= $3"
                    params.append(end_timestamp)
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            if not rows or rows[0]['count'] == 0:
                return {}
            
            row = rows[0]
            return {
                'count': int(row['count']),
                'min_spread': float(row['min_spread']) if row['min_spread'] is not None else None,
                'max_spread': float(row['max_spread']) if row['max_spread'] is not None else None,
                'avg_spread': float(row['avg_spread']) if row['avg_spread'] is not None else None,
                'stddev_spread': float(row['stddev_spread']) if row['stddev_spread'] is not None else None,
                'min_spread_percent': float(row['min_spread_percent']) if row['min_spread_percent'] is not None else None,
                'max_spread_percent': float(row['max_spread_percent']) if row['max_spread_percent'] is not None else None,
                'avg_spread_percent': float(row['avg_spread_percent']) if row['avg_spread_percent'] is not None else None,
                'avg_volume_imbalance': float(row['avg_volume_imbalance']) if row['avg_volume_imbalance'] is not None else None
            }
            
        except Exception as e:
            logger.error(f"Error getting spread statistics: {e}")
            return {}
    
    async def delete_old_order_books(
        self,
        symbol: str,
        before_timestamp: int
    ) -> int:
        """Удалить старые стаканы заявок"""
        try:
            query = """
                DELETE FROM order_books
                WHERE symbol = $1 AND timestamp < $2
            """
            
            return await self.db_manager.execute_command(query, (symbol, before_timestamp))
            
        except Exception as e:
            logger.error(f"Error deleting old order books: {e}")
            return 0
    
    async def cleanup_old_order_books(self, days_to_keep: int = 7) -> int:
        """Очистка старых стаканов заявок"""
        try:
            query = """
                DELETE FROM order_books
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """
            
            return await self.db_manager.execute_command(query % days_to_keep)
            
        except Exception as e:
            logger.error(f"Error cleaning up old order books: {e}")
            return 0
    
    async def get_liquidity_analysis(
        self,
        symbol: str,
        depth_levels: int = 10,
        latest_only: bool = True
    ) -> Dict[str, Any]:
        """Анализ ликвидности стакана"""
        try:
            if latest_only:
                order_book = await self.get_latest_order_book(symbol)
                if not order_book:
                    return {}
                
                order_books = [order_book]
            else:
                # Получаем последние 100 стаканов для анализа
                query = """
                    SELECT symbol, timestamp, bids, asks, spread, 
                           spread_percent, volume_imbalance, created_at
                    FROM order_books
                    WHERE symbol = $1
                    ORDER BY timestamp DESC
                    LIMIT 100
                """
                
                rows = await self.db_manager.execute_query(query, (symbol,))
                order_books = [self._row_to_order_book(row) for row in rows]
            
            if not order_books:
                return {}
            
            # Анализируем ликвидность
            total_bid_volume = 0
            total_ask_volume = 0
            spreads = []
            
            for ob in order_books:
                # Суммируем объемы на указанной глубине
                bid_volume = sum(level.volume for level in ob.bids[:depth_levels])
                ask_volume = sum(level.volume for level in ob.asks[:depth_levels])
                
                total_bid_volume += bid_volume
                total_ask_volume += ask_volume
                
                if ob.spread_percent is not None:
                    spreads.append(ob.spread_percent)
            
            avg_bid_volume = total_bid_volume / len(order_books)
            avg_ask_volume = total_ask_volume / len(order_books)
            avg_spread = sum(spreads) / len(spreads) if spreads else 0
            
            return {
                'symbol': symbol,
                'samples_count': len(order_books),
                'depth_levels': depth_levels,
                'avg_bid_volume': avg_bid_volume,
                'avg_ask_volume': avg_ask_volume,
                'total_avg_volume': avg_bid_volume + avg_ask_volume,
                'volume_imbalance': (avg_bid_volume - avg_ask_volume) / (avg_bid_volume + avg_ask_volume) if (avg_bid_volume + avg_ask_volume) > 0 else 0,
                'avg_spread_percent': avg_spread,
                'liquidity_score': self._calculate_liquidity_score(avg_bid_volume + avg_ask_volume, avg_spread)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing liquidity: {e}")
            return {}
    
    def _calculate_liquidity_score(self, total_volume: float, spread_percent: float) -> float:
        """Вычислить оценку ликвидности (0-100)"""
        try:
            if total_volume <= 0 or spread_percent <= 0:
                return 0
            
            # Нормализуем объем (логарифмическая шкала)
            volume_score = min(100, max(0, 50 + 10 * (total_volume / 1000)))
            
            # Инвертируем спред (меньше спред = лучше)
            spread_score = max(0, 100 - spread_percent * 20)
            
            # Взвешенная оценка
            return (volume_score * 0.6 + spread_score * 0.4)
            
        except Exception as e:
            logger.error(f"Error calculating liquidity score: {e}")
            return 0
    
    def _row_to_order_book(self, row: Dict[str, Any]) -> OrderBook:
        """Преобразовать строку БД в объект OrderBook"""
        try:
            # Парсим JSON данные
            bids_data = json.loads(row['bids']) if isinstance(row['bids'], str) else row['bids']
            asks_data = json.loads(row['asks']) if isinstance(row['asks'], str) else row['asks']
            
            # Создаем объект OrderBook
            order_book = OrderBook(
                symbol=row['symbol'],
                timestamp=int(row['timestamp']),
                bids=bids_data,
                asks=asks_data
            )
            
            # Устанавливаем дополнительные поля если они есть
            if row.get('spread') is not None:
                order_book.spread = float(row['spread'])
            if row.get('spread_percent') is not None:
                order_book.spread_percent = float(row['spread_percent'])
            if row.get('volume_imbalance') is not None:
                order_book.volume_imbalance = float(row['volume_imbalance'])
            
            return order_book
            
        except Exception as e:
            logger.error(f"Error converting row to OrderBook: {e}")
            logger.debug(f"Row data: {row}")
            raise