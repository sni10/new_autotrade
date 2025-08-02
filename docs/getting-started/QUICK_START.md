# 🏃 Быстрый старт AutoTrade v2.4.0

> **Запустите торговую систему за 5 минут**

---

## 🎯 Предварительные требования

### 📋 Что вам понадобится:
- **Python 3.8+** с pip
- **API ключи Binance** (sandbox или production)
- **Минимум 100 USDT** на счете (для тестирования)
- **Стабильное интернет-соединение**

---

## ⚡ Быстрая установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-repo/autotrade.git
cd autotrade
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка API ключей
```bash
# Создайте файл с API ключами
mkdir -p binance_keys
# Добавьте ваши ключи в binance_keys/
```

### 4. Базовая конфигурация
```bash
# Копируйте и отредактируйте конфигурацию
cp config/config.json.example config/config.json
```

---

## 🚀 Первый запуск

### 🧪 Тестовый режим (рекомендуется)
```bash
# Запуск в sandbox режиме
python main.py --sandbox
```

### 🎯 Основные параметры запуска
```bash
# Полный запуск с логированием
python main.py --verbose --log-level DEBUG

# Запуск с конкретной торговой парой
python main.py --symbol ETH/USDT

# Запуск с ограничением по времени
python main.py --max-runtime 3600  # 1 час
```

---

## 📊 Мониторинг работы

### 📈 Что вы увидите:
```
🚀 AutoTrade v2.4.0 запущен
📊 Торговая пара: ETH/USDT
💰 Баланс: 150.00 USDT
🔄 Мониторинг рынка...

🎯 Получен сигнал BUY: уверенность 85%
💰 Создан BUY ордер: 0.05 ETH по 3000 USDT
✅ Ордер исполнен успешно
🔄 Создан виртуальный SELL ордер: 0.05 ETH по 3090 USDT
⏰ Ожидание исполнения...
```

### 🔍 Файлы логов:
- `logs/autotrade_YYYY-MM-DD_HH-MM-SS.log`
- Консольный вывод в реальном времени

---

## ⚙️ Базовые настройки

### 🎛️ Важные параметры в config.json:
```json
{
  "trading": {
    "symbol": "ETH/USDT",
    "deal_quota": 50.0,
    "profit_markup": 3.0,
    "max_open_deals": 1
  },
  "risk_management": {
    "stop_loss_percent": 2.0,
    "enable_smart_stop_loss": true
  },
  "orderbook_analyzer": {
    "min_volume_threshold": 1000,
    "max_spread_percent": 0.3
  }
}
```

### 🔧 Быстрая настройка:
```bash
# Установка торговой пары
export SYMBOL="BTC/USDT"

# Установка бюджета на сделку
export DEAL_QUOTA=100.0

# Режим sandbox
export USE_SANDBOX=true
```

---

## 🛡️ Безопасность

### ⚠️ Важные правила:
1. **Всегда начинайте с sandbox** режима
2. **Не используйте все средства** сразу
3. **Следите за логами** в реальном времени
4. **Установите стоп-лосс** для защиты

### 🔐 Защита API ключей:
```bash
# Права доступа только для чтения
chmod 600 binance_keys/*

# Никогда не коммитьте ключи в git
echo "binance_keys/" >> .gitignore
```

---

## 🎯 Первые результаты

### 📊 Что ожидать:
- **Первые сигналы**: через 1-5 минут
- **Первая сделка**: через 5-15 минут
- **Прибыль**: 1-5% с каждой сделки

### 📈 Типичный день:
```
📊 Статистика за сессию:
- Всего сделок: 8
- Прибыльных: 6 (75%)
- Общая прибыль: +12.5 USDT (+2.5%)
- Время работы: 4h 23m
```

---

## 🔧 Быстрое устранение проблем

### 🚨 Частые ошибки:

#### ❌ "API ключи не найдены"
```bash
# Проверьте наличие файлов
ls -la binance_keys/
# Должны быть: api_key.txt, secret_key.txt
```

#### ❌ "Недостаточно средств"
```bash
# Проверьте баланс
python -c "from src.infrastructure.connectors.exchange_connector import ExchangeConnector; print(ExchangeConnector().fetch_balance())"
```

#### ❌ "Соединение не удалось"
```bash
# Проверьте интернет и настройки прокси
curl -I https://api.binance.com/api/v3/ping
```

---

## 🎉 Готово!

### 🎯 Что дальше:
1. [📊 Изучите интеграцию стакана](../guides/ORDERBOOK_INTEGRATION.md)
2. [⚙️ Настройте продвинутые параметры](CONFIGURATION.md)
3. [🛡️ Изучите управление рисками](../guides/RISK_MANAGEMENT.md)
4. [🔧 Настройте мониторинг](../guides/BUY_ORDER_MONITOR.md)

### 🏆 Успешной торговли!

> *"Лучший способ изучить торговлю - начать с малого и постепенно наращивать опыт"*

---

**Нужна помощь?** Проверьте [FAQ](../troubleshooting/FAQ.md) или [Troubleshooting](../troubleshooting/TROUBLESHOOTING.md)

*Последнее обновление: 15 июля 2025*