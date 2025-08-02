-- Схема для хранения истории стаканов ордеров
-- Поле 'data' хранит полный объект OrderBook.
CREATE TABLE IF NOT EXISTS order_books_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp BIGINT NOT NULL,
    data JSONB NOT NULL,
    
    UNIQUE(symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_order_books_history_symbol_timestamp ON order_books_history(symbol, timestamp DESC);
