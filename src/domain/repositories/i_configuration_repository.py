from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from src.domain.entities.configuration import Configuration, ConfigCategory, ConfigType


class IConfigurationRepository(ABC):
    """Интерфейс репозитория для управления динамической конфигурацией"""
    
    @abstractmethod
    async def save(self, config: Configuration) -> None:
        """Сохранить конфигурацию"""
        pass
    
    @abstractmethod
    async def save_batch(self, configs: List[Configuration]) -> None:
        """Сохранить пакет конфигураций"""
        pass
    
    @abstractmethod
    async def get_by_key(self, key: str, category: ConfigCategory) -> Optional[Configuration]:
        """Получить конфигурацию по ключу и категории"""
        pass
    
    @abstractmethod
    async def get_by_full_key(self, full_key: str) -> Optional[Configuration]:
        """Получить конфигурацию по полному ключу (category.key)"""
        pass
    
    @abstractmethod
    async def get_by_category(self, category: ConfigCategory) -> List[Configuration]:
        """Получить все конфигурации категории"""
        pass
    
    @abstractmethod
    async def get_all(self, include_secrets: bool = False) -> List[Configuration]:
        """Получить все конфигурации"""
        pass
    
    @abstractmethod
    async def get_by_tags(self, tags: List[str]) -> List[Configuration]:
        """Получить конфигурации по тегам"""
        pass
    
    @abstractmethod
    async def get_required_configs(self) -> List[Configuration]:
        """Получить обязательные конфигурации"""
        pass
    
    @abstractmethod
    async def get_modified_configs(self) -> List[Configuration]:
        """Получить измененные конфигурации (отличающиеся от default)"""
        pass
    
    @abstractmethod
    async def update_value(
        self, 
        key: str, 
        category: ConfigCategory, 
        new_value: Any
    ) -> Optional[Configuration]:
        """Обновить значение конфигурации"""
        pass
    
    @abstractmethod
    async def delete(self, key: str, category: ConfigCategory) -> bool:
        """Удалить конфигурацию"""
        pass
    
    @abstractmethod
    async def reset_to_default(self, key: str, category: ConfigCategory) -> Optional[Configuration]:
        """Сбросить конфигурацию к значению по умолчанию"""
        pass
    
    @abstractmethod
    async def reset_category_to_default(self, category: ConfigCategory) -> int:
        """Сбросить всю категорию к значениям по умолчанию"""
        pass
    
    @abstractmethod
    async def validate_all(self) -> Dict[str, List[str]]:
        """Валидировать все конфигурации (возвращает ошибки по ключам)"""
        pass
    
    @abstractmethod
    async def get_config_value(
        self, 
        key: str, 
        category: ConfigCategory,
        default: Any = None
    ) -> Any:
        """Получить только значение конфигурации"""
        pass
    
    @abstractmethod
    async def set_config_value(
        self, 
        key: str, 
        category: ConfigCategory,
        value: Any,
        description: Optional[str] = None,
        config_type: ConfigType = ConfigType.STRING
    ) -> Configuration:
        """Установить значение конфигурации (создать или обновить)"""
        pass
    
    @abstractmethod
    async def get_secrets(self) -> List[Configuration]:
        """Получить секретные конфигурации"""
        pass
    
    @abstractmethod
    async def export_to_dict(
        self, 
        category: Optional[ConfigCategory] = None,
        include_secrets: bool = False
    ) -> Dict[str, Any]:
        """Экспортировать конфигурации в словарь"""
        pass
    
    @abstractmethod
    async def import_from_dict(
        self, 
        config_dict: Dict[str, Any],
        category: Optional[ConfigCategory] = None,
        overwrite_existing: bool = True
    ) -> int:
        """Импортировать конфигурации из словаря (возвращает количество импортированных)"""
        pass
    
    @abstractmethod
    async def backup_configs(self, backup_name: str) -> str:
        """Создать резервную копию конфигураций"""
        pass
    
    @abstractmethod
    async def restore_configs(self, backup_name: str) -> int:
        """Восстановить конфигурации из резервной копии"""
        pass
    
    @abstractmethod
    async def count_by_category(self, category: ConfigCategory) -> int:
        """Подсчитать количество конфигураций в категории"""
        pass
    
    @abstractmethod
    async def get_all_categories(self) -> List[ConfigCategory]:
        """Получить все используемые категории"""
        pass