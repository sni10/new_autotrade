# Issue #8: ConfigurationService - Управление конфигурацией

**💰 Стоимость:** $150 (10 часов × $15/час)  
**🔥 Приоритет:** ВЫСОКИЙ  
**🏗️ Milestone:** M2 - Персистентность и управление данными  
**🏷️ Labels:** `high-priority`, `security`, `configuration`, `environment`

## 📝 Описание проблемы

В текущей версии критические проблемы с конфигурацией:
- **API ключи в открытом виде** в config.json - серьезная уязвимость безопасности
- **Хардкод путей и настроек** в коде - сложность развертывания
- **Отсутствие валидации конфигурации** - runtime ошибки из-за неверных настроек
- **Невозможность hot-reload** настроек без перезапуска
- **Нет разделения по окружениям** (dev/staging/prod)

Это критично для production deployment и security compliance.

## 🎯 Цель

Создать безопасную, гибкую систему управления конфигурацией с поддержкой переменных окружения, валидации и hot-reload.

## 🔧 Техническое решение

### 1. Создать `infrastructure/config/configuration_service.py`

```python
class ConfigurationService:
    def __init__(self, env_file: str = '.env'):
        self.env_file = env_file
        self.config_cache = {}
        self.validators = {}
        self.watchers = {}
        self.encryption_key = None
        
    async def initialize(self):
        \"\"\"Инициализация сервиса конфигурации\"\"\"
        
    async def get_config(self, key: str, default=None) -> Any:
        \"\"\"Получение значения конфигурации\"\"\"
        
    async def set_config(self, key: str, value: Any, persist: bool = True):
        \"\"\"Установка значения конфигурации\"\"\"
        
    async def get_secure_config(self, key: str) -> str:
        \"\"\"Получение зашифрованного значения (API ключи)\"\"\"
        
    async def validate_all_config(self) -> ConfigValidationResult:
        \"\"\"Валидация всей конфигурации\"\"\"
        
    async def reload_config(self):
        \"\"\"Hot-reload конфигурации без перезапуска\"\"\"
        
    async def watch_config_changes(self, callback):
        \"\"\"Отслеживание изменений конфигурации\"\"\"
        
    def register_validator(self, key: str, validator: Callable):
        \"\"\"Регистрация валидатора для ключа\"\"\"
```

### 2. Структура конфигурации

```python
@dataclass
class TradingConfig:
    \"\"\"Торговые настройки\"\"\"
    symbol: str
    budget_per_deal: float
    max_open_deals: int
    profit_markup_percent: float
    order_lifetime_seconds: int
    
    def validate(self) -> List[str]:
        errors = []
        if self.budget_per_deal <= 0:
            errors.append(\"Budget per deal must be positive\")
        if self.max_open_deals <= 0:
            errors.append(\"Max open deals must be positive\")
        if not (0.1 <= self.profit_markup_percent <= 50):
            errors.append(\"Profit markup must be between 0.1% and 50%\")
        return errors

@dataclass
class RiskConfig:
    \"\"\"Настройки управления рисками\"\"\"
    max_position_percent: float
    stop_loss_percent: float
    max_daily_loss_percent: float
    max_open_positions: int
    emergency_close_positions: bool
    balance_buffer_percent: float
    
    def validate(self) -> List[str]:
        errors = []
        if not (1 <= self.max_position_percent <= 50):
            errors.append(\"Max position percent must be between 1% and 50%\")
        if not (-20 <= self.stop_loss_percent <= -1):
            errors.append(\"Stop loss must be between -20% and -1%\")
        return errors

@dataclass
class ExchangeConfig:
    \"\"\"Настройки биржи\"\"\"
    name: str
    api_key: str  # Зашифровано
    private_key_path: str
    sandbox_mode: bool
    rate_limit_requests_per_minute: int
    
    def validate(self) -> List[str]:
        errors = []
        if not self.api_key:
            errors.append(\"API key is required\")
        if not os.path.exists(self.private_key_path):
            errors.append(f\"Private key file not found: {self.private_key_path}\")
        return errors
```

### 3. Environment Variables и .env файл

```python
async def load_from_environment(self):
    \"\"\"Загрузка конфигурации из переменных окружения\"\"\"
    
    # Загружаем .env файл если существует
    if os.path.exists(self.env_file):
        load_dotenv(self.env_file)
        
    # Trading Configuration
    self.config_cache['trading'] = TradingConfig(
        symbol=os.getenv('TRADING_SYMBOL', 'VICUSDT'),
        budget_per_deal=float(os.getenv('TRADING_BUDGET_PER_DEAL', '10.0')),
        max_open_deals=int(os.getenv('TRADING_MAX_OPEN_DEALS', '3')),
        profit_markup_percent=float(os.getenv('TRADING_PROFIT_MARKUP', '1.5')),
        order_lifetime_seconds=int(os.getenv('TRADING_ORDER_LIFETIME', '3600'))
    )
    
    # Risk Configuration  
    self.config_cache['risk'] = RiskConfig(
        max_position_percent=float(os.getenv('RISK_MAX_POSITION_PERCENT', '5.0')),
        stop_loss_percent=float(os.getenv('RISK_STOP_LOSS_PERCENT', '-3.0')),
        max_daily_loss_percent=float(os.getenv('RISK_MAX_DAILY_LOSS', '-10.0')),
        max_open_positions=int(os.getenv('RISK_MAX_OPEN_POSITIONS', '3')),
        emergency_close_positions=os.getenv('RISK_EMERGENCY_CLOSE', 'true').lower() == 'true',
        balance_buffer_percent=float(os.getenv('RISK_BALANCE_BUFFER', '5.0'))
    )
    
    # Exchange Configuration
    environment = os.getenv('ENVIRONMENT', 'development')
    sandbox_mode = environment != 'production'
    
    self.config_cache['exchange'] = ExchangeConfig(
        name=os.getenv('EXCHANGE_NAME', 'binance'),
        api_key=await self._get_encrypted_value('BINANCE_API_KEY'),
        private_key_path=os.getenv('BINANCE_PRIVATE_KEY_PATH'),
        sandbox_mode=sandbox_mode,
        rate_limit_requests_per_minute=int(os.getenv('EXCHANGE_RATE_LIMIT', '1000'))
    )
    
    # Database Configuration
    self.config_cache['database'] = {
        'url': os.getenv('DATABASE_URL', 'sqlite:///data/trading_bot.db'),
        'pool_size': int(os.getenv('DATABASE_POOL_SIZE', '10')),
        'timeout': int(os.getenv('DATABASE_TIMEOUT', '30'))
    }
    
    # Logging Configuration
    self.config_cache['logging'] = {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'file_path': os.getenv('LOG_FILE_PATH', 'logs/trading_bot.log'),
        'max_file_size': os.getenv('LOG_MAX_FILE_SIZE', '100MB'),
        'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
    }
```

### 4. Шифрование чувствительных данных

```python
async def _initialize_encryption(self):
    \"\"\"Инициализация шифрования для sensitive данных\"\"\"
    
    # Используем ключ из переменной окружения или генерируем новый
    key_env = os.getenv('ENCRYPTION_KEY')
    if key_env:
        self.encryption_key = base64.b64decode(key_env)
    else:
        # Генерируем новый ключ (только для development)
        if os.getenv('ENVIRONMENT') == 'development':
            self.encryption_key = Fernet.generate_key()
            logger.warning(\"🔐 Generated new encryption key for development\")
        else:
            raise ConfigurationError(\"ENCRYPTION_KEY environment variable is required in production\")

async def _get_encrypted_value(self, env_key: str) -> str:
    \"\"\"Получение и расшифровка чувствительного значения\"\"\"
    encrypted_value = os.getenv(env_key)
    if not encrypted_value:
        raise ConfigurationError(f\"Required environment variable {env_key} not found\")
        
    try:
        # Если значение начинается с 'enc:', это зашифрованные данные
        if encrypted_value.startswith('enc:'):
            cipher_suite = Fernet(self.encryption_key)
            decrypted_bytes = cipher_suite.decrypt(encrypted_value[4:].encode())
            return decrypted_bytes.decode()
        else:
            # Незашифрованное значение (для development)
            if os.getenv('ENVIRONMENT') == 'production':
                logger.warning(f\"⚠️ {env_key} is not encrypted in production!\")
            return encrypted_value
            
    except Exception as e:
        raise ConfigurationError(f\"Cannot decrypt {env_key}: {e}\")

async def encrypt_sensitive_value(self, value: str) -> str:
    \"\"\"Шифрование чувствительного значения для хранения\"\"\"
    cipher_suite = Fernet(self.encryption_key)
    encrypted_bytes = cipher_suite.encrypt(value.encode())
    return f\"enc:{encrypted_bytes.decode()}\"
```

### 5. Валидация конфигурации

```python
async def validate_all_config(self) -> ConfigValidationResult:
    \"\"\"Комплексная валидация всей конфигурации\"\"\"
    errors = []
    warnings = []
    
    try:
        # Валидируем каждую секцию конфигурации
        for section_name, config_obj in self.config_cache.items():
            if hasattr(config_obj, 'validate'):
                section_errors = config_obj.validate()
                errors.extend([f\"{section_name}.{error}\" for error in section_errors])
                
        # Специальные межсекционные проверки
        trading_config = self.config_cache.get('trading')
        risk_config = self.config_cache.get('risk')
        
        if trading_config and risk_config:
            # Проверяем совместимость торговых и риск параметров
            if trading_config.max_open_deals > risk_config.max_open_positions:
                warnings.append(
                    \"Trading max_open_deals exceeds risk max_open_positions\"
                )
                
        # Проверяем файловую систему
        database_url = self.config_cache.get('database', {}).get('url', '')
        if database_url.startswith('sqlite:'):
            db_path = database_url.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except Exception as e:
                    errors.append(f\"Cannot create database directory {db_dir}: {e}\")
                    
        # Проверяем сетевые настройки
        exchange_config = self.config_cache.get('exchange')
        if exchange_config:
            # Тестируем подключение к бирже (если не в тестовом режиме)
            if not getattr(exchange_config, 'sandbox_mode', True):
                try:
                    await self._test_exchange_connection(exchange_config)
                except Exception as e:
                    warnings.append(f\"Exchange connection test failed: {e}\")
                    
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_at=datetime.now()
        )
        
    except Exception as e:
        return ConfigValidationResult(
            is_valid=False,
            errors=[f\"Validation failed: {e}\"],
            warnings=[],
            validated_at=datetime.now()
        )
```

### 6. Hot-reload конфигурации

```python
async def reload_config(self):
    \"\"\"Hot-reload конфигурации без перезапуска бота\"\"\"
    logger.info(\"🔄 Starting configuration reload...\")
    
    try:
        # Сохраняем текущую конфигурацию для rollback
        old_config = copy.deepcopy(self.config_cache)
        
        # Загружаем новую конфигурацию
        await self.load_from_environment()
        
        # Валидируем новую конфигурацию
        validation_result = await self.validate_all_config()
        
        if not validation_result.is_valid:
            # Rollback при ошибках валидации
            self.config_cache = old_config
            logger.error(f\"❌ Config reload failed, rolled back: {validation_result.errors}\")
            raise ConfigurationError(f\"Invalid configuration: {validation_result.errors}\")
            
        # Уведомляем watchers об изменениях
        changes = self._detect_config_changes(old_config, self.config_cache)
        if changes:
            await self._notify_config_watchers(changes)
            logger.info(f\"✅ Configuration reloaded with {len(changes)} changes\")
        else:
            logger.info(\"✅ Configuration reloaded (no changes detected)\")
            
    except Exception as e:
        logger.error(f\"❌ Configuration reload failed: {e}\")
        raise ConfigurationError(f\"Cannot reload configuration: {e}\")

async def watch_config_changes(self, callback):
    \"\"\"Регистрация callback для уведомлений об изменениях\"\"\"
    watcher_id = str(uuid.uuid4())
    self.watchers[watcher_id] = callback
    return watcher_id

async def _notify_config_watchers(self, changes: List[ConfigChange]):
    \"\"\"Уведомление всех watchers об изменениях\"\"\"
    for watcher_id, callback in self.watchers.items():
        try:
            await callback(changes)
        except Exception as e:
            logger.error(f\"Config watcher {watcher_id} failed: {e}\")
```

## ✅ Критерии готовности

- [ ] API ключи перенесены в переменные окружения
- [ ] Все чувствительные данные зашифрованы
- [ ] Валидация конфигурации при запуске
- [ ] Hot-reload конфигурации работает
- [ ] Поддержка разных окружений (dev/staging/prod)
- [ ] Интеграция с другими сервисами через dependency injection
- [ ] Comprehensive тесты всех сценариев
- [ ] Документация по настройке
- [ ] CLI команды для управления конфигурацией

## 🧪 План тестирования

1. **Unit тесты:**
   - Тест загрузки из переменных окружения
   - Тест шифрования/расшифровки
   - Тест валидации каждой секции
   - Тест hot-reload механизма

2. **Integration тесты:**
   - Тест полного цикла initialization
   - Тест с реальными .env файлами
   - Тест rollback при неверной конфигурации

3. **Security тесты:**
   - Тест защиты API ключей
   - Тест encryption/decryption
   - Тест handling неверных ключей шифрования

## 🔗 Связанные задачи

- **Зависит от:** Issue #6 (DatabaseService) - для хранения конфигурации
- **Связано с:** Issue #11 (SecurityService) - шифрование данных
- **Используется в:** Всех остальных сервисах

## 📋 Подзадачи

- [ ] Создать структуру конфигурационных классов
- [ ] Реализовать загрузку из environment variables
- [ ] Добавить шифрование sensitive данных
- [ ] Реализовать систему валидации
- [ ] Добавить hot-reload функциональность
- [ ] Создать CLI для управления конфигурацией
- [ ] Интегрировать со всеми существующими сервисами
- [ ] Написать comprehensive тесты
- [ ] Создать migration script с текущего config.json
- [ ] Добавить documentation и examples

## 📁 Пример .env файла

```bash
# Trading Bot Configuration

# Environment
ENVIRONMENT=development  # development, staging, production
ENCRYPTION_KEY=<base64-encoded-key>

# Trading Settings
TRADING_SYMBOL=VICUSDT
TRADING_BUDGET_PER_DEAL=10.0
TRADING_MAX_OPEN_DEALS=3
TRADING_PROFIT_MARKUP=1.5
TRADING_ORDER_LIFETIME=3600

# Risk Management
RISK_MAX_POSITION_PERCENT=5.0
RISK_STOP_LOSS_PERCENT=-3.0
RISK_MAX_DAILY_LOSS=-10.0
RISK_MAX_OPEN_POSITIONS=3
RISK_EMERGENCY_CLOSE=true
RISK_BALANCE_BUFFER=5.0

# Exchange Configuration
EXCHANGE_NAME=binance
BINANCE_API_KEY=enc:gAAAAABh8x1x2x3x4x5x6x...  # Encrypted
BINANCE_PRIVATE_KEY_PATH=/path/to/private.pem

# Database
DATABASE_URL=sqlite:///data/trading_bot.db
DATABASE_POOL_SIZE=10
DATABASE_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/trading_bot.log
LOG_MAX_FILE_SIZE=100MB
LOG_BACKUP_COUNT=5

# Rate Limiting
EXCHANGE_RATE_LIMIT=1000
```

## ⚠️ Критические моменты безопасности

1. **Шифрование в production** - все API ключи должны быть зашифрованы
2. **Ключи шифрования** - хранить отдельно от кода и конфигурации
3. **Environment segregation** - разные настройки для dev/staging/prod
4. **Access control** - ограничить доступ к .env файлам
5. **Audit trail** - логировать все изменения конфигурации
6. **Backup** - регулярные бэкапы конфигурации

## 💡 Дополнительные заметки

- Начать с простой реализации, постепенно добавлять advanced features
- Предусмотреть backward compatibility при миграции с текущего config.json
- Добавить configuration schema для IDE autocompletion
- Рассмотреть integration с external config management (Consul, etcd в будущем)
- Важно: never commit .env файлы в git, всегда использовать .env.example
