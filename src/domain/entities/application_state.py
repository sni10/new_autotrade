from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from src.domain.entities.deal import Deal
from src.domain.entities.order import Order


class ApplicationState(Enum):
    """Состояния приложения"""
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RECOVERY = "recovery"


class ShutdownReason(Enum):
    """Причины остановки приложения"""
    USER_REQUEST = "user_request"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"
    ERROR_SHUTDOWN = "error_shutdown"
    EMERGENCY_STOP = "emergency_stop"
    SYSTEM_SIGNAL = "system_signal"
    MAINTENANCE = "maintenance"


@dataclass
class TradingSessionState:
    """Состояние торговой сессии"""
    session_id: str
    currency_pair: str
    is_active: bool
    start_timestamp: int
    last_activity_timestamp: int
    active_deals_count: int
    open_orders_count: int
    total_profit: float = 0.0
    total_fees: float = 0.0
    processed_tickers: int = 0
    generated_signals: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemSnapshot:
    """Снимок состояния системы"""
    snapshot_id: str
    timestamp: int
    application_state: ApplicationState
    trading_sessions: List[TradingSessionState] = field(default_factory=list)
    active_deals: List[Dict[str, Any]] = field(default_factory=list)
    pending_orders: List[Dict[str, Any]] = field(default_factory=list)
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    configuration_checksum: Optional[str] = None
    error_info: Optional[Dict[str, Any]] = None


@dataclass 
class RecoveryInfo:
    """Информация для восстановления"""
    snapshot_id: str
    created_at: int
    application_version: str
    recovery_priority: int = 1  # 1=highest, 5=lowest
    recovery_notes: Optional[str] = None
    validation_status: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateTransition:
    """Переход состояний"""
    from_state: ApplicationState
    to_state: ApplicationState
    timestamp: int
    reason: str
    success: bool
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApplicationStateInfo:
    """Полная информация о состоянии приложения"""
    current_state: ApplicationState
    previous_state: Optional[ApplicationState] = None
    state_changed_at: Optional[int] = None
    uptime_seconds: int = 0
    restart_count: int = 0
    last_shutdown_reason: Optional[ShutdownReason] = None
    last_error: Optional[Dict[str, Any]] = None
    
    # Операционная информация
    trading_active: bool = False
    maintenance_mode: bool = False
    safe_shutdown_requested: bool = False
    emergency_stop_active: bool = False
    
    # Статистика сессии
    session_start_time: Optional[int] = None
    deals_processed: int = 0
    orders_processed: int = 0
    errors_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для сериализации"""
        return {
            'current_state': self.current_state.value,
            'previous_state': self.previous_state.value if self.previous_state else None,
            'state_changed_at': self.state_changed_at,
            'uptime_seconds': self.uptime_seconds,
            'restart_count': self.restart_count,
            'last_shutdown_reason': self.last_shutdown_reason.value if self.last_shutdown_reason else None,
            'last_error': self.last_error,
            'trading_active': self.trading_active,
            'maintenance_mode': self.maintenance_mode,
            'safe_shutdown_requested': self.safe_shutdown_requested,
            'emergency_stop_active': self.emergency_stop_active,
            'session_start_time': self.session_start_time,
            'deals_processed': self.deals_processed,
            'orders_processed': self.orders_processed,
            'errors_count': self.errors_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationStateInfo':
        """Создать из словаря"""
        return cls(
            current_state=ApplicationState(data['current_state']),
            previous_state=ApplicationState(data['previous_state']) if data.get('previous_state') else None,
            state_changed_at=data.get('state_changed_at'),
            uptime_seconds=data.get('uptime_seconds', 0),
            restart_count=data.get('restart_count', 0),
            last_shutdown_reason=ShutdownReason(data['last_shutdown_reason']) if data.get('last_shutdown_reason') else None,
            last_error=data.get('last_error'),
            trading_active=data.get('trading_active', False),
            maintenance_mode=data.get('maintenance_mode', False),
            safe_shutdown_requested=data.get('safe_shutdown_requested', False),
            emergency_stop_active=data.get('emergency_stop_active', False),
            session_start_time=data.get('session_start_time'),
            deals_processed=data.get('deals_processed', 0),
            orders_processed=data.get('orders_processed', 0),
            errors_count=data.get('errors_count', 0)
        )