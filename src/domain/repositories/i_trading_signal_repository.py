from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.domain.entities.trading_signal import TradingSignal, SignalType, SignalSource


class ITradingSignalRepository(ABC):
    """Интерфейс репозитория для сохранения и извлечения торговых сигналов"""
    
    @abstractmethod
    async def save(self, signal: TradingSignal) -> None:
        """Сохранить торговый сигнал"""
        pass
    
    @abstractmethod
    async def save_batch(self, signals: List[TradingSignal]) -> None:
        """Сохранить пакет сигналов"""
        pass
    
    @abstractmethod
    async def get_by_id(self, signal_id: str) -> Optional[TradingSignal]:
        """Получить сигнал по ID"""
        pass
    
    @abstractmethod
    async def get_by_symbol(self, symbol: str, limit: int = 100) -> List[TradingSignal]:
        """Получить сигналы по символу"""
        pass
    
    @abstractmethod
    async def get_latest(self, symbol: str) -> Optional[TradingSignal]:
        """Получить последний сигнал для символа"""
        pass
    
    @abstractmethod
    async def get_by_type(
        self, 
        symbol: str, 
        signal_type: SignalType,
        limit: int = 100
    ) -> List[TradingSignal]:
        """Получить сигналы по типу"""
        pass
    
    @abstractmethod
    async def get_by_source(
        self, 
        symbol: str, 
        source: SignalSource,
        limit: int = 100
    ) -> List[TradingSignal]:
        """Получить сигналы по источнику"""
        pass
    
    @abstractmethod
    async def get_actionable_signals(
        self, 
        symbol: str,
        min_confidence: float = 0.6,
        min_strength: float = 0.3,
        limit: int = 50
    ) -> List[TradingSignal]:
        """Получить сигналы, по которым можно действовать"""
        pass
    
    @abstractmethod
    async def get_by_time_range(
        self, 
        symbol: str,
        start_timestamp: int,
        end_timestamp: int,
        signal_type: Optional[SignalType] = None
    ) -> List[TradingSignal]:
        """Получить сигналы за период времени"""
        pass
    
    @abstractmethod
    async def get_conflicting_signals(
        self, 
        symbol: str,
        time_window_ms: int = 60000  # 1 минута
    ) -> List[List[TradingSignal]]:
        """Найти конфликтующие сигналы в временном окне"""
        pass
    
    @abstractmethod
    async def get_combined_signals(
        self, 
        symbol: str,
        limit: int = 50
    ) -> List[TradingSignal]:
        """Получить комбинированные сигналы"""
        pass
    
    @abstractmethod
    async def get_signal_statistics(
        self, 
        symbol: str,
        time_window_ms: int = 86400000  # 24 часа
    ) -> Dict[str, Any]:
        """Получить статистику сигналов за период"""
        pass
    
    @abstractmethod
    async def delete_old(self, symbol: str, older_than_timestamp: int) -> int:
        """Удалить старые сигналы (возвращает количество удаленных)"""
        pass
    
    @abstractmethod
    async def count_by_symbol(self, symbol: str) -> int:
        """Подсчитать количество сигналов для символа"""
        pass
    
    @abstractmethod
    async def get_all_symbols(self) -> List[str]:
        """Получить все символы, для которых есть сигналы"""
        pass