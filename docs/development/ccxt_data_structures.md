## Структуры данных CCXT

Этот документ описывает унифицированные структуры данных, которые библиотека CCXT использует для взаимодействия с различными криптовалютными биржами.

### Exchange Structure (Структура Биржи)

Это корневой объект, представляющий саму биржу и её возможности.

```json
{
  "id": "exchange",
  "name": "Exchange",
  "countries": [ "US", "CN", "EU" ],
  "urls": {
    "api": "https://api.example.com/data",
    "www": "https://www.example.com",
    "doc": "https://docs.example.com/api"
  },
  "version": "v1",
  "has": {
    "cancelOrder": true,
    "createOrder": true,
    "fetchBalance": true,
    "fetchMarkets": true,
    "fetchOHLCV": true,
    "fetchTicker": true,
    "fetchOrderBook": true
  },
  "timeframes": {
    "1m": "1minute",
    "1h": "1hour",
    "1d": "1day"
  },
  "timeout": 10000,
  "rateLimit": 2000,
  "markets": { "...": "..." },
  "symbols": [ "...": "..." ],
  "currencies": { "...": "..." },
  "apiKey": "...",
  "secret": "...",
  "password": "...",
  "uid": "...",
  "options": { "...": "..." }
}
```

### 📌 Примеры базового использования CCXT

```python
import ccxt

# Инициализация биржи и включение режима песочницы
exchange = ccxt.binance()
exchange.set_sandbox_mode(True)

# Загрузка рынков
exchange.load_markets()

# Получение тикера
ticker = exchange.fetch_ticker('BTC/USDT')
print(ticker['last'])

# Создание рыночного ордера
order = exchange.create_market_buy_order('BTC/USDT', 0.001)
print(order['id'])
```

### ⚠️ Обработка ошибок и rate limits

```python
try:
    ticker = exchange.fetch_ticker('BTC/USDT')
except ccxt.NetworkError as e:
    print(f'Network error: {e}')
except ccxt.ExchangeError as e:
    print(f'Exchange error: {e}')

import time
time.sleep(exchange.rateLimit / 1000)
```
### `load_markets()` (Market Structure)

Структура, описывающая торговую пару и её правила.

```json
{
    "BTC/USDT": {
        "id": "BTCUSDT",
        "symbol": "BTC/USDT",
        "base": "BTC",
        "quote": "USDT",
        "baseId": "btc",
        "quoteId": "usdt",
        "active": true,
        "type": "spot",
        "spot": true,
        "margin": true,
        "future": false,
        "swap": false,
        "option": false,
        "contract": false,
        "taker": 0.002,
        "maker": 0.0016,
        "limits": {
            "amount": {
                "min": 0.00001,
                "max": 10000.0
            },
            "price": {
                "min": 0.01,
                "max": 1000000.0
            },
            "cost": {
                "min": 10.0
            },
            "leverage": {
                "min": 1.0,
                "max": 125.0
            }
        },
        "precision": {
            "amount": 8,
            "price": 2,
            "cost": 8
        },
        "info": {}
    }
}
```

### `fetch_ticker()` (Ticker Structure)

Структура, содержащая статистику цен по торговой паре за последние 24 часа.

```json
{
    "symbol": "BTC/USDT",
    "timestamp": 1672531200000,
    "datetime": "2023-01-01T00:00:00.000Z",
    "high": 61000.0,
    "low": 59000.0,
    "bid": 60000.2,
    "bidVolume": 0.5,
    "ask": 60001.8,
    "askVolume": 0.8,
    "vwap": 60100.0,
    "open": 59500.0,
    "close": 60200.0,
    "last": 60200.0,
    "previousClose": 59400.0,
    "change": 700.0,
    "percentage": 1.17,
    "average": 59850.0,
    "baseVolume": 1000.0,
    "quoteVolume": 60100000.0,
    "info": {}
}
```

### `fetch_order_book()` (Order Book Structure)

Структура, представляющая стакан ордеров (цены и объемы на покупку и продажу).

```json
{
  "bids": [
    [60000.2, 0.5],
    [60000.1, 1.2],
    [60000.0, 2.5]
  ],
  "asks": [
    [60001.8, 0.8],
    [60001.9, 1.5],
    [60002.0, 3.1]
  ],
  "symbol": "BTC/USDT",
  "timestamp": 1672531200000,
  "datetime": "2023-01-01T00:00:00.000Z",
  "nonce": 1234567890
}
```

### `fetch_balance()` (Balance Structure)

Структура, описывающая баланс пользователя на бирже.

```json
{
    "info": {},
    "free": {
        "BTC": 0.01,
        "ETH": 0.5,
        "USDT": 1000.0
    },
    "used": {
        "BTC": 0.005,
        "ETH": 0.0,
        "USDT": 250.0
    },
    "total": {
        "BTC": 0.015,
        "ETH": 0.5,
        "USDT": 1250.0
    }
}
```

### `create_order()` / `fetch_order()` (Order Structure)

Структура, описывающая ордер.

```json
{
    "id": "12345-67890:09876/54321",
    "clientOrderId": "abcdef-ghijkl-mnopqr-stuvwx",
    "datetime": "2017-08-17 12:42:48.000",
    "timestamp": 1502962968000,
    "lastTradeTimestamp": 1502962968123,
    "status": "open",
    "symbol": "BTC/USD",
    "type": "limit",
    "timeInForce": "GTC",
    "side": "sell",
    "price": 6000.0,
    "average": 6050.0,
    "amount": 1.0,
    "filled": 0.5,
    "remaining": 0.5,
    "cost": 3025.0,
    "trades": [],
    "fee": {
        "cost": 0.005,
        "currency": "USD",
        "rate": 0.0005
    },
    "info": {}
}
```