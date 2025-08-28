# 🛠️ Руководство по устранению неполадок

> **Решение самых частых проблем AutoTrade v2.4.0**

---

## 🚨 Критические ошибки

### ❌ Система не запускается

#### **Симптомы:**
- Ошибка при запуске `python main.py`
- Crash сразу после старта
- ImportError или ModuleNotFoundError

#### **Диагностика:**
```bash
# Проверка версии Python
python --version  # Должна быть 3.8+

# Проверка зависимостей
pip list | grep -E "(ccxt|pandas|numpy|asyncio)"

# Проверка config.json
python -c "import json; print(json.load(open('config/config.json')))"
```

#### **Решение:**
```bash
# 1. Переустановка зависимостей
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# 2. Проверка конфигурации
cp config/config.json.example config/config.json

# 3. Проверка Python пути
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

### ❌ Ошибки API ключей

#### **Симптомы:**
- "Invalid API key" или "API key not found"
- "Permission denied" для торговых операций
- Проблемы с аутентификацией

#### **Диагностика:**
```bash
# Проверка наличия ключей
ls -la binance_keys/
# Должны быть файлы с правильными правами

# Проверка содержимого ключей
head -1 binance_keys/api_key.txt
# Должен быть действительный API ключ

# Тест подключения
python -c "
from src.infrastructure.connectors.exchange_connector import ExchangeConnector
connector = ExchangeConnector(use_sandbox=True)
print(connector.fetch_balance())
"
```

#### **Решение:**
```bash
# 1. Проверка файлов ключей
chmod 600 binance_keys/*
ls -la binance_keys/

# 2. Пересоздание ключей в Binance
# - Войдите в API Management
# - Создайте новые ключи
# - Установите права: Spot Trading

# 3. Обновление конфигурации
echo "your_api_key_here" > binance_keys/api_key.txt
echo "your_secret_key_here" > binance_keys/secret_key.txt
```

---

### ❌ WebSocket соединение не работает

#### **Симптомы:**
- "WebSocket connection failed"
- Нет обновлений тикеров
- Постоянные переподключения

#### **Диагностика:**
```bash
# Проверка интернет соединения
ping -c 3 api.binance.com

# Проверка портов
telnet stream.binance.com 9443

# Проверка DNS
nslookup api.binance.com
```

#### **Решение:**
```bash
# 1. Проверка настроек прокси
unset HTTP_PROXY HTTPS_PROXY

# 2. Обновление ccxt
pip install --upgrade ccxt

# 3. Альтернативный endpoint
# В config.json добавить:
{
  "exchange": {
    "urls": {
      "api": "https://api1.binance.com",
      "stream": "wss://stream.binance.com:9443"
    }
  }
}
```

---

## ⚠️ Торговые проблемы

### ❌ Ордера не исполняются

#### **Симптомы:**
- BUY ордера висят долго
- Сделки не закрываются
- Статус "PENDING" не меняется

#### **Диагностика:**
```bash
# Проверка баланса
python -c "
from src.infrastructure.connectors.exchange_connector import ExchangeConnector
connector = ExchangeConnector()
print('Balance:', connector.fetch_balance())
"

# Проверка открытых ордеров
python -c "
from src.infrastructure.connectors.exchange_connector import ExchangeConnector
connector = ExchangeConnector()
print('Open orders:', connector.fetch_open_orders())
"

# Проверка цен
python -c "
from src.infrastructure.connectors.exchange_connector import ExchangeConnector
connector = ExchangeConnector()
print('Ticker:', connector.fetch_ticker('ETH/USDT'))
"
```

#### **Решение:**
```bash
# 1. Проверка настроек цены
# В config.json уменьшить profit_markup
{
  "trading": {
    "profit_markup": 2.0  # Было 3.0
  }
}

# 2. Проверка лимитов биржи
# Увеличить минимальный размер ордера

# 3. Принудительная отмена ордеров
python -c "
from src.domain.services.order_service import OrderService
service = OrderService()
service.cancel_all_orders()
"
```

---

### ❌ Убыточные сделки

#### **Симптомы:**
- Много убыточных сделок подряд
- Стоп-лосс не срабатывает
- Большие потери

#### **Диагностика:**
```bash
# Анализ истории сделок
python order_history_viewer.py

# Проверка настроек риск-менеджмента
grep -A 5 "risk_management" config/config.json

# Проверка рыночных условий
python -c "
from src.domain.services.market_data.ticker_service import TickerService
service = TickerService()
print('Market conditions:', service.get_market_analysis())
"
```

#### **Решение:**
```bash
# 1. Уменьшение размера позиций
# В config.json:
{
  "trading": {
    "deal_quota": 25.0  # Было 50.0
  }
}

# 2. Ужесточение стоп-лосса
{
  "risk_management": {
    "stop_loss_percent": 1.0,  # Было 2.0
    "enable_smart_stop_loss": true
  }
}

# 3. Пауза в торговле
# Добавить в config.json:
{
  "trading": {
    "pause_after_loss": true,
    "pause_duration_minutes": 30
  }
}
```

---

## 🔧 Проблемы производительности

### ❌ Медленная работа системы

#### **Симптомы:**
- Задержки в обработке сигналов
- Высокое потребление CPU/RAM
- Долгие ответы API

#### **Диагностика:**
```bash
# Мониторинг ресурсов
top -p $(pgrep -f "python main.py")

# Профилирование Python
python -m cProfile -o profile.stats main.py

# Анализ логов производительности
grep "Performance" logs/autotrade_*.log | tail -20
```

#### **Решение:**
```bash
# 1. Оптимизация кэширования
# В config.json:
{
  "performance": {
    "cache_indicators": true,
    "cache_orderbook": true,
    "cache_ttl_seconds": 30
  }
}

# 2. Уменьшение частоты запросов
{
  "intervals": {
    "ticker_update": 5,      # Было 1
    "orderbook_update": 10,  # Было 5
    "order_check": 30        # Было 10
  }
}

# 3. Очистка логов
find logs/ -name "*.log" -mtime +7 -delete
```

---

## 📊 Проблемы с данными

### ❌ Неточные сигналы

#### **Симптомы:**
- Много ложных сигналов
- Сигналы не генерируются
- Противоречивые индикаторы

#### **Диагностика:**
```bash
# Проверка исторических данных
python -c "
from src.domain.services.market_data.ticker_service import TickerService
service = TickerService()
print('Historical data:', service.get_historical_data('ETH/USDT', '1h', 100))
"

# Проверка настроек индикаторов
grep -A 10 "indicators" config/config.json

# Анализ качества сигналов
python -c "
from src.domain.services.trading.signal_analysis import SignalAnalysis
analyzer = SignalAnalysis()
print('Signal quality:', analyzer.analyze_recent_signals())
"
```

#### **Решение:**
```bash
# 1. Настройка параметров MACD
# В config.json:
{
  "indicators": {
    "macd": {
      "fast_period": 12,
      "slow_period": 26,
      "signal_period": 9
    }
  }
}

# 2. Улучшение фильтрации
{
  "signal_filters": {
    "min_confidence": 0.7,     # Было 0.5
    "require_volume": true,
    "check_spread": true
  }
}

# 3. Добавление дополнительных индикаторов
{
  "indicators": {
    "use_rsi": true,
    "use_bollinger": true,
    "use_volume": true
  }
}
```

---

## 🔍 Отладка и диагностика

### 🔬 Включение детального логирования

```bash
# Полное логирование
python main.py --log-level DEBUG --verbose

# Логирование конкретных компонентов
export LOG_LEVEL=DEBUG
export LOG_COMPONENTS="trading,orderbook,signals"
python main.py
```

### 📋 Сбор диагностической информации

```bash
# Создание отчета о системе
python -c "
import sys, platform, subprocess
print('Python version:', sys.version)
print('Platform:', platform.platform())
print('Packages:', subprocess.check_output(['pip', 'list']).decode())
"

# Проверка статуса системы
python -c "
from src.application.utils.system_diagnostics import SystemDiagnostics
diag = SystemDiagnostics()
print(diag.get_system_status())
"
```

### 🧪 Тестирование компонентов

```bash
# Тест подключения к бирже
python -c "
from src.infrastructure.connectors.exchange_connector import ExchangeConnector
connector = ExchangeConnector(use_sandbox=True)
try:
    balance = connector.fetch_balance()
    print('✅ Подключение OK:', balance)
except Exception as e:
    print('❌ Ошибка подключения:', e)
"

# Тест генерации сигналов
python -c "
from src.domain.services.market_data.ticker_service import TickerService
service = TickerService()
try:
    signal = service.get_signal('ETH/USDT')
    print('✅ Сигнал OK:', signal)
except Exception as e:
    print('❌ Ошибка сигнала:', e)
"
```

---

## 🚑 Экстренные процедуры

### 🔴 Экстренная остановка системы

```bash
# Мягкая остановка
pkill -TERM -f "python main.py"

# Жесткая остановка
pkill -KILL -f "python main.py"

# Остановка через код
python -c "
from src.domain.services.trading.emergency_stop import EmergencyStop
EmergencyStop().stop_all_trading()
"
```

### 🔴 Принудительное закрытие позиций

```bash
# Через веб-интерфейс Binance
# https://www.binance.com/en/my/orders

# Через код
python -c "
from src.domain.services.trading.trading_service import TradingService
service = TradingService()
service.force_close_all_deals()
"

# Отмена всех ордеров
python -c "
from src.infrastructure.connectors.exchange_connector import ExchangeConnector
connector = ExchangeConnector()
connector.cancel_all_orders()
"
```

---

## 📞 Получение поддержки

### 🔍 Подготовка к обращению в поддержку

```bash
# Сбор необходимой информации
echo "=== System Info ===" > support_report.txt
python --version >> support_report.txt
cat config/config.json >> support_report.txt

echo "=== Recent Logs ===" >> support_report.txt
tail -50 logs/autotrade_*.log >> support_report.txt

echo "=== Error Messages ===" >> support_report.txt
grep -i "error\|exception" logs/autotrade_*.log | tail -20 >> support_report.txt
```

### 📧 Контакты для поддержки

- **GitHub Issues**: [создать issue](https://github.com/your-repo/issues)
- **Discord**: [присоединиться к серверу](https://discord.gg/autotrade)
- **Email**: support@autotrade.dev
- **Telegram**: @autotrade_support

---

## 🎯 Профилактические меры

### ✅ Регулярное обслуживание

```bash
# Еженедельно
# 1. Обновление зависимостей
pip install -r requirements.txt --upgrade

# 2. Очистка логов
find logs/ -name "*.log" -mtime +30 -delete

# 3. Проверка конфигурации
python -c "
from src.config.config_loader import ConfigLoader
loader = ConfigLoader()
print('Config OK:', loader.validate_config())
"

# 4. Резервное копирование
cp -r config/ backup/config_$(date +%Y%m%d)
```

### ⚙️ Мониторинг здоровья системы

```bash
# Скрипт мониторинга
#!/bin/bash
while true; do
    if ! pgrep -f "python main.py" > /dev/null; then
        echo "System down! Restarting..." | mail -s "AutoTrade Alert" admin@example.com
        python main.py &
    fi
    sleep 60
done
```

---

## 🎉 Успешного устранения проблем!

> *"Каждая решенная проблема делает систему более стабильной и надежной"*

**Проблема не решена?** Обратитесь к [FAQ](FAQ.md) или создайте issue в GitHub.

---

*Последнее обновление: 15 июля 2025*