-- Схема для хранения истории тикеров
-- Обновлена для соответствия текущей структуре БД и требованиям кода
-- Содержит все поля из текущей БД + обязательное поле 'data' типа JSONB
CREATE TABLE IF NOT EXISTS tickers_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp BIGINT NOT NULL,
    last_price NUMERIC NOT NULL,
    bid_price NUMERIC,
    ask_price NUMERIC,
    volume NUMERIC,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    
    UNIQUE(symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_tickers_history_symbol_timestamp ON tickers_history(symbol, timestamp DESC);