import asyncio
import logging
import signal
import time
import hashlib
import json
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime
import uuid

from src.domain.entities.application_state import (
    ApplicationState, ApplicationStateInfo, SystemSnapshot, 
    RecoveryInfo, StateTransition, TradingSessionState, ShutdownReason
)
from src.domain.repositories.i_state_repository import IStateRepository
from src.domain.repositories.i_deals_repository import IDealsRepository
from src.domain.repositories.i_orders_repository import IOrdersRepository
from src.domain.repositories.i_statistics_repository import IStatisticsRepository
from src.domain.repositories.i_configuration_repository import IConfigurationRepository
from src.domain.entities.statistics import StatisticCategory

logger = logging.getLogger(__name__)


class StateManagementService:
    """
    Сервис управления состоянием приложения.
    Отвечает за graceful shutdown, recovery и state persistence.
    """
    
    def __init__(
        self,
        state_repo: IStateRepository,
        deals_repo: Optional[IDealsRepository] = None,
        orders_repo: Optional[IOrdersRepository] = None,
        statistics_repo: Optional[IStatisticsRepository] = None,
        config_repo: Optional[IConfigurationRepository] = None
    ):
        self.state_repo = state_repo
        self.deals_repo = deals_repo
        self.orders_repo = orders_repo
        self.statistics_repo = statistics_repo
        self.config_repo = config_repo
        
        # Текущее состояние
        self.current_state = ApplicationState.STARTING
        self.state_info = ApplicationStateInfo(current_state=self.current_state)
        self.trading_sessions: Dict[str, TradingSessionState] = {}
        
        # Обработчики событий
        self.state_change_handlers: Dict[ApplicationState, List[Callable]] = {}
        self.shutdown_handlers: List[Callable] = []
        self.recovery_handlers: List[Callable] = []
        
        # Контроль выполнения
        self.shutdown_requested = False
        self.emergency_stop = False
        self.snapshot_interval_seconds = 300  # 5 минут
        self.last_snapshot_time = 0
        
        # Метрики
        self.start_time = time.time()
        self.state_transitions_count = 0
        self.snapshots_created = 0
        self.recovery_attempts = 0
        
        # Установка обработчиков сигналов
        self._setup_signal_handlers()
    
    async def initialize(self) -> bool:
        """Инициализация сервиса состояний"""
        try:
            logger.info("🔄 Initializing State Management Service...")
            
            # Загружаем последнее состояние
            await self._load_previous_state()
            
            # Проверяем необходимость восстановления
            recovery_needed = await self._check_recovery_needed()
            if recovery_needed:
                await self._perform_recovery()
            
            # Устанавливаем состояние RUNNING
            await self.transition_to_state(ApplicationState.RUNNING, "Initialization completed")
            
            # Запускаем фоновые задачи
            asyncio.create_task(self._periodic_snapshot_task())
            asyncio.create_task(self._state_monitoring_task())
            
            logger.info("✅ State Management Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize State Management Service: {e}")
            await self.transition_to_state(ApplicationState.ERROR, f"Initialization error: {e}")
            return False
    
    async def transition_to_state(
        self, 
        new_state: ApplicationState, 
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Переход в новое состояние"""
        try:
            if new_state == self.current_state:
                return True
            
            start_time = time.time()
            previous_state = self.current_state
            
            logger.info(f"🔄 State transition: {previous_state.value} → {new_state.value} ({reason})")
            
            # Выполняем пре-обработчики
            success = await self._execute_pre_transition_handlers(previous_state, new_state)
            if not success:
                logger.error(f"❌ Pre-transition handlers failed for {previous_state.value} → {new_state.value}")
                return False
            
            # Записываем переход
            transition = StateTransition(
                from_state=previous_state,
                to_state=new_state,
                timestamp=int(time.time() * 1000),
                reason=reason,
                success=True,
                duration_ms=int((time.time() - start_time) * 1000),
                metadata=metadata or {}
            )
            await self.state_repo.log_state_transition(transition)

            # Обновляем состояние
            self.current_state = new_state
            self.state_info.previous_state = previous_state
            self.state_info.current_state = new_state
            self.state_info.state_changed_at = int(time.time() * 1000)
            self.state_transitions_count += 1
            
            # Выполняем пост-обработчики
            await self._execute_post_transition_handlers(previous_state, new_state)
            
            # Сохраняем состояние
            await self.state_repo.save_application_state(self.state_info)
            
            # Обновляем статистику
            if self.statistics_repo:
                await self.statistics_repo.increment_counter(
                    f"state_transitions_{new_state.value}",
                    StatisticCategory.SYSTEM
                )
            
            logger.info(f"✅ State transition completed: {previous_state.value} → {new_state.value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ State transition failed: {e}")
            
            # Записываем неудачный переход
            failed_transition = StateTransition(
                from_state=previous_state if 'previous_state' in locals() else self.current_state,
                to_state=new_state,
                timestamp=int(time.time() * 1000),
                reason=reason,
                success=False,
                error_message=str(e),
                metadata=metadata or {}
            )
            
            try:
                await self.state_repo.log_state_transition(failed_transition)
            except:
                pass  # Не критично если не удалось записать
            
            return False
    
    async def request_graceful_shutdown(self, reason: ShutdownReason = ShutdownReason.USER_REQUEST) -> bool:
        """Запросить graceful shutdown"""
        try:
            logger.warning(f"🛑 Graceful shutdown requested: {reason.value}")
            
            self.shutdown_requested = True
            self.state_info.safe_shutdown_requested = True
            self.state_info.last_shutdown_reason = reason
            
            # Переходим в состояние остановки
            await self.transition_to_state(
                ApplicationState.STOPPING, 
                f"Graceful shutdown: {reason.value}"
            )
            
            # Создаем финальный снимок
            await self.create_system_snapshot("pre_shutdown")
            
            # Выполняем shutdown handlers
            await self._execute_shutdown_handlers()
            
            # Завершаем торговые сессии
            await self._shutdown_trading_sessions()
            
            # Финальное состояние
            await self.transition_to_state(ApplicationState.STOPPED, "Graceful shutdown completed")
            
            logger.info("✅ Graceful shutdown completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Graceful shutdown failed: {e}")
            await self.emergency_shutdown()
            return False
    
    async def emergency_shutdown(self) -> None:
        """Экстренная остановка"""
        try:
            logger.critical("🚨 Emergency shutdown initiated")
            
            self.emergency_stop = True
            self.state_info.emergency_stop_active = True
            
            # Быстрый переход в состояние ошибки
            self.current_state = ApplicationState.ERROR
            self.state_info.current_state = ApplicationState.ERROR
            
            # Попытка сохранить критическое состояние
            try:
                await self.create_system_snapshot("emergency_shutdown")
                await self.state_repo.save_application_state(self.state_info)
            except:
                pass  # Игнорируем ошибки при экстренной остановке
            
            logger.critical("🚨 Emergency shutdown completed")
            
        except Exception as e:
            logger.critical(f"🚨 Emergency shutdown error: {e}")
    
    async def create_system_snapshot(self, snapshot_type: str = "periodic") -> Optional[str]:
        """Создать снимок состояния системы"""
        try:
            snapshot_id = f"{snapshot_type}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Собираем данные о сделках
            active_deals = []
            if self.deals_repo:
                deals = await self.deals_repo.get_active_deals()
                active_deals = [deal.to_dict() if hasattr(deal, 'to_dict') else deal for deal in deals]
            
            # Собираем данные о заказах
            pending_orders = []
            if self.orders_repo:
                orders = await self.orders_repo.get_open_orders()
                pending_orders = [order.to_dict() if hasattr(order, 'to_dict') else order for order in orders]
            
            # Собираем системные метрики
            system_metrics = await self._collect_system_metrics()
            
            # Создаем снимок
            snapshot = SystemSnapshot(
                snapshot_id=snapshot_id,
                timestamp=int(time.time() * 1000),
                application_state=self.current_state,
                trading_sessions=list(self.trading_sessions.values()),
                active_deals=active_deals,
                pending_orders=pending_orders,
                system_metrics=system_metrics,
                configuration_checksum=await self._calculate_config_checksum()
            )
            
            # Сохраняем снимок
            success = await self.state_repo.save_system_snapshot(snapshot)
            if success:
                self.snapshots_created += 1
                self.last_snapshot_time = time.time()
                
                # Создаем информацию для восстановления
                recovery_info = RecoveryInfo(
                    snapshot_id=snapshot_id,
                    created_at=snapshot.timestamp,
                    application_version="2.4.0",  # TODO: получать из конфигурации
                    recovery_priority=self._calculate_recovery_priority(),
                    recovery_notes=f"Auto-generated {snapshot_type} snapshot"
                )
                
                await self.state_repo.save_recovery_info(recovery_info)
                
                logger.debug(f"📸 System snapshot created: {snapshot_id}")
                return snapshot_id
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to create system snapshot: {e}")
            return None
    
    async def start_trading_session(
        self, 
        currency_pair: str,
        session_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Запустить торговую сессию"""
        try:
            session_id = f"{currency_pair}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            session_state = TradingSessionState(
                session_id=session_id,
                currency_pair=currency_pair,
                is_active=True,
                start_timestamp=int(time.time() * 1000),
                last_activity_timestamp=int(time.time() * 1000),
                active_deals_count=0,
                open_orders_count=0,
                metadata=session_config or {}
            )
            
            self.trading_sessions[session_id] = session_state
            await self.state_repo.save_trading_session_state(session_state)
            
            self.state_info.trading_active = True
            await self.state_repo.save_application_state(self.state_info)
            
            logger.info(f"📈 Trading session started: {session_id} for {currency_pair}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Failed to start trading session: {e}")
            raise
    
    async def stop_trading_session(self, session_id: str, reason: str = "User request") -> bool:
        """Остановить торговую сессию"""
        try:
            if session_id not in self.trading_sessions:
                logger.warning(f"⚠️ Trading session not found: {session_id}")
                return False
            
            session = self.trading_sessions[session_id]
            session.is_active = False
            session.metadata['stop_reason'] = reason
            session.metadata['stop_timestamp'] = int(time.time() * 1000)
            
            await self.state_repo.save_trading_session_state(session)
            del self.trading_sessions[session_id]
            
            # Проверяем, есть ли еще активные сессии
            if not self.trading_sessions:
                self.state_info.trading_active = False
                await self.state_repo.save_application_state(self.state_info)
            
            logger.info(f"📉 Trading session stopped: {session_id} ({reason})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop trading session: {e}")
            return False
    
    def register_state_change_handler(self, state: ApplicationState, handler: Callable) -> None:
        """Зарегистрировать обработчик изменения состояния"""
        if state not in self.state_change_handlers:
            self.state_change_handlers[state] = []
        self.state_change_handlers[state].append(handler)
    
    def register_shutdown_handler(self, handler: Callable) -> None:
        """Зарегистрировать обработчик shutdown"""
        self.shutdown_handlers.append(handler)
    
    def register_recovery_handler(self, handler: Callable) -> None:
        """Зарегистрировать обработчик recovery"""
        self.recovery_handlers.append(handler)
    
    async def get_state_summary(self) -> Dict[str, Any]:
        """Получить сводку состояния"""
        uptime = time.time() - self.start_time
        
        return {
            'current_state': self.current_state.value,
            'uptime_seconds': int(uptime),
            'trading_active': self.state_info.trading_active,
            'active_sessions': len(self.trading_sessions),
            'shutdown_requested': self.shutdown_requested,
            'emergency_stop': self.emergency_stop,
            'state_transitions_count': self.state_transitions_count,
            'snapshots_created': self.snapshots_created,
            'last_snapshot_age_seconds': int(time.time() - self.last_snapshot_time) if self.last_snapshot_time > 0 else None,
            'recovery_attempts': self.recovery_attempts,
            'sessions': {sid: {
                'currency_pair': session.currency_pair,
                'active_deals': session.active_deals_count,
                'open_orders': session.open_orders_count,
                'uptime_minutes': (time.time() * 1000 - session.start_timestamp) / (1000 * 60)
            } for sid, session in self.trading_sessions.items()}
        }
    
    # Внутренние методы
    
    async def _load_previous_state(self) -> None:
        """Загрузить предыдущее состояние"""
        try:
            previous_state = await self.state_repo.load_application_state()
            if previous_state:
                self.state_info = previous_state
                self.state_info.restart_count += 1
                self.state_info.uptime_seconds = 0  # Сбрасываем uptime
                
                logger.info(f"📥 Previous state loaded: {previous_state.current_state.value}")
            else:
                logger.info("📥 No previous state found, starting fresh")
                
        except Exception as e:
            logger.error(f"❌ Failed to load previous state: {e}")
    
    async def _check_recovery_needed(self) -> bool:
        """Проверить необходимость восстановления"""
        try:
            # Проверяем последнее состояние
            if self.state_info.current_state in [ApplicationState.ERROR, ApplicationState.STOPPING]:
                logger.warning("⚠️ Previous session ended unexpectedly, recovery may be needed")
                return True
            
            # Проверяем активные торговые сессии
            active_sessions = await self.state_repo.get_active_trading_sessions()
            if active_sessions:
                logger.warning(f"⚠️ Found {len(active_sessions)} active trading sessions from previous run")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to check recovery status: {e}")
            return False
    
    async def _perform_recovery(self) -> None:
        """Выполнить восстановление"""
        try:
            logger.info("🔄 Starting recovery process...")
            self.recovery_attempts += 1
            
            await self.transition_to_state(ApplicationState.RECOVERY, "Recovery initiated")
            
            # Получаем кандидатов для восстановления
            recovery_candidates = await self.state_repo.get_recovery_candidates()
            
            if recovery_candidates:
                # Выбираем лучший кандидат
                best_candidate = recovery_candidates[0]
                snapshot = await self.state_repo.load_system_snapshot(best_candidate.snapshot_id)
                
                if snapshot:
                    # Восстанавливаем торговые сессии
                    for session_state in snapshot.trading_sessions:
                        if session_state.is_active:
                            self.trading_sessions[session_state.session_id] = session_state
                    
                    # Выполняем recovery handlers
                    await self._execute_recovery_handlers(snapshot)
                    
                    logger.info(f"✅ Recovery completed from snapshot: {best_candidate.snapshot_id}")
                else:
                    logger.error("❌ Failed to load recovery snapshot")
            else:
                logger.info("ℹ️ No recovery candidates found, starting clean")
            
        except Exception as e:
            logger.error(f"❌ Recovery failed: {e}")
            await self.transition_to_state(ApplicationState.ERROR, f"Recovery failed: {e}")
    
    async def _execute_pre_transition_handlers(
        self, 
        from_state: ApplicationState, 
        to_state: ApplicationState
    ) -> bool:
        """Выполнить пре-обработчики перехода состояний"""
        try:
            handlers = self.state_change_handlers.get(to_state, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(from_state, to_state)
                    else:
                        handler(from_state, to_state)
                except Exception as e:
                    logger.error(f"❌ State change handler failed: {e}")
                    return False
            return True
            
        except Exception as e:
            logger.error(f"❌ Pre-transition handlers failed: {e}")
            return False
    
    async def _execute_post_transition_handlers(
        self, 
        from_state: ApplicationState, 
        to_state: ApplicationState
    ) -> None:
        """Выполнить пост-обработчики перехода состояний"""
        try:
            # Дополнительная логика после успешного перехода
            if to_state == ApplicationState.RUNNING:
                self.state_info.session_start_time = int(time.time() * 1000)
            elif to_state == ApplicationState.STOPPED:
                self.state_info.trading_active = False
                
        except Exception as e:
            logger.error(f"❌ Post-transition handlers failed: {e}")
    
    async def _execute_shutdown_handlers(self) -> None:
        """Выполнить shutdown handlers"""
        try:
            for handler in self.shutdown_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler()
                    else:
                        handler()
                except Exception as e:
                    logger.error(f"❌ Shutdown handler failed: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Shutdown handlers execution failed: {e}")
    
    async def _execute_recovery_handlers(self, snapshot: SystemSnapshot) -> None:
        """Выполнить recovery handlers"""
        try:
            for handler in self.recovery_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(snapshot)
                    else:
                        handler(snapshot)
                except Exception as e:
                    logger.error(f"❌ Recovery handler failed: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Recovery handlers execution failed: {e}")
    
    async def _shutdown_trading_sessions(self) -> None:
        """Остановить все торговые сессии"""
        try:
            session_ids = list(self.trading_sessions.keys())
            for session_id in session_ids:
                await self.stop_trading_session(session_id, "System shutdown")
                
        except Exception as e:
            logger.error(f"❌ Failed to shutdown trading sessions: {e}")
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Собрать системные метрики"""
        try:
            uptime = time.time() - self.start_time
            
            metrics = {
                'uptime_seconds': int(uptime),
                'state_transitions': self.state_transitions_count,
                'snapshots_created': self.snapshots_created,
                'recovery_attempts': self.recovery_attempts,
                'active_sessions_count': len(self.trading_sessions),
                'memory_usage_mb': self._get_memory_usage(),
                'timestamp': int(time.time() * 1000)
            }
            
            # Добавляем статистику из statistics_repo
            if self.statistics_repo:
                try:
                    # Получаем системные метрики за последний час
                    current_time = int(time.time() * 1000)
                    hour_ago = current_time - (60 * 60 * 1000)
                    
                    system_stats = await self.statistics_repo.get_statistics_range(
                        hour_ago, current_time, StatisticCategory.SYSTEM
                    )
                    
                    metrics['system_statistics_count'] = len(system_stats)
                except Exception as e:
                    logger.debug(f"Could not collect system statistics: {e}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to collect system metrics: {e}")
            return {}
    
    async def _calculate_config_checksum(self) -> Optional[str]:
        """Вычислить контрольную сумму конфигурации"""
        try:
            if not self.config_repo:
                return None
            
            all_configs = await self.config_repo.get_all_configs(include_secrets=False)
            config_data = json.dumps(all_configs, sort_keys=True)
            
            return hashlib.md5(config_data.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate config checksum: {e}")
            return None
    
    def _calculate_recovery_priority(self) -> int:
        """Вычислить приоритет восстановления"""
        priority = 3  # Средний приоритет по умолчанию
        
        # Повышаем приоритет если есть активные сессии
        if self.trading_sessions:
            priority = 1
        
        # Понижаем приоритет если в состоянии ошибки
        if self.current_state == ApplicationState.ERROR:
            priority = 5
        
        return priority
    
    def _get_memory_usage(self) -> float:
        """Получить использование памяти в MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _setup_signal_handlers(self) -> None:
        """Настроить обработчики сигналов"""
        try:
            def signal_handler(signum, frame):
                logger.warning(f"🔔 Received signal {signum}")
                
                if signum in [signal.SIGTERM, signal.SIGINT]:
                    # Graceful shutdown
                    asyncio.create_task(
                        self.request_graceful_shutdown(ShutdownReason.SYSTEM_SIGNAL)
                    )
                elif signum == signal.SIGUSR1:
                    # Create snapshot
                    asyncio.create_task(self.create_system_snapshot("signal_requested"))
            
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            
            # SIGUSR1 for snapshot creation (Unix only)
            if hasattr(signal, 'SIGUSR1'):
                signal.signal(signal.SIGUSR1, signal_handler)
                
        except Exception as e:
            logger.warning(f"⚠️ Could not setup signal handlers: {e}")
    
    async def _periodic_snapshot_task(self) -> None:
        """Фоновая задача для периодических снимков"""
        try:
            while not self.shutdown_requested:
                await asyncio.sleep(self.snapshot_interval_seconds)
                
                if self.current_state == ApplicationState.RUNNING:
                    await self.create_system_snapshot("periodic")
                    
        except asyncio.CancelledError:
            logger.info("📸 Periodic snapshot task cancelled")
        except Exception as e:
            logger.error(f"❌ Periodic snapshot task error: {e}")
    
    async def _state_monitoring_task(self) -> None:
        """Фоновая задача мониторинга состояния"""
        try:
            while not self.shutdown_requested:
                await asyncio.sleep(60)  # Проверка каждую минуту
                
                # Обновляем uptime
                self.state_info.uptime_seconds = int(time.time() - self.start_time)
                
                # Обновляем активность торговых сессий
                current_time = int(time.time() * 1000)
                for session in self.trading_sessions.values():
                    session.last_activity_timestamp = current_time
                
                # Сохраняем обновленное состояние
                await self.state_repo.save_application_state(self.state_info)
                
        except asyncio.CancelledError:
            logger.info("📊 State monitoring task cancelled")
        except Exception as e:
            logger.error(f"❌ State monitoring task error: {e}")