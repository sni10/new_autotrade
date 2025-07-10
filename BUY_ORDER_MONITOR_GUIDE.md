# BUY_ORDER_MONITOR_GUIDE.md.new - Руководство по использованию
# 🕒 BuyOrderMonitor - Руководство по использованию

## 📋 ЧТО ЭТО ТАКОЕ

**BuyOrderMonitor** - простой сервис для автоматического мониторинга "протухших" BUY ордеров и их пересоздания по актуальным ценам.

## 🎯 ПРОБЛЕМА КОТОРУЮ РЕШАЕТ

**Сценарий:** Робот создал BUY ордер на покупку MAGIC по цене 1.50 USDT. Через 10 минут цена выросла до 2.00 USDT.

**БЕЗ BuyOrderMonitor:**
- Ордер висит по старой цене 1.50 ❌
- Никто не продаст по 1.50 когда рынок 2.00 ❌
- Капитал заблокирован бесконечно ❌

**С BuyOrderMonitor:**
- Через 15 минут или при отклонении >3% ордер автоматически отменяется ✅
- Создается новый BUY ордер по цене ~1.998 (чуть ниже рынка) ✅
- Торговля продолжается ✅

## ⚙️ НАСТРОЙКА

### Конфигурация в config.json:
```json
{
  "buy_order_monitor": {
    "enabled": true,
    "max_age_minutes": 15.0,              // 15 минут максимум
    "max_price_deviation_percent": 3.0,   // 3% отклонение от рынка
    "check_interval_seconds": 60,         // Проверка каждую минуту
    "auto_recreate_orders": true,         // Пересоздавать ордера
    "min_time_between_recreations_minutes": 5.0  // Пауза между пересозданиями
  }
}
```

### Инициализация в коде:
```python
from domain.services.buy_order_monitor import BuyOrderMonitor

buy_order_monitor = BuyOrderMonitor(
    order_service=order_service,
    exchange_connector=enhanced_exchange_connector,
    max_age_minutes=15.0,           # 15 минут максимум
    max_price_deviation_percent=3.0, # 3% отклонение цены
    check_interval_seconds=60       # Проверка каждую минуту
)

# Запуск в фоне
asyncio.create_task(buy_order_monitor.start_monitoring())
```

## 🔧 ЛОГИКА РАБОТЫ

### 1. Проверка возраста ордера
```python
age_minutes = (current_time - order.created_at) / 1000 / 60

if age_minutes > max_age_minutes:
    # Ордер протух по времени
    cancel_and_recreate()
```

### 2. Проверка отклонения цены
```python
current_price = get_market_price()
price_deviation = ((current_price - order.price) / order.price) * 100

if price_deviation > max_price_deviation_percent:
    # Ордер протух по цене  
    cancel_and_recreate()
```

### 3. Пересоздание ордера
```python
# Отменяем старый
await order_service.cancel_order(old_order)

# Создаем новый по актуальной цене
new_price = current_market_price * 0.999  # -0.1% для вероятности исполнения
new_order = await order_service.create_and_place_buy_order(...)
```

## 📊 МОНИТОРИНГ И СТАТИСТИКА

### Получение статистики:
```python
stats = buy_order_monitor.get_statistics()
print(stats)

# Результат:
# {
#   'running': True,
#   'max_age_minutes': 15.0,
#   'max_price_deviation_percent': 3.0,
#   'check_interval_seconds': 60,
#   'checks_performed': 150,
#   'stale_orders_found': 5,
#   'orders_cancelled': 5,
#   'orders_recreated': 4
# }
```

### Логи в консоли:
```
🕒 BUY ордер 123 протух по времени: 16.2 мин
📈 BUY ордер 456 протух по цене: рынок 2.0000, ордер 1.5000 (+33.3%)
🚨 Обрабатываем протухший BUY ордер 123
✅ BUY ордер 123 отменен
🔄 Пересоздаем BUY ордер: старая цена 1.5000, новая цена 1.9980
✅ BUY ордер пересозdan: 123 -> 789
```

## ⚙️ НАСТРОЙКА ПАРАМЕТРОВ

### Консервативные настройки (безопасно):
```python
BuyOrderMonitor(
    max_age_minutes=10.0,           # Короткий лимит времени
    max_price_deviation_percent=2.0, # Низкий лимит отклонения
    check_interval_seconds=30       # Частые проверки
)
```

### Агрессивные настройки (больше сделок):
```python
BuyOrderMonitor(
    max_age_minutes=30.0,           # Длинный лимит времени
    max_price_deviation_percent=5.0, # Высокий лимит отклонения  
    check_interval_seconds=120      # Редкие проверки
)
```

### Рекомендуемые настройки:
```python
BuyOrderMonitor(
    max_age_minutes=15.0,           # Средний лимит
    max_price_deviation_percent=3.0, # Умеренное отклонение
    check_interval_seconds=60       # Проверка каждую минуту
)
```

## 🛡️ БЕЗОПАСНОСТЬ

### Ограничения:
- Мониторинг только **BUY ордеров** (SELL ордера не трогает)
- Пересоздание только с **понижением цены** (безопасно)
- **Проверка баланса** перед пересозданием
- **Логирование всех операций**

### Защиты:
- Максимум попыток пересоздания
- Минимальный интервал между пересозданиями
- Graceful shutdown при ошибках
- Откат к старой логике при сбоях

## 🧪 ТЕСТИРОВАНИЕ

### Запуск тестов:
```bash
python test_buy_order_monitor.py.new
```

### Ожидаемый результат:
```
🧪 Тестирование BuyOrderMonitor...
✅ BuyOrderMonitor создан
🔍 Тестируем проверку протухшего ордера...
🕒 Ордер протух?: True
✅ Ордер корректно определен как протухший
🚨 Тестируем обработку протухшего ордера...
✅ Старый ордер отменен
✅ Новый ордер создан
🎉 Тест завершен!
```

## 📋 ИНТЕГРАЦИЯ В ПРОЕКТ

### 1. Копирование файлов:
```bash
# Основной сервис
cp domain/services/buy_order_monitor.py.new domain/services/buy_order_monitor.py

# Обновленный main.py
cp main.py.new main.py

# Обновленный config
cp config/config.json.new config/config.json
```

### 2. Проверка работы:
```bash
# Запуск тестов
python test_buy_order_monitor.py.new

# Запуск основного приложения
python main.py
```

### 3. Проверка логов:
Ищите в логах строки:
- `🕒 Запуск мониторинга BUY ордеров`
- `🚨 Обрабатываем протухший BUY ордер`
- `✅ BUY ордер пересозdan`

## ⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ

1. **Только BUY ордера** - SELL ордера будет обрабатывать RiskManager позже
2. **Sandbox режим** - начинайте с тестового режима
3. **Мониторинг балансов** - следите за тратами на комиссии
4. **Логирование** - весь процесс детально логируется
5. **Остановка** - сервис автоматически останавливается при завершении программы

## 🚀 РЕЗУЛЬТАТ

После внедрения BuyOrderMonitor:
- ✅ **НЕТ висящих ордеров** - старые ордера автоматически отменяются
- ✅ **Актуальные цены** - новые ордера по текущему рынку
- ✅ **Непрерывная торговля** - система продолжает работать при любых движениях цены
- ✅ **Эффективное использование капитала** - деньги не блокируются в протухших ордерах
- ✅ **Полная автоматизация** - вмешательство человека не требуется

**Теперь ваш торговый робот умеет справляться с "улетевшими в луну" ценами! 🚀**
