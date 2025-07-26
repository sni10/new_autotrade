import logging
from typing import Dict, Any, Optional
from src.domain.repositories.i_stream_data_repository import IStreamDataRepository

logger = logging.getLogger(__name__)


class TickerProcessor:
    """
    Сервис для обработки и валидации тикеров.
    Соблюдает принцип единственной ответственности (SRP).
    Отвечает ТОЛЬКО за получение и первичную обработку данных тикеров.
    """
    
    def __init__(self, stream_repository: IStreamDataRepository):
        self.stream_repository = stream_repository
        self._stats = {
            "processed_tickers": 0,
            "invalid_tickers": 0,
            "validation_errors": 0
        }
    
    async def process_ticker(self, symbol: str, ticker_data: Dict[str, Any]) -> bool:
        """
        Обработать и сохранить данные тикера после валидации
        
        Args:
            symbol: Торговая пара
            ticker_data: Сырые данные тикера
            
        Returns:
            bool: True если тикер успешно обработан, False если ошибка
        """
        try:
            # 1. Валидация данных тикера
            if not self._validate_ticker_data(ticker_data):
                self._stats["invalid_tickers"] += 1
                return False
            
            # 2. Нормализация данных
            normalized_data = self._normalize_ticker_data(ticker_data)
            
            # 3. Сохранение в потоковый репозиторий
            await self.stream_repository.append_ticker_data(symbol, normalized_data)
            
            self._stats["processed_tickers"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error processing ticker for {symbol}: {e}")
            self._stats["validation_errors"] += 1
            return False
    
    def _validate_ticker_data(self, ticker_data: Dict[str, Any]) -> bool:
        """Валидация данных тикера"""
        required_fields = ['close', 'timestamp']
        
        # Проверка обязательных полей
        for field in required_fields:
            if field not in ticker_data:
                logger.warning(f"Missing required field '{field}' in ticker data")
                return False
        
        # Проверка типов данных
        try:
            price = float(ticker_data['close'])
            timestamp = int(ticker_data['timestamp'])
            
            # Проверка разумности значений
            if price <= 0:
                logger.warning(f"Invalid price value: {price}")
                return False
                
            if timestamp <= 0:
                logger.warning(f"Invalid timestamp value: {timestamp}")
                return False
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid data types in ticker: {e}")
            return False
        
        return True
    
    def _normalize_ticker_data(self, ticker_data: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализация данных тикера"""
        normalized = {
            'timestamp': int(ticker_data['timestamp']),
            'close': float(ticker_data['close']),
        }
        
        # Добавляем дополнительные поля если они есть
        optional_fields = ['open', 'high', 'low', 'volume', 'quoteVolume']
        for field in optional_fields:
            if field in ticker_data:
                try:
                    normalized[field] = float(ticker_data[field])
                except (ValueError, TypeError):
                    logger.debug(f"Could not convert {field} to float: {ticker_data[field]}")
        
        return normalized
    
    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """Получить последнюю цену для символа"""
        try:
            latest_ticker = await self.stream_repository.get_latest_ticker(symbol)
            if latest_ticker and 'close' in latest_ticker:
                return float(latest_ticker['close'])
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {e}")
            return None
    
    async def get_ticker_count(self, symbol: str) -> int:
        """Получить количество обработанных тикеров для символа"""
        try:
            stats = await self.stream_repository.get_data_stats(symbol)
            return stats.get('ticker_count', 0)
            
        except Exception as e:
            logger.error(f"Error getting ticker count for {symbol}: {e}")
            return 0
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Получить статистику обработки"""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Сбросить статистику"""
        self._stats = {
            "processed_tickers": 0,
            "invalid_tickers": 0,
            "validation_errors": 0
        }