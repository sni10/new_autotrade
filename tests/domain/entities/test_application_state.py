import pytest
import time
from datetime import datetime

from src.domain.entities.application_state import (
    ApplicationState, ApplicationStateInfo, SystemSnapshot,
    RecoveryInfo, StateTransition, TradingSessionState, ShutdownReason
)


class TestApplicationState:
    """Тесты для ApplicationState enum"""
    
    def test_application_states_exist(self):
        """Тест наличия всех состояний приложения"""
        assert ApplicationState.STARTING
        assert ApplicationState.RUNNING
        assert ApplicationState.PAUSING
        assert ApplicationState.PAUSED
        assert ApplicationState.STOPPING
        assert ApplicationState.STOPPED
        assert ApplicationState.ERROR
        assert ApplicationState.RECOVERY
    
    def test_application_state_values(self):
        """Тест значений состояний"""
        assert ApplicationState.STARTING.value == "starting"
        assert ApplicationState.RUNNING.value == "running"
        assert ApplicationState.ERROR.value == "error"


class TestShutdownReason:
    """Тесты для ShutdownReason enum"""
    
    def test_shutdown_reasons_exist(self):
        """Тест наличия всех причин остановки"""
        assert ShutdownReason.USER_REQUEST
        assert ShutdownReason.GRACEFUL_SHUTDOWN
        assert ShutdownReason.ERROR_SHUTDOWN
        assert ShutdownReason.EMERGENCY_STOP
        assert ShutdownReason.SYSTEM_SIGNAL
        assert ShutdownReason.MAINTENANCE
    
    def test_shutdown_reason_values(self):
        """Тест значений причин остановки"""
        assert ShutdownReason.USER_REQUEST.value == "user_request"
        assert ShutdownReason.GRACEFUL_SHUTDOWN.value == "graceful_shutdown"
        assert ShutdownReason.EMERGENCY_STOP.value == "emergency_stop"


class TestTradingSessionState:
    """Тесты для TradingSessionState"""
    
    def test_create_trading_session_state(self):
        """Тест создания состояния торговой сессии"""
        timestamp = int(time.time() * 1000)
        metadata = {"strategy": "scalping", "leverage": 1.0}
        
        session = TradingSessionState(
            session_id="session_001",
            currency_pair="BTCUSDT",
            is_active=True,
            start_timestamp=timestamp,
            last_activity_timestamp=timestamp,
            active_deals_count=3,
            open_orders_count=5,
            total_profit=125.50,
            total_fees=2.75,
            processed_tickers=1000,
            generated_signals=15,
            metadata=metadata
        )
        
        assert session.session_id == "session_001"
        assert session.currency_pair == "BTCUSDT"
        assert session.is_active is True
        assert session.start_timestamp == timestamp
        assert session.last_activity_timestamp == timestamp
        assert session.active_deals_count == 3
        assert session.open_orders_count == 5
        assert session.total_profit == 125.50
        assert session.total_fees == 2.75
        assert session.processed_tickers == 1000
        assert session.generated_signals == 15
        assert session.metadata == metadata
    
    def test_trading_session_state_defaults(self):
        """Тест значений по умолчанию для торговой сессии"""
        timestamp = int(time.time() * 1000)
        
        session = TradingSessionState(
            session_id="session_002",
            currency_pair="ETHUSDT",
            is_active=False,
            start_timestamp=timestamp,
            last_activity_timestamp=timestamp,
            active_deals_count=0,
            open_orders_count=0
        )
        
        assert session.total_profit == 0.0
        assert session.total_fees == 0.0
        assert session.processed_tickers == 0
        assert session.generated_signals == 0
        assert session.metadata == {}


class TestSystemSnapshot:
    """Тесты для SystemSnapshot"""
    
    def test_create_system_snapshot(self):
        """Тест создания снимка системы"""
        timestamp = int(time.time() * 1000)
        
        # Создаем торговые сессии
        sessions = [
            TradingSessionState(
                "session_1", "BTCUSDT", True, timestamp, timestamp, 2, 3
            ),
            TradingSessionState(
                "session_2", "ETHUSDT", True, timestamp, timestamp, 1, 2
            )
        ]
        
        # Создаем данные о сделках и ордерах
        active_deals = [
            {"deal_id": "deal_1", "symbol": "BTCUSDT", "status": "ACTIVE"},
            {"deal_id": "deal_2", "symbol": "ETHUSDT", "status": "WAITING_SELL"}
        ]
        
        pending_orders = [
            {"order_id": "order_1", "symbol": "BTCUSDT", "side": "BUY"},
            {"order_id": "order_2", "symbol": "ETHUSDT", "side": "SELL"}
        ]
        
        system_metrics = {
            "uptime_seconds": 3600,
            "memory_usage_mb": 128.5,
            "active_connections": 5
        }
        
        snapshot = SystemSnapshot(
            snapshot_id="test_snapshot_1",
            timestamp=timestamp,
            application_state=ApplicationState.RUNNING,
            trading_sessions=sessions,
            active_deals=active_deals,
            pending_orders=pending_orders,
            system_metrics=system_metrics,
            configuration_checksum="abc123",
            error_info=None
        )
        
        assert snapshot.timestamp == timestamp
        assert snapshot.application_state == ApplicationState.RUNNING
        assert len(snapshot.trading_sessions) == 2
        assert len(snapshot.active_deals) == 2
        assert len(snapshot.pending_orders) == 2
        assert snapshot.system_metrics == system_metrics
        assert snapshot.configuration_checksum == "abc123"
        assert snapshot.error_info is None
    
    def test_system_snapshot_defaults(self):
        """Тест значений по умолчанию для снимка системы"""
        timestamp = int(time.time() * 1000)
        
        snapshot = SystemSnapshot(
            snapshot_id="test_snapshot_1",
            timestamp=timestamp,
            application_state=ApplicationState.STARTING
        )
        
        assert snapshot.trading_sessions == []
        assert snapshot.active_deals == []
        assert snapshot.pending_orders == []
        assert snapshot.system_metrics == {}
        assert snapshot.configuration_checksum is None
        assert snapshot.error_info is None


class TestRecoveryInfo:
    """Тесты для RecoveryInfo"""
    
    def test_create_recovery_info(self):
        """Тест создания информации для восстановления"""
        timestamp = int(time.time() * 1000)
        metadata = {"auto_generated": True, "source": "periodic_snapshot"}
        
        recovery = RecoveryInfo(
            snapshot_id="snapshot_001",
            created_at=timestamp,
            application_version="2.4.0",
            recovery_priority=1,
            recovery_notes="High priority recovery point",
            validation_status="validated",
            metadata=metadata
        )
        
        assert recovery.snapshot_id == "snapshot_001"
        assert recovery.created_at == timestamp
        assert recovery.application_version == "2.4.0"
        assert recovery.recovery_priority == 1
        assert recovery.recovery_notes == "High priority recovery point"
        assert recovery.validation_status == "validated"
        assert recovery.metadata == metadata
    
    def test_recovery_info_defaults(self):
        """Тест значений по умолчанию для информации восстановления"""
        timestamp = int(time.time() * 1000)
        
        recovery = RecoveryInfo(
            snapshot_id="snapshot_002",
            created_at=timestamp,
            application_version="2.4.0"
        )
        
        assert recovery.recovery_priority == 1
        assert recovery.recovery_notes is None
        assert recovery.validation_status is None
        assert recovery.metadata == {}


class TestStateTransition:
    """Тесты для StateTransition"""
    
    def test_create_state_transition(self):
        """Тест создания перехода состояний"""
        timestamp = int(time.time() * 1000)
        metadata = {"user_id": "admin", "reason_code": "USER_INITIATED"}
        
        transition = StateTransition(
            from_state=ApplicationState.RUNNING,
            to_state=ApplicationState.PAUSED,
            timestamp=timestamp,
            reason="User requested pause",
            success=True,
            duration_ms=250,
            error_message=None,
            metadata=metadata
        )
        
        assert transition.from_state == ApplicationState.RUNNING
        assert transition.to_state == ApplicationState.PAUSED
        assert transition.timestamp == timestamp
        assert transition.reason == "User requested pause"
        assert transition.success is True
        assert transition.duration_ms == 250
        assert transition.error_message is None
        assert transition.metadata == metadata
    
    def test_failed_state_transition(self):
        """Тест неудачного перехода состояний"""
        timestamp = int(time.time() * 1000)
        
        transition = StateTransition(
            from_state=ApplicationState.RUNNING,
            to_state=ApplicationState.STOPPED,
            timestamp=timestamp,
            reason="Emergency shutdown",
            success=False,
            error_message="Failed to save state"
        )
        
        assert transition.success is False
        assert transition.error_message == "Failed to save state"
        assert transition.duration_ms is None
        assert transition.metadata == {}


class TestApplicationStateInfo:
    """Тесты для ApplicationStateInfo"""
    
    def test_create_application_state_info(self):
        """Тест создания информации о состоянии приложения"""
        current_time = int(time.time() * 1000)
        error_info = {"error_type": "ConnectionError", "message": "Database timeout"}
        
        state_info = ApplicationStateInfo(
            current_state=ApplicationState.RUNNING,
            previous_state=ApplicationState.STARTING,
            state_changed_at=current_time,
            uptime_seconds=3600,
            restart_count=2,
            last_shutdown_reason=ShutdownReason.GRACEFUL_SHUTDOWN,
            last_error=error_info,
            trading_active=True,
            maintenance_mode=False,
            safe_shutdown_requested=False,
            emergency_stop_active=False,
            session_start_time=current_time - 3600000,
            deals_processed=50,
            orders_processed=125,
            errors_count=3
        )
        
        assert state_info.current_state == ApplicationState.RUNNING
        assert state_info.previous_state == ApplicationState.STARTING
        assert state_info.state_changed_at == current_time
        assert state_info.uptime_seconds == 3600
        assert state_info.restart_count == 2
        assert state_info.last_shutdown_reason == ShutdownReason.GRACEFUL_SHUTDOWN
        assert state_info.last_error == error_info
        assert state_info.trading_active is True
        assert state_info.maintenance_mode is False
        assert state_info.safe_shutdown_requested is False
        assert state_info.emergency_stop_active is False
        assert state_info.session_start_time == current_time - 3600000
        assert state_info.deals_processed == 50
        assert state_info.orders_processed == 125
        assert state_info.errors_count == 3
    
    def test_application_state_info_defaults(self):
        """Тест значений по умолчанию для информации о состоянии"""
        state_info = ApplicationStateInfo(
            current_state=ApplicationState.STARTING
        )
        
        assert state_info.current_state == ApplicationState.STARTING
        assert state_info.previous_state is None
        assert state_info.state_changed_at is None
        assert state_info.uptime_seconds == 0
        assert state_info.restart_count == 0
        assert state_info.last_shutdown_reason is None
        assert state_info.last_error is None
        assert state_info.trading_active is False
        assert state_info.maintenance_mode is False
        assert state_info.safe_shutdown_requested is False
        assert state_info.emergency_stop_active is False
        assert state_info.session_start_time is None
        assert state_info.deals_processed == 0
        assert state_info.orders_processed == 0
        assert state_info.errors_count == 0
    
    def test_to_dict(self):
        """Тест сериализации в словарь"""
        current_time = int(time.time() * 1000)
        error_info = {"error_type": "ValidationError", "details": "Invalid config"}
        
        state_info = ApplicationStateInfo(
            current_state=ApplicationState.ERROR,
            previous_state=ApplicationState.RUNNING,
            state_changed_at=current_time,
            uptime_seconds=1800,
            restart_count=1,
            last_shutdown_reason=ShutdownReason.ERROR_SHUTDOWN,
            last_error=error_info,
            trading_active=False,
            maintenance_mode=True,
            safe_shutdown_requested=True,
            emergency_stop_active=False,
            session_start_time=current_time - 1800000,
            deals_processed=25,
            orders_processed=75,
            errors_count=5
        )
        
        data = state_info.to_dict()
        
        assert data['current_state'] == "error"
        assert data['previous_state'] == "running"
        assert data['state_changed_at'] == current_time
        assert data['uptime_seconds'] == 1800
        assert data['restart_count'] == 1
        assert data['last_shutdown_reason'] == "error_shutdown"
        assert data['last_error'] == error_info
        assert data['trading_active'] is False
        assert data['maintenance_mode'] is True
        assert data['safe_shutdown_requested'] is True
        assert data['emergency_stop_active'] is False
        assert data['session_start_time'] == current_time - 1800000
        assert data['deals_processed'] == 25
        assert data['orders_processed'] == 75
        assert data['errors_count'] == 5
    
    def test_to_dict_with_none_values(self):
        """Тест сериализации с None значениями"""
        state_info = ApplicationStateInfo(
            current_state=ApplicationState.STARTING
        )
        
        data = state_info.to_dict()
        
        assert data['current_state'] == "starting"
        assert data['previous_state'] is None
        assert data['state_changed_at'] is None
        assert data['last_shutdown_reason'] is None
        assert data['last_error'] is None
        assert data['session_start_time'] is None
    
    def test_from_dict(self):
        """Тест десериализации из словаря"""
        current_time = int(time.time() * 1000)
        error_info = {"error_type": "NetworkError", "retries": 3}
        
        data = {
            'current_state': 'paused',
            'previous_state': 'running',
            'state_changed_at': current_time,
            'uptime_seconds': 2400,
            'restart_count': 0,
            'last_shutdown_reason': 'user_request',
            'last_error': error_info,
            'trading_active': False,
            'maintenance_mode': False,
            'safe_shutdown_requested': True,
            'emergency_stop_active': False,
            'session_start_time': current_time - 2400000,
            'deals_processed': 15,
            'orders_processed': 45,
            'errors_count': 1
        }
        
        state_info = ApplicationStateInfo.from_dict(data)
        
        assert state_info.current_state == ApplicationState.PAUSED
        assert state_info.previous_state == ApplicationState.RUNNING
        assert state_info.state_changed_at == current_time
        assert state_info.uptime_seconds == 2400
        assert state_info.restart_count == 0
        assert state_info.last_shutdown_reason == ShutdownReason.USER_REQUEST
        assert state_info.last_error == error_info
        assert state_info.trading_active is False
        assert state_info.maintenance_mode is False
        assert state_info.safe_shutdown_requested is True
        assert state_info.emergency_stop_active is False
        assert state_info.session_start_time == current_time - 2400000
        assert state_info.deals_processed == 15
        assert state_info.orders_processed == 45
        assert state_info.errors_count == 1
    
    def test_from_dict_with_none_values(self):
        """Тест десериализации с None значениями"""
        data = {
            'current_state': 'starting',
            'previous_state': None,
            'state_changed_at': None,
            'uptime_seconds': 0,
            'restart_count': 0,
            'last_shutdown_reason': None,
            'last_error': None,
            'trading_active': False,
            'maintenance_mode': False,
            'safe_shutdown_requested': False,
            'emergency_stop_active': False,
            'session_start_time': None,
            'deals_processed': 0,
            'orders_processed': 0,
            'errors_count': 0
        }
        
        state_info = ApplicationStateInfo.from_dict(data)
        
        assert state_info.current_state == ApplicationState.STARTING
        assert state_info.previous_state is None
        assert state_info.state_changed_at is None
        assert state_info.last_shutdown_reason is None
        assert state_info.last_error is None
        assert state_info.session_start_time is None
    
    def test_from_dict_minimal(self):
        """Тест десериализации с минимальными данными"""
        data = {
            'current_state': 'running'
        }
        
        state_info = ApplicationStateInfo.from_dict(data)
        
        assert state_info.current_state == ApplicationState.RUNNING
        assert state_info.uptime_seconds == 0
        assert state_info.restart_count == 0
        assert state_info.trading_active is False