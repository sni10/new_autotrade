# domain/services/utils/orderbook_cache.py
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class OrderBookCache:
    """
    Простой кеш для данных стакана заявок с TTL
    """
    
    def __init__(self, ttl_seconds: int = 30):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict] = {}
        self._timestamps: Dict[str, float] = {}
    
    def get(self, symbol: str) -> Optional[Dict]:
        """Получить кешированный стакан"""
        current_time = time.time()
        
        if symbol not in self._cache:
            return None
            
        # Проверяем TTL
        if current_time - self._timestamps[symbol] > self.ttl_seconds:
            self._remove(symbol)
            return None
            
        return self._cache[symbol]
    
    def set(self, symbol: str, orderbook: Dict):
        """Сохранить стакан в кеш"""
        self._cache[symbol] = orderbook
        self._timestamps[symbol] = time.time()
        
        logger.debug(f"📦 Кешируем стакан для {symbol}")
    
    def _remove(self, symbol: str):
        """Удалить устаревший элемент из кеша"""
        if symbol in self._cache:
            del self._cache[symbol]
        if symbol in self._timestamps:
            del self._timestamps[symbol]
            
        logger.debug(f"🗑️ Удален устаревший кеш стакана для {symbol}")
    
    def clear(self):
        """Очистить весь кеш"""
        self._cache.clear()
        self._timestamps.clear()
        logger.debug("🧹 Кеш стакана полностью очищен")
    
    def get_stats(self) -> Dict:
        """Статистика кеша"""
        current_time = time.time()
        valid_entries = 0
        
        for symbol, timestamp in self._timestamps.items():
            if current_time - timestamp <= self.ttl_seconds:
                valid_entries += 1
                
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "ttl_seconds": self.ttl_seconds
        }