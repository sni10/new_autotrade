-- Схема для хранения истории рассчитанных индикаторов
CREATE TABLE IF NOT EXISTS indicators_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp BIGINT NOT NULL,
    -- Храним все значения индикаторов в одном поле JSONB для гибкости.
    values JSONB NOT NULL,
    
    UNIQUE(symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_indicators_history_symbol_timestamp ON indicators_history(symbol, timestamp DESC);
