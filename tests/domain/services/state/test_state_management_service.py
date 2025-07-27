
import pytest
import asyncio
import time
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.domain.services.state.state_management_service import StateManagementService
from src.domain.entities.application_state import (
    ApplicationState, ApplicationStateInfo, SystemSnapshot,
    RecoveryInfo, StateTransition, TradingSessionState, ShutdownReason
)
from src.infrastructure.repositories.in_memory_state_repository import InMemoryStateRepository


class MockDealsRepository:
    def __init__(self):
        self.deals = []
    async def get_active_deals(self):
        return [d for d in self.deals if d.get('status') == 'ACTIVE']

class MockOrdersRepository:
    def __init__(self):
        self.orders = []
    async def get_open_orders(self):
        return [o for o in self.orders if o.get('status') in ['OPEN', 'PENDING']]

@pytest.fixture
def state_repo():
    return InMemoryStateRepository()

@pytest.fixture
def mock_deals_repo():
    return MockDealsRepository()

@pytest.fixture
def mock_orders_repo():
    return MockOrdersRepository()

@pytest.fixture
def state_service(state_repo, mock_deals_repo, mock_orders_repo):
    service = StateManagementService(
        state_repo=state_repo,
        deals_repo=mock_deals_repo,
        orders_repo=mock_orders_repo
    )
    # Отключаем фоновые задачи для упрощения тестов
    service._periodic_snapshot_task = AsyncMock()
    service._state_monitoring_task = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_initialize_fresh_start(state_service):
    """Тест инициализации с чистого старта."""
    result = await state_service.initialize()
    assert result is True
    assert state_service.current_state == ApplicationState.RUNNING

@pytest.mark.asyncio
async def test_transition_to_state(state_service):
    """Тест перехода между состояниями."""
    await state_service.initialize()
    result = await state_service.transition_to_state(ApplicationState.PAUSED, "Test")
    assert result is True
    assert state_service.current_state == ApplicationState.PAUSED

@pytest.mark.asyncio
async def test_create_system_snapshot(state_service, mock_deals_repo, mock_orders_repo):
    """Тест создания снимка системы с данными."""
    await state_service.initialize()
    mock_deals_repo.deals = [{'deal_id': 'd1', 'status': 'ACTIVE'}]
    mock_orders_repo.orders = [{'order_id': 'o1', 'status': 'OPEN'}]
    
    snapshot_id = await state_service.create_system_snapshot("test_snapshot")
    assert snapshot_id is not None
    
    snapshot = await state_service.state_repo.load_system_snapshot(snapshot_id)
    assert snapshot is not None
    assert len(snapshot.active_deals) == 1
    assert snapshot.active_deals[0]['deal_id'] == 'd1'
    assert len(snapshot.pending_orders) == 1
    assert snapshot.pending_orders[0]['order_id'] == 'o1'

@pytest.mark.asyncio
async def test_start_and_stop_trading_session(state_service):
    """Тест запуска и остановки торговой сессии."""
    await state_service.initialize()
    session_id = await state_service.start_trading_session("BTCUSDT")
    assert session_id in state_service.trading_sessions
    assert state_service.state_info.trading_active is True
    
    result = await state_service.stop_trading_session(session_id)
    assert result is True
    assert session_id not in state_service.trading_sessions
    assert state_service.state_info.trading_active is False

@pytest.mark.asyncio
async def test_recovery_with_active_session(state_service, state_repo):
    """Тест, проверяющий необходимость восстановления при наличии активной сессии."""
    active_session = TradingSessionState(
        session_id="s1", currency_pair="BTCUSDT", is_active=True,
        start_timestamp=int(time.time() * 1000), last_activity_timestamp=int(time.time() * 1000),
        active_deals_count=0, open_orders_count=0
    )
    await state_repo.save_trading_session_state(active_session)
    
    # Этот метод теперь просто флаг, а не полная логика восстановления
    needs_recovery = await state_service._check_recovery_needed()
    assert needs_recovery is True

@pytest.mark.asyncio
async def test_error_handling_in_transition(state_service, state_repo):
    """Тест обработки ошибок при переходе состояния."""
    await state_service.initialize()
    state_repo.log_state_transition = AsyncMock(side_effect=Exception("Repo Error"))
    
    result = await state_service.transition_to_state(ApplicationState.PAUSED, "Error Test")
    
    assert result is False
    # Состояние не должно измениться, если произошла ошибка
    assert state_service.current_state == ApplicationState.RUNNING
