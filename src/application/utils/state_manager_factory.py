import logging
from typing import Optional, Dict, Any

from src.domain.services.state.state_management_service import StateManagementService
from src.domain.repositories.i_state_repository import IStateRepository
from src.domain.repositories.i_deals_repository import IDealsRepository
from src.domain.repositories.i_orders_repository import IOrdersRepository
from src.domain.repositories.i_statistics_repository import IStatisticsRepository
from src.domain.repositories.i_configuration_repository import IConfigurationRepository

from src.infrastructure.repositories.in_memory_state_repository import InMemoryStateRepository
from src.infrastructure.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class StateManagerFactory:
    """
    Фабрика для создания StateManagementService с нужными зависимостями
    """
    
    @staticmethod
    def create_state_manager(
        config: Dict[str, Any],
        deals_repo: Optional[IDealsRepository] = None,
        orders_repo: Optional[IOrdersRepository] = None,
        statistics_repo: Optional[IStatisticsRepository] = None,
        config_repo: Optional[IConfigurationRepository] = None,
        db_manager: Optional[DatabaseManager] = None
    ) -> StateManagementService:
        """
        Создать StateManagementService с правильными зависимостями
        
        Args:
            config: Конфигурация приложения
            deals_repo: Репозиторий сделок
            orders_repo: Репозиторий ордеров
            statistics_repo: Репозиторий статистики
            config_repo: Репозиторий конфигурации
            db_manager: Менеджер базы данных
            
        Returns:
            Настроенный StateManagementService
        """
        try:
            # Определяем тип репозитория состояний
            state_repo_type = config.get('state_management', {}).get('repository_type', 'in_memory')
            
            # Создаем репозиторий состояний
            if state_repo_type == 'database' and db_manager:
                state_repo = StateManagerFactory._create_database_state_repo(db_manager)
            else:
                state_repo = InMemoryStateRepository()
                logger.info("📦 Using InMemoryStateRepository for state management")
            
            # Создаем StateManagementService
            state_manager = StateManagementService(
                state_repo=state_repo,
                deals_repo=deals_repo,
                orders_repo=orders_repo,
                statistics_repo=statistics_repo,
                config_repo=config_repo
            )
            
            # Конфигурируем интервалы
            snapshot_config = config.get('state_management', {}).get('snapshots', {})
            if 'interval_seconds' in snapshot_config:
                state_manager.snapshot_interval_seconds = snapshot_config['interval_seconds']
            
            logger.info("✅ StateManagementService created successfully")
            return state_manager
            
        except Exception as e:
            logger.error(f"❌ Failed to create StateManagementService: {e}")
            raise
    
    @staticmethod
    def _create_database_state_repo(db_manager: DatabaseManager) -> IStateRepository:
        """Создать database-based репозиторий состояний"""
        try:
            if db_manager.db_type == 'postgresql':
                from src.infrastructure.repositories.postgresql.postgresql_state_repository import PostgreSQLStateRepository
                return PostgreSQLStateRepository(db_manager)
            elif db_manager.db_type == 'sqlite':
                from src.infrastructure.repositories.sqlite.sqlite_state_repository import SQLiteStateRepository
                return SQLiteStateRepository(db_manager)
            else:
                logger.warning(f"⚠️ Unsupported database type for state repository: {db_manager.db_type}")
                return InMemoryStateRepository()
                
        except ImportError as e:
            logger.warning(f"⚠️ Database state repository not available: {e}. Using in-memory fallback.")
            return InMemoryStateRepository()
        except Exception as e:
            logger.error(f"❌ Failed to create database state repository: {e}")
            return InMemoryStateRepository()
    
    @staticmethod
    def create_development_state_manager(
        enable_database: bool = False,
        enable_statistics: bool = True
    ) -> StateManagementService:
        """
        Создать StateManagementService для разработки с минимальными зависимостями
        
        Args:
            enable_database: Использовать ли database репозитории
            enable_statistics: Включить ли сбор статистики
            
        Returns:
            StateManagementService для разработки
        """
        try:
            # Создаем in-memory репозитории
            state_repo = InMemoryStateRepository()
            
            # Опционально добавляем статистику
            statistics_repo = None
            if enable_statistics:
                try:
                    from src.infrastructure.repositories.in_memory_statistics_repository import InMemoryStatisticsRepository
                    statistics_repo = InMemoryStatisticsRepository()
                except ImportError:
                    logger.warning("⚠️ InMemoryStatisticsRepository not available")
            
            state_manager = StateManagementService(
                state_repo=state_repo,
                statistics_repo=statistics_repo
            )
            
            # Более частые снимки для разработки
            state_manager.snapshot_interval_seconds = 60  # 1 минута
            
            logger.info("🛠️ Development StateManagementService created")
            return state_manager
            
        except Exception as e:
            logger.error(f"❌ Failed to create development StateManagementService: {e}")
            raise
    
    @staticmethod
    def create_production_state_manager(
        config: Dict[str, Any],
        all_repositories: Dict[str, Any]
    ) -> StateManagementService:
        """
        Создать StateManagementService для продакшена со всеми зависимостями
        
        Args:
            config: Полная конфигурация приложения
            all_repositories: Словарь всех репозиториев системы
            
        Returns:
            Полностью настроенный StateManagementService
        """
        try:
            state_manager = StateManagerFactory.create_state_manager(
                config=config,
                deals_repo=all_repositories.get('deals'),
                orders_repo=all_repositories.get('orders'),
                statistics_repo=all_repositories.get('statistics'),
                config_repo=all_repositories.get('configuration'),
                db_manager=all_repositories.get('db_manager')
            )
            
            # Дополнительная конфигурация для продакшена
            state_config = config.get('state_management', {})
            
            # Настройка интервалов
            if 'snapshot_interval_seconds' in state_config:
                state_manager.snapshot_interval_seconds = state_config['snapshot_interval_seconds']
            
            logger.info("🚀 Production StateManagementService created")
            return state_manager
            
        except Exception as e:
            logger.error(f"❌ Failed to create production StateManagementService: {e}")
            raise
    
    @staticmethod
    def validate_state_manager_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация конфигурации для StateManagementService
        
        Args:
            config: Конфигурация для проверки
            
        Returns:
            Результат валидации с ошибками и предупреждениями
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            state_config = config.get('state_management', {})
            
            # Проверка типа репозитория
            repo_type = state_config.get('repository_type', 'in_memory')
            if repo_type not in ['in_memory', 'database']:
                result['errors'].append(f"Invalid repository_type: {repo_type}")
                result['valid'] = False
            
            # Проверка конфигурации снимков
            snapshot_config = state_config.get('snapshots', {})
            if 'interval_seconds' in snapshot_config:
                interval = snapshot_config['interval_seconds']
                if not isinstance(interval, int) or interval < 60:
                    result['errors'].append("snapshot interval_seconds must be integer >= 60")
                    result['valid'] = False
                elif interval < 300:
                    result['warnings'].append("snapshot interval < 5 minutes may impact performance")
            
            # Проверка конфигурации очистки
            cleanup_config = state_config.get('cleanup', {})
            if 'snapshots_days_to_keep' in cleanup_config:
                days = cleanup_config['snapshots_days_to_keep']
                if not isinstance(days, int) or days < 1:
                    result['errors'].append("snapshots_days_to_keep must be integer >= 1")
                    result['valid'] = False
                elif days < 7:
                    result['warnings'].append("keeping snapshots < 7 days may limit recovery options")
            
            return result
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Config validation error: {e}")
            return result