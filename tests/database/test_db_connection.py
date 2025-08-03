#!/usr/bin/env python3
# test_db_connection.py
import asyncio
import asyncpg

async def test_connection():
    """Тест подключения к PostgreSQL"""
    try:
        print("🔌 Тестируем подключение к PostgreSQL...")
        
        conn = await asyncpg.connect(
            host="localhost",
            port=5434,
            user="airflow", 
            password="airflow",
            database="airflow"
        )
        
        result = await conn.fetchval("SELECT version()")
        print(f"✅ PostgreSQL подключение успешно!")
        print(f"📊 Версия: {result}")
        
        # Тест создания таблицы
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        print("✅ Тест создания таблицы успешен")
        
        # Тест вставки данных
        await conn.execute("""
            INSERT INTO test_table (name) VALUES ($1)
        """, "test_migration")
        print("✅ Тест вставки данных успешен")
        
        # Тест чтения данных
        rows = await conn.fetch("SELECT * FROM test_table LIMIT 5")
        print(f"✅ Тест чтения данных успешен: найдено {len(rows)} записей")
        
        # Очистка тестовых данных
        await conn.execute("DROP TABLE IF EXISTS test_table")
        print("✅ Тестовые данные очищены")
        
        await conn.close()
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! PostgreSQL готов к работе!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        print("🔧 Проверьте:")
        print("   - Запущен ли Docker контейнер: docker ps")
        print("   - Правильные ли параметры подключения в config.json")
        print("   - Доступен ли порт 5434")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())