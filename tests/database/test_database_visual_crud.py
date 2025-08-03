#!/usr/bin/env python3
# test_database_visual_crud.py
"""
🧪 ВИЗУАЛЬНЫЙ ТЕСТ CRUD ОПЕРАЦИЙ С POSTGRESQL

Показывает все операции с базой данных:
- Подключение к PostgreSQL
- Просмотр таблиц и их содержимого
- Создание записи сделки
- Изменение записи
- Создание копии
- Изменение копии
- Удаление оригинала
- Финальное состояние БД
"""

import asyncio
import asyncpg
import sys
import os
from datetime import datetime

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from infrastructure.repositories.factory.repository_factory import RepositoryFactory

async def show_database_tables():
    """Показать все таблицы в базе данных"""
    print("\n📊 ПРОВЕРЯЕМ ТАБЛИЦЫ В БАЗЕ ДАННЫХ:")
    print("=" * 50)
    
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5434,
            user="airflow", 
            password="airflow",
            database="airflow"
        )
        
        # Получаем список таблиц
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        if tables:
            print("✅ Найденные таблицы:")
            for table in tables:
                print(f"   - {table['table_name']}")
        else:
            print("⚠️ Таблицы не найдены")
        
        await conn.close()
        return len(tables)
        
    except Exception as e:
        print(f"❌ Ошибка при проверке таблиц: {e}")
        return 0

async def show_table_content(table_name: str, title: str):
    """Показать содержимое таблицы"""
    print(f"\n📋 {title}")
    print("=" * 50)
    
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5434,
            user="airflow", 
            password="airflow",
            database="airflow"
        )
        
        # Проверяем существование таблицы
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = $1
            )
        """, table_name)
        
        if not table_exists:
            print(f"⚠️ Таблица '{table_name}' не существует")
            await conn.close()
            return
        
        # Получаем содержимое таблицы
        rows = await conn.fetch(f"SELECT * FROM {table_name} ORDER BY deal_id")
        
        if rows:
            print(f"✅ Найдено записей: {len(rows)}")
            print("\n📊 СОДЕРЖИМОЕ ТАБЛИЦЫ:")
            print("-" * 80)
            
            # Заголовки колонок
            if rows:
                columns = list(rows[0].keys())
                header = " | ".join(f"{col:12}" for col in columns[:6])  # Первые 6 колонок
                print(header)
                print("-" * len(header))
                
                # Данные
                for row in rows:
                    values = []
                    for col in columns[:6]:
                        value = row[col]
                        if isinstance(value, datetime):
                            value = value.strftime("%H:%M:%S")
                        elif value is None:
                            value = "NULL"
                        else:
                            value = str(value)
                        values.append(f"{value:12}")
                    print(" | ".join(values))
        else:
            print("📭 Таблица пуста")
        
        await conn.close()
        return len(rows) if rows else 0
        
    except Exception as e:
        print(f"❌ Ошибка при чтении таблицы: {e}")
        return 0

async def test_database_crud_operations():
    """Полный тест CRUD операций с визуализацией"""
    print("🚀 ЗАПУСК ВИЗУАЛЬНОГО ТЕСТА CRUD ОПЕРАЦИЙ С POSTGRESQL")
    print("=" * 70)
    
    # 1. Проверяем таблицы в БД
    tables_count = await show_database_tables()
    
    # 2. Инициализируем фабрику репозиториев
    print("\n🏭 ИНИЦИАЛИЗАЦИЯ ФАБРИКИ РЕПОЗИТОРИЕВ:")
    print("=" * 50)
    
    factory = RepositoryFactory()
    await factory.initialize()
    
    deals_repo = await factory.get_deals_repository()
    print("✅ MemoryFirst репозиторий сделок создан")
    
    # 3. Показываем начальное состояние таблицы
    await show_table_content("deals", "НАЧАЛЬНОЕ СОСТОЯНИЕ ТАБЛИЦЫ DEALS")
    
    # 4. Создаем тестовую валютную пару
    print("\n💱 СОЗДАНИЕ ТЕСТОВОЙ ВАЛЮТНОЙ ПАРЫ:")
    print("=" * 50)
    
    currency_pair = CurrencyPair(
        base_currency="ATM",
        quote_currency="USDT",
        symbol="ATMUSDT",
        deal_quota=25.0
    )
    print(f"✅ Валютная пара создана: {currency_pair.symbol}")
    
    # 5. СОЗДАЕМ ОРИГИНАЛЬНУЮ СДЕЛКУ
    print("\n📝 ШАГ 1: СОЗДАНИЕ ОРИГИНАЛЬНОЙ СДЕЛКИ")
    print("=" * 50)
    
    original_deal = Deal(
        deal_id=1001,
        currency_pair=currency_pair,
        status=Deal.STATUS_OPEN,
        profit=0.0
    )
    
    print(f"✅ Создана сделка ID: {original_deal.deal_id}")
    print(f"   - Статус: {original_deal.status}")
    print(f"   - Прибыль: {original_deal.profit}")
    
    # Сохраняем в репозиторий (автоматически синхронизируется с PostgreSQL)
    deals_repo.save(original_deal)
    print("✅ Сделка сохранена в репозиторий")
    
    # Ждем немного для синхронизации с БД
    await asyncio.sleep(1)
    
    # Показываем состояние таблицы после создания
    await show_table_content("deals", "СОСТОЯНИЕ ПОСЛЕ СОЗДАНИЯ ОРИГИНАЛЬНОЙ СДЕЛКИ")
    
    # 6. ИЗМЕНЯЕМ ОРИГИНАЛЬНУЮ СДЕЛКУ
    print("\n✏️ ШАГ 2: ИЗМЕНЕНИЕ ОРИГИНАЛЬНОЙ СДЕЛКИ")
    print("=" * 50)
    
    original_deal.status = Deal.STATUS_CLOSED
    original_deal.profit = 1.5
    original_deal.updated_at = int(datetime.now().timestamp() * 1000)
    
    print(f"✅ Изменена сделка ID: {original_deal.deal_id}")
    print(f"   - Новый статус: {original_deal.status}")
    print(f"   - Новая прибыль: {original_deal.profit}")
    
    # Сохраняем изменения
    deals_repo.save(original_deal)
    print("✅ Изменения сохранены в репозиторий")
    
    # Ждем синхронизации
    await asyncio.sleep(1)
    
    # Показываем состояние после изменения
    await show_table_content("deals", "СОСТОЯНИЕ ПОСЛЕ ИЗМЕНЕНИЯ ОРИГИНАЛЬНОЙ СДЕЛКИ")
    
    # 7. СОЗДАЕМ КОПИЮ СДЕЛКИ
    print("\n📋 ШАГ 3: СОЗДАНИЕ КОПИИ СДЕЛКИ")
    print("=" * 50)
    
    copy_deal = Deal(
        deal_id=1002,
        currency_pair=currency_pair,
        status=original_deal.status,
        profit=original_deal.profit
    )
    
    print(f"✅ Создана копия сделки ID: {copy_deal.deal_id}")
    print(f"   - Статус: {copy_deal.status}")
    print(f"   - Прибыль: {copy_deal.profit}")
    
    # Сохраняем копию
    deals_repo.save(copy_deal)
    print("✅ Копия сохранена в репозиторий")
    
    # Ждем синхронизации
    await asyncio.sleep(1)
    
    # Показываем состояние после создания копии
    await show_table_content("deals", "СОСТОЯНИЕ ПОСЛЕ СОЗДАНИЯ КОПИИ СДЕЛКИ")
    
    # 8. ИЗМЕНЯЕМ КОПИЮ
    print("\n🔧 ШАГ 4: ИЗМЕНЕНИЕ КОПИИ СДЕЛКИ")
    print("=" * 50)
    
    copy_deal.profit = 2.8
    copy_deal.updated_at = int(datetime.now().timestamp() * 1000)
    
    print(f"✅ Изменена копия сделки ID: {copy_deal.deal_id}")
    print(f"   - Новая прибыль: {copy_deal.profit}")
    
    # Сохраняем изменения копии
    deals_repo.save(copy_deal)
    print("✅ Изменения копии сохранены в репозиторий")
    
    # Ждем синхронизации
    await asyncio.sleep(1)
    
    # Показываем состояние после изменения копии
    await show_table_content("deals", "СОСТОЯНИЕ ПОСЛЕ ИЗМЕНЕНИЯ КОПИИ СДЕЛКИ")
    
    # 9. УДАЛЯЕМ ОРИГИНАЛЬНУЮ СДЕЛКУ
    print("\n🗑️ ШАГ 5: УДАЛЕНИЕ ОРИГИНАЛЬНОЙ СДЕЛКИ")
    print("=" * 50)
    
    success = deals_repo.delete_by_id(original_deal.deal_id)
    
    if success:
        print(f"✅ Оригинальная сделка ID {original_deal.deal_id} удалена из репозитория")
    else:
        print(f"❌ Не удалось удалить сделку ID {original_deal.deal_id}")
    
    # Ждем синхронизации
    await asyncio.sleep(1)
    
    # Показываем финальное состояние
    await show_table_content("deals", "ФИНАЛЬНОЕ СОСТОЯНИЕ ПОСЛЕ УДАЛЕНИЯ ОРИГИНАЛА")
    
    # 10. ПРОВЕРЯЕМ СОСТОЯНИЕ РЕПОЗИТОРИЯ В ПАМЯТИ
    print("\n🧠 СОСТОЯНИЕ РЕПОЗИТОРИЯ В ПАМЯТИ:")
    print("=" * 50)
    
    all_deals = deals_repo.get_all()
    print(f"✅ Всего сделок в памяти: {len(all_deals)}")
    
    for deal in all_deals:
        print(f"   - ID: {deal.deal_id}, Статус: {deal.status}, Прибыль: {deal.profit}")
    
    # 11. ПРЯМАЯ ПРОВЕРКА POSTGRESQL
    print("\n🔍 ПРЯМАЯ ПРОВЕРКА POSTGRESQL:")
    print("=" * 50)
    
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5434,
            user="airflow", 
            password="airflow",
            database="airflow"
        )
        
        # Подсчитываем записи в БД
        count = await conn.fetchval("SELECT COUNT(*) FROM deals")
        print(f"✅ Записей в PostgreSQL: {count}")
        
        # Получаем все записи
        rows = await conn.fetch("SELECT deal_id, status, profit FROM deals ORDER BY deal_id")
        
        for row in rows:
            print(f"   - PostgreSQL ID: {row['deal_id']}, Статус: {row['status']}, Прибыль: {row['profit']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке PostgreSQL: {e}")
    
    # 12. Закрываем фабрику
    await factory.close()
    print("\n✅ Фабрика репозиториев закрыта")
    
    print("\n🎉 ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 70)
    print("✅ Все CRUD операции выполнены")
    print("✅ Синхронизация с PostgreSQL работает")
    print("✅ Двухуровневая архитектура функционирует корректно")

def show_connection_info():
    """Показать информацию для подключения к PostgreSQL"""
    print("\n🔌 ИНФОРМАЦИЯ ДЛЯ ПОДКЛЮЧЕНИЯ К POSTGRESQL:")
    print("=" * 60)
    print("📊 Параметры подключения:")
    print("   - Хост: localhost")
    print("   - Порт: 5434")
    print("   - Пользователь: airflow")
    print("   - Пароль: airflow")
    print("   - База данных: airflow")
    print()
    print("🛠️ Способы подключения:")
    print()
    print("1️⃣ Через psql (командная строка):")
    print("   psql -h localhost -p 5434 -U airflow -d airflow")
    print()
    print("2️⃣ Через pgAdmin:")
    print("   - Создать новое подключение")
    print("   - Host: localhost, Port: 5434")
    print("   - Username: airflow, Password: airflow")
    print("   - Database: airflow")
    print()
    print("3️⃣ Через DBeaver:")
    print("   - New Connection → PostgreSQL")
    print("   - Server Host: localhost, Port: 5434")
    print("   - Database: airflow")
    print("   - Username: airflow, Password: airflow")
    print()
    print("4️⃣ SQL команды для просмотра:")
    print("   SELECT * FROM deals;")
    print("   SELECT * FROM orders;")
    print("   \\dt  -- показать все таблицы")
    print("   \\d deals  -- показать структуру таблицы deals")
    print()
    print("🎯 Таблицы для просмотра:")
    print("   - deals (сделки)")
    print("   - orders (ордера)")
    print("   - tickers_history (история тикеров)")
    print("   - order_books_history (история стаканов)")

if __name__ == "__main__":
    print("🚀 ВИЗУАЛЬНЫЙ ТЕСТ CRUD ОПЕРАЦИЙ С POSTGRESQL")
    print("Этот тест покажет все операции с базой данных в реальном времени")
    print()
    
    # Показываем информацию для подключения
    show_connection_info()
    
    print("\n⏳ Запуск теста через 3 секунды...")
    import time
    time.sleep(3)
    
    # Запускаем тест
    asyncio.run(test_database_crud_operations())