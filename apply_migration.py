#!/usr/bin/env python3
"""
Apply database schema migration to fix critical issues
"""
import asyncio
import asyncpg

async def apply_migration():
    """Apply the database migration script"""
    print("🔧 ПРИМЕНЕНИЕ МИГРАЦИИ СХЕМЫ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host="localhost",
            port=5434,
            user="airflow", 
            password="airflow",
            database="airflow"
        )
        
        print("✅ Подключение к базе данных установлено")
        
        # Read migration script
        with open("database_schema_migration.sql", "r", encoding="utf-8") as f:
            migration_sql = f.read()
        
        print("📄 Миграционный скрипт загружен")
        
        # Execute migration
        print("🚀 Выполнение миграции...")
        await conn.execute(migration_sql)
        
        print("✅ МИГРАЦИЯ УСПЕШНО ПРИМЕНЕНА!")
        
        # Verify the results
        print("\n📊 ПРОВЕРКА РЕЗУЛЬТАТОВ:")
        
        # Check orders table structure
        orders_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'orders' 
            ORDER BY ordinal_position
        """)
        
        print("\n🗂️ СТРУКТУРА ТАБЛИЦЫ ORDERS:")
        for col in orders_columns:
            nullable = "NULL" if col['is_nullable'] == "YES" else "NOT NULL"
            print(f"  - {col['column_name']}: {col['data_type']} ({nullable})")
        
        # Check if data column exists and is NOT NULL
        data_column = [col for col in orders_columns if col['column_name'] == 'data']
        if data_column and data_column[0]['is_nullable'] == 'NO':
            print("✅ Колонка 'data' найдена и настроена как NOT NULL")
        else:
            print("❌ Проблема с колонкой 'data'")
        
        # Check order_id data type
        order_id_column = [col for col in orders_columns if col['column_name'] == 'order_id']
        if order_id_column and 'bigint' in order_id_column[0]['data_type']:
            print("✅ order_id теперь имеет тип BIGINT")
        else:
            print("❌ Проблема с типом order_id")
        
        await conn.close()
        print("\n🎉 МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        
    except Exception as e:
        print(f"❌ Ошибка при применении миграции: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(apply_migration())
    if success:
        print("\n✅ Теперь можно запускать приложение - ошибки схемы исправлены!")
    else:
        print("\n❌ Миграция не удалась. Проверьте ошибки выше.")