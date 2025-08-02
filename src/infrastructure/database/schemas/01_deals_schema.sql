-- Схема для таблицы сделок (Deals)
-- Содержит ключевые поля для индексации и внешних ключей.
CREATE TABLE IF NOT EXISTS deals (
    id SERIAL PRIMARY KEY,
    deal_id BIGINT UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    buy_order_id BIGINT,
    sell_order_id BIGINT,
    created_at BIGINT NOT NULL,
    closed_at BIGINT
);

CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_symbol ON deals(symbol);