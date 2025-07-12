# Issue #13: SecurityService - Безопасность
### Статус: запланировано

**🏗️ Milestone:** M3  
**📈 Приоритет:** HIGH  
**🔗 Зависимости:** Issue #15 (ConfigurationService)

---

## 📝 Описание проблемы


### 🔍 Текущие проблемы безопасности:
- API ключи в открытом виде в config.json
- Private keys на диске без шифрования
- Нет аудита доступа к sensitive данным
- Логи могут содержать чувствительную информацию
- Отсутствие защиты от injection атак

### 🎯 Желаемый результат:
- Шифрование всех sensitive данных
- Безопасное хранение API ключей
- Аудит доступа к данным
- Защита от common атак
- Production-ready security

---

## 📋 Технические требования

### 🏗️ Архитектура

```python
class SecurityService:
    \"\"\"Централизованная система безопасности\"\"\"
    
    def __init__(self, master_key: str):
        self.encryption_key = self._derive_key(master_key)
        self.audit_logger = SecurityAuditLogger()
        
    async def encrypt_sensitive_data(self, data: str) -> str:
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
    async def store_api_keys(self, keys: Dict[str, str]) -> bool:
    async def get_api_key(self, service: str) -> str:
    async def validate_request_signature(self, request: Dict) -> bool:
    async def audit_access(self, action: str, resource: str, user: str):
    def sanitize_logs(self, log_message: str) -> str:
    def hash_password(self, password: str) -> str:
    def verify_password(self, password: str, hash: str) -> bool:

class SecureVault:
    \"\"\"Безопасное хранилище ключей\"\"\"
    
    async def store(self, key: str, value: str) -> bool:
    async def retrieve(self, key: str) -> Optional[str]:
    async def delete(self, key: str) -> bool:
    async def rotate_keys(self) -> bool:

class SecurityAuditLogger:
    \"\"\"Аудит безопасности\"\"\"
    
    async def log_access(self, event: SecurityEvent):
    async def log_failure(self, event: SecurityEvent);
    async def get_security_report(self, start: datetime, end: datetime) -> SecurityReport:
```

### 🔐 Схема безопасности

```python
@dataclass
class SecurityConfig:
    encryption_algorithm: str = 'AES-256-GCM'
    key_derivation: str = 'PBKDF2'
    hash_algorithm: str = 'SHA-256'
    audit_enabled: bool = True
    max_failed_attempts: int = 5
    key_rotation_days: int = 90

@dataclass
class SecurityEvent:
    timestamp: datetime
    event_type: str  # 'ACCESS', 'FAILURE', 'ROTATION', 'VIOLATION'
    resource: str
    user: str
    ip_address: Optional[str]
    success: bool
    details: Dict[str, Any]

@dataclass
class SecurityReport:
    period_start: datetime
    period_end: datetime
    total_access_attempts: int
    failed_attempts: int
    security_violations: List[SecurityEvent]
    recommendations: List[str]
```

---

## 🛠️ Детальная реализация

### 1. **Основной SecurityService**

**Файл:** `domain/services/security_service.py`

```python
import os
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta

class SecurityService:
    def __init__(self, master_password: str):
        self.salt = self._get_or_generate_salt()
        self.encryption_key = self._derive_key(master_password, self.salt)
        self.fernet = Fernet(self.encryption_key)
        self.audit_logger = SecurityAuditLogger()
        
        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        self.failed_attempts = {}
        
    def _get_or_generate_salt(self) -> bytes:
        \"\"\"Получить или сгенерировать соль для шифрования\"\"\"
        salt_file = 'security/salt.key'
        
        if os.path.exists(salt_file):
            with open(salt_file, 'rb') as f:
                return f.read()
        else:
            # Создать папку если не существует
            os.makedirs('security', exist_ok=True)
            
            # Сгенерировать новую соль
            salt = os.urandom(16)
            with open(salt_file, 'wb') as f:
                f.write(salt)
            return salt
            
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        \"\"\"Получение ключа шифрования из пароля\"\"\"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
        
    async def encrypt_sensitive_data(self, data: str) -> str:
        \"\"\"Шифрование чувствительных данных\"\"\"
        try:
            encrypted = self.fernet.encrypt(data.encode())
            await self.audit_logger.log_access(SecurityEvent(
                timestamp=datetime.now(),
                event_type='ENCRYPT',
                resource='sensitive_data',
                user='system',
                ip_address=None,
                success=True,
                details={'data_length': len(data)}
            ))
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            await self.audit_logger.log_failure(SecurityEvent(
                timestamp=datetime.now(),
                event_type='ENCRYPT',
                resource='sensitive_data', 
                user='system',
                ip_address=None,
                success=False,
                details={'error': str(e)}
            ))
            raise
            
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        \"\"\"Расшифровка чувствительных данных\"\"\"
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(decoded_data)
            
            await self.audit_logger.log_access(SecurityEvent(
                timestamp=datetime.now(),
                event_type='DECRYPT',
                resource='sensitive_data',
                user='system',
                ip_address=None,
                success=True,
                details={'data_length': len(decrypted)}
            ))
            
            return decrypted.decode()
        except Exception as e:
            await self.audit_logger.log_failure(SecurityEvent(
                timestamp=datetime.now(),
                event_type='DECRYPT',
                resource='sensitive_data',
                user='system', 
                ip_address=None,
                success=False,
                details={'error': str(e)}
            ))
            raise
            
    async def store_api_keys(self, keys: Dict[str, str]) -> bool:
        \"\"\"Безопасное хранение API ключей\"\"\"
        try:
            secure_vault = SecureVault(self.fernet)
            
            for service, api_key in keys.items():
                vault_key = f\"api_key_{service}\"
                success = await secure_vault.store(vault_key, api_key)
                
                if success:
                    await self.audit_logger.log_access(SecurityEvent(
                        timestamp=datetime.now(),
                        event_type='STORE_API_KEY',
                        resource=service,
                        user='system',
                        ip_address=None,
                        success=True,
                        details={'service': service}
                    ))
                else:
                    raise Exception(f\"Failed to store API key for {service}\")
                    
            return True
        except Exception as e:
            await self.audit_logger.log_failure(SecurityEvent(
                timestamp=datetime.now(),
                event_type='STORE_API_KEY',
                resource='multiple_services',
                user='system',
                ip_address=None,
                success=False,
                details={'error': str(e), 'services': list(keys.keys())}
            ))
            return False
            
    async def get_api_key(self, service: str) -> str:
        \"\"\"Получение API ключа\"\"\"
        
        # Проверка блокировки
        if self._is_locked_out('system'):
            raise SecurityException(\"Too many failed attempts. Access locked.\")
            
        try:
            secure_vault = SecureVault(self.fernet)
            vault_key = f\"api_key_{service}\"
            api_key = await secure_vault.retrieve(vault_key)
            
            if api_key:
                await self.audit_logger.log_access(SecurityEvent(
                    timestamp=datetime.now(),
                    event_type='RETRIEVE_API_KEY',
                    resource=service,
                    user='system',
                    ip_address=None,
                    success=True,
                    details={'service': service}
                ))
                
                # Сброс счетчика неудачных попыток
                self.failed_attempts.pop('system', None)
                return api_key
            else:
                raise SecurityException(f\"API key not found for service: {service}\")
                
        except Exception as e:
            # Увеличение счетчика неудачных попыток
            self._record_failed_attempt('system')
            
            await self.audit_logger.log_failure(SecurityEvent(
                timestamp=datetime.now(),
                event_type='RETRIEVE_API_KEY',
                resource=service,
                user='system',
                ip_address=None,
                success=False,
                details={'error': str(e), 'service': service}
            ))
            raise
            
    def sanitize_logs(self, log_message: str) -> str:
        \"\"\"Очистка логов от чувствительной информации\"\"\"
        
        # Паттерны для скрытия чувствительных данных
        sensitive_patterns = [
            (r'(api[_-]?key[_-]?[=:]\\s*)([a-zA-Z0-9]{20,})', r'\\1***HIDDEN***'),
            (r'(password[_-]?[=:]\\s*)([a-zA-Z0-9]{8,})', r'\\1***HIDDEN***'),
            (r'(secret[_-]?[=:]\\s*)([a-zA-Z0-9]{16,})', r'\\1***HIDDEN***'),
            (r'(token[_-]?[=:]\\s*)([a-zA-Z0-9]{20,})', r'\\1***HIDDEN***'),
            # Bitcoin/crypto addresses
            (r'\\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\\b', '***CRYPTO_ADDRESS***'),
            # Email addresses
            (r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', '***EMAIL***'),
        ]
        
        sanitized = log_message
        for pattern, replacement in sensitive_patterns:
            sanitized = re.sub(pattern, replacement, sanitized)
            
        return sanitized
        
    def hash_password(self, password: str) -> str:
        \"\"\"Хеширование пароля\"\"\"
        # Генерация соли для пароля
        salt = secrets.token_hex(16)
        
        # Создание хеша
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        # Комбинирование соли и хеша
        return f\"{salt}:{password_hash.hex()}\"
        
    def verify_password(self, password: str, stored_hash: str) -> bool:
        \"\"\"Проверка пароля\"\"\"
        try:
            salt, hash_hex = stored_hash.split(':')
            
            # Воссоздание хеша
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            
            return password_hash.hex() == hash_hex
        except Exception:
            return False
            
    def _is_locked_out(self, user: str) -> bool:
        \"\"\"Проверка блокировки пользователя\"\"\"
        if user not in self.failed_attempts:
            return False
            
        attempts, last_attempt = self.failed_attempts[user]
        
        # Если прошло достаточно времени, сбрасываем счетчик
        if datetime.now() - last_attempt > self.lockout_duration:
            del self.failed_attempts[user]
            return False
            
        return attempts >= self.max_failed_attempts
        
    def _record_failed_attempt(self, user: str):
        \"\"\"Запись неудачной попытки\"\"\"
        now = datetime.now()
        
        if user in self.failed_attempts:
            attempts, _ = self.failed_attempts[user]
            self.failed_attempts[user] = (attempts + 1, now)
        else:
            self.failed_attempts[user] = (1, now)

class SecureVault:
    def __init__(self, fernet: Fernet):
        self.fernet = fernet
        self.vault_file = 'security/vault.enc'
        
    async def store(self, key: str, value: str) -> bool:
        \"\"\"Сохранение значения в зашифрованном виде\"\"\"
        try:
            # Загрузка существующих данных
            vault_data = await self._load_vault()
            
            # Добавление нового ключа
            vault_data[key] = value
            
            # Сохранение обратно
            return await self._save_vault(vault_data)
        except Exception as e:
            return False
            
    async def retrieve(self, key: str) -> Optional[str]:
        \"\"\"Получение значения из хранилища\"\"\"
        try:
            vault_data = await self._load_vault()
            return vault_data.get(key)
        except Exception:
            return None
            
    async def delete(self, key: str) -> bool:
        \"\"\"Удаление ключа из хранилища\"\"\"
        try:
            vault_data = await self._load_vault()
            if key in vault_data:
                del vault_data[key]
                return await self._save_vault(vault_data)
            return True
        except Exception:
            return False
            
    async def _load_vault(self) -> Dict[str, str]:
        \"\"\"Загрузка и расшифровка хранилища\"\"\"
        if not os.path.exists(self.vault_file):
            return {}
            
        with open(self.vault_file, 'rb') as f:
            encrypted_data = f.read()
            
        if not encrypted_data:
            return {}
            
        decrypted_data = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
        
    async def _save_vault(self, vault_data: Dict[str, str]) -> bool:
        \"\"\"Шифрование и сохранение хранилища\"\"\"
        try:
            # Создать папку если не существует
            os.makedirs('security', exist_ok=True)
            
            # Шифрование данных
            json_data = json.dumps(vault_data)
            encrypted_data = self.fernet.encrypt(json_data.encode())
            
            # Атомарная запись
            temp_file = self.vault_file + '.tmp'
            with open(temp_file, 'wb') as f:
                f.write(encrypted_data)
                
            # Переименование для атомарности
            os.rename(temp_file, self.vault_file)
            return True
        except Exception:
            return False

class SecurityAuditLogger:
    def __init__(self):
        self.log_file = 'security/audit.log'
        
    async def log_access(self, event: SecurityEvent):
        \"\"\"Логирование успешного доступа\"\"\"
        await self._write_log(event)
        
    async def log_failure(self, event: SecurityEvent):
        \"\"\"Логирование неудачного доступа\"\"\"
        await self._write_log(event)
        
    async def _write_log(self, event: SecurityEvent):
        \"\"\"Запись в аудит лог\"\"\"
        try:
            os.makedirs('security', exist_ok=True)
            
            log_entry = {
                'timestamp': event.timestamp.isoformat(),
                'event_type': event.event_type,
                'resource': event.resource,
                'user': event.user,
                'ip_address': event.ip_address,
                'success': event.success,
                'details': event.details
            }
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\\n')
        except Exception:
            # Не должны падать если не можем писать аудит
            pass

class SecurityException(Exception):
    \"\"\"Исключение безопасности\"\"\"
    pass
```

### 2. **Миграция конфигурации на SecurityService**

**Файл:** `infrastructure/config/secure_configuration_service.py`

```python
from domain.services.security_service import SecurityService
import json
import os

class SecureConfigurationService:
    def __init__(self, security_service: SecurityService):
        self.security = security_service
        self.config_file = 'config/config.json'
        
    async def migrate_to_secure_config(self):
        \"\"\"Миграция существующего config.json на безопасное хранение\"\"\"
        
        if not os.path.exists(self.config_file):
            return
            
        # Читаем текущий конфиг
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            
        # Извлекаем sensitive данные
        sensitive_keys = {}
        
        if 'binance' in config:
            for env in ['sandbox', 'production']:
                if env in config['binance'] and 'apiKey' in config['binance'][env]:
                    api_key = config['binance'][env]['apiKey']
                    sensitive_keys[f'binance_{env}_api_key'] = api_key
                    
                    # Заменяем в конфиге на placeholder
                    config['binance'][env]['apiKey'] = '***SECURE_VAULT***'
                    
        # Сохраняем sensitive данные в SecurityService
        await self.security.store_api_keys(sensitive_keys)
        
        # Сохраняем обновленный конфиг
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(\"✅ Configuration migrated to secure storage\")
        
    async def get_api_key(self, service: str, environment: str) -> str:
        \"\"\"Получение API ключа из безопасного хранилища\"\"\"
        vault_key = f\"{service}_{environment}_api_key\"
        return await self.security.get_api_key(vault_key)
```

---

## ✅ Критерии приемки

### Функциональные требования:
- [ ] Все API ключи зашифрованы и безопасно хранятся
- [ ] Логи очищены от sensitive информации
- [ ] Аудит всех обращений к чувствительным данным
- [ ] Защита от brute force атак
- [ ] Миграция существующего config.json

### Безопасность:
- [ ] AES-256 шифрование для всех sensitive данных
- [ ] PBKDF2 для деривации ключей
- [ ] Блокировка после неудачных попыток
- [ ] Атомарные операции записи

### Совместимость:
- [ ] Seamless интеграция с существующим кодом
- [ ] Backward compatibility для конфигурации
- [ ] Простая процедура первичной настройки

---

## 🚧 Риски и митигация

### Риск 1: Потеря master password
**Митигация:** Backup процедуры, recovery mechanism

### Риск 2: Performance overhead от шифрования
**Митигация:** Кеширование расшифрованных ключей в памяти

### Риск 3: Сложность первичной настройки
**Митигация:** Автоматическая миграция и четкая документация

---

## 📚 Связанные материалы

- Issue #15: ConfigurationService  
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [Python Cryptography Documentation](https://cryptography.io/)
