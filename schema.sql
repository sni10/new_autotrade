-- SQL схема для проекта AutoTrade

-- Таблица для хранения ордеров
CREATE TABLE IF NOT EXISTS orders (
    id BIGINT PRIMARY KEY,
    side VARCHAR(4) NOT NULL, -- 'BUY' или 'SELL'
    type VARCHAR(20) NOT NULL, -- 'LIMIT', 'MARKET', и т.д.
    price DECIMAL(20, 8) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    closed_at TIMESTAMP WITH TIME ZONE,
    deal_id BIGINT,
    exchange_id VARCHAR(255),
    symbol VARCHAR(20) NOT NULL,
    filled_amount DECIMAL(20, 8) DEFAULT 0.0,
    remaining_amount DECIMAL(20, 8) DEFAULT 0.0,
    average_price DECIMAL(20, 8) DEFAULT 0.0,
    fees DECIMAL(20, 8) DEFAULT 0.0,
    fee_currency VARCHAR(10),
    time_in_force VARCHAR(10),
    client_order_id VARCHAR(255),
    exchange_timestamp TIMESTAMP WITH TIME ZONE,
    last_update TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retries INT DEFAULT 0,
    metadata JSONB,
    exchange_raw_data JSONB
);

-- Таблица для хранения сделок
CREATE TABLE IF NOT EXISTS deals (
    id BIGINT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL,
    buy_order JSONB, -- Полные данные ордера на покупку
    sell_order JSONB, -- Полные данные ордера на продажу
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Индексы для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_orders_exchange_id ON orders (exchange_id);
CREATE INDEX IF NOT EXISTS idx_orders_deal_id ON orders (deal_id);
CREATE INDEX IF NOT EXISTS idx_orders_symbol_status ON orders (symbol, status);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals (status);

-- Комментарии к таблицам и столбцам для ясности
COMMENT ON TABLE orders IS 'Таблица для хранения всех ордеров, как активных, так и завершенных.';
COMMENT ON COLUMN orders.id IS 'Уникальный внутренний ID ордера.';
COMMENT ON COLUMN orders.exchange_id IS 'ID ордера, присвоенный биржей.';
COMMENT ON COLUMN orders.metadata IS 'Дополнительные метаданные в формате JSON.';
COMMENT ON COLUMN orders.exchange_raw_data IS 'Полный сырой ответ от биржи в формате JSON.';

COMMENT ON TABLE deals IS 'Таблица для хранения сделок, которые объединяют ордера на покупку и продажу.';
COMMENT ON COLUMN deals.buy_order IS 'Полные данные ордера на покупку в формате JSONB.';
COMMENT ON COLUMN deals.sell_order IS 'Полные данные ордера на продажу в формате JSONB.';
