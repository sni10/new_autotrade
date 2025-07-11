# Issue #10: ErrorHandlingService - Обработка ошибок

**🔥 Приоритет:** ВЫСОКИЙ  
**🏗️ Milestone:** M3 - Безопасность и надежность  
**🏷️ Labels:** `high-priority`, `reliability`, `error-handling`, `monitoring`

## 📝 Описание проблемы

В текущей версии критические недостатки обработки ошибок:
- **Только общий try-catch** в main loop - плохая granularity
- **Нет retry механизмов** - временные сбои приводят к остановке бота
- **Отсутствие circuit breaker** - cascade failures при проблемах с API
- **Нет categorization ошибок** - все обрабатываются одинаково
- **Отсутствие alerting** - критические ошибки остаются незамеченными
- **Нет graceful degradation** - при сбое одного компонента падает всё

Это критично для production торгового бота, который должен работать 24/7.

## 🎯 Цель

Создать комплексную систему обработки ошибок с retry механизмами, circuit breaker, alerting и graceful degradation для максимальной надежности.

## 🔧 Техническое решение

### 1. Создать `application/services/error_handling_service.py`

```python
class ErrorHandlingService:
    def __init__(
        self,
        config_service: ConfigurationService,
        notification_service: NotificationService,
        database_service: DatabaseService
    ):
        self.config = config_service
        self.notifications = notification_service
        self.db = database_service
        self.circuit_breakers = {}
        self.retry_strategies = {}
        self.error_history = defaultdict(list)
        
    async def handle_error(
        self, 
        error: Exception, 
        context: ErrorContext, 
        recovery_action: Optional[Callable] = None
    ) -> ErrorHandlingResult:
        \"\"\"Главный метод обработки ошибок\"\"\"
        
    async def register_retry_strategy(
        self, 
        operation_type: str, 
        strategy: RetryStrategy
    ):
        \"\"\"Регистрация retry стратегии для типа операций\"\"\"
        
    async def execute_with_retry(
        self, 
        operation: Callable, 
        operation_type: str,
        context: Dict = None
    ):
        \"\"\"Выполнение операции с retry логикой\"\"\"
        
    async def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        \"\"\"Получение circuit breaker для сервиса\"\"\"
        
    async def record_error_metrics(self, error: Exception, context: ErrorContext):
        \"\"\"Запись метрик ошибок для мониторинга\"\"\"
        
    async def should_alert(self, error: Exception, context: ErrorContext) -> bool:
        \"\"\"Определение необходимости отправки alert\"\"\"
```

### 2. Классификация и модели ошибок

```python
class ErrorSeverity(Enum):
    LOW = \"low\"           # Логируем, но не влияет на работу
    MEDIUM = \"medium\"     # Требует внимания, но бот продолжает работу
    HIGH = \"high\"         # Серьезная проблема, может влиять на торговлю
    CRITICAL = \"critical\" # Критическая ошибка, требует немедленного вмешательства

class ErrorCategory(Enum):
    NETWORK = \"network\"               # Сетевые ошибки (API, WebSocket)
    EXCHANGE = \"exchange\"             # Ошибки биржи (invalid orders, insufficient balance)
    DATABASE = \"database\"             # Ошибки БД (connection, queries)
    VALIDATION = \"validation\"         # Ошибки валидации данных
    CALCULATION = \"calculation\"       # Ошибки в расчетах (индикаторы, стратегии)
    CONFIGURATION = \"configuration\"   # Ошибки конфигурации
    SECURITY = \"security\"             # Ошибки безопасности
    UNKNOWN = \"unknown\"               # Неклассифицированные ошибки

@dataclass
class ErrorContext:
    \"\"\"Контекст возникновения ошибки\"\"\"
    operation: str                    # Название операции где произошла ошибка
    component: str                    # Компонент (service/repository/connector)
    trading_pair: Optional[str]       # Торговая пара если применимо
    deal_id: Optional[int]           # ID сделки если применимо
    order_id: Optional[int]          # ID ордера если применимо
    user_data: Dict[str, Any]        # Дополнительные данные
    timestamp: datetime              # Время возникновения
    
@dataclass
class ErrorHandlingResult:
    \"\"\"Результат обработки ошибки\"\"\"
    handled: bool                    # Была ли ошибка обработана
    should_retry: bool              # Нужно ли повторить операцию
    should_continue: bool           # Можно ли продолжать работу
    recovery_action_taken: bool     # Было ли выполнено восстановление
    alert_sent: bool               # Было ли отправлено уведомление
    error_id: str                  # Уникальный ID ошибки для трекинга
    message: str                   # Сообщение для пользователя
```

### 3. Retry механизмы

```python
@dataclass
class RetryStrategy:
    \"\"\"Стратегия повторных попыток\"\"\"
    max_attempts: int
    base_delay: float               # Базовая задержка в секундах
    max_delay: float               # Максимальная задержка
    backoff_multiplier: float      # Множитель для exponential backoff
    jitter: bool                   # Добавлять ли случайный jitter
    retryable_exceptions: List[Type[Exception]]
    
class RetryableErrors:
    \"\"\"Список ошибок, которые можно повторить\"\"\"
    NETWORK_ERRORS = [
        ConnectionError,
        TimeoutError,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        ccxt.NetworkError,
        ccxt.RequestTimeout
    ]
    
    EXCHANGE_TEMPORARY_ERRORS = [
        ccxt.ExchangeNotAvailable,
        ccxt.RateLimitExceeded,
        ccxt.DDoSProtection
    ]
    
    DATABASE_TEMPORARY_ERRORS = [
        sqlite3.OperationalError,  # Database is locked
        psycopg2.OperationalError  # Connection issues
    ]

async def execute_with_retry(
    self, 
    operation: Callable, 
    operation_type: str,
    context: Dict = None
) -> Any:
    \"\"\"Выполнение операции с retry логикой\"\"\"
    
    strategy = self.retry_strategies.get(operation_type, self._get_default_strategy())
    error_context = ErrorContext(
        operation=operation.__name__ if hasattr(operation, '__name__') else str(operation),
        component=context.get('component', 'unknown') if context else 'unknown',
        trading_pair=context.get('trading_pair') if context else None,
        timestamp=datetime.now()
    )
    
    last_exception = None
    
    for attempt in range(strategy.max_attempts):
        try:
            result = await operation()
            
            # Логируем успешное выполнение после ошибок
            if attempt > 0:
                logger.info(f\"✅ Operation {error_context.operation} succeeded on attempt {attempt + 1}\")
                
            return result
            
        except Exception as e:
            last_exception = e
            
            # Проверяем, можно ли повторить эту ошибку
            if not self._is_retryable_error(e, strategy):
                logger.error(f\"❌ Non-retryable error in {error_context.operation}: {e}\")
                await self.handle_error(e, error_context)
                raise
                
            # Логируем попытку
            logger.warning(
                f\"⚠️ Attempt {attempt + 1}/{strategy.max_attempts} failed for {error_context.operation}: {e}\"
            )
            
            # Если это последняя попытка, не ждем
            if attempt == strategy.max_attempts - 1:
                break
                
            # Рассчитываем задержку с exponential backoff
            delay = min(
                strategy.base_delay * (strategy.backoff_multiplier ** attempt),
                strategy.max_delay
            )
            
            # Добавляем jitter для избежания thundering herd
            if strategy.jitter:
                delay *= (0.5 + random.random() * 0.5)
                
            logger.info(f\"⏳ Waiting {delay:.2f}s before retry #{attempt + 2}\")
            await asyncio.sleep(delay)
    
    # Все попытки исчерпаны
    logger.error(f\"❌ All {strategy.max_attempts} attempts failed for {error_context.operation}\")
    await self.handle_error(last_exception, error_context)
    raise last_exception
```

### 4. Circuit Breaker Pattern

```python
class CircuitBreakerState(Enum):
    CLOSED = \"closed\"       # Нормальная работа
    OPEN = \"open\"           # Ошибки превысили threshold, все запросы блокируются
    HALF_OPEN = \"half_open\" # Тестирование восстановления

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5      # Количество ошибок для открытия
    recovery_timeout: int = 60      # Время ожидания перед переходом в HALF_OPEN
    success_threshold: int = 3      # Количество успехов для закрытия
    timeout: float = 10.0          # Timeout для операций

class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig, service_name: str):
        self.config = config
        self.service_name = service_name
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        
    async def call(self, operation: Callable) -> Any:
        \"\"\"Выполнение операции через circuit breaker\"\"\"
        
        # Проверяем текущее состояние
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info(f\"🔄 Circuit breaker for {self.service_name} moved to HALF_OPEN\")
            else:
                raise CircuitBreakerOpenError(f\"Circuit breaker for {self.service_name} is OPEN\")
                
        try:
            # Выполняем операцию с timeout
            result = await asyncio.wait_for(operation(), timeout=self.config.timeout)
            
            # Обрабатываем успешное выполнение
            await self._on_success()
            return result
            
        except Exception as e:
            # Обрабатываем ошибку
            await self._on_failure()
            raise
            
    async def _on_success(self):
        \"\"\"Обработка успешного выполнения\"\"\"
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info(f\"✅ Circuit breaker for {self.service_name} CLOSED (recovered)\")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0  # Reset failure count on success
            
    async def _on_failure(self):
        \"\"\"Обработка ошибки\"\"\"
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if (self.state == CircuitBreakerState.CLOSED and 
            self.failure_count >= self.config.failure_threshold):
            self.state = CircuitBreakerState.OPEN
            logger.error(f\"🚨 Circuit breaker for {self.service_name} OPENED after {self.failure_count} failures\")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f\"⚠️ Circuit breaker for {self.service_name} returned to OPEN state\")
```

### 5. Graceful Degradation

```python
class GracefulDegradationService:
    \"\"\"Сервис для graceful degradation при сбоях компонентов\"\"\"
    
    def __init__(self):
        self.degraded_services = set()
        self.fallback_strategies = {}
        
    async def mark_service_degraded(self, service_name: str, reason: str):
        \"\"\"Пометить сервис как degraded\"\"\"
        if service_name not in self.degraded_services:
            self.degraded_services.add(service_name)
            logger.warning(f\"⚠️ Service {service_name} marked as DEGRADED: {reason}\")
            
    async def is_service_degraded(self, service_name: str) -> bool:
        \"\"\"Проверить, degraded ли сервис\"\"\"
        return service_name in self.degraded_services
        
    async def execute_with_fallback(
        self, 
        primary_operation: Callable,
        fallback_operation: Callable,
        service_name: str
    ):
        \"\"\"Выполнить операцию с fallback при degradation\"\"\"
        
        if await self.is_service_degraded(service_name):
            logger.info(f\"🔄 Using fallback for degraded service {service_name}\")
            return await fallback_operation()
        
        try:
            return await primary_operation()
        except Exception as e:
            logger.error(f\"❌ Primary operation failed for {service_name}: {e}\")
            await self.mark_service_degraded(service_name, str(e))
            
            if fallback_operation:
                logger.info(f\"🔄 Executing fallback for {service_name}\")
                return await fallback_operation()
            else:
                raise

# Примеры fallback стратегий
async def orderbook_analysis_fallback():
    \"\"\"Fallback для анализа стакана - используем простую логику\"\"\"
    return {
        'execute': True,
        'confidence': 0.5,
        'reason': 'Orderbook analysis unavailable, using simple strategy'
    }

async def market_data_fallback():
    \"\"\"Fallback для рыночных данных - используем кешированные данные\"\"\"
    cached_data = await get_cached_market_data()
    if cached_data and is_recent(cached_data):
        return cached_data
    else:
        raise ServiceUnavailableError(\"No recent cached market data available\")
```

### 6. Error Monitoring и Alerting

```python
async def record_error_metrics(self, error: Exception, context: ErrorContext):
    \"\"\"Запись метрик ошибок\"\"\"
    
    # Классифицируем ошибку
    category = self._classify_error(error)
    severity = self._determine_severity(error, category, context)
    
    # Создаем запись об ошибке
    error_record = {
        'id': str(uuid.uuid4()),
        'timestamp': context.timestamp,
        'category': category.value,
        'severity': severity.value,
        'error_type': type(error).__name__,
        'message': str(error),
        'operation': context.operation,
        'component': context.component,
        'trading_pair': context.trading_pair,
        'deal_id': context.deal_id,
        'order_id': context.order_id,
        'stack_trace': traceback.format_exc(),
        'context_data': context.user_data
    }
    
    # Сохраняем в БД для анализа
    await self.db.execute_query(
        \"INSERT INTO error_events (id, timestamp, category, severity, data) VALUES (?, ?, ?, ?, ?)\",
        {
            'id': error_record['id'],
            'timestamp': error_record['timestamp'],
            'category': error_record['category'],
            'severity': error_record['severity'],
            'data': json.dumps(error_record)
        }
    )
    
    # Обновляем статистику ошибок
    await self._update_error_statistics(category, severity)
    
    # Проверяем необходимость отправки alert
    if await self.should_alert(error, context):
        await self._send_error_alert(error_record)

async def should_alert(self, error: Exception, context: ErrorContext) -> bool:
    \"\"\"Определение необходимости alert\"\"\"
    
    category = self._classify_error(error)
    severity = self._determine_severity(error, category, context)
    
    # Всегда алертим критические ошибки
    if severity == ErrorSeverity.CRITICAL:
        return True
        
    # Алертим высокие ошибки в торговых операциях
    if (severity == ErrorSeverity.HIGH and 
        context.operation in ['execute_order', 'create_deal', 'process_signal']):
        return True
        
    # Алертим если много ошибок одного типа за короткое время
    recent_errors = self.error_history[type(error).__name__]
    recent_count = len([e for e in recent_errors 
                       if e > datetime.now() - timedelta(minutes=10)])
    
    if recent_count >= 5:  # 5 ошибок за 10 минут
        return True
        
    return False
```

## ✅ Критерии готовности

- [ ] Все типы ошибок правильно классифицированы и обрабатываются
- [ ] Retry механизмы работают для временных сбоев
- [ ] Circuit breaker защищает от cascade failures
- [ ] Graceful degradation при сбоях компонентов
- [ ] Comprehensive error logging и metrics
- [ ] Alerting для критических ошибок
- [ ] Integration со всеми существующими сервисами
- [ ] Error recovery не прерывает торговлю
- [ ] Performance impact минимален (<1ms overhead)
- [ ] Подробная документация по troubleshooting

## 🧪 План тестирования

1. **Unit тесты:**
   - Тест retry механизмов с mock failures
   - Тест circuit breaker state transitions
   - Тест classification ошибок
   - Тест alerting logic

2. **Integration тесты:**
   - Тест с реальными сетевыми сбоями
   - Тест recovery после database failures
   - Тест graceful degradation scenarios

3. **Chaos Engineering:**
   - Искусственные сбои API
   - Network partitions
   - Database unavailability
   - High load scenarios

## 🔗 Связанные задачи

- **Зависит от:** Issue #2 (OrderExecutionService), Issue #6 (DatabaseService)
- **Связано с:** Issue #12 (HealthCheckService) - мониторинг
- **Интегрируется с:** Всеми сервисами системы

## 📋 Подзадачи

- [ ] Создать error classification system
- [ ] Реализовать retry механизмы с exponential backoff
- [ ] Добавить circuit breaker для всех external dependencies
- [ ] Реализовать graceful degradation strategies
- [ ] Создать error monitoring и metrics
- [ ] Добавить alerting system
- [ ] Интегрировать со всеми существующими сервисами
- [ ] Написать comprehensive тесты
- [ ] Добавить error recovery procedures
- [ ] Создать troubleshooting documentation

## ⚠️ Критические моменты

1. **Не скрывать критические ошибки** - некоторые ошибки должны останавливать торговлю
2. **Performance impact** - error handling не должен замедлять hot paths
3. **Infinite retry loops** - всегда иметь max attempts и circuit breakers
4. **State consistency** - error recovery не должен нарушать консистентность данных
5. **Alert fatigue** - не спамить уведомлениями, группировать похожие ошибки
6. **Security** - не логировать sensitive данные в error messages

## 💡 Дополнительные заметки

- Начать с простой реализации, постепенно добавлять advanced features
- Использовать structured logging для лучшего анализа ошибок
- Предусмотреть integration с external monitoring tools (Sentry, Datadog)
- Добавить error budgets для SLA tracking
- Важно: error handling не должен быть single point of failure
