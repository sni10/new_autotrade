-- Схема для таблицы сделок (Deals)
-- Обновлена для соответствия текущей структуре БД и требованиям кода
CREATE TABLE IF NOT EXISTS deals (
    deal_id BIGINT PRIMARY KEY,
    currency_pair VARCHAR(20) NOT NULL,
    base_currency VARCHAR(10) NOT NULL,
    quote_currency VARCHAR(10) NOT NULL,
    deal_quota NUMERIC NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    closed_at TIMESTAMP WITHOUT TIME ZONE,
    buy_order_id BIGINT,
    sell_order_id BIGINT,
    profit NUMERIC DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_symbol ON deals(currency_pair);
CREATE INDEX IF NOT EXISTS idx_deals_buy_order ON deals(buy_order_id);
CREATE INDEX IF NOT EXISTS idx_deals_sell_order ON deals(sell_order_id);