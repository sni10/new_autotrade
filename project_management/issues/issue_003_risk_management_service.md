# Issue #3: RiskManagementService - Управление рисками
### Статус: запланировано

**🔥 Приоритет:** ВЫСОКИЙ  
**🏗️ Milestone:** M1 - Основные сервисы  
**🏷️ Labels:** `high-priority`, `risk-management`, `safety`

## 📝 Описание проблемы

В текущей версии отсутствуют механизмы контроля рисков:
- Нет проверки доступного баланса перед сделками
- Отсутствует stop-loss защита  
- Нет ограничений на размер позиций
- Возможна потеря всех средств при неблагоприятном движении рынка
- Нет emergency shutdown механизмов

Это критически опасно для реальной торговли с реальными деньгами.

## 🎯 Цель

Создать комплексную систему управления рисками для защиты от финансовых потерь и обеспечения безопасной торговли.

## 🔧 Техническое решение

### 1. Создать `domain/services/risk_management_service.py`

```python
class RiskManagementService:
    def __init__(
        self,
        exchange_connector: ExchangeConnector,
        config_service: ConfigurationService,
        portfolio_service: PortfolioService
    ):
        self.exchange = exchange_connector
        self.config = config_service
        self.portfolio = portfolio_service
        self.emergency_stop = False
        
    async def validate_trade_risk(
        self, 
        symbol: str, 
        side: str, 
        amount: float, 
        price: float
    ) -> RiskValidationResult:
        \"\"\"Комплексная проверка торгового риска\"\"\"
        
    async def check_balance_sufficiency(
        self, 
        required_amount: float, 
        currency: str
    ) -> bool:
        \"\"\"Проверка достаточности баланса\"\"\"
        
    async def calculate_position_size(
        self, 
        symbol: str, 
        risk_percent: float = 2.0
    ) -> float:
        \"\"\"Расчет безопасного размера позиции\"\"\"
        
    async def check_stop_loss_trigger(
        self, 
        current_price: float, 
        entry_price: float, 
        stop_loss_percent: float = 5.0
    ) -> bool:
        \"\"\"Проверка срабатывания stop-loss\"\"\"
        
    async def emergency_shutdown(self, reason: str):
        \"\"\"Экстренная остановка всех торговых операций\"\"\"
        
    async def monitor_portfolio_health(self) -> PortfolioHealthStatus:
        \"\"\"Мониторинг общего состояния портфеля\"\"\"
```

### 2. Проверка баланса перед сделками

```python
async def validate_trade_risk(
    self, 
    symbol: str, 
    side: str, 
    amount: float, 
    price: float
) -> RiskValidationResult:
    try:
        # 1. Проверка баланса
        balance_check = await self.check_balance_sufficiency(
            required_amount=amount * price if side == 'BUY' else amount,
            currency='USDT' if side == 'BUY' else symbol.split('/')[0]
        )
        
        if not balance_check:
            return RiskValidationResult(
                approved=False,
                reason="Недостаточно средств на балансе",
                risk_level=RiskLevel.HIGH
            )
            
        # 2. Проверка размера позиции
        total_portfolio_value = await self.portfolio.get_total_value()
        position_value = amount * price
        position_percent = (position_value / total_portfolio_value) * 100
        
        max_position_percent = self.config.get('risk.max_position_percent', 10.0)
        if position_percent > max_position_percent:
            return RiskValidationResult(
                approved=False,
                reason=f"Размер позиции {position_percent:.1f}% превышает лимит {max_position_percent}%",
                risk_level=RiskLevel.HIGH
            )
            
        # 3. Проверка общего количества открытых позиций
        open_positions = await self.portfolio.get_open_positions_count()
        max_positions = self.config.get('risk.max_open_positions', 5)
        
        if open_positions >= max_positions:
            return RiskValidationResult(
                approved=False,
                reason=f"Достигнут лимит открытых позиций: {open_positions}/{max_positions}",
                risk_level=RiskLevel.MEDIUM
            )
            
        # 4. Проверка дневных потерь
        daily_pnl = await self.portfolio.get_daily_pnl()
        max_daily_loss = self.config.get('risk.max_daily_loss_percent', -10.0)
        
        if daily_pnl < max_daily_loss:
            return RiskValidationResult(
                approved=False,
                reason=f"Превышен дневной лимит потерь: {daily_pnl:.1f}%",
                risk_level=RiskLevel.CRITICAL
            )
            
        return RiskValidationResult(
            approved=True,
            reason="Все проверки рисков пройдены",
            risk_level=RiskLevel.LOW
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки рисков: {e}")
        return RiskValidationResult(
            approved=False,
            reason=f"Ошибка валидации: {e}",
            risk_level=RiskLevel.CRITICAL
        )
```

### 3. Stop-Loss логика

```python
async def monitor_stop_loss(self, deals: List[Deal]):
    \"\"\"Мониторинг stop-loss для всех открытых сделок\"\"\"
    for deal in deals:
        if deal.status != 'OPEN':
            continue
            
        current_price = await self.exchange.fetch_ticker(deal.symbol)['last']
        
        # Расчет убытка
        if deal.side == 'BUY':
            loss_percent = ((current_price - deal.entry_price) / deal.entry_price) * 100
        else:
            loss_percent = ((deal.entry_price - current_price) / deal.entry_price) * 100
            
        stop_loss_threshold = self.config.get('risk.stop_loss_percent', -5.0)
        
        if loss_percent <= stop_loss_threshold:
            logger.warning(f"⚠️ STOP-LOSS TRIGGERED для сделки {deal.id}: {loss_percent:.2f}%")
            await self.trigger_stop_loss(deal, current_price, loss_percent)
            
async def trigger_stop_loss(self, deal: Deal, current_price: float, loss_percent: float):
    \"\"\"Экстренное закрытие убыточной позиции\"\"\"
    try:
        # Отменяем все связанные ордера
        if deal.sell_order and deal.sell_order.status == 'PENDING':
            await self.order_executor.cancel_order(deal.sell_order)
            
        # Размещаем market ордер для быстрого закрытия
        emergency_order = await self.order_executor.execute_sell_order(
            symbol=deal.symbol,
            amount=deal.amount,
            price=None,  # Market order
            order_type="MARKET"
        )
        
        # Уведомляем о срабатывании stop-loss
        await self.send_alert(
            f"🚨 STOP-LOSS: Сделка {deal.id} закрыта с убытком {loss_percent:.2f}%",
            AlertLevel.HIGH
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка выполнения stop-loss для сделки {deal.id}: {e}")
        await self.emergency_shutdown(f"Не удалось выполнить stop-loss: {e}")
```

### 4. Emergency Shutdown

```python
async def emergency_shutdown(self, reason: str):
    \"\"\"Экстренная остановка всех торговых операций\"\"\"
    logger.critical(f"🚨 EMERGENCY SHUTDOWN: {reason}")
    
    self.emergency_stop = True
    
    try:
        # 1. Отменяем все pending ордера
        pending_orders = await self.orders_repo.get_pending_orders()
        for order in pending_orders:
            try:
                await self.order_executor.cancel_order(order)
            except Exception as e:
                logger.error(f"Не удалось отменить ордер {order.id}: {e}")
                
        # 2. Закрываем все открытые позиции по market цене (опционально)
        emergency_close = self.config.get('risk.emergency_close_positions', False)
        if emergency_close:
            open_deals = await self.deals_repo.get_open_deals()
            for deal in open_deals:
                try:
                    await self.force_close_position(deal)
                except Exception as e:
                    logger.error(f"Не удалось закрыть позицию {deal.id}: {e}")
                    
        # 3. Отправляем критическое уведомление
        await self.send_alert(
            f"🚨 EMERGENCY SHUTDOWN: {reason}\\nВсе торговые операции остановлены!",
            AlertLevel.CRITICAL
        )
        
    except Exception as e:
        logger.critical(f"Ошибка в emergency shutdown: {e}")
```

## ✅ Критерии готовности

- [ ] Проверка баланса перед каждой сделкой
- [ ] Ограничение размера позиции относительно портфеля
- [ ] Stop-loss автоматически срабатывает при убытках > 5%
- [ ] Контроль максимального количества открытых позиций
- [ ] Мониторинг дневных убытков с автоостановкой
- [ ] Emergency shutdown при критических ситуациях
- [ ] Уведомления о критических событиях
- [ ] Интеграция с TradingOrchestrator
- [ ] Настраиваемые параметры рисков в конфигурации
- [ ] Подробное логирование всех решений по рискам

## 🧪 План тестирования

1. **Unit тесты:**
   - Тест проверки баланса с различными сценариями
   - Тест расчета размера позиции
   - Тест срабатывания stop-loss
   - Тест emergency shutdown

2. **Integration тесты:**
   - Тест полного цикла risk validation
   - Тест взаимодействия с OrderExecutionService
   - Тест реальных балансов (на testnet)

3. **Stress тесты:**
   - Симуляция рыночного краха
   - Множественные одновременные stop-loss
   - Сетевые сбои во время emergency shutdown

## 🔗 Связанные задачи

- **Зависит от:** Issue #2 (OrderExecutionService) - для закрытия позиций
- **Блокирует:** Issue #6 (DatabaseService) - для сохранения risk events
- **Связано с:** Issue #8 (ConfigurationService) - для настройки параметров рисков

## 📋 Подзадачи

- [ ] Спроектировать RiskManagementService API
- [ ] Реализовать проверку баланса и лимитов
- [ ] Добавить stop-loss мониторинг  
- [ ] Реализовать emergency shutdown
- [ ] Создать систему алертов и уведомлений
- [ ] Добавить конфигурируемые параметры рисков
- [ ] Интегрировать с TradingOrchestrator
- [ ] Написать comprehensive тесты
- [ ] Добавить metrics и мониторинг
- [ ] Документация по настройке рисков

## ⚠️ Критические параметры

```yaml
# Рекомендуемые настройки рисков для начала:
risk:
  max_position_percent: 5.0      # Максимум 5% портфеля на одну позицию
  stop_loss_percent: -3.0        # Stop-loss при убытке 3%
  max_daily_loss_percent: -10.0  # Остановка при дневном убытке 10%  
  max_open_positions: 3          # Максимум 3 открытые позиции
  emergency_close_positions: true # Закрывать позиции при emergency
  balance_buffer_percent: 5.0    # 5% буфер от доступного баланса
```

## 💡 Дополнительные заметки

- Начать с консервативных параметров рисков, постепенно оптимизировать
- Предусмотреть возможность ручного override для emergency situations  
- Добавить risk scoring для оценки общего уровня риска портфеля
- Рассмотреть интеграцию с внешними risk management tools в будущем
- Важно: всегда err on the side of caution - лучше пропустить прибыльную сделку, чем получить большой убыток
