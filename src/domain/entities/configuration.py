from dataclasses import dataclass
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
import json
from enum import Enum


class ConfigCategory(Enum):
    """Категории конфигурации"""
    TRADING = "trading"
    RISK_MANAGEMENT = "risk_management"
    TECHNICAL_INDICATORS = "technical_indicators"
    ORDER_BOOK = "order_book"
    EXCHANGE = "exchange"
    SYSTEM = "system"
    NOTIFICATIONS = "notifications"
    LOGGING = "logging"
    PERFORMANCE = "performance"


class ConfigType(Enum):
    """Типы конфигурационных значений"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    DICT = "dict"


@dataclass
class Configuration:
    """Сущность для управления динамической конфигурацией"""
    
    def __init__(
        self,
        key: str,
        value: Any,
        category: ConfigCategory,
        config_type: ConfigType = ConfigType.STRING,
        description: Optional[str] = None,
        is_secret: bool = False,
        is_required: bool = False,
        default_value: Optional[Any] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        self.key = key
        self.value = value
        self.category = category
        self.config_type = config_type
        self.description = description
        self.is_secret = is_secret
        self.is_required = is_required
        self.default_value = default_value
        self.validation_rules = validation_rules or {}
        self.tags = tags or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Валидация при создании
        self._validate_value()
    
    @property
    def full_key(self) -> str:
        """Полный ключ с категорией"""
        return f"{self.category.value}.{self.key}"
    
    def _validate_value(self) -> None:
        """Валидация значения согласно типу и правилам"""
        # Проверка типа
        if not self._is_type_valid():
            raise ValueError(f"Value {self.value} is not valid for type {self.config_type.value}")
        
        # Применение правил валидации
        self._apply_validation_rules()
    
    def _is_type_valid(self) -> bool:
        """Проверка соответствия типу"""
        if self.value is None:
            return not self.is_required
        
        type_mapping = {
            ConfigType.STRING: str,
            ConfigType.INTEGER: int,
            ConfigType.FLOAT: (int, float),
            ConfigType.BOOLEAN: bool,
            ConfigType.LIST: list,
            ConfigType.DICT: dict
        }
        
        if self.config_type == ConfigType.JSON:
            # JSON может быть любым сериализуемым типом
            try:
                json.dumps(self.value)
                return True
            except (TypeError, ValueError):
                return False
        
        expected_type = type_mapping.get(self.config_type)
        if expected_type:
            return isinstance(self.value, expected_type)
        
        return True
    
    def _apply_validation_rules(self) -> None:
        """Применение правил валидации"""
        if not self.validation_rules:
            return
        
        # Проверка минимального значения
        if "min_value" in self.validation_rules and self.is_numeric():
            min_val = self.validation_rules["min_value"]
            if self.get_numeric_value() < min_val:
                raise ValueError(f"Value {self.value} is less than minimum {min_val}")
        
        # Проверка максимального значения
        if "max_value" in self.validation_rules and self.is_numeric():
            max_val = self.validation_rules["max_value"]
            if self.get_numeric_value() > max_val:
                raise ValueError(f"Value {self.value} is greater than maximum {max_val}")
        
        # Проверка длины строки
        if "max_length" in self.validation_rules and isinstance(self.value, str):
            max_len = self.validation_rules["max_length"]
            if len(self.value) > max_len:
                raise ValueError(f"String length {len(self.value)} exceeds maximum {max_len}")
        
        # Проверка допустимых значений
        if "allowed_values" in self.validation_rules:
            allowed = self.validation_rules["allowed_values"]
            if self.value not in allowed:
                raise ValueError(f"Value {self.value} not in allowed values: {allowed}")
        
        # Проверка регулярного выражения
        if "regex" in self.validation_rules and isinstance(self.value, str):
            import re
            pattern = self.validation_rules["regex"]
            if not re.match(pattern, self.value):
                raise ValueError(f"Value {self.value} does not match pattern {pattern}")
    
    def is_numeric(self) -> bool:
        """Проверка, является ли значение числовым"""
        return isinstance(self.value, (int, float))
    
    def get_numeric_value(self) -> Optional[float]:
        """Получение числового значения"""
        if self.is_numeric():
            return float(self.value)
        return None
    
    def get_bool_value(self) -> Optional[bool]:
        """Получение булевого значения с умной конвертацией"""
        if isinstance(self.value, bool):
            return self.value
        if isinstance(self.value, str):
            return self.value.lower() in ("true", "yes", "1", "on", "enabled")
        if isinstance(self.value, (int, float)):
            return bool(self.value)
        return None
    
    def get_list_value(self) -> Optional[List[Any]]:
        """Получение списка с умной конвертацией"""
        if isinstance(self.value, list):
            return self.value
        if isinstance(self.value, str):
            # Пробуем распарсить как JSON или разделить по запятым
            try:
                parsed = json.loads(self.value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # Разделяем по запятым
                return [item.strip() for item in self.value.split(",") if item.strip()]
        return None
    
    def get_dict_value(self) -> Optional[Dict[str, Any]]:
        """Получение словаря с умной конвертацией"""
        if isinstance(self.value, dict):
            return self.value
        if isinstance(self.value, str):
            try:
                parsed = json.loads(self.value)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        return None
    
    def update_value(self, new_value: Any) -> None:
        """Обновление значения с валидацией"""
        old_value = self.value
        self.value = new_value
        self.updated_at = datetime.now()
        
        try:
            self._validate_value()
        except ValueError:
            # Откатываем изменения при ошибке валидации
            self.value = old_value
            raise
    
    def reset_to_default(self) -> bool:
        """Сброс к значению по умолчанию"""
        if self.default_value is not None:
            self.update_value(self.default_value)
            return True
        return False
    
    def add_tag(self, tag: str) -> None:
        """Добавление тега"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """Удаление тега"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def has_tag(self, tag: str) -> bool:
        """Проверка наличия тега"""
        return tag in self.tags
    
    def is_modified(self) -> bool:
        """Проверка, было ли значение изменено"""
        return self.value != self.default_value
    
    def get_display_value(self) -> str:
        """Получение значения для отображения (скрывает секреты)"""
        if self.is_secret:
            return "***HIDDEN***" if self.value else "***NOT_SET***"
        
        if isinstance(self.value, (dict, list)):
            return json.dumps(self.value, indent=2)
        
        return str(self.value)
    
    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Конвертация в словарь для сериализации"""
        result = {
            "key": self.key,
            "category": self.category.value,
            "config_type": self.config_type.value,
            "description": self.description,
            "is_secret": self.is_secret,
            "is_required": self.is_required,
            "default_value": self.default_value,
            "validation_rules": self.validation_rules,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_modified": self.is_modified()
        }
        
        # Включаем значение только если не секрет или явно запрошено
        if include_secrets or not self.is_secret:
            result["value"] = self.value
        else:
            result["value"] = self.get_display_value()
        
        return result
    
    def to_json(self, include_secrets: bool = False) -> str:
        """Конвертация в JSON строку"""
        return json.dumps(self.to_dict(include_secrets))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Configuration':
        """Создание из словаря"""
        config = cls(
            key=data["key"],
            value=data["value"],
            category=ConfigCategory(data["category"]),
            config_type=ConfigType(data.get("config_type", "string")),
            description=data.get("description"),
            is_secret=data.get("is_secret", False),
            is_required=data.get("is_required", False),
            default_value=data.get("default_value"),
            validation_rules=data.get("validation_rules", {}),
            tags=data.get("tags", [])
        )
        
        if "created_at" in data:
            config.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            config.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return config
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Configuration':
        """Создание из JSON строки"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        return f"Configuration({self.full_key}={self.get_display_value()})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Configuration):
            return False
        return self.full_key == other.full_key