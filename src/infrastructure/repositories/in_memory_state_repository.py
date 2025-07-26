import asyncio
import logging
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from src.domain.entities.application_state import (
    ApplicationStateInfo, SystemSnapshot, RecoveryInfo, 
    StateTransition, TradingSessionState
)
from src.domain.repositories.i_state_repository import IStateRepository

logger = logging.getLogger(__name__)


class InMemoryStateRepository(IStateRepository):
    """
    In-memory реализация репозитория состояний для разработки и тестирования
    """
    
    def __init__(self):
        self._application_state: Optional[ApplicationStateInfo] = None
        self._system_snapshots: Dict[str, SystemSnapshot] = {}
        self._recovery_info: Dict[str, RecoveryInfo] = {}
        self._state_transitions: List[StateTransition] = []
        self._trading_sessions: Dict[str, TradingSessionState] = {}
        
        # Для упорядочивания
        self._snapshot_order: List[str] = []
        self._transition_order: List[StateTransition] = []
    
    async def save_application_state(self, state_info: ApplicationStateInfo) -> bool:
        """Сохранить текущее состояние приложения"""
        try:
            self._application_state = state_info
            logger.debug(f"💾 Application state saved: {state_info.current_state.value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save application state: {e}")
            return False
    
    async def load_application_state(self) -> Optional[ApplicationStateInfo]:
        """Загрузить последнее состояние приложения"""
        try:
            if self._application_state:
                logger.debug(f"📥 Application state loaded: {self._application_state.current_state.value}")
            return self._application_state
            
        except Exception as e:
            logger.error(f"❌ Failed to load application state: {e}")
            return None
    
    async def save_system_snapshot(self, snapshot: SystemSnapshot) -> bool:
        """Сохранить снимок системы"""
        try:
            snapshot_id = f"snapshot_{snapshot.timestamp}_{len(self._system_snapshots)}"
            self._system_snapshots[snapshot_id] = snapshot
            self._snapshot_order.append(snapshot_id)
            
            logger.debug(f"📸 System snapshot saved: {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save system snapshot: {e}")
            return False
    
    async def load_system_snapshot(self, snapshot_id: Optional[str] = None) -> Optional[SystemSnapshot]:
        """Загрузить снимок системы (последний или по ID)"""
        try:
            if snapshot_id:
                return self._system_snapshots.get(snapshot_id)
            
            # Возвращаем последний снимок
            if self._snapshot_order:
                latest_id = self._snapshot_order[-1]
                return self._system_snapshots.get(latest_id)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to load system snapshot: {e}")
            return None
    
    async def get_system_snapshots(
        self, 
        limit: int = 10,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None
    ) -> List[SystemSnapshot]:
        """Получить список снимков системы"""
        try:
            snapshots = []
            
            # Сортируем по времени (новые сначала)
            sorted_ids = sorted(
                self._snapshot_order, 
                key=lambda sid: self._system_snapshots[sid].timestamp, 
                reverse=True
            )
            
            for snapshot_id in sorted_ids[:limit]:
                snapshot = self._system_snapshots[snapshot_id]
                
                # Фильтр по времени
                if start_timestamp and snapshot.timestamp < start_timestamp:
                    continue
                if end_timestamp and snapshot.timestamp > end_timestamp:
                    continue
                
                snapshots.append(snapshot)
            
            return snapshots
            
        except Exception as e:
            logger.error(f"❌ Failed to get system snapshots: {e}")
            return []
    
    async def save_recovery_info(self, recovery_info: RecoveryInfo) -> bool:
        """Сохранить информацию для восстановления"""
        try:
            self._recovery_info[recovery_info.snapshot_id] = recovery_info
            logger.debug(f"💾 Recovery info saved: {recovery_info.snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save recovery info: {e}")
            return False
    
    async def get_recovery_info(self, snapshot_id: str) -> Optional[RecoveryInfo]:
        """Получить информацию для восстановления"""
        try:
            return self._recovery_info.get(snapshot_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to get recovery info: {e}")
            return None
    
    async def log_state_transition(self, transition: StateTransition) -> bool:
        """Записать переход состояний"""
        try:
            self._state_transitions.append(transition)
            self._transition_order.append(transition)
            
            logger.debug(f"📝 State transition logged: {transition.from_state.value} → {transition.to_state.value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log state transition: {e}")
            return False
    
    async def get_state_transitions(
        self,
        limit: int = 50,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None
    ) -> List[StateTransition]:
        """Получить историю переходов состояний"""
        try:
            transitions = []
            
            # Сортируем по времени (новые сначала)
            sorted_transitions = sorted(
                self._state_transitions, 
                key=lambda t: t.timestamp, 
                reverse=True
            )
            
            for transition in sorted_transitions[:limit]:
                # Фильтр по времени
                if start_timestamp and transition.timestamp < start_timestamp:
                    continue
                if end_timestamp and transition.timestamp > end_timestamp:
                    continue
                
                transitions.append(transition)
            
            return transitions
            
        except Exception as e:
            logger.error(f"❌ Failed to get state transitions: {e}")
            return []
    
    async def save_trading_session_state(self, session_state: TradingSessionState) -> bool:
        """Сохранить состояние торговой сессии"""
        try:
            self._trading_sessions[session_state.session_id] = session_state
            logger.debug(f"💾 Trading session state saved: {session_state.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save trading session state: {e}")
            return False
    
    async def load_trading_session_state(self, session_id: str) -> Optional[TradingSessionState]:
        """Загрузить состояние торговой сессии"""
        try:
            return self._trading_sessions.get(session_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to load trading session state: {e}")
            return None
    
    async def get_active_trading_sessions(self) -> List[TradingSessionState]:
        """Получить активные торговые сессии"""
        try:
            active_sessions = []
            
            for session in self._trading_sessions.values():
                if session.is_active:
                    active_sessions.append(session)
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"❌ Failed to get active trading sessions: {e}")
            return []
    
    async def cleanup_old_snapshots(self, days_to_keep: int = 30) -> int:
        """Очистить старые снимки"""
        try:
            cutoff_time = int((datetime.now() - timedelta(days=days_to_keep)).timestamp() * 1000)
            
            snapshots_to_remove = []
            for snapshot_id, snapshot in self._system_snapshots.items():
                if snapshot.timestamp < cutoff_time:
                    snapshots_to_remove.append(snapshot_id)
            
            # Удаляем старые снимки
            for snapshot_id in snapshots_to_remove:
                del self._system_snapshots[snapshot_id]
                if snapshot_id in self._snapshot_order:
                    self._snapshot_order.remove(snapshot_id)
                # Удаляем связанную recovery info
                self._recovery_info.pop(snapshot_id, None)
            
            logger.debug(f"🧹 Cleaned up {len(snapshots_to_remove)} old snapshots")
            return len(snapshots_to_remove)
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old snapshots: {e}")
            return 0
    
    async def cleanup_old_transitions(self, days_to_keep: int = 90) -> int:
        """Очистить старые переходы состояний"""
        try:
            cutoff_time = int((datetime.now() - timedelta(days=days_to_keep)).timestamp() * 1000)
            
            original_count = len(self._state_transitions)
            
            # Фильтруем переходы
            self._state_transitions = [
                transition for transition in self._state_transitions
                if transition.timestamp >= cutoff_time
            ]
            
            # Обновляем порядок
            self._transition_order = [
                transition for transition in self._transition_order
                if transition.timestamp >= cutoff_time
            ]
            
            removed_count = original_count - len(self._state_transitions)
            
            logger.debug(f"🧹 Cleaned up {removed_count} old state transitions")
            return removed_count
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old transitions: {e}")
            return 0
    
    async def get_recovery_candidates(self) -> List[RecoveryInfo]:
        """Получить кандидатов для восстановления (отсортированных по приоритету)"""
        try:
            candidates = list(self._recovery_info.values())
            
            # Сортируем по приоритету (1 = highest) и времени создания
            candidates.sort(key=lambda r: (r.recovery_priority, -r.created_at))
            
            return candidates
            
        except Exception as e:
            logger.error(f"❌ Failed to get recovery candidates: {e}")
            return []
    
    # Дополнительные методы для отладки и тестирования
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику репозитория"""
        return {
            'snapshots_count': len(self._system_snapshots),
            'transitions_count': len(self._state_transitions),
            'trading_sessions_count': len(self._trading_sessions),
            'recovery_info_count': len(self._recovery_info),
            'active_sessions_count': len([s for s in self._trading_sessions.values() if s.is_active])
        }
    
    def clear_all_data(self) -> None:
        """Очистить все данные (для тестирования)"""
        self._application_state = None
        self._system_snapshots.clear()
        self._recovery_info.clear()
        self._state_transitions.clear()
        self._trading_sessions.clear()
        self._snapshot_order.clear()
        self._transition_order.clear()
        
        logger.debug("🧹 All state repository data cleared")
    
    async def export_state_data(self) -> Dict[str, Any]:
        """Экспорт всех данных состояния"""
        try:
            return {
                'application_state': self._application_state.to_dict() if self._application_state else None,
                'system_snapshots': {
                    sid: {
                        'timestamp': snapshot.timestamp,
                        'application_state': snapshot.application_state.value,
                        'trading_sessions_count': len(snapshot.trading_sessions),
                        'active_deals_count': len(snapshot.active_deals),
                        'pending_orders_count': len(snapshot.pending_orders),
                        'system_metrics': snapshot.system_metrics
                    }
                    for sid, snapshot in self._system_snapshots.items()
                },
                'recovery_info': {
                    rid: {
                        'snapshot_id': info.snapshot_id,
                        'created_at': info.created_at,
                        'application_version': info.application_version,
                        'recovery_priority': info.recovery_priority,
                        'recovery_notes': info.recovery_notes
                    }
                    for rid, info in self._recovery_info.items()
                },
                'state_transitions': [
                    {
                        'from_state': t.from_state.value,
                        'to_state': t.to_state.value,
                        'timestamp': t.timestamp,
                        'reason': t.reason,
                        'success': t.success,
                        'duration_ms': t.duration_ms
                    }
                    for t in self._state_transitions[-50:]  # Последние 50
                ],
                'trading_sessions': {
                    sid: {
                        'session_id': session.session_id,
                        'currency_pair': session.currency_pair,
                        'is_active': session.is_active,
                        'start_timestamp': session.start_timestamp,
                        'active_deals_count': session.active_deals_count,
                        'open_orders_count': session.open_orders_count
                    }
                    for sid, session in self._trading_sessions.items()
                },
                'repository_stats': self.get_statistics()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to export state data: {e}")
            return {}