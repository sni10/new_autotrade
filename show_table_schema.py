#!/usr/bin/env python3
"""
Показать структуру таблиц PostgreSQL
"""
import asyncio
import asyncpg

async def show_table_schema():
    """Показать структуру всех таблиц в базе данных"""
    print("📊 СТРУКТУРА ВСЕХ ТАБЛИЦ В БД:")
    print("=" * 80)
    
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5434,
            user="airflow", 
            password="airflow",
            database="airflow"
        )
        
        # Получаем список всех таблиц
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        if not tables:
            print("⚠️ Таблицы не найдены")
            await conn.close()
            return
            
        print(f"Найдено таблиц: {len(tables)}")
        print("-" * 80)
        
        for table in tables:
            table_name = table['table_name']
            print(f"\n🗂️ ТАБЛИЦА: {table_name.upper()}")
            print("-" * 60)
            
            # Получаем структуру каждой таблицы
            schema = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = $1 
                ORDER BY ordinal_position
            """, table_name)
            
            if schema:
                print(f"{'Колонка':<20} | {'Тип':<15} | {'NULL':<8} | {'По умолчанию'}")
                print("-" * 70)
                for col in schema:
                    nullable = "YES" if col['is_nullable'] == "YES" else "NO"
                    default = col['column_default'] or ""
                    print(f"{col['column_name']:<20} | {col['data_type']:<15} | {nullable:<8} | {default}")
            else:
                print("⚠️ Структура таблицы не найдена")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при получении структуры: {e}")

if __name__ == "__main__":
    asyncio.run(show_table_schema())