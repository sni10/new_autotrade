# 🛡️ AutoTrade v3.0: Безопасная Стратегия Миграции

**Версия:** 1.0 (Дополнение к INFRASTRUCTURE_MIGRATION_PLAN_V2.md)  
**Статус:** Надежная стратегия  
**Принцип:** "НЕ СЛОМАЙ НИХУЯ"  

---

## 🎯 Философия Безопасности

### Основной принцип:
> **Меняем ПО ОДНОЙ СТРОКЕ КОДА за раз. Тестируем. Если сломалось - откатываем за 30 секунд.**

### Гарантии:
- ✅ **Торговая логика не меняется** - тот же API, те же методы
- ✅ **Полный откат за 30 секунд** - через изменение конфига  
- ✅ **Тестирование каждого шага** - на реальных данных
- ✅ **Fallback репозитории** - старые остаются как резерв

---

## 🧱 Стратегия "Один Кирпичик - Один Тест"

### **ЭТАП 1: DealService (5 минут)**

#### **Что меняем:**
**Файл:** `src/domain/services/deals/deal_service.py`
```python
# БЫЛО:
def __init__(self, deals_repo: InMemoryDealsRepository, order_service, deal_factory, exchange_connector):

# СТАЛО:  
def __init__(self, deals_repo: IDealsRepository, order_service, deal_factory, exchange_connector):
```

**ИЗМЕНИЛИ:** 1 строку кода. Больше НИЧЕГО.

#### **Как тестируем:**
```python
# Запускаем систему в sandbox
# Проверяем:
deal = Deal("ETH/USDT")
saved_deal = await deal_service.create_new_deal(deal)
assert saved_deal.id is not None  # Сохранилось

deals = await deal_service.get_open_deals()
assert len(deals) >= 0  # Читается

print("✅ DealService работает с новым репозиторием")
```

#### **Откат (если сломалось):**
```python
# Возвращаем:
def __init__(self, deals_repo: InMemoryDealsRepository, ...):
```

#### **Настройка в main.py:**
```python
# ДОБАВЛЯЕМ (старое оставляем закомментированным):
deals_repo = await repository_factory.get_deals_repository()
# deals_repo = InMemoryDealsRepository()  # ← FALLBACK

deal_service = DealService(deals_repo, order_service, deal_factory, pro_exchange_connector_sandbox)
```

#### **Настройка fallback в config.json:**
```json
{
  "storage": {
    "deals_type": "memory_first_postgres"
    // "deals_type": "in_memory_legacy"  ← ОТКАТ ЧЕРЕЗ КОНФИГ
  }
}
```

---

### **ЭТАП 2: OrderService (5 минут)**

**ТОЛЬКО ПОСЛЕ** успешного тестирования DealService!

#### **Что меняем:**
**Файл:** `src/domain/services/orders/order_service.py`
```python
# БЫЛО:
def __init__(self, orders_repo: InMemoryOrdersRepository, ...):

# СТАЛО:
def __init__(self, orders_repo: IOrdersRepository, ...):
```

#### **Как тестируем:**
```python
# Создаем ордер
order = Order("ETH/USDT", "BUY", 0.1, 3000)
saved_order = await order_service.create_and_place_buy_order(currency_pair, 25.0)
assert saved_order.id is not None

# Читаем ордера
orders = await order_service.get_open_orders()
assert isinstance(orders, list)

print("✅ OrderService работает с новым репозиторием")
```

#### **Настройка в main.py:**
```python
orders_repo = await repository_factory.get_orders_repository()
# orders_repo = InMemoryOrdersRepository(max_orders=50000)  # ← FALLBACK

order_service = OrderService(orders_repo, order_factory, pro_exchange_connector_sandbox, symbol_ccxt)
```

---

### **ЭТАП 3: Интеграционный Тест (10 минут)**

**ТОЛЬКО ПОСЛЕ** успешного тестирования обоих сервисов!

#### **Тест полного цикла сделки:**
```python
async def test_full_deal_cycle():
    """Тест: создание сделки → создание BUY ордера → проверка сохранения."""
    
    # 1. Создаем валютную пару
    currency_pair = CurrencyPair("ETH/USDT", "ETH", "USDT", 25.0)
    
    # 2. Создаем новую сделку
    deal = await deal_service.create_new_deal(currency_pair, 25.0)
    assert deal.id is not None
    print(f"✅ Сделка создана: {deal.id}")
    
    # 3. Создаем BUY ордер
    buy_order = await order_service.create_and_place_buy_order(currency_pair, 25.0)
    assert buy_order.id is not None
    print(f"✅ BUY ордер создан: {buy_order.id}")
    
    # 4. Проверяем связь
    deal.buy_order = buy_order
    updated_deal = await deal_service.deals_repo.save(deal)
    assert updated_deal.buy_order.id == buy_order.id
    print(f"✅ Связь сделка-ордер работает")
    
    # 5. Проверяем чтение
    open_deals = await deal_service.get_open_deals()
    deal_ids = [d.id for d in open_deals]
    assert deal.id in deal_ids
    print(f"✅ Чтение открытых сделок работает")
    
    print("🎉 ПОЛНЫЙ ЦИКЛ СДЕЛКИ РАБОТАЕТ!")

# Запускаем тест
await test_full_deal_cycle()
```

---

## 🚨 Процедура Экстренного Отката

### **Если что-то пошло не так:**

#### **Вариант 1: Быстрый откат через конфиг (30 секунд)**
```json
// config.json
{
  "storage": {
    "deals_type": "in_memory_legacy",      // ← Откат DealService
    "orders_type": "in_memory_legacy"      // ← Откат OrderService
  }
}
```

**Перезапускаем систему.** Фабрика автоматически создаст старые репозитории.

#### **Вариант 2: Откат через код (1 минута)**
```python
// main.py
// Раскомментируем старые строки:
deals_repo = InMemoryDealsRepository()                    // ← Раскомментировать
orders_repo = InMemoryOrdersRepository(max_orders=50000)  // ← Раскомментировать

// Комментируем новые:
// deals_repo = await repository_factory.get_deals_repository()   // ← Закомментировать
// orders_repo = await repository_factory.get_orders_repository() // ← Закомментировать
```

#### **Вариант 3: Откат кода (2 минуты)**
```python
// src/domain/services/deals/deal_service.py
def __init__(self, deals_repo: InMemoryDealsRepository, ...):  // ← Вернуть старый тип

// src/domain/services/orders/order_service.py  
def __init__(self, orders_repo: InMemoryOrdersRepository, ...): // ← Вернуть старый тип
```

---

## 🔒 Гарантии Безопасности

### **1. API не меняется**
```python
// ДО миграции:
await deal_service.create_new_deal(currency_pair, 25.0)
await deal_service.get_open_deals()
await order_service.create_and_place_buy_order(currency_pair, 25.0)

// ПОСЛЕ миграции:
await deal_service.create_new_deal(currency_pair, 25.0)  // ← ТОТ ЖЕ КОД
await deal_service.get_open_deals()                      // ← ТОТ ЖЕ КОД  
await order_service.create_and_place_buy_order(currency_pair, 25.0)  // ← ТОТ ЖЕ КОД
```

### **2. Результаты не меняются**
```python
// ДО: 
deals: List[Deal] = await deal_service.get_open_deals()

// ПОСЛЕ:
deals: List[Deal] = await deal_service.get_open_deals()  // ← ТОТ ЖЕ ТИП
```

### **3. Торговая логика не меняется**
- **run_realtime_trading.py** - без изменений
- **BuyOrderMonitor** - без изменений  
- **DealCompletionMonitor** - без изменений
- **OrderExecutionService** - без изменений

**Меняется ТОЛЬКО ГДЕ данные хранятся. КАК они используются - не меняется.**

---

## 📊 Чек-лист Безопасной Миграции

### **Перед началом:**
- [ ] Backup всей кодовой базы
- [ ] PostgreSQL настроена и доступна
- [ ] Фабрика репозиториев реализована с fallback'ами
- [ ] Система запускается в текущем состоянии

### **После ЭТАПА 1 (DealService):**
- [ ] Система запускается без ошибок
- [ ] Можно создать новую сделку
- [ ] Можно получить список открытых сделок  
- [ ] PostgreSQL содержит записи о сделках
- [ ] Время отклика не ухудшилось

### **После ЭТАПА 2 (OrderService):**
- [ ] Система запускается без ошибок
- [ ] Можно создать новый ордер
- [ ] Можно получить список открытых ордеров
- [ ] PostgreSQL содержит записи об ордерах
- [ ] Связи сделка-ордер работают

### **После ЭТАПА 3 (Интеграция):**
- [ ] Полный цикл сделки работает
- [ ] Торговый процесс запускается  
- [ ] Мониторы работают без ошибок
- [ ] Данные корректно сохраняются и читаются
- [ ] Graceful shutdown работает

---

## 🎯 Критерии Успеха

### **Технические:**
- ✅ Система запускается за то же время
- ✅ Торговые операции выполняются за то же время
- ✅ Память используется в тех же пределах  
- ✅ PostgreSQL записи создаются корректно

### **Функциональные:**
- ✅ Создание сделок работает
- ✅ Создание ордеров работает
- ✅ Чтение данных работает
- ✅ Связи между объектами работают

### **Операционные:**
- ✅ Логи не содержат критических ошибок
- ✅ Можно остановить и запустить систему
- ✅ Данные сохраняются между перезапусками
- ✅ Откат работает за заявленное время

---

## 🚫 Красные Флаги (СТОП-сигналы)

### **Немедленно откатываемся если:**
- ❌ Время создания сделки > 100ms (было ~1ms)
- ❌ Время чтения сделок > 50ms (было ~1ms)  
- ❌ Потребление памяти выросло > 2x
- ❌ В логах PostgreSQL connection errors
- ❌ Торговый цикл зависает > 5 секунд
- ❌ Любая критическая ошибка в торговле

### **Процедура СТОП:**
1. **Останавливаем торговлю** (Ctrl+C)
2. **Меняем конфиг** на `"in_memory_legacy"`  
3. **Перезапускаем систему**
4. **Проверяем что торговля работает**
5. **Анализируем проблему в спокойной обстановке**

---

## 🎉 Заключение

Данная стратегия обеспечивает **максимально безопасную миграцию** с возможностью отката на любом этапе.

### **Ключевые принципы:**
- 🧱 **По одному компоненту** - минимизация рисков
- 🔒 **Полная обратимость** - откат в любой момент  
- 🧪 **Тестирование каждого шага** - никаких сюрпризов
- ⚡ **Сохранение производительности** - торговля не страдает

### **Результат:**
После успешного завершения получаем **надежную персистентность** без потери скорости торговли и с возможностью мощной аналитики через DataFrame.

**Если хоть что-то пойдет не так - откатываемся и остаемся с рабочей системой.**