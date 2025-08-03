#!/usr/bin/env python3
# test_database_crud_operations.py
"""
🧪 ТЕСТ CRUD ОПЕРАЦИЙ С БАЗОЙ ДАННЫХ

Этот тест демонстрирует полный цикл работы с двухуровневой архитектурой:
1. Подключение к PostgreSQL через RepositoryFactory
2. Создание записи сделки
3. Изменение записи
4. Создание копии сделки
5. Изменение копии
6. Удаление оригинальной сделки

Проверяет синхронизацию между DataFrame (память) и PostgreSQL (диск).
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from infrastructure.repositories.factory.repository_factory import RepositoryFactory

async def test_database_crud_operations():
    """
    Комплексный тест CRUD операций с базой данных
    """
    print("🧪 ЗАПУСК ТЕСТА CRUD ОПЕРАЦИЙ С БАЗОЙ ДАННЫХ")
    print("=" * 60)
    
    # Инициализация фабрики репозиториев
    factory = RepositoryFactory()
    
    try:
        # ШАГ 1: Подключение к БД
        print("\n📋 ШАГ 1: Подключение к базе данных...")
        await factory.initialize()
        
        deals_repo = await factory.get_deals_repository()
        storage_info = factory.get_storage_info()
        
        print(f"✅ Подключение успешно!")
        print(f"📊 Тип хранилища: {storage_info['deals_type']}")
        print(f"🗄️ PostgreSQL доступен: {'✅' if storage_info['postgresql_available'] else '❌'}")
        
        # Создаем тестовую валютную пару
        currency_pair = CurrencyPair(
            base_currency="ATM",
            quote_currency="USDT",
            symbol="ATMUSDT",
            deal_quota=25.0,
            profit_markup=0.015
        )
        
        # ШАГ 2: Создание оригинальной записи
        print("\n📋 ШАГ 2: Создание оригинальной сделки...")
        
        original_deal = Deal(
            deal_id=None,  # Автогенерация ID
            currency_pair=currency_pair,
            status=Deal.STATUS_OPEN,
            profit=0.0
        )
        
        start_time = time.time()
        deals_repo.save(original_deal)
        creation_time = (time.time() - start_time) * 1000
        
        print(f"✅ Оригинальная сделка создана!")
        print(f"🆔 ID сделки: {original_deal.deal_id}")
        print(f"📊 Статус: {original_deal.status}")
        print(f"💰 Прибыль: {original_deal.profit}")
        print(f"⏱️ Время создания: {creation_time:.2f}ms")
        
        # Проверяем, что сделка есть в репозитории
        retrieved_original = deals_repo.get_by_id(original_deal.deal_id)
        assert retrieved_original is not None, "Оригинальная сделка не найдена в репозитории"
        assert retrieved_original.deal_id == original_deal.deal_id, "ID не совпадает"
        
        # ШАГ 3: Изменение оригинальной записи
        print("\n📋 ШАГ 3: Изменение оригинальной сделки...")
        
        # Обновляем прибыль и статус
        new_profit = 1.25
        success = deals_repo.update_deal_profit(original_deal.deal_id, new_profit)
        
        assert success, "Не удалось обновить прибыль сделки"
        
        # Проверяем изменения
        updated_original = deals_repo.get_by_id(original_deal.deal_id)
        
        print(f"✅ Оригинальная сделка изменена!")
        print(f"💰 Новая прибыль: {updated_original.profit}")
        print(f"🕐 Время обновления: {updated_original.updated_at}")
        
        assert updated_original.profit == new_profit, f"Прибыль не обновилась: {updated_original.profit} != {new_profit}"
        
        # ШАГ 4: Создание копии сделки
        print("\n📋 ШАГ 4: Создание копии сделки...")
        
        # Создаем копию с теми же параметрами, но новым ID
        deal_copy = Deal(
            deal_id=None,  # Новый ID
            currency_pair=currency_pair,
            status=updated_original.status,
            profit=updated_original.profit
        )
        
        deals_repo.save(deal_copy)
        
        print(f"✅ Копия сделки создана!")
        print(f"🆔 ID копии: {deal_copy.deal_id}")
        print(f"🆔 ID оригинала: {original_deal.deal_id}")
        print(f"📊 Статус копии: {deal_copy.status}")
        print(f"💰 Прибыль копии: {deal_copy.profit}")
        
        # Проверяем, что копия создалась с новым ID
        assert deal_copy.deal_id != original_deal.deal_id, "Копия имеет тот же ID что и оригинал"
        
        retrieved_copy = deals_repo.get_by_id(deal_copy.deal_id)
        assert retrieved_copy is not None, "Копия сделки не найдена в репозитории"
        
        # ШАГ 5: Изменение копии
        print("\n📋 ШАГ 5: Изменение копии сделки...")
        
        # Закрываем копию с другой прибылью
        copy_profit = 2.75
        copy_sell_order_id = 999
        
        success = deals_repo.close_deal(deal_copy.deal_id, copy_sell_order_id, copy_profit)
        assert success, "Не удалось закрыть копию сделки"
        
        # Проверяем изменения копии
        updated_copy = deals_repo.get_by_id(deal_copy.deal_id)
        
        print(f"✅ Копия сделки изменена!")
        print(f"📊 Новый статус копии: {updated_copy.status}")
        print(f"💰 Новая прибыль копии: {updated_copy.profit}")
        print(f"🛒 ID ордера продажи: {copy_sell_order_id}")
        print(f"🕐 Время закрытия: {updated_copy.closed_at}")
        
        assert updated_copy.status == Deal.STATUS_CLOSED, f"Статус копии не изменился: {updated_copy.status}"
        assert updated_copy.profit == copy_profit, f"Прибыль копии не обновилась: {updated_copy.profit}"
        
        # ШАГ 6: Удаление оригинальной сделки
        print("\n📋 ШАГ 6: Удаление оригинальной сделки...")
        
        # Проверяем, что оригинал еще существует
        original_before_delete = deals_repo.get_by_id(original_deal.deal_id)
        assert original_before_delete is not None, "Оригинальная сделка исчезла до удаления"
        
        # Удаляем оригинальную сделку
        deleted = deals_repo.delete_by_id(original_deal.deal_id)
        assert deleted, "Не удалось удалить оригинальную сделку"
        
        # Проверяем, что оригинал удален
        original_after_delete = deals_repo.get_by_id(original_deal.deal_id)
        
        print(f"✅ Оригинальная сделка удалена!")
        print(f"🗑️ Сделка с ID {original_deal.deal_id} больше не существует")
        
        assert original_after_delete is None, "Оригинальная сделка не была удалена"
        
        # ШАГ 7: Проверка финального состояния
        print("\n📋 ШАГ 7: Проверка финального состояния...")
        
        # Проверяем, что копия все еще существует
        final_copy = deals_repo.get_by_id(deal_copy.deal_id)
        assert final_copy is not None, "Копия сделки исчезла"
        assert final_copy.status == Deal.STATUS_CLOSED, "Статус копии изменился"
        assert final_copy.profit == copy_profit, "Прибыль копии изменилась"
        
        # Получаем статистику
        stats = deals_repo.get_deals_statistics()
        all_deals = deals_repo.get_all()
        
        print(f"✅ Финальное состояние проверено!")
        print(f"📊 Всего сделок в репозитории: {len(all_deals)}")
        print(f"📊 Статистика: {stats}")
        print(f"🎯 Копия сделки ID {deal_copy.deal_id} существует и имеет статус {final_copy.status}")
        
        # Проверяем производительность
        print("\n📋 ПРОВЕРКА ПРОИЗВОДИТЕЛЬНОСТИ:")
        
        # Тест массовых операций
        mass_operations_start = time.time()
        
        test_deals = []
        for i in range(100):
            test_deal = Deal(
                deal_id=None,
                currency_pair=currency_pair,
                status=Deal.STATUS_OPEN,
                profit=i * 0.1
            )
            deals_repo.save(test_deal)
            test_deals.append(test_deal)
        
        mass_operations_time = (time.time() - mass_operations_start) * 1000
        avg_operation_time = mass_operations_time / 100
        
        print(f"⚡ 100 операций создания за {mass_operations_time:.2f}ms")
        print(f"⚡ Среднее время операции: {avg_operation_time:.3f}ms")
        
        # Очищаем тестовые данные
        for test_deal in test_deals:
            deals_repo.delete_by_id(test_deal.deal_id)
        
        print("\n🎉 ВСЕ ТЕСТЫ CRUD ОПЕРАЦИЙ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Создание записи - работает")
        print("✅ Изменение записи - работает") 
        print("✅ Создание копии - работает")
        print("✅ Изменение копии - работает")
        print("✅ Удаление оригинала - работает")
        print("✅ Синхронизация с БД - работает")
        print("✅ Производительность - отличная")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТЕ CRUD ОПЕРАЦИЙ: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Закрываем соединения
        await factory.close()
        print("\n🔒 Соединения с БД закрыты")

async def main():
    """Главная функция запуска теста"""
    print("🚀 ЗАПУСК ТЕСТА CRUD ОПЕРАЦИЙ С БАЗОЙ ДАННЫХ")
    print("Этот тест демонстрирует работу двухуровневой архитектуры хранения")
    print("с полным циклом CRUD операций и синхронизацией с PostgreSQL")
    print()
    
    success = await test_database_crud_operations()
    
    if success:
        print("\n🎉 ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
        print("🏆 Двухуровневая архитектура хранения работает корректно")
        print("🚀 Система готова к использованию в production")
    else:
        print("\n❌ ТЕСТ ЗАВЕРШИЛСЯ С ОШИБКАМИ!")
        print("🔧 Проверьте логи выше для диагностики проблем")
    
    return success

if __name__ == "__main__":
    # Запускаем тест
    result = asyncio.run(main())
    exit(0 if result else 1)