import asyncio
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json

from src.domain.entities.configuration import Configuration, ConfigCategory, ConfigType
from src.domain.repositories.i_configuration_repository import IConfigurationRepository
from src.infrastructure.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PostgreSQLConfigurationRepository(IConfigurationRepository):
    """
    PostgreSQL реализация репозитория конфигурации
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._ensure_postgresql()
        self._config_cache = {}  # Кэш для частых обращений
    
    def _ensure_postgresql(self):
        """Проверяем, что используется PostgreSQL"""
        if self.db_manager.db_type != 'postgresql':
            raise ValueError("PostgreSQLConfigurationRepository requires PostgreSQL database")
    
    async def save_config(self, config: Configuration) -> bool:
        """Сохранить конфигурацию"""
        try:
            query = """
                INSERT INTO configuration (
                    key, category, value, config_type, description,
                    is_secret, is_required, default_value, validation_rules, tags
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (key, category) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    config_type = EXCLUDED.config_type,
                    description = EXCLUDED.description,
                    is_secret = EXCLUDED.is_secret,
                    is_required = EXCLUDED.is_required,
                    default_value = EXCLUDED.default_value,
                    validation_rules = EXCLUDED.validation_rules,
                    tags = EXCLUDED.tags
            """
            
            params = (
                config.key,
                config.category.value,
                config.value,
                config.config_type.value,
                config.description,
                config.is_secret,
                config.is_required,
                config.default_value,
                json.dumps(config.validation_rules or {}),
                config.tags or []
            )
            
            await self.db_manager.execute_command(query, params)
            
            # Обновляем кэш
            cache_key = f"{config.key}_{config.category.value}"
            self._config_cache[cache_key] = config
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    async def get_config(
        self,
        key: str,
        category: ConfigCategory,
        use_cache: bool = True
    ) -> Optional[Configuration]:
        """Получить конфигурацию"""
        try:
            cache_key = f"{key}_{category.value}"
            
            # Проверяем кэш
            if use_cache and cache_key in self._config_cache:
                return self._config_cache[cache_key]
            
            query = """
                SELECT id, key, category, value, config_type, description,
                       is_secret, is_required, default_value, validation_rules,
                       tags, created_at, updated_at
                FROM configuration
                WHERE key = $1 AND category = $2
            """
            
            rows = await self.db_manager.execute_query(query, (key, category.value))
            
            if not rows:
                return None
            
            config = self._row_to_config(rows[0])
            
            # Обновляем кэш
            if use_cache:
                self._config_cache[cache_key] = config
            
            return config
            
        except Exception as e:
            logger.error(f"Error getting configuration: {e}")
            return None
    
    async def get_config_value(
        self,
        key: str,
        category: ConfigCategory,
        default_value: Any = None,
        expected_type: Optional[ConfigType] = None
    ) -> Any:
        """Получить значение конфигурации с преобразованием типа"""
        try:
            config = await self.get_config(key, category)
            
            if not config:
                return default_value
            
            # Определяем тип для преобразования
            target_type = expected_type or config.config_type
            
            return self._convert_config_value(config.value, target_type, default_value)
            
        except Exception as e:
            logger.error(f"Error getting config value: {e}")
            return default_value
    
    async def set_config_value(
        self,
        key: str,
        category: ConfigCategory,
        value: Any,
        config_type: Optional[ConfigType] = None,
        description: Optional[str] = None
    ) -> bool:
        """Установить значение конфигурации"""
        try:
            # Получаем существующую конфигурацию или создаем новую
            existing_config = await self.get_config(key, category, use_cache=False)
            
            if existing_config:
                # Обновляем существующую
                existing_config.value = str(value)
                if config_type:
                    existing_config.config_type = config_type
                if description:
                    existing_config.description = description
                config = existing_config
            else:
                # Создаем новую
                config = Configuration(
                    key=key,
                    category=category,
                    value=str(value),
                    config_type=config_type or ConfigType.STRING,
                    description=description
                )
            
            return await self.save_config(config)
            
        except Exception as e:
            logger.error(f"Error setting config value: {e}")
            return False
    
    async def get_configs_by_category(
        self,
        category: ConfigCategory,
        include_secrets: bool = False
    ) -> List[Configuration]:
        """Получить все конфигурации по категории"""
        try:
            query = """
                SELECT id, key, category, value, config_type, description,
                       is_secret, is_required, default_value, validation_rules,
                       tags, created_at, updated_at
                FROM configuration
                WHERE category = $1
            """
            
            if not include_secrets:
                query += " AND is_secret = false"
            
            query += " ORDER BY key"
            
            rows = await self.db_manager.execute_query(query, (category.value,))
            
            return [self._row_to_config(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting configs by category: {e}")
            return []
    
    async def get_all_configs(
        self,
        include_secrets: bool = False
    ) -> Dict[str, List[Configuration]]:
        """Получить все конфигурации сгруппированные по категориям"""
        try:
            query = """
                SELECT id, key, category, value, config_type, description,
                       is_secret, is_required, default_value, validation_rules,
                       tags, created_at, updated_at
                FROM configuration
            """
            
            if not include_secrets:
                query += " WHERE is_secret = false"
            
            query += " ORDER BY category, key"
            
            rows = await self.db_manager.execute_query(query)
            
            # Группируем по категориям
            result = {}
            for row in rows:
                config = self._row_to_config(row)
                category = config.category.value
                
                if category not in result:
                    result[category] = []
                
                result[category].append(config)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all configs: {e}")
            return {}
    
    async def get_required_configs(self) -> List[Configuration]:
        """Получить все обязательные конфигурации"""
        try:
            query = """
                SELECT id, key, category, value, config_type, description,
                       is_secret, is_required, default_value, validation_rules,
                       tags, created_at, updated_at
                FROM configuration
                WHERE is_required = true
                ORDER BY category, key
            """
            
            rows = await self.db_manager.execute_query(query)
            
            return [self._row_to_config(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting required configs: {e}")
            return []
    
    async def validate_config(self, config: Configuration) -> Dict[str, Any]:
        """Валидация конфигурации"""
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Проверка типа
            try:
                converted_value = self._convert_config_value(
                    config.value, 
                    config.config_type, 
                    None
                )
                
                # Применяем правила валидации
                if config.validation_rules:
                    self._apply_validation_rules(
                        converted_value, 
                        config.validation_rules, 
                        validation_result
                    )
                
            except (ValueError, TypeError) as e:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Type conversion error: {e}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {e}"],
                'warnings': []
            }
    
    async def delete_config(
        self,
        key: str,
        category: ConfigCategory
    ) -> bool:
        """Удалить конфигурацию"""
        try:
            query = "DELETE FROM configuration WHERE key = $1 AND category = $2"
            
            result = await self.db_manager.execute_command(query, (key, category.value))
            
            # Удаляем из кэша
            cache_key = f"{key}_{category.value}"
            self._config_cache.pop(cache_key, None)
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting configuration: {e}")
            return False
    
    async def reset_to_defaults(self, category: Optional[ConfigCategory] = None) -> int:
        """Сбросить конфигурации к значениям по умолчанию"""
        try:
            query = """
                UPDATE configuration 
                SET value = default_value 
                WHERE default_value IS NOT NULL
            """
            params = []
            
            if category:
                query += " AND category = $1"
                params.append(category.value)
            
            result = await self.db_manager.execute_command(query, tuple(params))
            
            # Очищаем кэш
            self._config_cache.clear()
            
            return result
            
        except Exception as e:
            logger.error(f"Error resetting to defaults: {e}")
            return 0
    
    async def export_configs(
        self,
        category: Optional[ConfigCategory] = None,
        include_secrets: bool = False
    ) -> Dict[str, Any]:
        """Экспорт конфигураций в JSON"""
        try:
            if category:
                configs_dict = {category.value: await self.get_configs_by_category(category, include_secrets)}
            else:
                configs_dict = await self.get_all_configs(include_secrets)
            
            # Преобразуем в словарь для экспорта
            export_data = {}
            for cat, configs in configs_dict.items():
                export_data[cat] = {}
                for config in configs:
                    export_data[cat][config.key] = {
                        'value': config.value,
                        'type': config.config_type.value,
                        'description': config.description,
                        'is_required': config.is_required,
                        'default_value': config.default_value,
                        'tags': config.tags
                    }
            
            return {
                'exported_at': datetime.now().isoformat(),
                'include_secrets': include_secrets,
                'configurations': export_data
            }
            
        except Exception as e:
            logger.error(f"Error exporting configs: {e}")
            return {}
    
    async def import_configs(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Импорт конфигураций из JSON"""
        try:
            result = {
                'imported': 0,
                'updated': 0,
                'errors': []
            }
            
            configurations = config_data.get('configurations', {})
            
            for category_name, category_configs in configurations.items():
                try:
                    category = ConfigCategory(category_name)
                except ValueError:
                    result['errors'].append(f"Unknown category: {category_name}")
                    continue
                
                for key, config_info in category_configs.items():
                    try:
                        # Проверяем существование
                        existing = await self.get_config(key, category, use_cache=False)
                        
                        # Создаем объект конфигурации
                        config = Configuration(
                            key=key,
                            category=category,
                            value=str(config_info['value']),
                            config_type=ConfigType(config_info.get('type', 'string')),
                            description=config_info.get('description'),
                            is_required=config_info.get('is_required', False),
                            default_value=config_info.get('default_value'),
                            tags=config_info.get('tags', [])
                        )
                        
                        if await self.save_config(config):
                            if existing:
                                result['updated'] += 1
                            else:
                                result['imported'] += 1
                        else:
                            result['errors'].append(f"Failed to save: {category_name}.{key}")
                    
                    except Exception as e:
                        result['errors'].append(f"Error importing {category_name}.{key}: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error importing configs: {e}")
            return {'imported': 0, 'updated': 0, 'errors': [str(e)]}
    
    def clear_cache(self) -> None:
        """Очистить кэш конфигураций"""
        self._config_cache.clear()
    
    def _convert_config_value(
        self,
        value: str,
        config_type: ConfigType,
        default_value: Any = None
    ) -> Any:
        """Преобразовать строковое значение к нужному типу"""
        try:
            if value is None:
                return default_value
            
            if config_type == ConfigType.STRING:
                return str(value)
            elif config_type == ConfigType.INTEGER:
                return int(value)
            elif config_type == ConfigType.FLOAT:
                return float(value)
            elif config_type == ConfigType.BOOLEAN:
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif config_type == ConfigType.JSON:
                return json.loads(value) if isinstance(value, str) else value
            elif config_type == ConfigType.LIST:
                if isinstance(value, str):
                    return json.loads(value)
                return list(value) if hasattr(value, '__iter__') else [value]
            elif config_type == ConfigType.DICT:
                if isinstance(value, str):
                    return json.loads(value)
                return dict(value) if isinstance(value, dict) else {}
            else:
                return value
                
        except Exception as e:
            logger.warning(f"Error converting config value '{value}' to {config_type}: {e}")
            return default_value
    
    def _apply_validation_rules(
        self,
        value: Any,
        rules: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Применить правила валидации"""
        try:
            # Проверка минимального значения
            if 'min' in rules and isinstance(value, (int, float)):
                if value < rules['min']:
                    result['valid'] = False
                    result['errors'].append(f"Value {value} is less than minimum {rules['min']}")
            
            # Проверка максимального значения
            if 'max' in rules and isinstance(value, (int, float)):
                if value > rules['max']:
                    result['valid'] = False
                    result['errors'].append(f"Value {value} is greater than maximum {rules['max']}")
            
            # Проверка допустимых значений
            if 'choices' in rules:
                if value not in rules['choices']:
                    result['valid'] = False
                    result['errors'].append(f"Value {value} not in allowed choices: {rules['choices']}")
            
            # Проверка регулярного выражения
            if 'pattern' in rules and isinstance(value, str):
                import re
                if not re.match(rules['pattern'], value):
                    result['valid'] = False
                    result['errors'].append(f"Value '{value}' does not match pattern '{rules['pattern']}'")
            
        except Exception as e:
            result['warnings'].append(f"Validation rule error: {e}")
    
    def _row_to_config(self, row: Dict[str, Any]) -> Configuration:
        """Преобразовать строку БД в объект Configuration"""
        try:
            validation_rules = row.get('validation_rules', '{}')
            if isinstance(validation_rules, str):
                validation_rules = json.loads(validation_rules)
            elif validation_rules is None:
                validation_rules = {}
            
            return Configuration(
                key=row['key'],
                category=ConfigCategory(row['category']),
                value=row['value'],
                config_type=ConfigType(row['config_type']),
                description=row.get('description'),
                is_secret=bool(row.get('is_secret', False)),
                is_required=bool(row.get('is_required', False)),
                default_value=row.get('default_value'),
                validation_rules=validation_rules,
                tags=row.get('tags', [])
            )
            
        except Exception as e:
            logger.error(f"Error converting row to Configuration: {e}")
            logger.debug(f"Row data: {row}")
            raise