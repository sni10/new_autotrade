-- AutoTrade v2.4.0 PostgreSQL Database Schema
-- Полная схема для миграции с JSON на реляционную СУБД

-- =================================================================
-- EXTENSIONS
-- =================================================================

-- Включаем UUID-расширение для генерации уникальных идентификаторов
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Включаем расширение для работы с JSON
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Для текстового поиска

-- =================================================================
-- ENUM TYPES
-- =================================================================

-- Типы ордеров
CREATE TYPE order_type AS ENUM ('LIMIT', 'MARKET', 'STOP_LOSS', 'TAKE_PROFIT');

-- Стороны ордеров
CREATE TYPE order_side AS ENUM ('BUY', 'SELL');

-- Статусы ордеров
CREATE TYPE order_status AS ENUM (
    'PENDING', 'OPEN', 'PARTIALLY_FILLED', 'FILLED', 
    'CANCELLED', 'REJECTED', 'EXPIRED', 'FAILED', 
    'NOT_FOUND_ON_EXCHANGE'
);

-- Статусы сделок
CREATE TYPE deal_status AS ENUM (
    'ACTIVE', 'WAITING_SELL', 'COMPLETED', 'CANCELLED', 'FAILED'
);

-- Типы индикаторов
CREATE TYPE indicator_type AS ENUM (
    'sma', 'ema', 'rsi', 'macd', 'macd_signal', 'macd_histogram',
    'bollinger_upper', 'bollinger_middle', 'bollinger_lower',
    'volume', 'volatility'
);

-- Уровни сложности индикаторов
CREATE TYPE indicator_level AS ENUM ('fast', 'medium', 'heavy');

-- Типы торговых сигналов
CREATE TYPE signal_type AS ENUM (
    'buy', 'sell', 'hold', 'strong_buy', 'strong_sell', 'weak_buy', 'weak_sell'
);

-- Источники сигналов
CREATE TYPE signal_source AS ENUM (
    'macd', 'rsi', 'sma_crossover', 'bollinger_bands', 
    'orderbook_analysis', 'volume_analysis', 'combined'
);

-- Категории статистики
CREATE TYPE statistic_category AS ENUM (
    'trading', 'performance', 'orders', 'deals', 'market_data',
    'risk_management', 'system', 'technical_indicators', 'order_book'
);

-- Типы статистических метрик
CREATE TYPE statistic_type AS ENUM (
    'counter', 'gauge', 'histogram', 'timing', 'rate', 'percentage'
);

-- Категории конфигурации
CREATE TYPE config_category AS ENUM (
    'trading', 'risk_management', 'technical_indicators', 'order_book',
    'exchange', 'system', 'notifications', 'logging', 'performance'
);

-- Типы конфигурационных значений
CREATE TYPE config_type AS ENUM (
    'string', 'integer', 'float', 'boolean', 'json', 'list', 'dict'
);

-- =================================================================
-- ОСНОВНЫЕ ТАБЛИЦЫ
-- =================================================================

-- Таблица валютных пар
CREATE TABLE currency_pairs (
    symbol VARCHAR(20) PRIMARY KEY,
    base_currency VARCHAR(10) NOT NULL,
    quote_currency VARCHAR(10) NOT NULL,
    precision_data JSONB NOT NULL DEFAULT '{}',
    limits_data JSONB NOT NULL DEFAULT '{}',
    maker_fee DECIMAL(10, 8) DEFAULT 0.001,
    taker_fee DECIMAL(10, 8) DEFAULT 0.001,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сделок
CREATE TABLE deals (
    deal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    currency_pair_symbol VARCHAR(20) NOT NULL REFERENCES currency_pairs(symbol),
    status deal_status NOT NULL DEFAULT 'ACTIVE',
    buy_order_id UUID,
    sell_order_id UUID,
    target_profit_percent DECIMAL(5, 4),
    actual_profit DECIMAL(15, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Таблица ордеров
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID REFERENCES deals(deal_id),
    symbol VARCHAR(20) NOT NULL REFERENCES currency_pairs(symbol),
    side order_side NOT NULL,
    order_type order_type NOT NULL,
    amount DECIMAL(18, 8) NOT NULL,
    price DECIMAL(18, 8),
    filled_amount DECIMAL(18, 8) DEFAULT 0,
    remaining_amount DECIMAL(18, 8),
    status order_status NOT NULL DEFAULT 'PENDING',
    exchange_id VARCHAR(100),
    client_order_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    placed_at TIMESTAMP,
    closed_at TIMESTAMP,
    exchange_timestamp BIGINT,
    retries INTEGER DEFAULT 0,
    error_message TEXT,
    fees DECIMAL(18, 8) DEFAULT 0,
    commission_asset VARCHAR(10),
    metadata JSONB DEFAULT '{}'
);

-- Таблица потоковых данных (тикеры и стаканы)
CREATE TABLE stream_data (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES currency_pairs(symbol),
    data_type VARCHAR(20) NOT NULL, -- 'ticker' или 'orderbook'
    data JSONB NOT NULL,
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица индикаторов
CREATE TABLE indicators (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES currency_pairs(symbol),
    indicator_type indicator_type NOT NULL,
    value DECIMAL(18, 8) NOT NULL,
    period INTEGER,
    level indicator_level NOT NULL DEFAULT 'fast',
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Таблица торговых сигналов
CREATE TABLE trading_signals (
    id BIGSERIAL PRIMARY KEY,
    signal_id VARCHAR(200) NOT NULL UNIQUE,
    symbol VARCHAR(20) NOT NULL REFERENCES currency_pairs(symbol),
    signal_type signal_type NOT NULL,
    source signal_source NOT NULL,
    strength DECIMAL(5, 4) NOT NULL CHECK (strength >= 0 AND strength <= 1),
    confidence DECIMAL(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    price DECIMAL(18, 8),
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Таблица стаканов заявок
CREATE TABLE order_books (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES currency_pairs(symbol),
    timestamp BIGINT NOT NULL,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    spread DECIMAL(18, 8),
    spread_percent DECIMAL(8, 4),
    volume_imbalance DECIMAL(8, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица статистики
CREATE TABLE statistics (
    id BIGSERIAL PRIMARY KEY,
    metric_id VARCHAR(300) NOT NULL UNIQUE,
    metric_name VARCHAR(100) NOT NULL,
    value TEXT NOT NULL, -- Может быть число или строка
    category statistic_category NOT NULL,
    metric_type statistic_type NOT NULL DEFAULT 'gauge',
    symbol VARCHAR(20),
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSONB DEFAULT '{}',
    description TEXT
);

-- Таблица конфигурации
CREATE TABLE configuration (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL,
    category config_category NOT NULL,
    value TEXT NOT NULL,
    config_type config_type NOT NULL DEFAULT 'string',
    description TEXT,
    is_secret BOOLEAN DEFAULT false,
    is_required BOOLEAN DEFAULT false,
    default_value TEXT,
    validation_rules JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(key, category)
);

-- Таблица кэша
CREATE TABLE cache_entries (
    id BIGSERIAL PRIMARY KEY,
    cache_key VARCHAR(300) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    ttl_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
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
-- ВНЕШНИЕ КЛЮЧИ
-- =================================================================

-- Добавляем внешние ключи для deals
ALTER TABLE deals 
ADD CONSTRAINT fk_deals_buy_order 
FOREIGN KEY (buy_order_id) REFERENCES orders(order_id) ON DELETE SET NULL;

ALTER TABLE deals 
ADD CONSTRAINT fk_deals_sell_order 
FOREIGN KEY (sell_order_id) REFERENCES orders(order_id) ON DELETE SET NULL;

-- =================================================================
-- ТРИГГЕРЫ ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ
-- =================================================================

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_currency_pairs_updated_at 
    BEFORE UPDATE ON currency_pairs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at 
    BEFORE UPDATE ON orders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configuration_updated_at 
    BEFORE UPDATE ON configuration 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =================================================================
-- ФУНКЦИИ ДЛЯ ОЧИСТКИ СТАРЫХ ДАННЫХ
-- =================================================================

-- Функция для очистки старых потоковых данных
CREATE OR REPLACE FUNCTION cleanup_old_stream_data(days_to_keep INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM stream_data 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Функция для очистки старых индикаторов
CREATE OR REPLACE FUNCTION cleanup_old_indicators(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM indicators 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Функция для очистки старых торговых сигналов
CREATE OR REPLACE FUNCTION cleanup_old_trading_signals(days_to_keep INTEGER DEFAULT 14)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM trading_signals 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Функция для очистки просроченного кэша
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM cache_entries 
    WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

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

-- Представление последних индикаторов по символам
CREATE VIEW latest_indicators_view AS
SELECT DISTINCT ON (symbol, indicator_type, period)
    symbol,
    indicator_type,
    value,
    period,
    level,
    timestamp,
    created_at
FROM indicators
ORDER BY symbol, indicator_type, period, timestamp DESC;

-- =================================================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- =================================================================

-- Вставляем базовую конфигурацию
INSERT INTO configuration (key, category, value, config_type, description, is_required) VALUES
('default_profit_percent', 'trading', '1.5', 'float', 'Процент прибыли по умолчанию', true),
('max_open_deals', 'trading', '5', 'integer', 'Максимальное количество открытых сделок', true),
('order_timeout_minutes', 'trading', '60', 'integer', 'Таймаут ордера в минутах', true),
('stop_loss_percent', 'risk_management', '5.0', 'float', 'Процент стоп-лосса', true),
('max_daily_loss_percent', 'risk_management', '10.0', 'float', 'Максимальная дневная потеря в %', true),
('indicator_update_interval_fast', 'technical_indicators', '1', 'integer', 'Интервал обновления быстрых индикаторов (тики)', true),
('indicator_update_interval_medium', 'technical_indicators', '10', 'integer', 'Интервал обновления средних индикаторов (тики)', true),
('indicator_update_interval_heavy', 'technical_indicators', '50', 'integer', 'Интервал обновления тяжелых индикаторов (тики)', true),
('orderbook_analysis_enabled', 'order_book', 'true', 'boolean', 'Включить анализ стакана заявок', true),
('min_spread_percent', 'order_book', '0.1', 'float', 'Минимальный спред в процентах', true),
('log_level', 'system', 'INFO', 'string', 'Уровень логирования', true),
('cache_ttl_seconds', 'performance', '300', 'integer', 'TTL кэша в секундах', true);

-- Комментарии к таблицам
COMMENT ON TABLE currency_pairs IS 'Торговые пары и их параметры';
COMMENT ON TABLE deals IS 'Торговые сделки';
COMMENT ON TABLE orders IS 'Ордера на покупку и продажу';
COMMENT ON TABLE stream_data IS 'Потоковые данные (тикеры и стаканы заявок)';
COMMENT ON TABLE indicators IS 'Технические индикаторы';
COMMENT ON TABLE trading_signals IS 'Торговые сигналы';
COMMENT ON TABLE order_books IS 'Снимки стаканов заявок';
COMMENT ON TABLE statistics IS 'Метрики производительности и статистика';
COMMENT ON TABLE configuration IS 'Динамическая конфигурация системы';
COMMENT ON TABLE cache_entries IS 'Кэш для быстрого доступа к данным';