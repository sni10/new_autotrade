-- Схема для хранения истории тикеров
-- Содержит ключевые поля для индексации и поле 'data' типа JSONB
-- для хранения полного объекта Ticker.
CREATE TABLE IF NOT EXISTS tickers_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp BIGINT NOT NULL,
    last_price REAL NOT NULL,
    data JSONB NOT NULL,
    
    UNIQUE(symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_tickers_history_symbol_timestamp ON tickers_history(symbol, timestamp DESC);