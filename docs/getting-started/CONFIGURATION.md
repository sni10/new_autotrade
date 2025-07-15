# ⚙️ Конфигурация AutoTrade v2.4.0

> **Полное руководство по настройке системы**

---

## 📋 Содержание

- [📖 Обзор системы конфигурации](#-обзор-системы-конфигурации)
- [🗂️ Структура конфигурационных файлов](#️-структура-конфигурационных-файлов)
- [🔧 Основные параметры](#-основные-параметры)
- [🛡️ Управление рисками](#️-управление-рисками)
- [📊 Анализ стакана](#-анализ-стакана)
- [🔐 Переменные окружения](#-переменные-окружения)
- [🎯 Примеры конфигураций](#-примеры-конфигураций)
- [🚨 Устранение неполадок](#-устранение-неполадок)

---

## 📖 Обзор системы конфигурации

AutoTrade v2.4.0 использует **двухуровневую систему конфигурации**:

1. **`src/config/config.json`** - основные настройки (не чувствительные данные)
2. **`.env`** - переменные окружения (API ключи, переопределения)

### 🔄 **Принцип работы**:
- Система загружает базовые настройки из `config.json`
- Переопределяет значения из `.env` файла
- Чувствительные данные (API ключи) хранятся только в `.env`

---

## 🗂️ Структура конфигурационных файлов

### 📁 **Основные файлы**:
```
new_autotrade/
├── src/config/
│   ├── config.json          # Основная конфигурация
│   └── config_loader.py     # Загрузчик конфигурации
├── .env                     # Переменные окружения (создается вами)
├── .env.example            # Шаблон переменных окружения
└── binance_keys/           # Приватные ключи API
    ├── id_ed25519.pem
    └── id_ed25519pub.pem
```

### 🔧 **Загрузчик конфигурации**:
```python
from src.config.config_loader import load_config

# Загрузить конфигурацию
config = load_config()
```

---

## 🔧 Основные параметры

### 💰 **Настройки валютной пары**

```json
{
  "currency_pair": {
    "base_currency": "ETH",        // Базовая валюта для торговли
    "quote_currency": "USDT",      // Котируемая валюта
    "order_life_time": 1,          // Время жизни ордера (минуты)
    "deal_quota": 25.0,            // Размер позиции в USDT
    "profit_markup": 0.015,        // Целевая прибыль (1.5%)
    "deal_count": 3                // Максимум активных сделок
  }
}
```

#### 📊 **Параметры**:
- **`base_currency`**: Актив для покупки (ETH, BTC, ADA, etc.)
- **`quote_currency`**: Валюта для оплаты (USDT, BUSD, BNB)
- **`deal_quota`**: Размер каждой сделки в котируемой валюте
- **`profit_markup`**: Желаемая прибыль в процентах (0.015 = 1.5%)
- **`deal_count`**: Максимальное количество одновременных сделок

### 🔐 **Настройки API Binance**

```json
{
  "binance": {
    "sandbox": {
      "apiKey": "",              // Заполняется из .env
      "secret": ""               // Заполняется из .env
    },
    "production": {
      "apiKey": "",              // Заполняется из .env
      "privateKeyPath": "binance_keys/id_ed25519.pem"
    }
  }
}
```

---

## 🛡️ Управление рисками

### 🆕 **Умная система стоп-лосса (v2.4.0)**

```json
{
  "risk_management": {
    "stop_loss_percent": 2.0,            // Базовый стоп-лосс (2%)
    "enable_stop_loss": true,            // Включить стоп-лосс
    "stop_loss_check_interval_seconds": 60, // Интервал проверки
    "smart_stop_loss": {
      "enabled": true,                   // Включить умный стоп-лосс
      "warning_percent": 5.0,            // 🟡 Предупреждение при убытке 5%
      "critical_percent": 10.0,          // 🟠 Критический уровень 10%
      "emergency_percent": 15.0,         // 🔴 Экстренное закрытие 15%
      "use_orderbook_analysis": true,    // Анализ стакана перед закрытием
      "require_support_break": true,     // Требовать пробой поддержки
      "volume_imbalance_threshold": -20.0, // Порог дисбаланса объемов
      "slippage_threshold": 2.0          // Порог слиппеджа
    }
  }
}
```

#### 🎯 **Уровни защиты**:
1. **🟡 Warning (5%)**: Предупреждение, позиция удерживается
2. **🟠 Critical (10%)**: Анализ стакана, возможное закрытие
3. **🔴 Emergency (15%)**: Принудительное закрытие позиции

#### 🧠 **Интеллектуальная логика**:
- **Анализ поддержки**: Не закрывать на сильных уровнях
- **Дисбаланс объемов**: Учитывать активность покупателей/продавцов
- **Слиппедж**: Избегать закрытия при высоком слиппедже

### 🔄 **Мониторинг BUY ордеров**

```json
{
  "buy_order_monitor": {
    "enabled": true,                         // Включить мониторинг
    "max_age_minutes": 5.0,                 // Максимальное время жизни (5 мин)
    "max_price_deviation_percent": 3.0,     // Максимальное отклонение цены (3%)
    "check_interval_seconds": 10,           // Интервал проверки (10 сек)
    "auto_recreate_orders": true,           // Автоматически пересоздавать ордера
    "min_time_between_recreations_minutes": 0.0 // Минимальный интервал между пересозданиями
  }
}
```

---

## 📊 Анализ стакана

### 📈 **Настройки анализатора стакана**

```json
{
  "orderbook_analyzer": {
    "min_volume_threshold": 1000,        // Минимальный объем для анализа
    "big_wall_threshold": 5000,          // Порог "большой стены"
    "max_spread_percent": 0.3,           // Максимальный спред (0.3%)
    "min_liquidity_depth": 15,           // Минимальная глубина ликвидности
    "typical_order_size": 10,            // Типичный размер ордера
    "enabled": true,                     // Включить анализ стакана
    "monitoring_interval": 0.1           // Интервал мониторинга (0.1 сек)
  }
}
```

### 🎯 **Торговые настройки**

```json
{
  "trading": {
    "enable_orderbook_validation": true,     // Включить валидацию стакана
    "orderbook_confidence_threshold": 0.6,   // Порог уверенности (60%)
    "require_orderbook_support": false,      // Требовать поддержку стакана
    "log_orderbook_analysis": true           // Логировать анализ стакана
  }
}
```

#### 📊 **Параметры анализа**:
- **`min_volume_threshold`**: Минимальный объем для валидного анализа
- **`big_wall_threshold`**: Размер "стены" для обнаружения поддержки/сопротивления
- **`max_spread_percent`**: Максимально допустимый спред
- **`min_liquidity_depth`**: Минимальная глубина ликвидности для торговли

---

## 🔐 Переменные окружения

### 📋 **Структура .env файла**

```bash
# Binance API keys
BINANCE_SANDBOX_API_KEY=your_sandbox_api_key
BINANCE_SANDBOX_SECRET=your_sandbox_secret
BINANCE_PROD_API_KEY=your_production_api_key
BINANCE_PROD_PRIVATE_KEY_PATH=binance_keys/id_ed25519.pem

# Orderbook analyzer settings
ORDERBOOK_ANALYZER_MIN_VOLUME_THRESHOLD=1000
ORDERBOOK_ANALYZER_BIG_WALL_THRESHOLD=5000
ORDERBOOK_ANALYZER_MAX_SPREAD_PERCENT=0.3
ORDERBOOK_ANALYZER_MIN_LIQUIDITY_DEPTH=15
ORDERBOOK_ANALYZER_TYPICAL_ORDER_SIZE=10
ORDERBOOK_ANALYZER_ENABLED=true
ORDERBOOK_ANALYZER_MONITORING_INTERVAL=0.1

# Trading settings
TRADING_ENABLE_ORDERBOOK_VALIDATION=true
TRADING_ORDERBOOK_CONFIDENCE_THRESHOLD=0.6
TRADING_REQUIRE_ORDERBOOK_SUPPORT=false
TRADING_LOG_ORDERBOOK_ANALYSIS=true

# Buy order monitor
BUY_ORDER_MONITOR_ENABLED=true
BUY_ORDER_MONITOR_MAX_AGE_MINUTES=5.0
BUY_ORDER_MONITOR_MAX_PRICE_DEVIATION_PERCENT=3.0
BUY_ORDER_MONITOR_CHECK_INTERVAL_SECONDS=10
BUY_ORDER_MONITOR_AUTO_RECREATE_ORDERS=true
BUY_ORDER_MONITOR_MIN_TIME_BETWEEN_RECREATIONS_MINUTES=0.0
```

### 🔑 **Переопределение через .env**

Любой параметр из `config.json` может быть переопределен через `.env`:

```bash
# Переопределить размер позиции
CURRENCY_PAIR_DEAL_QUOTA=50.0

# Переопределить целевую прибыль
CURRENCY_PAIR_PROFIT_MARKUP=0.02

# Переопределить максимальное количество сделок
CURRENCY_PAIR_DEAL_COUNT=5
```

---

## 🎯 Примеры конфигураций

### 🏖️ **Консервативная стратегия**

```json
{
  "currency_pair": {
    "base_currency": "BTC",
    "quote_currency": "USDT",
    "deal_quota": 50.0,            // Больший размер позиции
    "profit_markup": 0.02,         // Более высокая прибыль (2%)
    "deal_count": 2                // Меньше активных сделок
  },
  "risk_management": {
    "stop_loss_percent": 1.5,      // Более жесткий стоп-лосс
    "smart_stop_loss": {
      "warning_percent": 3.0,      // Более раннее предупреждение
      "critical_percent": 7.0,     // Более ранний критический уровень
      "emergency_percent": 10.0    // Более раннее экстренное закрытие
    }
  },
  "orderbook_analyzer": {
    "max_spread_percent": 0.2,     // Более строгий спред
    "min_liquidity_depth": 20      // Более глубокая ликвидность
  }
}
```

### 🚀 **Агрессивная стратегия**

```json
{
  "currency_pair": {
    "base_currency": "ETH",
    "quote_currency": "USDT",
    "deal_quota": 15.0,            // Меньший размер позиции
    "profit_markup": 0.01,         // Меньшая прибыль (1%)
    "deal_count": 5                // Больше активных сделок
  },
  "risk_management": {
    "stop_loss_percent": 3.0,      // Более мягкий стоп-лосс
    "smart_stop_loss": {
      "warning_percent": 7.0,      // Более позднее предупреждение
      "critical_percent": 12.0,    // Более поздний критический уровень
      "emergency_percent": 18.0    // Более позднее экстренное закрытие
    }
  },
  "buy_order_monitor": {
    "max_age_minutes": 2.0,        // Более быстрое пересоздание
    "max_price_deviation_percent": 2.0 // Более чувствительный к цене
  }
}
```

### 🎭 **Тестирование и разработка**

```json
{
  "currency_pair": {
    "base_currency": "ADA",
    "quote_currency": "USDT",
    "deal_quota": 10.0,            // Минимальный размер
    "profit_markup": 0.005,        // Минимальная прибыль (0.5%)
    "deal_count": 1                // Только одна сделка
  },
  "risk_management": {
    "stop_loss_percent": 5.0,      // Мягкий стоп-лосс для тестов
    "smart_stop_loss": {
      "enabled": false             // Отключить умный стоп-лосс
    }
  },
  "trading": {
    "log_orderbook_analysis": true, // Максимальное логирование
    "enable_orderbook_validation": false // Отключить валидацию для тестов
  }
}
```

---

## 🚨 Устранение неполадок

### 🔴 **Проблема**: "Config validation failed"

**Причины**:
- Неправильный формат JSON
- Отсутствующие обязательные поля
- Неверные типы данных

**Решение**:
```bash
# Проверить синтаксис JSON
python -m json.tool src/config/config.json

# Проверить обязательные поля
python -c "
from src.config.config_loader import load_config
try:
    config = load_config()
    print('✅ Конфигурация валидна')
except Exception as e:
    print(f'❌ Ошибка: {e}')
"
```

### 🔴 **Проблема**: "Environment variable not found"

**Причины**:
- Отсутствует `.env` файл
- Неправильное имя переменной
- Пробелы в `.env` файле

**Решение**:
```bash
# Проверить .env файл
cat .env | grep -v '^#' | grep -v '^$'

# Проверить переменные окружения
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('BINANCE_SANDBOX_API_KEY:', os.getenv('BINANCE_SANDBOX_API_KEY'))
"
```

### 🔴 **Проблема**: "API key validation failed"

**Причины**:
- Неправильные API ключи
- Истекший срок действия ключей
- Недостаточные разрешения

**Решение**:
```bash
# Проверить API ключи
python -c "
import asyncio
from src.infrastructure.connectors.exchange_connector import ExchangeConnector

async def test_keys():
    connector = ExchangeConnector(use_sandbox=True)
    try:
        balance = await connector.fetch_balance()
        print('✅ API ключи работают')
    except Exception as e:
        print(f'❌ Ошибка API: {e}')

asyncio.run(test_keys())
"
```

### 🔴 **Проблема**: "OrderBook analyzer not working"

**Причины**:
- Неправильные параметры анализатора
- Проблемы с WebSocket подключением
- Отсутствие данных стакана

**Решение**:
```bash
# Проверить параметры анализатора
python -c "
from src.config.config_loader import load_config
config = load_config()
print('OrderBook Analyzer Config:')
print(config.get('orderbook_analyzer', {}))
"
```

### 🔴 **Проблема**: "Stop loss not triggering"

**Причины**:
- Отключен stop loss
- Неправильные пороги
- Проблемы с мониторингом

**Решение**:
```bash
# Проверить настройки риск-менеджмента
python -c "
from src.config.config_loader import load_config
config = load_config()
risk_config = config.get('risk_management', {})
print(f'Stop Loss Enabled: {risk_config.get(\"enable_stop_loss\")}')
print(f'Stop Loss Percent: {risk_config.get(\"stop_loss_percent\")}')
print(f'Smart Stop Loss: {risk_config.get(\"smart_stop_loss\", {}).get(\"enabled\")}')
"
```

---

## 🎯 Рекомендации по настройке

### 🚀 **Для начинающих**:
1. Начните с **малых позиций** (deal_quota: 10-25 USDT)
2. Используйте **консервативные настройки** риск-менеджмента
3. Включите **все системы мониторинга**
4. Тестируйте сначала в **sandbox режиме**

### 💪 **Для опытных трейдеров**:
1. Настройте **индивидуальные параметры** под свою стратегию
2. Используйте **переменные окружения** для быстрого переключения
3. Мониторьте **логи системы** для оптимизации
4. Экспериментируйте с **параметрами анализа стакана**

### 🎯 **Для продакшена**:
1. Используйте **отдельные API ключи** для продакшена
2. Настройте **мониторинг и алерты**
3. Регулярно **проверяйте логи** системы
4. Создайте **резервные копии** конфигурации

---

## 📚 Дополнительные ресурсы

### 🔗 **Связанные документы**:
- [Installation Guide](../installation/INSTALLATION.md)
- [API Reference](../api/API_REFERENCE.md)
- [Troubleshooting](../troubleshooting/TROUBLESHOOTING.md)

### 📖 **Полезные ссылки**:
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)
- [JSON Validator](https://jsonlint.com/)
- [Environment Variables Guide](https://12factor.net/config)

---

**Успешной настройки!** ⚙️

> *"Правильная конфигурация - половина успеха в автоматической торговле"*