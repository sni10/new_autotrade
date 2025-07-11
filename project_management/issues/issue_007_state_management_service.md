# Issue #7: StateManagementService - Управление состоянием

**🔥 Приоритет:** ВЫСОКИЙ  
**🏗️ Milestone:** M2 - Персистентность и управление данными  
**🏷️ Labels:** `high-priority`, `state-management`, `recovery`

## 📝 Описание проблемы

В текущей версии отсутствует система управления состоянием:
- **Потеря контекста при перезапуске** - открытые сделки, активные стратегии
- **Нет синхронизации с биржей** при старте приложения
- **Невозможность graceful restart** без потери торговых позиций
- **Отсутствие recovery механизмов** после сбоев
- **Рассинхронизация данных** между локальным состоянием и биржей

Это критично для production торгового бота, который должен работать 24/7.

## 🎯 Цель

Создать надежную систему управления состоянием, которая обеспечивает непрерывность торговых операций при перезапусках и сбоях.

## 🔧 Техническое решение

### 1. Создать `domain/services/state_management_service.py`

```python
class StateManagementService:
    def __init__(
        self,
        database_service: DatabaseService,
        exchange_connector: ExchangeConnector,
        deals_repository: DealsRepository,
        orders_repository: OrdersRepository
    ):
        self.db = database_service
        self.exchange = exchange_connector
        self.deals_repo = deals_repository
        self.orders_repo = orders_repository
        self.current_state = TradingState()
        
    async def save_state(self, state: TradingState):
        \"\"\"Сохранение текущего состояния в БД\"\"\"
        
    async def load_state(self) -> TradingState:
        \"\"\"Загрузка последнего сохраненного состояния\"\"\"
        
    async def sync_with_exchange(self):
        \"\"\"Синхронизация локального состояния с биржей\"\"\"
        
    async def recover_interrupted_operations(self):
        \"\"\"Восстановление прерванных операций\"\"\"
        
    async def validate_state_consistency(self) -> StateValidationResult:
        \"\"\"Проверка консистентности состояния\"\"\"
        
    async def handle_graceful_shutdown(self):
        \"\"\"Обработка graceful завершения работы\"\"\"
        
    async def emergency_state_backup(self):
        \"\"\"Экстренное сохранение состояния\"\"\"
```

### 2. Модель состояния торгового бота

```python
@dataclass
class TradingState:
    \"\"\"Полное состояние торгового бота\"\"\"
    timestamp: datetime
    bot_status: BotStatus  # RUNNING, PAUSED, SHUTDOWN, ERROR
    active_pairs: List[str]
    open_deals: List[Deal]
    pending_orders: List[Order]
    risk_parameters: RiskParameters
    performance_metrics: PerformanceMetrics
    last_processed_tick: Dict[str, datetime]
    error_history: List[ErrorEvent]
    
    def to_dict(self) -> Dict:
        \"\"\"Сериализация состояния для хранения\"\"\"
        
    @classmethod  
    def from_dict(cls, data: Dict) -> 'TradingState':
        \"\"\"Десериализация состояния из хранилища\"\"\"

@dataclass        
class RiskParameters:
    max_position_size: float
    stop_loss_percent: float
    max_daily_loss: float
    current_exposure: float
    available_balance: Dict[str, float]

@dataclass
class PerformanceMetrics:
    total_trades: int
    profitable_trades: int
    total_pnl: float
    max_drawdown: float
    win_rate: float
    avg_trade_duration: timedelta
```

### 3. Сохранение и загрузка состояния

```python
async def save_state(self, state: TradingState):
    \"\"\"Atomic сохранение состояния\"\"\"
    try:
        # Сериализуем состояние
        state_data = {
            'timestamp': state.timestamp.isoformat(),
            'bot_status': state.bot_status.value,
            'active_pairs': state.active_pairs,
            'risk_parameters': asdict(state.risk_parameters),
            'performance_metrics': asdict(state.performance_metrics),
            'last_processed_tick': {
                pair: timestamp.isoformat() 
                for pair, timestamp in state.last_processed_tick.items()
            },
            'metadata': {
                'version': '1.0',
                'checksum': self._calculate_checksum(state)
            }
        }
        
        # Atomic запись в БД
        await self.db.execute_transaction([
            DatabaseOperation(
                'upsert', 
                'bot_state',
                {
                    'id': 'current',
                    'state_data': json.dumps(state_data),
                    'updated_at': datetime.now()
                }
            )
        ])
        
        logger.info(f\"✅ State saved: {state.bot_status} with {len(state.open_deals)} deals\")
        
    except Exception as e:
        logger.error(f\"❌ Failed to save state: {e}\")
        raise StateManagementError(f\"Cannot save state: {e}\")

async def load_state(self) -> TradingState:
    \"\"\"Загрузка и валидация состояния\"\"\"
    try:
        # Загружаем из БД
        result = await self.db.execute_query(
            \"SELECT state_data FROM bot_state WHERE id = 'current'\"
        )
        
        if not result:
            logger.info(\"🆕 No previous state found, creating fresh state\")
            return self._create_fresh_state()
            
        state_data = json.loads(result[0]['state_data'])
        
        # Валидируем checksum
        if not self._validate_checksum(state_data):
            logger.warning(\"⚠️ State checksum invalid, creating fresh state\")
            return self._create_fresh_state()
            
        # Десериализуем
        state = TradingState(
            timestamp=datetime.fromisoformat(state_data['timestamp']),
            bot_status=BotStatus(state_data['bot_status']),
            active_pairs=state_data['active_pairs'],
            open_deals=await self._load_deals_from_db(),
            pending_orders=await self._load_orders_from_db(),
            risk_parameters=RiskParameters(**state_data['risk_parameters']),
            performance_metrics=PerformanceMetrics(**state_data['performance_metrics']),
            last_processed_tick={
                pair: datetime.fromisoformat(timestamp)
                for pair, timestamp in state_data['last_processed_tick'].items()
            },
            error_history=[]
        )
        
        logger.info(f\"✅ State loaded: {state.bot_status} with {len(state.open_deals)} deals\")
        return state
        
    except Exception as e:
        logger.error(f\"❌ Failed to load state: {e}\")
        return self._create_fresh_state()
```

### 4. Синхронизация с биржей

```python
async def sync_with_exchange(self):
    \"\"\"Синхронизация локального состояния с биржей\"\"\"
    logger.info(\"🔄 Starting exchange synchronization...\")
    
    sync_results = []
    
    try:
        # 1. Проверяем балансы
        exchange_balances = await self.exchange.fetch_balance()
        local_balances = self.current_state.risk_parameters.available_balance
        
        balance_diff = self._compare_balances(local_balances, exchange_balances)
        if balance_diff:
            logger.warning(f\"⚠️ Balance mismatch detected: {balance_diff}\")
            sync_results.append(f\"Balance updated: {balance_diff}\")
            
        # 2. Синхронизируем ордера  
        exchange_orders = await self.exchange.fetch_open_orders()
        local_orders = await self.orders_repo.get_pending_orders()
        
        order_sync_result = await self._sync_orders(local_orders, exchange_orders)
        sync_results.extend(order_sync_result)
        
        # 3. Проверяем позиции
        position_sync_result = await self._sync_positions()
        sync_results.extend(position_sync_result)
        
        # 4. Обновляем состояние
        self.current_state.risk_parameters.available_balance = exchange_balances
        await self.save_state(self.current_state)
        
        logger.info(f\"✅ Exchange sync completed: {len(sync_results)} changes\")
        return sync_results
        
    except Exception as e:
        logger.error(f\"❌ Exchange sync failed: {e}\")
        raise StateSyncError(f\"Cannot sync with exchange: {e}\")

async def _sync_orders(
    self, 
    local_orders: List[Order], 
    exchange_orders: List[Dict]
) -> List[str]:
    \"\"\"Синхронизация ордеров между локальной БД и биржей\"\"\"
    changes = []
    
    # Создаем маппинг по exchange_order_id
    exchange_map = {order['id']: order for order in exchange_orders}
    local_map = {order.exchange_order_id: order for order in local_orders}
    
    # Проверяем ордера, которые есть локально, но нет на бирже
    for order in local_orders:
        if order.exchange_order_id not in exchange_map:
            # Ордер был отменен/исполнен на бирже, но мы не знаем
            logger.warning(f\"⚠️ Order {order.id} missing on exchange\")
            
            # Получаем историю ордера
            try:
                order_history = await self.exchange.fetch_order(
                    order.exchange_order_id, order.symbol
                )
                
                if order_history['status'] == 'closed':
                    order.status = OrderStatus.FILLED
                    order.filled_amount = order_history['filled']
                    changes.append(f\"Order {order.id} marked as FILLED\")
                elif order_history['status'] == 'canceled':
                    order.status = OrderStatus.CANCELLED  
                    changes.append(f\"Order {order.id} marked as CANCELLED\")
                    
                await self.orders_repo.save(order)
                
            except Exception as e:
                logger.error(f\"Cannot fetch order history for {order.id}: {e}\")
    
    # Проверяем ордера, которые есть на бирже, но нет локально
    for exchange_order in exchange_orders:
        if exchange_order['id'] not in local_map:
            logger.warning(f\"⚠️ Unknown order on exchange: {exchange_order['id']}\")
            changes.append(f\"Found unknown order: {exchange_order['id']}\")
            
    return changes
```

### 5. Recovery прерванных операций

```python
async def recover_interrupted_operations(self):
    \"\"\"Восстановление операций, прерванных во время сбоя\"\"\"
    logger.info(\"🔄 Starting recovery of interrupted operations...\")
    
    recovery_actions = []
    
    try:
        # 1. Находим незавершенные сделки
        incomplete_deals = await self.deals_repo.get_deals_by_status('PROCESSING')
        
        for deal in incomplete_deals:
            logger.info(f\"🔧 Recovering deal {deal.id}\")
            
            # Проверяем статус связанных ордеров
            if deal.buy_order:
                buy_status = await self._check_order_final_status(deal.buy_order)
                if buy_status == OrderStatus.FILLED and not deal.sell_order:
                    # Buy исполнился, но sell ордер не создан
                    await self._create_missing_sell_order(deal)
                    recovery_actions.append(f\"Created missing sell order for deal {deal.id}\")
                    
            # Обновляем статус сделки
            deal.status = self._determine_deal_status(deal)
            await self.deals_repo.save(deal)
            
        # 2. Проверяем hanging ордера
        hanging_orders = await self.orders_repo.get_orders_by_status('PROCESSING')
        
        for order in hanging_orders:
            final_status = await self._check_order_final_status(order)
            if final_status != order.status:
                order.status = final_status
                await self.orders_repo.save(order)
                recovery_actions.append(f\"Updated order {order.id} status to {final_status}\")
                
        # 3. Проверяем orphaned ордера (ордера без сделок)
        orphaned_orders = await self._find_orphaned_orders()
        for order in orphaned_orders:
            logger.warning(f\"⚠️ Found orphaned order {order.id}\")
            await self.exchange.cancel_order(order.exchange_order_id, order.symbol)
            recovery_actions.append(f\"Cancelled orphaned order {order.id}\")
            
        logger.info(f\"✅ Recovery completed: {len(recovery_actions)} actions taken\")
        return recovery_actions
        
    except Exception as e:
        logger.error(f\"❌ Recovery failed: {e}\")
        raise RecoveryError(f\"Cannot recover interrupted operations: {e}\")
```

## ✅ Критерии готовности

- [ ] Состояние сохраняется автоматически каждые 30 секунд
- [ ] Корректное восстановление состояния после перезапуска
- [ ] Синхронизация с биржей при старте приложения  
- [ ] Recovery прерванных торговых операций
- [ ] Валидация консистентности данных
- [ ] Graceful shutdown с сохранением состояния
- [ ] Emergency backup при критических ошибках
- [ ] Детальное логирование всех операций со состоянием
- [ ] Unit и integration тесты
- [ ] Performance тесты (state save/load < 100ms)

## 🧪 План тестирования

1. **Unit тесты:**
   - Тест сериализации/десериализации состояния
   - Тест валидации checksum
   - Тест recovery логики
   - Мocking exchange API

2. **Integration тесты:**
   - Полный цикл save → restart → load
   - Тест синхронизации с реальной биржей (testnet)
   - Тест recovery после искусственных сбоев

3. **Stress тесты:**
   - Большие объемы данных (сотни сделок)
   - Concurrent access к состоянию

## 🔗 Связанные задачи

- **Зависит от:** Issue #6 (DatabaseService) - для хранения состояния
- **Связано с:** Issue #1 (TradingOrchestrator) - интеграция в основной цикл
- **Связано с:** Issue #2 (OrderExecutionService) - синхронизация ордеров

## 📋 Подзадачи

- [ ] Спроектировать модель TradingState
- [ ] Реализовать serialization/deserialization
- [ ] Создать систему checksum для валидации
- [ ] Реализовать save/load состояния в БД
- [ ] Добавить синхронизацию с биржей
- [ ] Реализовать recovery прерванных операций
- [ ] Интегрировать с TradingOrchestrator
- [ ] Написать comprehensive тесты  
- [ ] Добавить performance monitoring
- [ ] Создать documentation по recovery procedures

## ⚠️ Критические моменты

1. **Atomic операции** - состояние должно сохраняться атомарно
2. **Checksum валидация** - защита от corrupted data
3. **Exchange API limits** - не превышать rate limits при синхронизации
4. **Memory usage** - эффективная работа с большими состояниями
5. **Backward compatibility** - поддержка миграции старых состояний
6. **Error isolation** - ошибка в state management не должна крашить бота

## 💡 Дополнительные заметки

- Состояние сохранять не только по времени, но и перед каждой критической операцией
- Предусмотреть возможность manual state correction через CLI
- Добавить state diff для понимания что изменилось между сохранениями
- Рассмотреть Redis для hot state, БД для cold storage
- Важно: всегда favor consistency over performance при работе с состоянием
