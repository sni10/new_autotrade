-- Схема для таблицы ордеров (Orders)
-- Обновлена для соответствия текущей структуре БД и требованиям кода
-- Содержит все необходимые поля + поле 'data' типа JSONB для полного объекта Order
CREATE TABLE IF NOT EXISTS orders (
    order_id BIGINT PRIMARY KEY,
    exchange_order_id VARCHAR(50),
    deal_id BIGINT,
    order_type VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    amount NUMERIC NOT NULL,
    price NUMERIC NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    filled_amount NUMERIC DEFAULT 0,
    fees NUMERIC DEFAULT 0,
    commission NUMERIC DEFAULT 0,
    data JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_deal_id ON orders(deal_id);
CREATE INDEX IF NOT EXISTS idx_orders_exchange_id ON orders(exchange_order_id);