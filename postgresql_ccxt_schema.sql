-- AutoTrade v2.4.0 CCXT COMPLIANT PostgreSQL Database Schema
-- Полная совместимость с CCXT структурами данных
-- Дата создания: 2025-01-27

-- =================================================================
-- EXTENSIONS
-- =================================================================

-- Включаем UUID-расширение для генерации уникальных идентификаторов
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Включаем расширение для работы с JSON
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Для текстового поиска

-- Включаем hstore для ключ-значение хранения
CREATE EXTENSION IF NOT EXISTS "hstore";

-- =================================================================
-- CCXT COMPLIANT ENUM TYPES
-- =================================================================

-- CCXT Order Status (точно по стандарту)
CREATE TYPE ccxt_order_status AS ENUM (
    'open',           -- Ордер размещен и ожидает исполнения
    'closed',         -- Ордер полностью исполнен
    'canceled',       -- Ордер отменен
    'expired',        -- Ордер истек
    'rejected',       -- Ордер отклонен биржей
    'pending'         -- Локальный статус: создан, но не размещен на бирже
);

-- CCXT Order Side (точно по стандарту)
CREATE TYPE ccxt_order_side AS ENUM ('buy', 'sell');

-- CCXT Order Type (точно по стандарту)
CREATE TYPE ccxt_order_type AS ENUM (
    'limit',              -- Лимитный ордер
    'market',             -- Рыночный ордер
    'stop',               -- Стоп ордер
    'stop_limit',         -- Стоп-лимит ордер
    'take_profit',        -- Тейк-профит ордер
    'take_profit_limit'   -- Тейк-профит лимит ордер
);

-- CCXT Time In Force (точно по стандарту)
CREATE TYPE ccxt_time_in_force AS ENUM (
    'GTC',  -- Good Till Canceled
    'IOC',  -- Immediate Or Cancel
    'FOK',  -- Fill Or Kill
    'PO'    -- Post Only
);

-- CCXT Market Type
CREATE TYPE ccxt_market_type AS ENUM (
    'spot',     -- Спотовый рынок
    'margin',   -- Маржинальный рынок
    'future',   -- Фьючерсный рынок
    'swap',     -- Своп рынок
    'option'    -- Опционный рынок
);

-- Deal Status (для AutoTrade)
CREATE TYPE deal_status AS ENUM (
    'active',         -- Сделка активна
    'waiting_sell',   -- Ожидает исполнения SELL ордера
    'completed',      -- Сделка завершена
    'canceled',       -- Сделка отменена
    'failed'          -- Сделка не удалась
);

-- Типы индикаторов
CREATE TYPE indicator_type AS ENUM (
    'sma', 'ema', 'rsi', 'macd', 'macd_signal', 'macd_histogram',
    'bollinger_upper', 'bollinger_middle', 'bollinger_lower',
    'volume', 'volatility', 'stoch_k', 'stoch_d', 'williams_r'
);

-- Типы торговых сигналов
CREATE TYPE signal_type AS ENUM (
    'buy', 'sell', 'hold', 'strong_buy', 'strong_sell', 'weak_buy', 'weak_sell'
);

-- Источники сигналов
CREATE TYPE signal_source AS ENUM (
    'macd', 'rsi', 'sma_crossover', 'bollinger_bands', 
    'orderbook_analysis', 'volume_analysis', 'combined'
);

-- =================================================================
-- CCXT COMPLIANT MAIN TABLES
-- =================================================================

-- CCXT Markets Table (Торговые пары)
CREATE TABLE ccxt_markets (
    id VARCHAR(50) PRIMARY KEY,                 -- биржевой идентификатор (BTCUSDT)
    symbol VARCHAR(50) NOT NULL UNIQUE,         -- стандартизированный символ (BTC/USDT)
    base VARCHAR(20) NOT NULL,                  -- базовая валюта (BTC)
    quote VARCHAR(20) NOT NULL,                 -- котируемая валюта (USDT)
    base_id VARCHAR(50),                        -- ID базовой валюты на бирже
    quote_id VARCHAR(50),                       -- ID котируемой валюты на бирже
    active BOOLEAN DEFAULT true,                -- активность торговой пары
    type ccxt_market_type DEFAULT 'spot',       -- тип рынка
    spot BOOLEAN DEFAULT true,                  -- доступность спот торговли
    margin BOOLEAN DEFAULT false,               -- доступность маржинальной торговли
    future BOOLEAN DEFAULT false,               -- доступность фьючерсной торговли
    swap BOOLEAN DEFAULT false,                 -- доступность своп торговли
    option BOOLEAN DEFAULT false,               -- доступность опционной торговли
    contract BOOLEAN DEFAULT false,             -- контрактная торговля
    
    -- CCXT Precision (точность)
    precision JSONB NOT NULL DEFAULT '{}',     -- {"amount": 8, "price": 2, "cost": 8}
    
    -- CCXT Limits (лимиты)
    limits JSONB NOT NULL DEFAULT '{}',        -- {"amount": {"min": 0.00001, "max": 1000}, ...}
    
    -- CCXT Fees (комиссии)
    maker DECIMAL(10, 8) DEFAULT 0.001,        -- комиссия мейкера
    taker DECIMAL(10, 8) DEFAULT 0.001,        -- комиссия тейкера
    
    -- CCXT Info (полная информация от биржи)
    info JSONB DEFAULT '{}',                   -- полный ответ от биржи
    
    -- AutoTrade поля
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CCXT Orders Table (ПОЛНАЯ СОВМЕСТИМОСТЬ)
CREATE TABLE ccxt_orders (
    -- CCXT СТАНДАРТНЫЕ ПОЛЯ
    id VARCHAR(100) PRIMARY KEY,                   -- exchange order ID (строка!)
    client_order_id VARCHAR(100),                  -- клиентский ID ордера
    datetime TIMESTAMP WITH TIME ZONE,             -- ISO8601 datetime
    timestamp BIGINT,                              -- Unix timestamp в миллисекундах
    last_trade_timestamp BIGINT,                   -- время последней сделки
    status ccxt_order_status NOT NULL,             -- статус ордера
    symbol VARCHAR(50) NOT NULL,                   -- торговая пара (BTC/USDT)
    type ccxt_order_type NOT NULL,                 -- тип ордера
    time_in_force ccxt_time_in_force,              -- время жизни ордера
    side ccxt_order_side NOT NULL,                 -- сторона ордера
    price DECIMAL(20, 8),                          -- цена за единицу
    amount DECIMAL(20, 8) NOT NULL,                -- запрошенное количество
    filled DECIMAL(20, 8) DEFAULT 0,               -- исполненное количество
    remaining DECIMAL(20, 8),                      -- оставшееся количество
    cost DECIMAL(20, 8),                           -- общая стоимость (filled * average)
    average DECIMAL(20, 8),                        -- средняя цена исполнения
    
    -- CCXT Сложные поля (JSON)
    trades JSONB DEFAULT '[]',                     -- массив сделок
    fee JSONB DEFAULT '{}',                        -- структура комиссии
    info JSONB DEFAULT '{}',                       -- полный ответ от биржи
    
    -- AUTOTRADE ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ
    deal_id UUID,                                  -- связь со сделкой AutoTrade
    local_order_id SERIAL,                         -- внутренний AutoTrade ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- время создания в AutoTrade
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- время последнего обновления
    error_message TEXT,                            -- сообщение об ошибке
    retries INTEGER DEFAULT 0,                     -- количество попыток
    metadata JSONB DEFAULT '{}',                   -- дополнительная информация проекта
    
    -- CONSTRAINTS
    CONSTRAINT unique_exchange_order_id UNIQUE (id),
    CONSTRAINT positive_amount CHECK (amount > 0),
    CONSTRAINT valid_filled CHECK (filled >= 0 AND filled <= amount),
    CONSTRAINT valid_remaining CHECK (remaining >= 0),
    CONSTRAINT valid_cost CHECK (cost IS NULL OR cost >= 0),
    CONSTRAINT valid_average CHECK (average IS NULL OR average > 0)
);

-- Deals Table (AutoTrade сделки)
CREATE TABLE deals (
    deal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL,                   -- ссылка на ccxt_markets.symbol
    status deal_status NOT NULL DEFAULT 'active',
    buy_order_id VARCHAR(100),                     -- ссылка на ccxt_orders.id
    sell_order_id VARCHAR(100),                    -- ссылка на ccxt_orders.id
    target_profit_percent DECIMAL(8, 4),
    actual_profit DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- CCXT Tickers Table (потоковые данные тикеров)
CREATE TABLE ccxt_tickers (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,                   -- BTC/USDT
    timestamp BIGINT NOT NULL,                     -- Unix timestamp
    datetime TIMESTAMP WITH TIME ZONE,             -- ISO8601 datetime
    high DECIMAL(20, 8),                          -- максимальная цена за 24ч
    low DECIMAL(20, 8),                           -- минимальная цена за 24ч
    bid DECIMAL(20, 8),                           -- лучшая цена покупки
    bid_volume DECIMAL(20, 8),                    -- объем по лучшей цене покупки
    ask DECIMAL(20, 8),                           -- лучшая цена продажи
    ask_volume DECIMAL(20, 8),                    -- объем по лучшей цене продажи
    vwap DECIMAL(20, 8),                          -- средневзвешенная цена
    open DECIMAL(20, 8),                          -- цена открытия
    close DECIMAL(20, 8),                         -- цена закрытия (последняя)
    last DECIMAL(20, 8),                          -- последняя цена
    previous_close DECIMAL(20, 8),                -- предыдущая цена закрытия
    change DECIMAL(20, 8),                        -- изменение цены
    percentage DECIMAL(8, 4),                     -- процентное изменение
    average DECIMAL(20, 8),                       -- средняя цена
    base_volume DECIMAL(20, 8),                   -- объем в базовой валюте
    quote_volume DECIMAL(20, 8),                  -- объем в котируемой валюте
    info JSONB DEFAULT '{}',                      -- полный ответ от биржи
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CCXT Order Books Table (стаканы заявок)
CREATE TABLE ccxt_order_books (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,                   -- BTC/USDT
    timestamp BIGINT NOT NULL,                     -- Unix timestamp
    datetime TIMESTAMP WITH TIME ZONE,             -- ISO8601 datetime
    nonce BIGINT,                                  -- номер обновления стакана
    bids JSONB NOT NULL DEFAULT '[]',              -- массив заявок на покупку [[price, amount], ...]
    asks JSONB NOT NULL DEFAULT '[]',              -- массив заявок на продажу [[price, amount], ...]
    
    -- Расчетные поля для анализа
    spread DECIMAL(20, 8),                         -- спред (ask - bid)
    spread_percent DECIMAL(8, 4),                  -- спред в процентах
    bid_volume DECIMAL(20, 8),                     -- общий объем заявок на покупку
    ask_volume DECIMAL(20, 8),                     -- общий объем заявок на продажу
    volume_imbalance DECIMAL(8, 4),                -- дисбаланс объемов
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Technical Indicators Table
CREATE TABLE technical_indicators (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    indicator_type indicator_type NOT NULL,
    value DECIMAL(20, 8) NOT NULL,
    period INTEGER,
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Trading Signals Table
CREATE TABLE trading_signals (
    id BIGSERIAL PRIMARY KEY,
    signal_id VARCHAR(200) NOT NULL UNIQUE,
    symbol VARCHAR(50) NOT NULL,
    signal_type signal_type NOT NULL,
    source signal_source NOT NULL,
    strength DECIMAL(5, 4) NOT NULL CHECK (strength >= 0 AND strength <= 1),
    confidence DECIMAL(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    price DECIMAL(20, 8),
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Statistics Table
CREATE TABLE statistics (
    id BIGSERIAL PRIMARY KEY,
    metric_id VARCHAR(300) NOT NULL UNIQUE,
    metric_name VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    symbol VARCHAR(50),
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSONB DEFAULT '{}',
    description TEXT
);

-- Configuration Table
CREATE TABLE configuration (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    config_type VARCHAR(20) NOT NULL DEFAULT 'string',
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

-- Cache Table
CREATE TABLE cache_entries (
    id BIGSERIAL PRIMARY KEY,
    cache_key VARCHAR(300) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    ttl_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- =================================================================
-- FOREIGN KEY CONSTRAINTS
-- =================================================================

-- Foreign keys для deals
ALTER TABLE deals 
ADD CONSTRAINT fk_deals_symbol 
FOREIGN KEY (symbol) REFERENCES ccxt_markets(symbol);

ALTER TABLE deals 
ADD CONSTRAINT fk_deals_buy_order 
FOREIGN KEY (buy_order_id) REFERENCES ccxt_orders(id) ON DELETE SET NULL;

ALTER TABLE deals 
ADD CONSTRAINT fk_deals_sell_order 
FOREIGN KEY (sell_order_id) REFERENCES ccxt_orders(id) ON DELETE SET NULL;

-- Foreign keys для ccxt_orders
ALTER TABLE ccxt_orders 
ADD CONSTRAINT fk_orders_symbol 
FOREIGN KEY (symbol) REFERENCES ccxt_markets(symbol);

ALTER TABLE ccxt_orders 
ADD CONSTRAINT fk_orders_deal 
FOREIGN KEY (deal_id) REFERENCES deals(deal_id) ON DELETE SET NULL;

-- Foreign keys для ccxt_tickers
ALTER TABLE ccxt_tickers 
ADD CONSTRAINT fk_tickers_symbol 
FOREIGN KEY (symbol) REFERENCES ccxt_markets(symbol);

-- Foreign keys для ccxt_order_books
ALTER TABLE ccxt_order_books 
ADD CONSTRAINT fk_orderbooks_symbol 
FOREIGN KEY (symbol) REFERENCES ccxt_markets(symbol);

-- Foreign keys для technical_indicators
ALTER TABLE technical_indicators 
ADD CONSTRAINT fk_indicators_symbol 
FOREIGN KEY (symbol) REFERENCES ccxt_markets(symbol);

-- Foreign keys для trading_signals
ALTER TABLE trading_signals 
ADD CONSTRAINT fk_signals_symbol 
FOREIGN KEY (symbol) REFERENCES ccxt_markets(symbol);

-- =================================================================
-- PERFORMANCE INDEXES
-- =================================================================

-- Индексы для ccxt_orders (КРИТИЧЕСКИ ВАЖНЫЕ)
CREATE INDEX idx_ccxt_orders_symbol ON ccxt_orders(symbol);
CREATE INDEX idx_ccxt_orders_status ON ccxt_orders(status);
CREATE INDEX idx_ccxt_orders_side ON ccxt_orders(side);
CREATE INDEX idx_ccxt_orders_type ON ccxt_orders(type);
CREATE INDEX idx_ccxt_orders_timestamp ON ccxt_orders(timestamp);
CREATE INDEX idx_ccxt_orders_deal_id ON ccxt_orders(deal_id);
CREATE INDEX idx_ccxt_orders_client_order_id ON ccxt_orders(client_order_id);
CREATE INDEX idx_ccxt_orders_symbol_status ON ccxt_orders(symbol, status);
CREATE INDEX idx_ccxt_orders_symbol_side ON ccxt_orders(symbol, side);
CREATE INDEX idx_ccxt_orders_status_timestamp ON ccxt_orders(status, timestamp);

-- Индексы для deals
CREATE INDEX idx_deals_symbol ON deals(symbol);
CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_deals_created_at ON deals(created_at);
CREATE INDEX idx_deals_buy_order_id ON deals(buy_order_id);
CREATE INDEX idx_deals_sell_order_id ON deals(sell_order_id);

-- Индексы для ccxt_markets
CREATE INDEX idx_ccxt_markets_base ON ccxt_markets(base);
CREATE INDEX idx_ccxt_markets_quote ON ccxt_markets(quote);
CREATE INDEX idx_ccxt_markets_active ON ccxt_markets(active);
CREATE INDEX idx_ccxt_markets_type ON ccxt_markets(type);

-- Индексы для ccxt_tickers
CREATE INDEX idx_ccxt_tickers_symbol ON ccxt_tickers(symbol);
CREATE INDEX idx_ccxt_tickers_timestamp ON ccxt_tickers(timestamp);
CREATE INDEX idx_ccxt_tickers_symbol_timestamp ON ccxt_tickers(symbol, timestamp);
CREATE INDEX idx_ccxt_tickers_created_at ON ccxt_tickers(created_at);

-- Индексы для ccxt_order_books
CREATE INDEX idx_ccxt_orderbooks_symbol ON ccxt_order_books(symbol);
CREATE INDEX idx_ccxt_orderbooks_timestamp ON ccxt_order_books(timestamp);
CREATE INDEX idx_ccxt_orderbooks_symbol_timestamp ON ccxt_order_books(symbol, timestamp);
CREATE INDEX idx_ccxt_orderbooks_nonce ON ccxt_order_books(nonce);

-- Индексы для technical_indicators
CREATE INDEX idx_indicators_symbol ON technical_indicators(symbol);
CREATE INDEX idx_indicators_type ON technical_indicators(indicator_type);
CREATE INDEX idx_indicators_timestamp ON technical_indicators(timestamp);
CREATE INDEX idx_indicators_symbol_type_period ON technical_indicators(symbol, indicator_type, period);

-- Индексы для trading_signals
CREATE INDEX idx_signals_symbol ON trading_signals(symbol);
CREATE INDEX idx_signals_type ON trading_signals(signal_type);
CREATE INDEX idx_signals_source ON trading_signals(source);
CREATE INDEX idx_signals_timestamp ON trading_signals(timestamp);
CREATE INDEX idx_signals_symbol_timestamp ON trading_signals(symbol, timestamp);

-- Индексы для statistics
CREATE INDEX idx_statistics_metric_name ON statistics(metric_name);
CREATE INDEX idx_statistics_category ON statistics(category);
CREATE INDEX idx_statistics_symbol ON statistics(symbol);
CREATE INDEX idx_statistics_timestamp ON statistics(timestamp);

-- Индексы для configuration
CREATE INDEX idx_config_category ON configuration(category);
CREATE INDEX idx_config_key_category ON configuration(key, category);

-- Индексы для cache
CREATE INDEX idx_cache_expires_at ON cache_entries(expires_at);
CREATE INDEX idx_cache_created_at ON cache_entries(created_at);

-- =================================================================
-- TRIGGERS FOR AUTO-UPDATE
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
CREATE TRIGGER update_ccxt_markets_updated_at 
    BEFORE UPDATE ON ccxt_markets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ccxt_orders_updated_at 
    BEFORE UPDATE ON ccxt_orders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configuration_updated_at 
    BEFORE UPDATE ON configuration 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Триггер для автоматического вычисления remaining
CREATE OR REPLACE FUNCTION update_order_remaining()
RETURNS TRIGGER AS $$
BEGIN
    -- Автоматически вычисляем remaining если не задано
    IF NEW.remaining IS NULL THEN
        NEW.remaining = NEW.amount - NEW.filled;
    END IF;
    
    -- Автоматически обновляем статус на основе filled
    IF NEW.filled >= NEW.amount THEN
        NEW.status = 'closed';
    ELSIF NEW.filled > 0 THEN
        NEW.status = 'partial';
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ccxt_orders_remaining 
    BEFORE INSERT OR UPDATE ON ccxt_orders 
    FOR EACH ROW EXECUTE FUNCTION update_order_remaining();

-- =================================================================
-- UTILITY FUNCTIONS
-- =================================================================

-- Функция для очистки старых тикеров
CREATE OR REPLACE FUNCTION cleanup_old_tickers(days_to_keep INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM ccxt_tickers 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Функция для очистки старых order books
CREATE OR REPLACE FUNCTION cleanup_old_order_books(hours_to_keep INTEGER DEFAULT 24)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM ccxt_order_books 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 hour' * hours_to_keep;
    
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
    DELETE FROM technical_indicators 
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

-- Функция для получения активных ордеров
CREATE OR REPLACE FUNCTION get_active_orders(p_symbol VARCHAR DEFAULT NULL)
RETURNS TABLE (
    order_id VARCHAR,
    symbol VARCHAR,
    side ccxt_order_side,
    type ccxt_order_type,
    status ccxt_order_status,
    amount DECIMAL,
    filled DECIMAL,
    remaining DECIMAL,
    price DECIMAL,
    deal_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.symbol,
        o.side,
        o.type,
        o.status,
        o.amount,
        o.filled,
        o.remaining,
        o.price,
        o.deal_id
    FROM ccxt_orders o
    WHERE o.status IN ('open', 'pending', 'partial')
    AND (p_symbol IS NULL OR o.symbol = p_symbol)
    ORDER BY o.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- VIEWS FOR CONVENIENCE
-- =================================================================

-- Представление активных сделок с полной информацией об ордерах
CREATE VIEW active_deals_view AS
SELECT 
    d.deal_id,
    d.symbol,
    d.status,
    d.target_profit_percent,
    d.created_at,
    
    -- Информация о BUY ордере
    bo.id as buy_order_id,
    bo.amount as buy_amount,
    bo.price as buy_price,
    bo.filled as buy_filled,
    bo.status as buy_status,
    bo.average as buy_average_price,
    bo.cost as buy_cost,
    
    -- Информация о SELL ордере
    so.id as sell_order_id,
    so.amount as sell_amount,
    so.price as sell_price,
    so.filled as sell_filled,
    so.status as sell_status,
    so.average as sell_average_price,
    so.cost as sell_cost,
    
    -- Расчетные поля
    CASE 
        WHEN bo.cost IS NOT NULL AND so.cost IS NOT NULL 
        THEN so.cost - bo.cost
        ELSE NULL
    END as current_profit
    
FROM deals d
LEFT JOIN ccxt_orders bo ON d.buy_order_id = bo.id
LEFT JOIN ccxt_orders so ON d.sell_order_id = so.id
WHERE d.status IN ('active', 'waiting_sell');

-- Представление открытых ордеров с информацией о сделках
CREATE VIEW open_orders_view AS
SELECT 
    o.id,
    o.client_order_id,
    o.symbol,
    o.side,
    o.type,
    o.status,
    o.amount,
    o.filled,
    o.remaining,
    o.price,
    o.average,
    o.cost,
    o.timestamp,
    o.created_at,
    o.deal_id,
    d.status as deal_status
FROM ccxt_orders o
LEFT JOIN deals d ON o.deal_id = d.deal_id
WHERE o.status IN ('open', 'pending', 'partial');

-- Представление последних тикеров
CREATE VIEW latest_tickers_view AS
SELECT DISTINCT ON (symbol)
    symbol,
    timestamp,
    datetime,
    last,
    bid,
    ask,
    high,
    low,
    base_volume,
    quote_volume,
    change,
    percentage,
    created_at
FROM ccxt_tickers
ORDER BY symbol, timestamp DESC;

-- Представление последних order books
CREATE VIEW latest_order_books_view AS
SELECT DISTINCT ON (symbol)
    symbol,
    timestamp,
    datetime,
    bids,
    asks,
    spread,
    spread_percent,
    bid_volume,
    ask_volume,
    volume_imbalance,
    created_at
FROM ccxt_order_books
ORDER BY symbol, timestamp DESC;

-- =================================================================
-- INITIAL DATA
-- =================================================================

-- Вставляем базовые торговые пары
INSERT INTO ccxt_markets (id, symbol, base, quote, base_id, quote_id, active, precision, limits, maker, taker) VALUES
('BTCUSDT', 'BTC/USDT', 'BTC', 'USDT', 'btc', 'usdt', true, 
 '{"amount": 8, "price": 2, "cost": 8}',
 '{"amount": {"min": 0.00001, "max": 1000}, "price": {"min": 0.01, "max": 1000000}, "cost": {"min": 10}}',
 0.001, 0.001),
('ETHUSDT', 'ETH/USDT', 'ETH', 'USDT', 'eth', 'usdt', true,
 '{"amount": 6, "price": 2, "cost": 8}',
 '{"amount": {"min": 0.0001, "max": 10000}, "price": {"min": 0.01, "max": 100000}, "cost": {"min": 10}}',
 0.001, 0.001);

-- Вставляем базовую конфигурацию
INSERT INTO configuration (key, category, value, config_type, description, is_required) VALUES
('default_profit_percent', 'trading', '1.5', 'float', 'Процент прибыли по умолчанию', true),
('max_open_deals', 'trading', '5', 'integer', 'Максимальное количество открытых сделок', true),
('order_timeout_minutes', 'trading', '60', 'integer', 'Таймаут ордера в минутах', true),
('stop_loss_percent', 'risk_management', '5.0', 'float', 'Процент стоп-лосса', true),
('max_daily_loss_percent', 'risk_management', '10.0', 'float', 'Максимальная дневная потеря в %', true),
('min_spread_percent', 'orderbook', '0.1', 'float', 'Минимальный спред в процентах', true),
('log_level', 'system', 'INFO', 'string', 'Уровень логирования', true),
('cache_ttl_seconds', 'performance', '300', 'integer', 'TTL кэша в секундах', true);

-- =================================================================
-- COMMENTS
-- =================================================================

COMMENT ON TABLE ccxt_markets IS 'CCXT совместимая таблица торговых пар';
COMMENT ON TABLE ccxt_orders IS 'CCXT совместимая таблица ордеров с полной поддержкой всех полей';
COMMENT ON TABLE deals IS 'AutoTrade сделки, связанные с CCXT ордерами';
COMMENT ON TABLE ccxt_tickers IS 'CCXT совместимая таблица тикеров';
COMMENT ON TABLE ccxt_order_books IS 'CCXT совместимая таблица стаканов заявок';
COMMENT ON TABLE technical_indicators IS 'Технические индикаторы';
COMMENT ON TABLE trading_signals IS 'Торговые сигналы';
COMMENT ON TABLE statistics IS 'Метрики производительности и статистика';
COMMENT ON TABLE configuration IS 'Динамическая конфигурация системы';
COMMENT ON TABLE cache_entries IS 'Кэш для быстрого доступа к данным';

-- =================================================================
-- SCHEMA VERSION
-- =================================================================

INSERT INTO configuration (key, category, value, config_type, description, is_required) VALUES
('schema_version', 'system', '2.4.0-ccxt', 'string', 'Версия схемы базы данных', true),
('schema_created_at', 'system', EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::TEXT, 'string', 'Время создания схемы', true),
('ccxt_compliance', 'system', 'true', 'boolean', 'Соответствие CCXT стандарту', true);

-- Финальный комментарий
COMMENT ON SCHEMA public IS 'AutoTrade v2.4.0 CCXT Compliant Database Schema - Полная совместимость с CCXT Unified API';