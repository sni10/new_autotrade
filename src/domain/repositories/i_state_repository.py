from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from src.domain.entities.application_state import (
    ApplicationStateInfo, SystemSnapshot, RecoveryInfo, 
    StateTransition, TradingSessionState
)


class IStateRepository(ABC):
    """
    Интерфейс репозитория для управления состоянием приложения
    """
    
    @abstractmethod
    async def save_application_state(self, state_info: ApplicationStateInfo) -> bool:
        """Сохранить текущее состояние приложения"""
        pass
    
    @abstractmethod
    async def load_application_state(self) -> Optional[ApplicationStateInfo]:
        """Загрузить последнее состояние приложения"""
        pass
    
    @abstractmethod
    async def save_system_snapshot(self, snapshot: SystemSnapshot) -> bool:
        """Сохранить снимок системы"""
        pass
    
    @abstractmethod
    async def load_system_snapshot(self, snapshot_id: Optional[str] = None) -> Optional[SystemSnapshot]:
        """Загрузить снимок системы (последний или по ID)"""
        pass
    
    @abstractmethod
    async def get_system_snapshots(
        self, 
        limit: int = 10,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None
    ) -> List[SystemSnapshot]:
        """Получить список снимков системы"""
        pass
    
    @abstractmethod
    async def save_recovery_info(self, recovery_info: RecoveryInfo) -> bool:
        """Сохранить информацию для восстановления"""
        pass
    
    @abstractmethod
    async def get_recovery_info(self, snapshot_id: str) -> Optional[RecoveryInfo]:
        """Получить информацию для восстановления"""
        pass
    
    @abstractmethod
    async def log_state_transition(self, transition: StateTransition) -> bool:
        """Записать переход состояний"""
        pass
    
    @abstractmethod
    async def get_state_transitions(
        self,
        limit: int = 50,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None
    ) -> List[StateTransition]:
        """Получить историю переходов состояний"""
        pass
    
    @abstractmethod
    async def save_trading_session_state(self, session_state: TradingSessionState) -> bool:
        """Сохранить состояние торговой сессии"""
        pass
    
    @abstractmethod
    async def load_trading_session_state(self, session_id: str) -> Optional[TradingSessionState]:
        """Загрузить состояние торговой сессии"""
        pass
    
    @abstractmethod
    async def get_active_trading_sessions(self) -> List[TradingSessionState]:
        """Получить активные торговые сессии"""
        pass
    
    @abstractmethod
    async def cleanup_old_snapshots(self, days_to_keep: int = 30) -> int:
        """Очистить старые снимки"""
        pass
    
    @abstractmethod
    async def cleanup_old_transitions(self, days_to_keep: int = 90) -> int:
        """Очистить старые переходы состояний"""
        pass
    
    @abstractmethod
    async def get_recovery_candidates(self) -> List[RecoveryInfo]:
        """Получить кандидатов для восстановления (отсортированных по приоритету)"""
        pass