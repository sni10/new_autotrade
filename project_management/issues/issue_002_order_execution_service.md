# Issue #2: OrderExecutionService - Реальное выставление ордеров
### Статус: запланировано

**🔥 Приоритет:** КРИТИЧЕСКИЙ  
**🏗️ Milestone:** M1 - Основные сервисы  
**🏷️ Labels:** `critical`, `trading`, `api-integration`

## 📝 Описание проблемы

В текущей версии ордера создаются в памяти, но не размещаются на реальной бирже:

```python
# Текущий код в deal_service.py создает ордера, но не отправляет их
buy_order = self.order_service.create_buy_order(price, amount)
sell_order = self.order_service.create_sell_order(price, amount)
# ❌ Ордера не размещаются на бирже!
```

Это означает, что бот не может:
- Реально торговать
- Отслеживать статус исполнения ордеров
- Реагировать на изменения рынка
- Получать прибыль от торговых сигналов

## 🎯 Цель

Реализовать сервис для реального размещения, отслеживания и управления ордерами на бирже с полной обработкой всех edge cases.

## 🔧 Техническое решение

### 1. Создать `domain/services/order_execution_service.py`

```python
class OrderExecutionService:
    def __init__(
        self,
        exchange_connector: ExchangeConnector,
        orders_repository: OrdersRepository,
        config_service: ConfigurationService
    ):
        self.exchange = exchange_connector
        self.orders_repo = orders_repository
        self.config = config_service
        
    async def execute_buy_order(
        self, 
        symbol: str, 
        amount: float, 
        price: float,
        order_type: str = "LIMIT"
    ) -> Order:
        \"\"\"Размещение buy ордера на бирже\"\"\"
        
    async def execute_sell_order(
        self, 
        symbol: str, 
        amount: float, 
        price: float,
        order_type: str = "LIMIT"  
    ) -> Order:
        \"\"\"Размещение sell ордера на бирже\"\"\"
        
    async def cancel_order(self, order: Order) -> bool:
        \"\"\"Отмена ордера на бирже\"\"\"
        
    async def check_order_status(self, order: Order) -> OrderStatus:
        \"\"\"Проверка текущего статуса ордера\"\"\"
        
    async def update_all_orders_status(self) -> List[Order]:
        \"\"\"Массовое обновление статусов всех активных ордеров\"\"\"
        
    async def handle_partial_fill(self, order: Order, filled_amount: float):
        \"\"\"Обработка частичного исполнения\"\"\"
```

### 2. Интеграция с Exchange API

```python
async def execute_buy_order(self, symbol: str, amount: float, price: float) -> Order:
    try:
        # Проверка баланса перед размещением
        balance = await self.exchange.fetch_balance()
        required_usdt = amount * price * 1.001  # +0.1% на комиссию
        
        if balance['USDT']['free'] < required_usdt:
            raise InsufficientBalanceError(f"Недостаточно USDT: {balance['USDT']['free']}")
            
        # Размещение ордера на бирже
        exchange_order = await self.exchange.create_order(
            symbol=symbol,
            type='limit',
            side='buy', 
            amount=amount,
            price=price
        )
        
        # Создание локального объекта ордера
        order = Order(
            id=generate_order_id(),
            exchange_order_id=exchange_order['id'],
            symbol=symbol,
            side='BUY',
            type='LIMIT',
            amount=amount,
            price=price,
            status='PENDING',
            created_at=datetime.now()
        )
        
        # Сохранение в БД
        await self.orders_repo.save(order)
        
        logger.info(f"✅ BUY ордер размещен: {order}")
        return order
        
    except Exception as e:
        logger.error(f"❌ Ошибка размещения BUY ордера: {e}")
        raise OrderExecutionError(f"Не удалось разместить ордер: {e}")
```

### 3. Отслеживание статусов ордеров

```python
async def check_order_status(self, order: Order) -> OrderStatus:
    try:
        exchange_order = await self.exchange.fetch_order(
            order.exchange_order_id, 
            order.symbol
        )
        
        # Маппинг статусов биржи в наши статусы
        status_mapping = {
            'open': OrderStatus.PENDING,
            'closed': OrderStatus.FILLED, 
            'canceled': OrderStatus.CANCELLED,
            'partially_filled': OrderStatus.PARTIAL_FILL
        }
        
        new_status = status_mapping.get(exchange_order['status'], OrderStatus.UNKNOWN)
        
        # Обновляем статус если изменился
        if order.status != new_status:
            order.update_status(new_status)
            if new_status == OrderStatus.PARTIAL_FILL:
                await self.handle_partial_fill(order, exchange_order['filled'])
            await self.orders_repo.save(order)
            
        return new_status
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки статуса ордера {order.id}: {e}")
        return OrderStatus.ERROR
```

### 4. Retry механизмы

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((NetworkError, ExchangeNotAvailable))
)
async def execute_order_with_retry(self, order_params: Dict) -> Order:
    \"\"\"Размещение ордера с retry логикой\"\"\"
    return await self._execute_order_internal(order_params)
```

## ✅ Критерии готовности

- [ ] Ордера реально размещаются на бирже (Binance)
- [ ] Корректное отслеживание всех статусов ордеров
- [ ] Обработка частичного исполнения ордеров
- [ ] Retry механизмы при сетевых ошибках  
- [ ] Проверка баланса перед каждым ордером
- [ ] Логирование всех торговых операций
- [ ] Graceful handling всех ошибок API
- [ ] Интеграция с TradingOrchestrator
- [ ] Unit и integration тесты
- [ ] Performance тесты (latency < 100ms)

## 🧪 План тестирования

1. **Unit тесты с mock биржей:**
   - Тест успешного размещения ордеров
   - Тест обработки ошибок API
   - Тест retry механизмов
   - Тест обработки partial fills

2. **Integration тесты с Binance Testnet:**
   - Тест полного цикла: размещение → отслеживание → исполнение
   - Тест отмены ордеров
   - Тест edge cases (недостаток баланса, невалидные параметры)

3. **Load тесты:**
   - Множественные параллельные ордера
   - Высокая частота обновления статусов

## 🔗 Связанные задачи

- **Зависит от:** Issue #1 (TradingOrchestrator) - для интеграции
- **Блокирует:** Issue #3 (RiskManagementService) - нужны реальные ордера
- **Связано с:** Issue #6 (DatabaseService) - для сохранения ордеров

## 📋 Подзадачи

- [ ] Спроектировать API для OrderExecutionService
- [ ] Реализовать execute_buy_order с полной обработкой ошибок
- [ ] Реализовать execute_sell_order с проверками
- [ ] Добавить систему отслеживания статусов ордеров  
- [ ] Реализовать cancel_order с подтверждением
- [ ] Добавить retry механизмы для сетевых ошибок
- [ ] Интегрировать с существующим order_service
- [ ] Написать unit тесты с mock
- [ ] Провести integration тесты на testnet
- [ ] Добавить подробное логирование и мониторинг
- [ ] Интегрировать с TradingOrchestrator
- [ ] Performance optimization и тестирование

## ⚠️ Критические моменты

1. **Безопасность API ключей** - использовать переменные окружения
2. **Rate Limiting** - соблюдать лимиты Binance API (1200 requests/minute)
3. **Network Error Handling** - правильные retry с backoff
4. **Partial Fills** - корректная обработка частичного исполнения
5. **Balance Checks** - всегда проверять баланс перед ордером
6. **Order ID Mapping** - правильное соответствие наших ID и биржевых ID

## 💡 Дополнительные заметки

- Начать с Binance Spot API (проще чем futures)
- Использовать ccxt.pro для WebSocket updates статусов ордеров
- Предусмотреть возможность работы с multiple exchanges в будущем
- Добавить detailed metrics для торговых операций
- Рассмотреть Circuit Breaker pattern для защиты от cascade failures
