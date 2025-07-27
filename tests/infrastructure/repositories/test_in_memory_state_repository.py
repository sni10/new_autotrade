import pytest
import asyncio
import time
from datetime import datetime, timedelta

from src.infrastructure.repositories.in_memory_state_repository import InMemoryStateRepository
from src.domain.entities.application_state import (
    ApplicationState, ApplicationStateInfo, SystemSnapshot,
    RecoveryInfo, StateTransition, TradingSessionState, ShutdownReason
)


class TestInMemoryStateRepository:
    """Тесты для InMemoryStateRepository"""
    
    @pytest.fixture
    def repository(self):
        """Фикстура для создания репозитория"""
        return InMemoryStateRepository()
    
    @pytest.fixture
    def sample_state_info(self):
        """Фикстура с примером информации о состоянии"""
        return ApplicationStateInfo(
            current_state=ApplicationState.RUNNING,
            previous_state=ApplicationState.STARTING,
            state_changed_at=int(time.time() * 1000),
            uptime_seconds=3600,
            restart_count=1,
            trading_active=True,
            deals_processed=25,
            orders_processed=75
        )
    
    @pytest.fixture
    def sample_trading_session(self):
        """Фикстура с примером торговой сессии"""
        timestamp = int(time.time() * 1000)
        return TradingSessionState(
            session_id="session_001",
            currency_pair="BTCUSDT",
            is_active=True,
            start_timestamp=timestamp,
            last_activity_timestamp=timestamp,
            active_deals_count=2,
            open_orders_count=3,
            total_profit=125.50,
            processed_tickers=1000
        )
    
    @pytest.fixture
    def sample_system_snapshot(self, sample_trading_session):
        """Фикстура с примером снимка системы"""
        timestamp = int(time.time() * 1000)
        return SystemSnapshot(
            snapshot_id="test_snapshot_1",
            timestamp=timestamp,
            application_state=ApplicationState.RUNNING,
            trading_sessions=[sample_trading_session],
            active_deals=[
                {"deal_id": "deal_1", "symbol": "BTCUSDT", "status": "ACTIVE"}
            ],
            pending_orders=[
                {"order_id": "order_1", "symbol": "BTCUSDT", "side": "BUY"}
            ],
            system_metrics={"uptime": 3600, "memory_mb": 128.5},
            configuration_checksum="abc123"
        )
    
    @pytest.mark.asyncio
    async def test_save_and_load_application_state(self, repository, sample_state_info):
        """Тест сохранения и загрузки состояния приложения"""
        # Изначально состояние отсутствует
        loaded_state = await repository.load_application_state()
        assert loaded_state is None
        
        # Сохраняем состояние
        result = await repository.save_application_state(sample_state_info)
        assert result is True
        
        # Загружаем состояние
        loaded_state = await repository.load_application_state()
        assert loaded_state is not None
        assert loaded_state.current_state == ApplicationState.RUNNING
        assert loaded_state.previous_state == ApplicationState.STARTING
        assert loaded_state.uptime_seconds == 3600
        assert loaded_state.restart_count == 1
        assert loaded_state.trading_active is True
        assert loaded_state.deals_processed == 25
        assert loaded_state.orders_processed == 75
    
    @pytest.mark.asyncio
    async def test_update_application_state(self, repository, sample_state_info):
        """Тест обновления состояния приложения"""
        # Сохраняем первоначальное состояние
        await repository.save_application_state(sample_state_info)
        
        # Обновляем состояние
        updated_state = ApplicationStateInfo(
            current_state=ApplicationState.PAUSED,
            previous_state=ApplicationState.RUNNING,
            uptime_seconds=7200,
            deals_processed=50
        )
        
        await repository.save_application_state(updated_state)
        
        # Проверяем что состояние обновилось
        loaded_state = await repository.load_application_state()
        assert loaded_state.current_state == ApplicationState.PAUSED
        assert loaded_state.previous_state == ApplicationState.RUNNING
        assert loaded_state.uptime_seconds == 7200
        assert loaded_state.deals_processed == 50
    
    @pytest.mark.asyncio
    async def test_save_and_load_system_snapshot(self, repository, sample_system_snapshot):
        """Тест сохранения и загрузки снимка системы"""
        # Сохраняем снимок
        result = await repository.save_system_snapshot(sample_system_snapshot)
        assert result is True
        
        # Загружаем последний снимок
        loaded_snapshot = await repository.load_system_snapshot()
        assert loaded_snapshot is not None
        assert loaded_snapshot.application_state == ApplicationState.RUNNING
        assert len(loaded_snapshot.trading_sessions) == 1
        assert len(loaded_snapshot.active_deals) == 1
        assert len(loaded_snapshot.pending_orders) == 1
        assert loaded_snapshot.configuration_checksum == "abc123"
    
    @pytest.mark.asyncio
    async def test_load_system_snapshot_by_id(self, repository, sample_system_snapshot):
        """Тест загрузки снимка по ID"""
        # Сохраняем несколько снимков
        await repository.save_system_snapshot(sample_system_snapshot)
        
        # Получаем ID первого снимка
        snapshot_id = repository._snapshot_order[0]
        
        # Создаем и сохраняем второй снимок
        second_snapshot = SystemSnapshot(
            snapshot_id="test_snapshot_2",
            timestamp=int(time.time() * 1000) + 1000,
            application_state=ApplicationState.PAUSED,
            trading_sessions=[],
            active_deals=[],
            pending_orders=[],
            system_metrics={}
        )
        await repository.save_system_snapshot(second_snapshot)
        
        # Загружаем первый снимок по ID
        loaded_snapshot = await repository.load_system_snapshot(snapshot_id)
        assert loaded_snapshot is not None
        assert loaded_snapshot.application_state == ApplicationState.RUNNING
        
        # Загружаем последний снимок (без ID)
        latest_snapshot = await repository.load_system_snapshot()
        assert latest_snapshot.application_state == ApplicationState.PAUSED
    
    @pytest.mark.asyncio
    async def test_get_system_snapshots(self, repository):
        """Тест получения списка снимков"""
        # Создаем несколько снимков
        base_timestamp = int(time.time() * 1000)
        snapshots = []
        
        for i in range(5):
            snapshot = SystemSnapshot(
                snapshot_id=f"snapshot_{i}",
                timestamp=base_timestamp + i * 1000,
                application_state=ApplicationState.RUNNING,
                system_metrics={"index": i}
            )
            snapshots.append(snapshot)
            await repository.save_system_snapshot(snapshot)
        
        # Получаем все снимки
        all_snapshots = await repository.get_system_snapshots(limit=10)
        assert len(all_snapshots) == 5
        
        # Проверяем порядок (новые сначала)
        assert all_snapshots[0].timestamp > all_snapshots[1].timestamp
        
        # Получаем ограниченное количество
        limited_snapshots = await repository.get_system_snapshots(limit=3)
        assert len(limited_snapshots) == 3
        
        # Тест фильтрации по времени
        mid_timestamp = base_timestamp + 2000
        filtered_snapshots = await repository.get_system_snapshots(
            start_timestamp=mid_timestamp,
            limit=10
        )
        assert len(filtered_snapshots) == 3  # Последние 3 снимка
    
    @pytest.mark.asyncio
    async def test_save_and_get_recovery_info(self, repository):
        """Тест сохранения и получения информации восстановления"""
        recovery_info = RecoveryInfo(
            snapshot_id="snapshot_001",
            created_at=int(time.time() * 1000),
            application_version="2.4.0",
            recovery_priority=1,
            recovery_notes="High priority recovery"
        )
        
        # Сохраняем информацию
        result = await repository.save_recovery_info(recovery_info)
        assert result is True
        
        # Получаем информацию
        loaded_info = await repository.get_recovery_info("snapshot_001")
        assert loaded_info is not None
        assert loaded_info.snapshot_id == "snapshot_001"
        assert loaded_info.application_version == "2.4.0"
        assert loaded_info.recovery_priority == 1
        assert loaded_info.recovery_notes == "High priority recovery"
        
        # Тест несуществующего ID
        missing_info = await repository.get_recovery_info("nonexistent")
        assert missing_info is None
    
    @pytest.mark.asyncio
    async def test_log_state_transition(self, repository):
        """Тест логирования переходов состояний"""
        transition = StateTransition(
            from_state=ApplicationState.STARTING,
            to_state=ApplicationState.RUNNING,
            timestamp=int(time.time() * 1000),
            reason="Initialization completed",
            success=True,
            duration_ms=500
        )
        
        # Логируем переход
        result = await repository.log_state_transition(transition)
        assert result is True
        
        # Проверяем что переход сохранен
        assert len(repository._state_transitions) == 1
        assert len(repository._transition_order) == 1
        
        logged_transition = repository._state_transitions[0]
        assert logged_transition.from_state == ApplicationState.STARTING
        assert logged_transition.to_state == ApplicationState.RUNNING
        assert logged_transition.reason == "Initialization completed"
        assert logged_transition.success is True
        assert logged_transition.duration_ms == 500
    
    @pytest.mark.asyncio
    async def test_get_state_transitions(self, repository):
        """Тест получения переходов состояний"""
        base_timestamp = int(time.time() * 1000)
        
        # Создаем несколько переходов
        transitions = [
            StateTransition(
                ApplicationState.STARTING, ApplicationState.RUNNING,
                base_timestamp + i * 1000, f"Transition {i}", True
            )
            for i in range(5)
        ]
        
        for transition in transitions:
            await repository.log_state_transition(transition)
        
        # Получаем все переходы
        all_transitions = await repository.get_state_transitions(limit=10)
        assert len(all_transitions) == 5
        
        # Проверяем порядок (новые сначала)
        assert all_transitions[0].timestamp > all_transitions[1].timestamp
        
        # Получаем ограниченное количество
        limited_transitions = await repository.get_state_transitions(limit=3)
        assert len(limited_transitions) == 3
        
        # Тест фильтрации по времени
        mid_timestamp = base_timestamp + 2000
        filtered_transitions = await repository.get_state_transitions(
            start_timestamp=mid_timestamp,
            limit=10
        )
        assert len(filtered_transitions) == 3  # Последние 3 перехода
    
    @pytest.mark.asyncio
    async def test_save_and_load_trading_session_state(self, repository, sample_trading_session):
        """Тест сохранения и загрузки состояния торговой сессии"""
        # Сохраняем состояние сессии
        result = await repository.save_trading_session_state(sample_trading_session)
        assert result is True
        
        # Загружаем состояние сессии
        loaded_session = await repository.load_trading_session_state("session_001")
        assert loaded_session is not None
        assert loaded_session.session_id == "session_001"
        assert loaded_session.currency_pair == "BTCUSDT"
        assert loaded_session.is_active is True
        assert loaded_session.active_deals_count == 2
        assert loaded_session.open_orders_count == 3
        assert loaded_session.total_profit == 125.50
        
        # Тест несуществующей сессии
        missing_session = await repository.load_trading_session_state("nonexistent")
        assert missing_session is None
    
    @pytest.mark.asyncio
    async def test_get_active_trading_sessions(self, repository):
        """Тест получения активных торговых сессий"""
        timestamp = int(time.time() * 1000)
        
        # Создаем активные и неактивные сессии
        active_session_1 = TradingSessionState(
            "active_1", "BTCUSDT", True, timestamp, timestamp, 1, 2
        )
        active_session_2 = TradingSessionState(
            "active_2", "ETHUSDT", True, timestamp, timestamp, 2, 3
        )
        inactive_session = TradingSessionState(
            "inactive_1", "ADAUSDT", False, timestamp, timestamp, 0, 0
        )
        
        # Сохраняем все сессии
        await repository.save_trading_session_state(active_session_1)
        await repository.save_trading_session_state(active_session_2)
        await repository.save_trading_session_state(inactive_session)
        
        # Получаем только активные сессии
        active_sessions = await repository.get_active_trading_sessions()
        assert len(active_sessions) == 2
        
        session_ids = [session.session_id for session in active_sessions]
        assert "active_1" in session_ids
        assert "active_2" in session_ids
        assert "inactive_1" not in session_ids
    
    @pytest.mark.asyncio
    async def test_cleanup_old_snapshots(self, repository):
        """Тест очистки старых снимков"""
        # Создаем снимки разного возраста
        current_time = datetime.now()
        old_time = current_time - timedelta(days=35)
        recent_time = current_time - timedelta(days=15)
        
        # Старый снимок
        old_snapshot = SystemSnapshot(
            snapshot_id="old_snapshot",
            timestamp=int(old_time.timestamp() * 1000),
            application_state=ApplicationState.RUNNING
        )
        
        # Недавний снимок
        recent_snapshot = SystemSnapshot(
            snapshot_id="recent_snapshot",
            timestamp=int(recent_time.timestamp() * 1000),
            application_state=ApplicationState.RUNNING
        )
        
        # Текущий снимок
        current_snapshot = SystemSnapshot(
            snapshot_id="current_snapshot",
            timestamp=int(current_time.timestamp() * 1000),
            application_state=ApplicationState.RUNNING
        )
        
        # Сохраняем все снимки
        await repository.save_system_snapshot(old_snapshot)
        await repository.save_system_snapshot(recent_snapshot)
        await repository.save_system_snapshot(current_snapshot)
        
        # Создаем recovery info для снимков
        for i, snapshot_id in enumerate(repository._snapshot_order):
            recovery_info = RecoveryInfo(
                snapshot_id=snapshot_id,
                created_at=int(time.time() * 1000),
                application_version="2.4.0"
            )
            await repository.save_recovery_info(recovery_info)
        
        # Проверяем что все снимки есть
        assert len(repository._system_snapshots) == 3
        assert len(repository._recovery_info) == 3
        
        # Очищаем старые снимки (старше 30 дней)
        removed_count = await repository.cleanup_old_snapshots(days_to_keep=30)
        
        # Проверяем результат
        assert removed_count == 1  # Удален 1 старый снимок
        assert len(repository._system_snapshots) == 2  # Остались 2
        assert len(repository._recovery_info) == 2  # Recovery info тоже очищена
    
    @pytest.mark.asyncio
    async def test_cleanup_old_transitions(self, repository):
        """Тест очистки старых переходов состояний"""
        # Создаем переходы разного возраста
        current_time = datetime.now()
        old_time = current_time - timedelta(days=100)
        recent_time = current_time - timedelta(days=50)
        
        # Старые переходы
        for i in range(3):
            old_transition = StateTransition(
                ApplicationState.STARTING, ApplicationState.RUNNING,
                int(old_time.timestamp() * 1000) + i,
                f"Old transition {i}", True
            )
            await repository.log_state_transition(old_transition)
        
        # Недавние переходы
        for i in range(2):
            recent_transition = StateTransition(
                ApplicationState.RUNNING, ApplicationState.PAUSED,
                int(recent_time.timestamp() * 1000) + i,
                f"Recent transition {i}", True
            )
            await repository.log_state_transition(recent_transition)
        
        # Проверяем что все переходы есть
        assert len(repository._state_transitions) == 5
        
        # Очищаем старые переходы (старше 90 дней)
        removed_count = await repository.cleanup_old_transitions(days_to_keep=90)
        
        # Проверяем результат
        assert removed_count == 3  # Удалены 3 старых перехода
        assert len(repository._state_transitions) == 2  # Остались 2
    
    @pytest.mark.asyncio
    async def test_get_recovery_candidates(self, repository):
        """Тест получения кандидатов для восстановления"""
        # Создаем recovery info с разными приоритетами
        recovery_candidates = [
            RecoveryInfo("snapshot_1", int(time.time() * 1000), "2.4.0", 3),  # Средний приоритет
            RecoveryInfo("snapshot_2", int(time.time() * 1000), "2.4.0", 1),  # Высокий приоритет
            RecoveryInfo("snapshot_3", int(time.time() * 1000), "2.4.0", 5),  # Низкий приоритет
            RecoveryInfo("snapshot_4", int(time.time() * 1000), "2.4.0", 1),  # Высокий приоритет
        ]
        
        # Сохраняем кандидатов
        for candidate in recovery_candidates:
            await repository.save_recovery_info(candidate)
        
        # Получаем кандидатов (должны быть отсортированы по приоритету)
        candidates = await repository.get_recovery_candidates()
        
        assert len(candidates) == 4
        
        # Проверяем сортировку по приоритету (1 = highest)
        assert candidates[0].recovery_priority == 1
        assert candidates[1].recovery_priority == 1
        assert candidates[2].recovery_priority == 3
        assert candidates[3].recovery_priority == 5
        
        # Проверяем ID кандидатов с высшим приоритетом
        high_priority_ids = [c.snapshot_id for c in candidates[:2]]
        assert "snapshot_2" in high_priority_ids
        assert "snapshot_4" in high_priority_ids
    
    def test_get_statistics(self, repository):
        """Тест получения статистики репозитория"""
        # Изначально пустая статистика
        stats = repository.get_statistics()
        assert stats['snapshots_count'] == 0
        assert stats['transitions_count'] == 0
        assert stats['trading_sessions_count'] == 0
        assert stats['recovery_info_count'] == 0
        assert stats['active_sessions_count'] == 0
    
    @pytest.mark.asyncio
    async def test_statistics_after_data_operations(self, repository, sample_system_snapshot, sample_trading_session):
        """Тест статистики после операций с данными"""
        # Добавляем данные
        await repository.save_system_snapshot(sample_system_snapshot)
        
        transition = StateTransition(
            ApplicationState.STARTING, ApplicationState.RUNNING,
            int(time.time() * 1000), "Test transition", True
        )
        await repository.log_state_transition(transition)
        
        await repository.save_trading_session_state(sample_trading_session)
        
        recovery_info = RecoveryInfo(
            "test_snapshot", int(time.time() * 1000), "2.4.0"
        )
        await repository.save_recovery_info(recovery_info)
        
        # Проверяем статистику
        stats = repository.get_statistics()
        assert stats['snapshots_count'] == 1
        assert stats['transitions_count'] == 1
        assert stats['trading_sessions_count'] == 1
        assert stats['recovery_info_count'] == 1
        assert stats['active_sessions_count'] == 1  # sample_trading_session активная
    
    @pytest.mark.asyncio
    async def test_clear_all_data(self, repository, sample_state_info, sample_system_snapshot):
        """Тест очистки всех данных"""
        # Добавляем данные
        await repository.save_application_state(sample_state_info)
        await repository.save_system_snapshot(sample_system_snapshot)
        
        transition = StateTransition(
            ApplicationState.STARTING, ApplicationState.RUNNING,
            int(time.time() * 1000), "Test", True
        )
        await repository.log_state_transition(transition)
        
        # Проверяем что данные есть
        stats_before = repository.get_statistics()
        assert stats_before['snapshots_count'] > 0
        assert stats_before['transitions_count'] > 0
        
        # Очищаем все данные
        repository.clear_all_data()
        
        # Проверяем что все очищено
        assert await repository.load_application_state() is None
        assert await repository.load_system_snapshot() is None
        
        stats_after = repository.get_statistics()
        assert stats_after['snapshots_count'] == 0
        assert stats_after['transitions_count'] == 0
        assert stats_after['trading_sessions_count'] == 0
        assert stats_after['recovery_info_count'] == 0
    
    @pytest.mark.asyncio
    async def test_export_state_data(self, repository, sample_state_info, sample_system_snapshot):
        """Тест экспорта данных состояния"""
        # Добавляем данные
        await repository.save_application_state(sample_state_info)
        await repository.save_system_snapshot(sample_system_snapshot)
        
        transition = StateTransition(
            ApplicationState.STARTING, ApplicationState.RUNNING,
            int(time.time() * 1000), "Export test", True
        )
        await repository.log_state_transition(transition)
        
        # Экспортируем данные
        exported_data = await repository.export_state_data()
        
        # Проверяем структуру экспорта
        assert 'application_state' in exported_data
        assert 'system_snapshots' in exported_data
        assert 'recovery_info' in exported_data
        assert 'state_transitions' in exported_data
        assert 'trading_sessions' in exported_data
        assert 'repository_stats' in exported_data
        
        # Проверяем содержимое
        assert exported_data['application_state'] is not None
        assert len(exported_data['system_snapshots']) == 1
        assert len(exported_data['state_transitions']) == 1
        assert exported_data['repository_stats']['snapshots_count'] == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository):
        """Тест конкурентных операций"""
        async def save_snapshots():
            for i in range(10):
                snapshot = SystemSnapshot(
                    snapshot_id=f"concurrent_snapshot_{i}",
                    timestamp=int(time.time() * 1000) + i,
                    application_state=ApplicationState.RUNNING
                )
                await repository.save_system_snapshot(snapshot)
        
        async def save_transitions():
            for i in range(10):
                transition = StateTransition(
                    ApplicationState.RUNNING, ApplicationState.PAUSED,
                    int(time.time() * 1000) + i,
                    f"Concurrent transition {i}", True
                )
                await repository.log_state_transition(transition)
        
        # Запускаем операции параллельно
        await asyncio.gather(save_snapshots(), save_transitions())
        
        # Проверяем целостность данных
        stats = repository.get_statistics()
        assert stats['snapshots_count'] == 10
        assert stats['transitions_count'] == 10
        
        # Проверяем что данные корректно упорядочены
        snapshots = await repository.get_system_snapshots(limit=20)
        assert len(snapshots) == 10
        
        transitions = await repository.get_state_transitions(limit=20)
        assert len(transitions) == 10