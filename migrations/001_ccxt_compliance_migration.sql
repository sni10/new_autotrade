-- Migration Script: AutoTrade v2.4.0 CCXT Compliance Migration
-- Дата: 2025-01-27
-- Версия: 001
-- Описание: Безопасная миграция с кастомной структуры на CCXT совместимую

-- =================================================================
-- BACKUP EXISTING DATA
-- =================================================================

-- Создаем таблицы для бэкапа существующих данных
CREATE TABLE IF NOT EXISTS backup_orders_pre_ccxt AS 
SELECT * FROM orders WHERE 1=0;  -- Создаем структуру без данных

CREATE TABLE IF NOT EXISTS backup_deals_pre_ccxt AS 
SELECT * FROM deals WHERE 1=0;

-- Делаем полный бэкап существующих данных
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'orders') THEN
        INSERT INTO backup_orders_pre_ccxt SELECT * FROM orders;
        RAISE NOTICE 'Backed up % orders', (SELECT COUNT(*) FROM backup_orders_pre_ccxt);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'deals') THEN
        INSERT INTO backup_deals_pre_ccxt SELECT * FROM deals;
        RAISE NOTICE 'Backed up % deals', (SELECT COUNT(*) FROM backup_deals_pre_ccxt);
    END IF;
END $$;

-- =================================================================
-- MIGRATION FUNCTIONS
-- =================================================================

-- Функция для конвертации старых статусов в CCXT
CREATE OR REPLACE FUNCTION convert_order_status_to_ccxt(old_status TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN CASE old_status
        WHEN 'OPEN' THEN 'open'
        WHEN 'CLOSED' THEN 'closed'
        WHEN 'CANCELED' THEN 'canceled'
        WHEN 'CANCELLED' THEN 'canceled'
        WHEN 'FAILED' THEN 'rejected'
        WHEN 'PENDING' THEN 'pending'
        WHEN 'FILLED' THEN 'closed'
        WHEN 'PARTIALLY_FILLED' THEN 'partial'
        WHEN 'NOT_FOUND_ON_EXCHANGE' THEN 'rejected'
        ELSE 'pending'  -- default fallback
    END;
END;
$$ LANGUAGE plpgsql;

-- Функция для конвертации старых типов ордеров в CCXT
CREATE OR REPLACE FUNCTION convert_order_type_to_ccxt(old_type TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN CASE old_type
        WHEN 'LIMIT' THEN 'limit'
        WHEN 'MARKET' THEN 'market'
        WHEN 'STOP_LOSS' THEN 'stop'
        WHEN 'TAKE_PROFIT' THEN 'take_profit'
        ELSE 'limit'  -- default fallback
    END;
END;
$$ LANGUAGE plpgsql;

-- Функция для конвертации старых сторон ордеров в CCXT
CREATE OR REPLACE FUNCTION convert_order_side_to_ccxt(old_side TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN CASE old_side
        WHEN 'BUY' THEN 'buy'
        WHEN 'SELL' THEN 'sell'
        ELSE 'buy'  -- default fallback
    END;
END;
$$ LANGUAGE plpgsql;

-- Функция для генерации ISO8601 datetime из timestamp
CREATE OR REPLACE FUNCTION timestamp_to_iso8601(ts BIGINT)
RETURNS TEXT AS $$
BEGIN
    IF ts IS NULL THEN
        RETURN NULL;
    END IF;
    RETURN to_char(to_timestamp(ts / 1000.0) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"');
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- STEP 1: CREATE CCXT SCHEMA (если еще не создана)
-- =================================================================

-- Загружаем CCXT схему (предполагается, что файл уже был выполнен)
-- Если нет, раскомментируйте следующую строку:
-- \i src/infrastructure/database/schemas/postgresql_ccxt_schema.sql

-- Если таблицы CCXT еще не созданы (например, в fresh install),
-- создаем минимально необходимую структуру для ccxt_orders
CREATE TABLE IF NOT EXISTS ccxt_orders (
            id VARCHAR(100) PRIMARY KEY,
            client_order_id VARCHAR(100),
            datetime TIMESTAMP WITH TIME ZONE,
            timestamp BIGINT,
            last_trade_timestamp BIGINT,
            status VARCHAR(20) NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            type VARCHAR(20) NOT NULL,
            time_in_force VARCHAR(10),
            side VARCHAR(10) NOT NULL,
            price DECIMAL(20, 8),
            amount DECIMAL(20, 8) NOT NULL,
            filled DECIMAL(20, 8) DEFAULT 0,
            remaining DECIMAL(20, 8),
            cost DECIMAL(20, 8),
            average DECIMAL(20, 8),
            trades JSONB DEFAULT '[]',
            fee JSONB DEFAULT '{}',
            info JSONB DEFAULT '{}',
            deal_id UUID,
            local_order_id SERIAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT,
            retries INTEGER DEFAULT 0,
            metadata JSONB DEFAULT '{}'
);

-- Индексы для частых запросов
CREATE INDEX IF NOT EXISTS idx_ccxt_orders_symbol ON ccxt_orders(symbol);
CREATE INDEX IF NOT EXISTS idx_ccxt_orders_status ON ccxt_orders(status);
CREATE INDEX IF NOT EXISTS idx_ccxt_orders_timestamp ON ccxt_orders(timestamp);

-- =================================================================
-- STEP 2: MIGRATE EXISTING DATA
-- =================================================================

-- Миграция валютных пар
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'currency_pairs') THEN
        -- Мигрируем существующие валютные пары в ccxt_markets
        INSERT INTO ccxt_markets (
            id, symbol, base, quote, base_id, quote_id, active, 
            precision, limits, maker, taker, info
        )
        SELECT 
            REPLACE(symbol, '/', ''),  -- BTC/USDT -> BTCUSDT
            symbol,                    -- BTC/USDT остается как есть
            base_currency,
            quote_currency,
            LOWER(base_currency),      -- btc
            LOWER(quote_currency),     -- usdt
            true,                      -- active по умолчанию
            COALESCE(precision_data, '{"amount": 8, "price": 2}'),
            COALESCE(limits_data, '{"amount": {"min": 0.00001}, "cost": {"min": 10}}'),
            COALESCE(maker_fee, 0.001),
            COALESCE(taker_fee, 0.001),
            '{}'::jsonb                -- пустой info
        FROM currency_pairs
        ON CONFLICT (symbol) DO UPDATE SET
            precision = EXCLUDED.precision,
            limits = EXCLUDED.limits,
            maker = EXCLUDED.maker,
            taker = EXCLUDED.taker,
            updated_at = CURRENT_TIMESTAMP;
            
        RAISE NOTICE 'Migrated % currency pairs to ccxt_markets', (SELECT COUNT(*) FROM currency_pairs);
    END IF;
END $$;

-- Миграция ордеров
DO $$
DECLARE
    order_record RECORD;
    new_order_id VARCHAR(100);
    migrated_count INTEGER := 0;
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'orders') THEN
        
        FOR order_record IN 
            SELECT * FROM orders 
        LOOP
            -- Генерируем новый ID для ордера (если exchange_id есть, используем его, иначе генерируем)
            new_order_id := COALESCE(
                order_record.exchange_id, 
                'local_' || order_record.order_id::TEXT
            );
            
            -- Вставляем ордер в новую CCXT совместимую таблицу
            INSERT INTO ccxt_orders (
                id,
                client_order_id,
                datetime,
                timestamp,
                last_trade_timestamp,
                status,
                symbol,
                type,
                time_in_force,
                side,
                price,
                amount,
                filled,
                remaining,
                cost,
                average,
                trades,
                fee,
                info,
                deal_id,
                local_order_id,
                created_at,
                updated_at,
                error_message,
                retries,
                metadata
            ) VALUES (
                new_order_id,
                order_record.client_order_id,
                timestamp_to_iso8601(COALESCE(order_record.created_at, extract(epoch from now()) * 1000))::TIMESTAMP WITH TIME ZONE,
                COALESCE(order_record.created_at, extract(epoch from now()) * 1000),
                order_record.exchange_timestamp,
                convert_order_status_to_ccxt(order_record.status)::ccxt_order_status,
                order_record.symbol,
                convert_order_type_to_ccxt(order_record.order_type)::ccxt_order_type,
                'GTC'::ccxt_time_in_force,  -- default time in force
                convert_order_side_to_ccxt(order_record.side)::ccxt_order_side,
                order_record.price,
                order_record.amount,
                COALESCE(order_record.filled_amount, 0),
                COALESCE(order_record.remaining_amount, order_record.amount),
                CASE 
                    WHEN order_record.filled_amount > 0 AND order_record.average_price > 0 
                    THEN order_record.filled_amount * order_record.average_price
                    ELSE NULL
                END,
                CASE 
                    WHEN order_record.average_price > 0 
                    THEN order_record.average_price
                    ELSE NULL
                END,
                '[]'::jsonb,  -- trades array (пустой)
                jsonb_build_object(
                    'cost', COALESCE(order_record.fees, 0),
                    'currency', COALESCE(order_record.fee_currency, 'USDT'),
                    'rate', NULL
                ),
                COALESCE(order_record.metadata, '{}'::jsonb),
                order_record.deal_id::UUID,
                order_record.order_id,
                COALESCE(
                    to_timestamp(order_record.created_at / 1000.0),
                    CURRENT_TIMESTAMP
                ),
                COALESCE(
                    to_timestamp(order_record.last_update / 1000.0),
                    CURRENT_TIMESTAMP
                ),
                order_record.error_message,
                COALESCE(order_record.retries, 0),
                COALESCE(order_record.metadata, '{}'::jsonb)
            )
            ON CONFLICT (id) DO NOTHING;  -- Skip если уже существует
            
            migrated_count := migrated_count + 1;
        END LOOP;
        
        RAISE NOTICE 'Migrated % orders to ccxt_orders', migrated_count;
    END IF;
END $$;

-- Миграция сделок
DO $$
DECLARE
    deal_record RECORD;
    migrated_count INTEGER := 0;
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'deals') THEN
        
        FOR deal_record IN 
            SELECT * FROM deals 
        LOOP
            -- Получаем новые ID ордеров для сделки
            DECLARE
                new_buy_order_id VARCHAR(100) := NULL;
                new_sell_order_id VARCHAR(100) := NULL;
            BEGIN
                -- Найти соответствующие новые ID ордеров
                SELECT id INTO new_buy_order_id 
                FROM ccxt_orders 
                WHERE local_order_id = deal_record.buy_order_id;
                
                SELECT id INTO new_sell_order_id 
                FROM ccxt_orders 
                WHERE local_order_id = deal_record.sell_order_id;
                
                -- Вставляем сделку
                INSERT INTO deals (
                    deal_id,
                    symbol,
                    status,
                    buy_order_id,
                    sell_order_id,
                    target_profit_percent,
                    actual_profit,
                    created_at,
                    completed_at,
                    metadata
                ) VALUES (
                    deal_record.deal_id,
                    deal_record.currency_pair_symbol,
                    CASE deal_record.status
                        WHEN 'OPEN' THEN 'active'
                        WHEN 'ACTIVE' THEN 'active'
                        WHEN 'WAITING_SELL' THEN 'waiting_sell'
                        WHEN 'COMPLETED' THEN 'completed'
                        WHEN 'CLOSED' THEN 'completed'
                        WHEN 'CANCELLED' THEN 'canceled'
                        WHEN 'CANCELED' THEN 'canceled'
                        WHEN 'FAILED' THEN 'failed'
                        ELSE 'active'
                    END::deal_status,
                    new_buy_order_id,
                    new_sell_order_id,
                    deal_record.target_profit_percent,
                    deal_record.actual_profit,
                    COALESCE(
                        to_timestamp(deal_record.created_at / 1000.0),
                        CURRENT_TIMESTAMP
                    ),
                    CASE 
                        WHEN deal_record.closed_at IS NOT NULL 
                        THEN to_timestamp(deal_record.closed_at / 1000.0)
                        ELSE NULL
                    END,
                    COALESCE(deal_record.metadata, '{}'::jsonb)
                )
                ON CONFLICT (deal_id) DO NOTHING;
                
                migrated_count := migrated_count + 1;
            END;
        END LOOP;
        
        RAISE NOTICE 'Migrated % deals', migrated_count;
    END IF;
END $$;

-- =================================================================
-- STEP 3: UPDATE FOREIGN KEYS IN CCXT_ORDERS
-- =================================================================

-- Обновляем deal_id в ccxt_orders на основе связей
UPDATE ccxt_orders 
SET deal_id = d.deal_id
FROM deals d
WHERE ccxt_orders.id = d.buy_order_id OR ccxt_orders.id = d.sell_order_id;

-- =================================================================
-- STEP 4: VERIFICATION
-- =================================================================

-- Проверка миграции
DO $$
DECLARE
    old_orders_count INTEGER := 0;
    new_orders_count INTEGER;
    old_deals_count INTEGER := 0;
    new_deals_count INTEGER;
BEGIN
    -- Подсчитываем старые данные
    SELECT COUNT(*) INTO old_orders_count FROM backup_orders_pre_ccxt;
    SELECT COUNT(*) INTO old_deals_count FROM backup_deals_pre_ccxt;
    
    -- Подсчитываем новые данные
    SELECT COUNT(*) INTO new_orders_count FROM ccxt_orders;
    SELECT COUNT(*) INTO new_deals_count FROM deals;
    
    -- Отчет о миграции
    RAISE NOTICE '=== MIGRATION REPORT ===';
    RAISE NOTICE 'Orders: % -> %', old_orders_count, new_orders_count;
    RAISE NOTICE 'Deals: % -> %', old_deals_count, new_deals_count;
    
    -- Проверка целостности
    IF new_orders_count < old_orders_count THEN
        RAISE WARNING 'Some orders may not have been migrated!';
    END IF;
    
    IF new_deals_count < old_deals_count THEN
        RAISE WARNING 'Some deals may not have been migrated!';
    END IF;
    
    RAISE NOTICE 'Migration completed successfully!';
END $$;

-- =================================================================
-- STEP 5: CLEANUP FUNCTIONS (выполнять ТОЛЬКО после проверки!)
-- =================================================================

-- Функция для удаления старых таблиц (НЕ ВЫЗЫВАТЬ АВТОМАТИЧЕСКИ!)
CREATE OR REPLACE FUNCTION drop_old_tables()
RETURNS TEXT AS $$
BEGIN
    -- ВНИМАНИЕ: Эта функция удалит старые таблицы!
    -- Вызывайте только после полной проверки миграции!
    
    DROP TABLE IF EXISTS orders CASCADE;
    DROP TABLE IF EXISTS currency_pairs CASCADE;
    
    RETURN 'Old tables dropped successfully';
END;
$$ LANGUAGE plpgsql;

-- Функция для удаления бэкап таблиц (НЕ ВЫЗЫВАТЬ АВТОМАТИЧЕСКИ!)
CREATE OR REPLACE FUNCTION drop_backup_tables()
RETURNS TEXT AS $$
BEGIN
    -- ВНИМАНИЕ: Эта функция удалит бэкап таблицы!
    -- Вызывайте только после полной проверки миграции!
    
    DROP TABLE IF EXISTS backup_orders_pre_ccxt;
    DROP TABLE IF EXISTS backup_deals_pre_ccxt;
    
    RETURN 'Backup tables dropped successfully';
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- STEP 6: POST-MIGRATION CLEANUP
-- =================================================================

-- Удаляем временные функции миграции
DROP FUNCTION IF EXISTS convert_order_status_to_ccxt(TEXT);
DROP FUNCTION IF EXISTS convert_order_type_to_ccxt(TEXT);
DROP FUNCTION IF EXISTS convert_order_side_to_ccxt(TEXT);
DROP FUNCTION IF EXISTS timestamp_to_iso8601(BIGINT);

-- Обновляем статистику таблиц для оптимизатора
ANALYZE ccxt_orders;
ANALYZE deals;
ANALYZE ccxt_markets;

-- Обновляем версию схемы
UPDATE configuration 
SET value = '2.4.0-ccxt-migrated', updated_at = CURRENT_TIMESTAMP
WHERE key = 'schema_version' AND category = 'system';

INSERT INTO configuration (key, category, value, config_type, description, is_required) VALUES
('migration_001_completed_at', 'system', EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::TEXT, 'string', 'Время завершения миграции 001', true)
ON CONFLICT (key, category) DO UPDATE SET 
value = EXCLUDED.value, 
updated_at = CURRENT_TIMESTAMP;

-- =================================================================
-- FINAL MESSAGE
-- =================================================================

DO $$
BEGIN
    RAISE NOTICE '=== CCXT COMPLIANCE MIGRATION COMPLETED ===';
    RAISE NOTICE 'Schema version: 2.4.0-ccxt-migrated';
    RAISE NOTICE 'Migration date: %', CURRENT_TIMESTAMP;
    RAISE NOTICE '';
    RAISE NOTICE 'NEXT STEPS:';
    RAISE NOTICE '1. Test the new CCXT compliant structure';
    RAISE NOTICE '2. Update application code to use new tables';
    RAISE NOTICE '3. After verification, run: SELECT drop_old_tables();';
    RAISE NOTICE '4. After full testing, run: SELECT drop_backup_tables();';
    RAISE NOTICE '';
    RAISE NOTICE 'BACKUP TABLES CREATED:';
    RAISE NOTICE '- backup_orders_pre_ccxt';
    RAISE NOTICE '- backup_deals_pre_ccxt';
END $$;