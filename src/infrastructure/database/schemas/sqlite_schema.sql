-- AutoTrade v2.4.0 SQLite Database Schema
-- Адаптированная схема для SQLite (для локальной разработки и тестирования)

-- =================================================================
-- ОСНОВНЫЕ ТАБЛИЦЫ
-- =================================================================

-- Включаем внешние ключи в SQLite
PRAGMA foreign_keys = ON;

-- Таблица валютных пар
CREATE TABLE currency_pairs (
    symbol TEXT PRIMARY KEY,
    base_currency TEXT NOT NULL,
    quote_currency TEXT NOT NULL,
    precision_data TEXT NOT NULL DEFAULT '{}', -- JSON as TEXT
    limits_data TEXT NOT NULL DEFAULT '{}',    -- JSON as TEXT
    maker_fee REAL DEFAULT 0.001,
    taker_fee REAL DEFAULT 0.001,
    active INTEGER DEFAULT 1, -- BOOLEAN as INTEGER
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сделок
CREATE TABLE deals (
    deal_id TEXT PRIMARY KEY, -- UUID as TEXT
    currency_pair_symbol TEXT NOT NULL REFERENCES currency_pairs(symbol),
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN (
        'ACTIVE', 'WAITING_SELL', 'COMPLETED', 'CANCELLED', 'FAILED'
    )),
    buy_order_id TEXT,
    sell_order_id TEXT,
    target_profit_percent REAL,
    actual_profit REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME,
    metadata TEXT DEFAULT '{}' -- JSON as TEXT
);

-- Таблица ордеров
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY, -- UUID as TEXT
    deal_id TEXT REFERENCES deals(deal_id),
    symbol TEXT NOT NULL REFERENCES currency_pairs(symbol),
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type TEXT NOT NULL CHECK (order_type IN (
        'LIMIT', 'MARKET', 'STOP_LOSS', 'TAKE_PROFIT'
    )),
    amount REAL NOT NULL,
    price REAL,
    filled_amount REAL DEFAULT 0,
    remaining_amount REAL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'OPEN', 'PARTIALLY_FILLED', 'FILLED', 
        'CANCELLED', 'REJECTED', 'EXPIRED', 'FAILED', 
        'NOT_FOUND_ON_EXCHANGE'
    )),
    exchange_id TEXT,
    client_order_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    placed_at DATETIME,
    closed_at DATETIME,
    exchange_timestamp INTEGER, -- BIGINT as INTEGER
    retries INTEGER DEFAULT 0,
    error_message TEXT,
    fees REAL DEFAULT 0,
    commission_asset TEXT,
    metadata TEXT DEFAULT '{}' -- JSON as TEXT
);

-- Таблица потоковых данных (тикеры и стаканы)
CREATE TABLE stream_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL REFERENCES currency_pairs(symbol),
    data_type TEXT NOT NULL CHECK (data_type IN ('ticker', 'orderbook')),
    data TEXT NOT NULL, -- JSON as TEXT
    timestamp INTEGER NOT NULL, -- BIGINT as INTEGER
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Таблица индикаторов
CREATE TABLE indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL REFERENCES currency_pairs(symbol),
    indicator_type TEXT NOT NULL CHECK (indicator_type IN (
        'sma', 'ema', 'rsi', 'macd', 'macd_signal', 'macd_histogram',
        'bollinger_upper', 'bollinger_middle', 'bollinger_lower',
        'volume', 'volatility'
    )),
    value REAL NOT NULL,
    period INTEGER,
    level TEXT NOT NULL DEFAULT 'fast' CHECK (level IN ('fast', 'medium', 'heavy')),
    timestamp INTEGER NOT NULL, -- BIGINT as INTEGER
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}' -- JSON as TEXT
);

-- Таблица торговых сигналов
CREATE TABLE trading_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id TEXT NOT NULL UNIQUE,
    symbol TEXT NOT NULL REFERENCES currency_pairs(symbol),
    signal_type TEXT NOT NULL CHECK (signal_type IN (
        'buy', 'sell', 'hold', 'strong_buy', 'strong_sell', 'weak_buy', 'weak_sell'
    )),
    source TEXT NOT NULL CHECK (source IN (
        'macd', 'rsi', 'sma_crossover', 'bollinger_bands', 
        'orderbook_analysis', 'volume_analysis', 'combined'
    )),
    strength REAL NOT NULL CHECK (strength >= 0 AND strength <= 1),
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    price REAL,
    timestamp INTEGER NOT NULL, -- BIGINT as INTEGER
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}' -- JSON as TEXT
);

-- Таблица стаканов заявок
CREATE TABLE order_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL REFERENCES currency_pairs(symbol),
    timestamp INTEGER NOT NULL, -- BIGINT as INTEGER
    bids TEXT NOT NULL, -- JSON as TEXT
    asks TEXT NOT NULL, -- JSON as TEXT
    spread REAL,
    spread_percent REAL,
    volume_imbalance REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Таблица статистики
CREATE TABLE statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id TEXT NOT NULL UNIQUE,
    metric_name TEXT NOT NULL,
    value TEXT NOT NULL, -- Может быть число или строка
    category TEXT NOT NULL CHECK (category IN (
        'trading', 'performance', 'orders', 'deals', 'market_data',
        'risk_management', 'system', 'technical_indicators', 'order_book'
    )),
    metric_type TEXT NOT NULL DEFAULT 'gauge' CHECK (metric_type IN (
        'counter', 'gauge', 'histogram', 'timing', 'rate', 'percentage'
    )),
    symbol TEXT,
    timestamp INTEGER NOT NULL, -- BIGINT as INTEGER
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    tags TEXT DEFAULT '{}', -- JSON as TEXT
    description TEXT
);

-- Таблица конфигурации
CREATE TABLE configuration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'trading', 'risk_management', 'technical_indicators', 'order_book',
        'exchange', 'system', 'notifications', 'logging', 'performance'
    )),
    value TEXT NOT NULL,
    config_type TEXT NOT NULL DEFAULT 'string' CHECK (config_type IN (
        'string', 'integer', 'float', 'boolean', 'json', 'list', 'dict'
    )),
    description TEXT,
    is_secret INTEGER DEFAULT 0, -- BOOLEAN as INTEGER
    is_required INTEGER DEFAULT 0, -- BOOLEAN as INTEGER
    default_value TEXT,
    validation_rules TEXT DEFAULT '{}', -- JSON as TEXT
    tags TEXT DEFAULT '[]', -- JSON array as TEXT
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(key, category)
);

-- Таблица кэша
CREATE TABLE cache_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL, -- JSON as TEXT
    ttl_seconds INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

-- =================================================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =================================================================

-- Индексы для deals
CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_deals_currency_pair ON deals(currency_pair_symbol);
CREATE INDEX idx_deals_created_at ON deals(created_at);

-- Индексы для orders
CREATE INDEX idx_orders_deal_id ON orders(deal_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_side ON orders(side);
CREATE INDEX idx_orders_exchange_id ON orders(exchange_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_symbol_status ON orders(symbol, status);

-- Индексы для stream_data
CREATE INDEX idx_stream_data_symbol ON stream_data(symbol);
CREATE INDEX idx_stream_data_type ON stream_data(data_type);
CREATE INDEX idx_stream_data_timestamp ON stream_data(timestamp);
CREATE INDEX idx_stream_data_symbol_type_timestamp ON stream_data(symbol, data_type, timestamp);

-- Индексы для indicators
CREATE INDEX idx_indicators_symbol ON indicators(symbol);
CREATE INDEX idx_indicators_type ON indicators(indicator_type);
CREATE INDEX idx_indicators_level ON indicators(level);
CREATE INDEX idx_indicators_timestamp ON indicators(timestamp);
CREATE INDEX idx_indicators_symbol_type_period ON indicators(symbol, indicator_type, period);

-- Индексы для trading_signals
CREATE INDEX idx_signals_symbol ON trading_signals(symbol);
CREATE INDEX idx_signals_type ON trading_signals(signal_type);
CREATE INDEX idx_signals_source ON trading_signals(source);
CREATE INDEX idx_signals_timestamp ON trading_signals(timestamp);
CREATE INDEX idx_signals_symbol_timestamp ON trading_signals(symbol, timestamp);

-- Индексы для order_books
CREATE INDEX idx_orderbooks_symbol ON order_books(symbol);
CREATE INDEX idx_orderbooks_timestamp ON order_books(timestamp);
CREATE INDEX idx_orderbooks_symbol_timestamp ON order_books(symbol, timestamp);

-- Индексы для statistics
CREATE INDEX idx_statistics_metric_name ON statistics(metric_name);
CREATE INDEX idx_statistics_category ON statistics(category);
CREATE INDEX idx_statistics_symbol ON statistics(symbol);
CREATE INDEX idx_statistics_timestamp ON statistics(timestamp);
CREATE INDEX idx_statistics_metric_category ON statistics(metric_name, category);

-- Индексы для configuration
CREATE INDEX idx_config_category ON configuration(category);
CREATE INDEX idx_config_key_category ON configuration(key, category);

-- Индексы для cache
CREATE INDEX idx_cache_expires_at ON cache_entries(expires_at);

-- =================================================================
-- ТРИГГЕРЫ ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ
-- =================================================================

-- Триггер для обновления updated_at в currency_pairs
CREATE TRIGGER update_currency_pairs_updated_at 
    AFTER UPDATE ON currency_pairs
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE currency_pairs SET updated_at = CURRENT_TIMESTAMP WHERE symbol = NEW.symbol;
END;

-- Триггер для обновления updated_at в orders
CREATE TRIGGER update_orders_updated_at 
    AFTER UPDATE ON orders
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE orders SET updated_at = CURRENT_TIMESTAMP WHERE order_id = NEW.order_id;
END;

-- Триггер для обновления updated_at в configuration
CREATE TRIGGER update_configuration_updated_at 
    AFTER UPDATE ON configuration
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE configuration SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- =================================================================
-- ПРЕДСТАВЛЕНИЯ ДЛЯ УДОБСТВА ЗАПРОСОВ
-- =================================================================

-- Представление активных сделок с информацией об ордерах
CREATE VIEW active_deals_view AS
SELECT 
    d.deal_id,
    d.currency_pair_symbol,
    d.status,
    d.target_profit_percent,
    d.created_at,
    bo.order_id as buy_order_id,
    bo.amount as buy_amount,
    bo.price as buy_price,
    bo.status as buy_status,
    so.order_id as sell_order_id,
    so.amount as sell_amount,
    so.price as sell_price,
    so.status as sell_status
FROM deals d
LEFT JOIN orders bo ON d.buy_order_id = bo.order_id
LEFT JOIN orders so ON d.sell_order_id = so.order_id
WHERE d.status IN ('ACTIVE', 'WAITING_SELL');

-- Представление открытых ордеров
CREATE VIEW open_orders_view AS
SELECT 
    o.*,
    d.currency_pair_symbol,
    d.status as deal_status
FROM orders o
LEFT JOIN deals d ON o.deal_id = d.deal_id
WHERE o.status IN ('PENDING', 'OPEN', 'PARTIALLY_FILLED');

-- =================================================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- =================================================================

-- Вставляем базовую конфигурацию
INSERT INTO configuration (key, category, value, config_type, description, is_required) VALUES
('default_profit_percent', 'trading', '1.5', 'float', 'Процент прибыли по умолчанию', 1),
('max_open_deals', 'trading', '5', 'integer', 'Максимальное количество открытых сделок', 1),
('order_timeout_minutes', 'trading', '60', 'integer', 'Таймаут ордера в минутах', 1),
('stop_loss_percent', 'risk_management', '5.0', 'float', 'Процент стоп-лосса', 1),
('max_daily_loss_percent', 'risk_management', '10.0', 'float', 'Максимальная дневная потеря в %', 1),
('indicator_update_interval_fast', 'technical_indicators', '1', 'integer', 'Интервал обновления быстрых индикаторов (тики)', 1),
('indicator_update_interval_medium', 'technical_indicators', '10', 'integer', 'Интервал обновления средних индикаторов (тики)', 1),
('indicator_update_interval_heavy', 'technical_indicators', '50', 'integer', 'Интервал обновления тяжелых индикаторов (тики)', 1),
('orderbook_analysis_enabled', 'order_book', 'true', 'boolean', 'Включить анализ стакана заявок', 1),
('min_spread_percent', 'order_book', '0.1', 'float', 'Минимальный спред в процентах', 1),
('log_level', 'system', 'INFO', 'string', 'Уровень логирования', 1),
('cache_ttl_seconds', 'performance', '300', 'integer', 'TTL кэша в секундах', 1);

-- =================================================================
-- ФУНКЦИИ-ЗАМЕНИТЕЛИ ДЛЯ ОЧИСТКИ (простые DELETE запросы)
-- =================================================================

-- В SQLite нет хранимых процедур, поэтому создаем комментарии с примерами запросов

/*
-- Пример очистки старых потоковых данных (за последние 7 дней)
DELETE FROM stream_data 
WHERE created_at < datetime('now', '-7 days');

-- Пример очистки старых индикаторов (за последние 30 дней)
DELETE FROM indicators 
WHERE created_at < datetime('now', '-30 days');

-- Пример очистки старых торговых сигналов (за последние 14 дней)
DELETE FROM trading_signals 
WHERE created_at < datetime('now', '-14 days');

-- Пример очистки просроченного кэша
DELETE FROM cache_entries 
WHERE expires_at IS NOT NULL AND expires_at < datetime('now');

-- Пример получения последних индикаторов по символам
SELECT * FROM (
    SELECT symbol, indicator_type, value, period, level, timestamp, created_at,
           ROW_NUMBER() OVER (PARTITION BY symbol, indicator_type, period ORDER BY timestamp DESC) as rn
    FROM indicators
) WHERE rn = 1;
*/