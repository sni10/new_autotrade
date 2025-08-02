-- Схема для таблицы ордеров (Orders)
-- Содержит ключевые поля для индексации и поле 'data' типа JSONB
-- для хранения полного, неструктурированного объекта Order.
-- Это обеспечивает полноту данных и гибкость на будущее.
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id BIGINT UNIQUE NOT NULL,
    exchange_id VARCHAR(50) UNIQUE,
    deal_id BIGINT,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at BIGINT NOT NULL,
    last_update BIGINT,
    data JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_deal_id ON orders(deal_id);