import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from src.domain.entities.trading_signal import TradingSignal, SignalType, SignalSource
from src.domain.repositories.i_trading_signal_repository import ITradingSignalRepository
from src.infrastructure.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PostgreSQLTradingSignalRepository(ITradingSignalRepository):
    """
    PostgreSQL реализация репозитория торговых сигналов
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._ensure_postgresql()
    
    def _ensure_postgresql(self):
        """Проверяем, что используется PostgreSQL"""
        if self.db_manager.db_type != 'postgresql':
            raise ValueError("PostgreSQLTradingSignalRepository requires PostgreSQL database")
    
    async def save_signal(self, signal: TradingSignal) -> bool:
        """Сохранить торговый сигнал"""
        try:
            query = """
                INSERT INTO trading_signals (
                    signal_id, symbol, signal_type, source, strength, 
                    confidence, price, timestamp, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (signal_id) 
                DO UPDATE SET 
                    signal_type = EXCLUDED.signal_type,
                    strength = EXCLUDED.strength,
                    confidence = EXCLUDED.confidence,
                    price = EXCLUDED.price,
                    metadata = EXCLUDED.metadata
            """
            
            params = (
                signal.signal_id,
                signal.symbol,
                signal.signal_type.value,
                signal.source.value,
                float(signal.strength),
                float(signal.confidence),
                float(signal.price) if signal.price else None,
                signal.timestamp,
                json.dumps(signal.metadata or {})
            )
            
            await self.db_manager.execute_command(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Error saving trading signal: {e}")
            return False
    
    async def save_signals_batch(self, signals: List[TradingSignal]) -> int:
        """Сохранить пакет торговых сигналов"""
        if not signals:
            return 0
        
        try:
            query = """
                INSERT INTO trading_signals (
                    signal_id, symbol, signal_type, source, strength, 
                    confidence, price, timestamp, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (signal_id) 
                DO UPDATE SET 
                    signal_type = EXCLUDED.signal_type,
                    strength = EXCLUDED.strength,
                    confidence = EXCLUDED.confidence,
                    price = EXCLUDED.price,
                    metadata = EXCLUDED.metadata
            """
            
            params_list = []
            for signal in signals:
                params_list.append((
                    signal.signal_id,
                    signal.symbol,
                    signal.signal_type.value,
                    signal.source.value,
                    float(signal.strength),
                    float(signal.confidence),
                    float(signal.price) if signal.price else None,
                    signal.timestamp,
                    json.dumps(signal.metadata or {})
                ))
            
            await self.db_manager.execute_many(query, params_list)
            return len(signals)
            
        except Exception as e:
            logger.error(f"Error saving signals batch: {e}")
            return 0
    
    async def get_signal_by_id(self, signal_id: str) -> Optional[TradingSignal]:
        """Получить сигнал по ID"""
        try:
            query = """
                SELECT signal_id, symbol, signal_type, source, strength, 
                       confidence, price, timestamp, created_at, metadata
                FROM trading_signals
                WHERE signal_id = $1
            """
            
            rows = await self.db_manager.execute_query(query, (signal_id,))
            
            if not rows:
                return None
            
            return self._row_to_signal(rows[0])
            
        except Exception as e:
            logger.error(f"Error getting signal by ID: {e}")
            return None
    
    async def get_latest_signals(
        self,
        symbol: str,
        source: Optional[SignalSource] = None,
        signal_type: Optional[SignalType] = None,
        limit: int = 50
    ) -> List[TradingSignal]:
        """Получить последние сигналы"""
        try:
            query = """
                SELECT signal_id, symbol, signal_type, source, strength, 
                       confidence, price, timestamp, created_at, metadata
                FROM trading_signals
                WHERE symbol = $1
            """
            params = [symbol]
            param_index = 2
            
            if source is not None:
                query += f" AND source = ${param_index}"
                params.append(source.value)
                param_index += 1
            
            if signal_type is not None:
                query += f" AND signal_type = ${param_index}"
                params.append(signal_type.value)
                param_index += 1
            
            query += f" ORDER BY timestamp DESC LIMIT ${param_index}"
            params.append(limit)
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            return [self._row_to_signal(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting latest signals: {e}")
            return []
    
    async def get_signals_range(
        self,
        symbol: str,
        start_timestamp: int,
        end_timestamp: int,
        source: Optional[SignalSource] = None,
        signal_type: Optional[SignalType] = None,
        min_strength: Optional[float] = None,
        min_confidence: Optional[float] = None
    ) -> List[TradingSignal]:
        """Получить сигналы за период"""
        try:
            query = """
                SELECT signal_id, symbol, signal_type, source, strength, 
                       confidence, price, timestamp, created_at, metadata
                FROM trading_signals
                WHERE symbol = $1 AND timestamp >= $2 AND timestamp <= $3
            """
            params = [symbol, start_timestamp, end_timestamp]
            param_index = 4
            
            if source is not None:
                query += f" AND source = ${param_index}"
                params.append(source.value)
                param_index += 1
            
            if signal_type is not None:
                query += f" AND signal_type = ${param_index}"
                params.append(signal_type.value)
                param_index += 1
            
            if min_strength is not None:
                query += f" AND strength >= ${param_index}"
                params.append(min_strength)
                param_index += 1
            
            if min_confidence is not None:
                query += f" AND confidence >= ${param_index}"
                params.append(min_confidence)
                param_index += 1
            
            query += " ORDER BY timestamp ASC"
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            return [self._row_to_signal(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting signals range: {e}")
            return []
    
    async def get_strong_signals(
        self,
        symbol: str,
        min_strength: float = 0.7,
        min_confidence: float = 0.6,
        hours_back: int = 24,
        limit: int = 100
    ) -> List[TradingSignal]:
        """Получить сильные сигналы за период"""
        try:
            # Вычисляем начальную временную метку
            current_time = int(datetime.now().timestamp() * 1000)
            start_timestamp = current_time - (hours_back * 60 * 60 * 1000)
            
            query = """
                SELECT signal_id, symbol, signal_type, source, strength, 
                       confidence, price, timestamp, created_at, metadata
                FROM trading_signals
                WHERE symbol = $1 
                  AND timestamp >= $2
                  AND strength >= $3 
                  AND confidence >= $4
                ORDER BY strength DESC, confidence DESC, timestamp DESC
                LIMIT $5
            """
            
            rows = await self.db_manager.execute_query(
                query,
                (symbol, start_timestamp, min_strength, min_confidence, limit)
            )
            
            return [self._row_to_signal(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting strong signals: {e}")
            return []
    
    async def get_signal_consensus(
        self,
        symbol: str,
        time_window_minutes: int = 30
    ) -> Dict[str, Any]:
        """Получить консенсус сигналов за временное окно"""
        try:
            # Вычисляем временное окно
            current_time = int(datetime.now().timestamp() * 1000)
            start_timestamp = current_time - (time_window_minutes * 60 * 1000)
            
            query = """
                SELECT 
                    signal_type,
                    source,
                    COUNT(*) as count,
                    AVG(strength) as avg_strength,
                    AVG(confidence) as avg_confidence,
                    MAX(strength) as max_strength,
                    MAX(confidence) as max_confidence
                FROM trading_signals
                WHERE symbol = $1 AND timestamp >= $2
                GROUP BY signal_type, source
                ORDER BY avg_strength DESC, avg_confidence DESC
            """
            
            rows = await self.db_manager.execute_query(
                query,
                (symbol, start_timestamp)
            )
            
            # Анализируем консенсус
            buy_signals = []
            sell_signals = []
            total_signals = 0
            
            for row in rows:
                signal_data = {
                    'signal_type': row['signal_type'],
                    'source': row['source'],
                    'count': int(row['count']),
                    'avg_strength': float(row['avg_strength']),
                    'avg_confidence': float(row['avg_confidence']),
                    'max_strength': float(row['max_strength']),
                    'max_confidence': float(row['max_confidence'])
                }
                
                total_signals += signal_data['count']
                
                if row['signal_type'] in ['buy', 'strong_buy', 'weak_buy']:
                    buy_signals.append(signal_data)
                elif row['signal_type'] in ['sell', 'strong_sell', 'weak_sell']:
                    sell_signals.append(signal_data)
            
            # Вычисляем общий консенсус
            buy_weight = sum(s['count'] * s['avg_strength'] * s['avg_confidence'] for s in buy_signals)
            sell_weight = sum(s['count'] * s['avg_strength'] * s['avg_confidence'] for s in sell_signals)
            
            total_weight = buy_weight + sell_weight
            consensus_direction = 'hold'
            consensus_strength = 0.0
            
            if total_weight > 0:
                if buy_weight > sell_weight:
                    consensus_direction = 'buy'
                    consensus_strength = buy_weight / total_weight
                elif sell_weight > buy_weight:
                    consensus_direction = 'sell'
                    consensus_strength = sell_weight / total_weight
            
            return {
                'symbol': symbol,
                'time_window_minutes': time_window_minutes,
                'total_signals': total_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'consensus_direction': consensus_direction,
                'consensus_strength': consensus_strength,
                'buy_weight': buy_weight,
                'sell_weight': sell_weight
            }
            
        except Exception as e:
            logger.error(f"Error getting signal consensus: {e}")
            return {}
    
    async def get_source_performance(
        self,
        source: SignalSource,
        symbol: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Получить статистику производительности источника сигналов"""
        try:
            # Вычисляем период
            current_time = int(datetime.now().timestamp() * 1000)
            start_timestamp = current_time - (days_back * 24 * 60 * 60 * 1000)
            
            query = """
                SELECT 
                    COUNT(*) as total_signals,
                    AVG(strength) as avg_strength,
                    AVG(confidence) as avg_confidence,
                    MIN(strength) as min_strength,
                    MAX(strength) as max_strength,
                    MIN(confidence) as min_confidence,
                    MAX(confidence) as max_confidence,
                    COUNT(CASE WHEN signal_type IN ('buy', 'strong_buy', 'weak_buy') THEN 1 END) as buy_signals,
                    COUNT(CASE WHEN signal_type IN ('sell', 'strong_sell', 'weak_sell') THEN 1 END) as sell_signals,
                    COUNT(CASE WHEN signal_type = 'hold' THEN 1 END) as hold_signals
                FROM trading_signals
                WHERE source = $1 AND timestamp >= $2
            """
            params = [source.value, start_timestamp]
            
            if symbol is not None:
                query += " AND symbol = $3"
                params.append(symbol)
            
            rows = await self.db_manager.execute_query(query, tuple(params))
            
            if not rows or rows[0]['total_signals'] == 0:
                return {}
            
            row = rows[0]
            total = int(row['total_signals'])
            
            return {
                'source': source.value,
                'symbol': symbol,
                'days_analyzed': days_back,
                'total_signals': total,
                'avg_strength': float(row['avg_strength']),
                'avg_confidence': float(row['avg_confidence']),
                'min_strength': float(row['min_strength']),
                'max_strength': float(row['max_strength']),
                'min_confidence': float(row['min_confidence']),
                'max_confidence': float(row['max_confidence']),
                'buy_signals': int(row['buy_signals']),
                'sell_signals': int(row['sell_signals']),
                'hold_signals': int(row['hold_signals']),
                'buy_ratio': int(row['buy_signals']) / total,
                'sell_ratio': int(row['sell_signals']) / total,
                'hold_ratio': int(row['hold_signals']) / total
            }
            
        except Exception as e:
            logger.error(f"Error getting source performance: {e}")
            return {}
    
    async def delete_old_signals(
        self,
        symbol: str,
        before_timestamp: int
    ) -> int:
        """Удалить старые сигналы"""
        try:
            query = """
                DELETE FROM trading_signals
                WHERE symbol = $1 AND timestamp < $2
            """
            
            return await self.db_manager.execute_command(query, (symbol, before_timestamp))
            
        except Exception as e:
            logger.error(f"Error deleting old signals: {e}")
            return 0
    
    async def cleanup_old_signals(self, days_to_keep: int = 14) -> int:
        """Очистка старых торговых сигналов"""
        try:
            # Используем функцию из схемы
            result = await self.db_manager.execute_query(
                "SELECT cleanup_old_trading_signals($1)",
                (days_to_keep,)
            )
            
            return result[0]['cleanup_old_trading_signals'] if result else 0
            
        except Exception as e:
            logger.error(f"Error cleaning up old signals: {e}")
            return 0
    
    async def delete_signals_by_source(
        self,
        source: SignalSource,
        symbol: Optional[str] = None
    ) -> int:
        """Удалить сигналы по источнику"""
        try:
            query = "DELETE FROM trading_signals WHERE source = $1"
            params = [source.value]
            
            if symbol is not None:
                query += " AND symbol = $2"
                params.append(symbol)
            
            return await self.db_manager.execute_command(query, tuple(params))
            
        except Exception as e:
            logger.error(f"Error deleting signals by source: {e}")
            return 0
    
    def _row_to_signal(self, row: Dict[str, Any]) -> TradingSignal:
        """Преобразовать строку БД в объект TradingSignal"""
        try:
            metadata = row.get('metadata', '{}')
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            elif metadata is None:
                metadata = {}
            
            return TradingSignal(
                signal_id=row['signal_id'],
                symbol=row['symbol'],
                signal_type=SignalType(row['signal_type']),
                source=SignalSource(row['source']),
                strength=float(row['strength']),
                confidence=float(row['confidence']),
                price=float(row['price']) if row.get('price') is not None else None,
                timestamp=int(row['timestamp']),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error converting row to TradingSignal: {e}")
            logger.debug(f"Row data: {row}")
            raise