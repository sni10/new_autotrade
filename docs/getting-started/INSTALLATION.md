# 📦 Установка AutoTrade v2.4.0

> **Полное руководство по установке и первоначальной настройке**

---

## 📋 Содержание

- [🔧 Системные требования](#-системные-требования)
- [📥 Установка](#-установка)
- [⚙️ Настройка](#️-настройка)
- [🚀 Первый запуск](#-первый-запуск)
- [✅ Проверка работы](#-проверка-работы)
- [🛠️ Устранение неполадок](#️-устранение-неполадок)

---

## 🔧 Системные требования

### 🐍 **Python**
- **Python 3.10+** (рекомендуется 3.11)
- **pip** (менеджер пакетов)

### 💻 **Операционная система**
- **Windows** 10/11
- **macOS** 12+
- **Linux** (Ubuntu 20.04+, Debian 11+)

### 🌐 **Подключение к интернету**
- Стабильное соединение для WebSocket подключений
- Доступ к API Binance

### 💾 **Свободное место**
- **Минимум**: 500 MB
- **Рекомендуется**: 2 GB (для логов и данных)

---

## 📥 Установка

### 1. **Клонирование репозитория**

```bash
# Клонировать репозиторий
git clone https://github.com/sni10/new_autotrade.git

# Перейти в папку проекта
cd new_autotrade
```

### 2. **Создание виртуального окружения**

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать виртуальное окружение
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### 3. **Установка зависимостей**

```bash
# Установить все зависимости
pip install -r requirements.txt

# Проверить установку
pip list
```

### 4. **Проверка структуры проекта**

```bash
# Проверить основные папки
ls -la
```

Должны присутствовать:
- `src/` - исходный код
- `binance_keys/` - папка для API ключей
- `config/` - файлы конфигурации
- `main.py` - точка входа
- `.env.example` - шаблон переменных окружения

---

## ⚙️ Настройка

### 1. **Настройка переменных окружения**

```bash
# Скопировать шаблон
cp .env.example .env

# Открыть файл для редактирования
nano .env  # или ваш любимый редактор
```

### 2. **Получение API ключей Binance**

#### 🏖️ **Sandbox (для тестирования)**
1. Перейти на [Binance Testnet](https://testnet.binance.vision/)
2. Войти/зарегистрироваться
3. Создать API ключ
4. Добавить в `.env`:
   ```bash
   BINANCE_SANDBOX_API_KEY=your_sandbox_api_key
   BINANCE_SANDBOX_SECRET=your_sandbox_secret
   ```

#### 🏭 **Production (для реальной торговли)**
1. Перейти на [Binance](https://www.binance.com/)
2. Аккаунт → API Management
3. Создать API ключ со следующими разрешениями:
   - ✅ **Spot Trading**
   - ✅ **Futures Trading** (при необходимости)
   - ❌ **Margin Trading** (не требуется)
   - ❌ **Withdrawals** (не требуется для безопасности)

### 3. **Настройка ключей для Production**

#### Создание RSA ключей:
```bash
# Создать приватный ключ
openssl genpkey -algorithm Ed25519 -out binance_keys/id_ed25519.pem

# Создать публичный ключ
openssl pkey -in binance_keys/id_ed25519.pem -pubout -out binance_keys/id_ed25519pub.pem
```

#### Добавить в `.env`:
```bash
BINANCE_PROD_API_KEY=your_production_api_key
BINANCE_PROD_PRIVATE_KEY_PATH=binance_keys/id_ed25519.pem
```

### 4. **Настройка торговых параметров**

Отредактировать `src/config/config.json`:

```json
{
  "currency_pair": {
    "base_currency": "ETH",      // Базовая валюта
    "quote_currency": "USDT",    // Котируемая валюта
    "deal_quota": 25.0,          // Размер позиции в USDT
    "profit_markup": 0.015,      // Целевая прибыль (1.5%)
    "deal_count": 3              // Максимум активных сделок
  },
  "risk_management": {
    "stop_loss_percent": 2.0,    // Базовый стоп-лосс (2%)
    "enable_stop_loss": true,
    "smart_stop_loss": {
      "enabled": true,
      "warning_percent": 5.0,    // Предупреждение при убытке 5%
      "critical_percent": 10.0,  // Критический уровень 10%
      "emergency_percent": 15.0  // Экстренное закрытие 15%
    }
  }
}
```

---

## 🚀 Первый запуск

### 1. **Проверка конфигурации**

```bash
# Проверить загрузку конфигурации
python -c "from src.config.config_loader import load_config; print('Config loaded successfully')"
```

### 2. **Запуск в режиме песочницы**

```bash
# Запустить в режиме тестирования
python main.py
```

### 3. **Первые логи**

При успешном запуске должны появиться логи:
```
🚀 AutoTrade v2.4.0 запущен!
📊 Режим: SANDBOX
💰 Валютная пара: ETH/USDT
🎯 Размер позиции: 25.0 USDT
```

### 4. **Остановка системы**

```bash
# Остановить систему (Ctrl+C)
# Или
python -c "import sys; sys.exit()"
```

---

## ✅ Проверка работы

### 1. **Проверка подключения к API**

```python
# Создать файл test_connection.py
import asyncio
from src.infrastructure.connectors.exchange_connector import ExchangeConnector

async def test_connection():
    connector = ExchangeConnector(use_sandbox=True)
    try:
        balance = await connector.fetch_balance()
        print("✅ Подключение к API успешно!")
        print(f"💰 Баланс: {balance}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

asyncio.run(test_connection())
```

### 2. **Проверка анализа стакана**

```python
# Создать файл test_orderbook.py
import asyncio
from src.domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer

async def test_orderbook():
    analyzer = OrderBookAnalyzer()
    try:
        # Здесь должен быть код для получения стакана
        print("✅ Анализ стакана работает!")
    except Exception as e:
        print(f"❌ Ошибка анализа стакана: {e}")

asyncio.run(test_orderbook())
```

### 3. **Проверка мониторинга**

```python
# Создать файл test_monitoring.py
from src.domain.services.orders.buy_order_monitor import BuyOrderMonitor

def test_monitoring():
    try:
        monitor = BuyOrderMonitor(
            order_service=None,  # Заглушка для теста
            exchange_connector=None,
            max_age_minutes=15.0
        )
        print("✅ Мониторинг ордеров настроен!")
    except Exception as e:
        print(f"❌ Ошибка мониторинга: {e}")

test_monitoring()
```

---

## 🛠️ Устранение неполадок

### 🔴 **Проблема**: "Module not found"

**Решение**:
```bash
# Проверить путь Python
export PYTHONPATH="${PYTHONPATH}:/path/to/new_autotrade"

# Или установить в editable mode
pip install -e .
```

### 🔴 **Проблема**: "API key invalid"

**Решение**:
1. Проверить правильность API ключей в `.env`
2. Убедиться, что ключи активны на Binance
3. Проверить разрешения ключей (Spot Trading должен быть включен)

### 🔴 **Проблема**: "WebSocket connection failed"

**Решение**:
```bash
# Проверить интернет соединение
ping api.binance.com

# Проверить брандмауэр
# Убедиться, что порты 443 и 9443 открыты
```

### 🔴 **Проблема**: "Permission denied на binance_keys/"

**Решение**:
```bash
# Настроить права доступа
chmod 600 binance_keys/id_ed25519.pem
chmod 644 binance_keys/id_ed25519pub.pem
```

### 🔴 **Проблема**: "Config load error"

**Решение**:
```bash
# Проверить синтаксис JSON
python -m json.tool src/config/config.json

# Проверить .env файл
cat .env | grep -v '^#'
```

---

## 🔧 Дополнительные настройки

### 1. **Настройка логирования**

```python
# В main.py добавить
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. **Настройка автозапуска (Linux)**

```bash
# Создать systemd сервис
sudo nano /etc/systemd/system/autotrade.service
```

Содержимое:
```ini
[Unit]
Description=AutoTrade v2.4.0
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/new_autotrade
ExecStart=/path/to/new_autotrade/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. **Мониторинг производительности**

```bash
# Установить дополнительные утилиты
pip install psutil
pip install memory_profiler
```

---

## 🎯 Заключение

После успешной установки и настройки у вас будет:

- ✅ **Работающая торговая система** с умным риск-менеджментом
- ✅ **Безопасная конфигурация** с защищенными API ключами
- ✅ **Асинхронный жизненный цикл** сделок
- ✅ **Трёхуровневая защита** от убытков

### 🚀 **Следующие шаги**:
1. Протестировать в sandbox режиме
2. Настроить параметры под вашу стратегию
3. Постепенно переходить к реальной торговле
4. Мониторить логи и статистику

### 📚 **Дополнительная документация**:
- [Configuration Guide](../configuration/CONFIGURATION.md)
- [API Reference](../api/API_REFERENCE.md)
- [Troubleshooting](../troubleshooting/TROUBLESHOOTING.md)

---

**Удачной торговли!** 🎯

> *"Подготовка - ключ к успешной торговле"*