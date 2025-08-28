-- Схема для хранения истории стаканов ордеров
-- Обновлена для соответствия текущей структуре БД и требованиям кода
-- Содержит все поля из текущей БД + обязательное поле 'data' типа JSONB
CREATE TABLE IF NOT EXISTS order_books_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp BIGINT NOT NULL,
    best_bid NUMERIC,
    best_ask NUMERIC,
    spread NUMERIC,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    
    UNIQUE(symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_order_books_history_symbol_timestamp ON order_books_history(symbol, timestamp DESC);
