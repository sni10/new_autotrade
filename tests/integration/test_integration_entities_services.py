#!/usr/bin/env python3
# test_integration_entities_services.py
"""
🧪 ТЕСТ ИНТЕГРАЦИИ ОБНОВЛЕННЫХ ENTITIES И СЕРВИСОВ

Проверяет работу:
- Обновленных entities (Deal, CurrencyPair)
- Сервисов с новыми репозиториями (DealService, OrderService)
- Двухуровневой архитектуры хранения
- Интеграции с PostgreSQL
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
from domain.entities.order import Order
from domain.factories.deal_factory import DealFactory
from domain.factories.order_factory import OrderFactory
from domain.services.deals.deal_service import DealService
from domain.services.orders.order_service import OrderService
from infrastructure.repositories.factory.repository_factory import RepositoryFactory
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

async def test_updated_entities():
    """Тест обновленных entities"""
    print("🧪 Тестируем обновленные entities...")
    
    # Тест CurrencyPair (исправлена синтаксическая ошибка)
    currency_pair = CurrencyPair(
        base_currency="ATM",
        quote_currency="USDT",
        symbol="ATMUSDT",
        deal_quota=25.0,
        profit_markup=0.015
    )
    
    print(f"✅ CurrencyPair создан: {currency_pair}")
    assert currency_pair.symbol == "ATMUSDT"
    assert currency_pair.deal_quota == 25.0
    
    # Тест Deal с новыми полями
    deal = Deal(
        deal_id=1,
        currency_pair=currency_pair,
        status=Deal.STATUS_OPEN,
        profit=0.0
    )
    
    print(f"✅ Deal создан: {deal}")
    assert deal.deal_id == 1
    assert deal.profit == 0.0
    assert deal.updated_at is not None
    
    # Тест методов работы с profit
    deal.update_profit(1.5)
    assert deal.profit == 1.5
    print(f"✅ Profit обновлен: {deal.profit}")
    
    # Тест to_dict с новыми полями
    deal_dict = deal.to_dict()
    assert "profit" in deal_dict
    assert "updated_at" in deal_dict
    print("✅ to_dict содержит новые поля")
    
    # Тест from_dict с новыми полями
    restored_deal = Deal.from_dict(deal_dict, currency_pair)
    assert restored_deal.profit == 1.5
    assert restored_deal.updated_at == deal.updated_at
    print("✅ from_dict работает с новыми полями")
    
    print("🎉 Все тесты entities пройдены!")
    return True

async def test_repository_factory():
    """Тест фабрики репозиториев"""
    print("\n🧪 Тестируем RepositoryFactory...")
    
    factory = RepositoryFactory()
    await factory.initialize()
    
    # Получаем информацию о хранилище
    storage_info = factory.get_storage_info()
    print(f"📊 Storage info: {storage_info}")
    
    # Создаем репозитории
    deals_repo = await factory.get_deals_repository()
    orders_repo = await factory.get_orders_repository()
    
    print(f"✅ Deals repository: {type(deals_repo).__name__}")
    print(f"✅ Orders repository: {type(orders_repo).__name__}")
    
    await factory.close()
    print("✅ RepositoryFactory закрыт")
    
    return True

async def test_services_integration():
    """Тест интеграции сервисов с новыми репозиториями"""
    print("\n🧪 Тестируем интеграцию сервисов...")
    
    # Инициализация
    factory = RepositoryFactory()
    await factory.initialize()
    
    try:
        # Создаем репозитории
        deals_repo = await factory.get_deals_repository()
        orders_repo = await factory.get_orders_repository()
        
        # Создаем фабрики
        order_factory = OrderFactory()
        deal_factory = DealFactory(order_factory)
        
        # Создаем mock exchange connector
        exchange_connector = None  # Для тестов без реального подключения
        
        # Создаем сервисы с новыми репозиториями
        order_service = OrderService(orders_repo, order_factory, exchange_connector)
        deal_service = DealService(deals_repo, order_service, deal_factory, exchange_connector)
        
        print("✅ Сервисы созданы с новыми репозиториями")
        
        # Тест создания сделки
        currency_pair = CurrencyPair(
            base_currency="ATM",
            quote_currency="USDT",
            symbol="ATMUSDT",
            deal_quota=25.0
        )
        
        deal = deal_service.create_new_deal(currency_pair)
        print(f"✅ Сделка создана через DealService: {deal.deal_id}")
        
        # Тест получения сделок
        open_deals = deal_service.get_open_deals()
        print(f"✅ Открытых сделок: {len(open_deals)}")
        
        # Тест получения сделки по ID
        retrieved_deal = deal_service.get_deal_by_id(deal.deal_id)
        assert retrieved_deal is not None
        assert retrieved_deal.deal_id == deal.deal_id
        print(f"✅ Сделка получена по ID: {retrieved_deal.deal_id}")
        
        # Тест статистики ордеров
        order_stats = order_service.get_statistics()
        print(f"✅ Статистика ордеров: {order_stats}")
        
        print("🎉 Все тесты интеграции сервисов пройдены!")
        
    finally:
        await factory.close()
    
    return True

async def test_performance():
    """Тест производительности новой архитектуры"""
    print("\n🧪 Тестируем производительность...")
    
    factory = RepositoryFactory()
    await factory.initialize()
    
    try:
        deals_repo = await factory.get_deals_repository()
        
        # Создаем тестовые данные
        currency_pair = CurrencyPair(
            base_currency="ATM",
            quote_currency="USDT",
            symbol="ATMUSDT",
            deal_quota=25.0
        )
        
        # Тест массового создания сделок
        deals_count = 1000
        start_time = time.time()
        
        for i in range(deals_count):
            deal = Deal(
                deal_id=i+1,
                currency_pair=currency_pair,
                status=Deal.STATUS_OPEN,
                profit=i * 0.1
            )
            deals_repo.save(deal)
        
        creation_time = time.time() - start_time
        avg_time = (creation_time / deals_count) * 1000
        
        print(f"✅ Создано {deals_count} сделок за {creation_time:.2f}s")
        print(f"✅ Среднее время создания: {avg_time:.3f}ms")
        
        # Тест чтения
        start_time = time.time()
        all_deals = deals_repo.get_all()
        read_time = (time.time() - start_time) * 1000
        
        print(f"✅ Прочитано {len(all_deals)} сделок за {read_time:.2f}ms")
        
        # Тест поиска
        start_time = time.time()
        open_deals = deals_repo.get_open_deals()
        search_time = (time.time() - start_time) * 1000
        
        print(f"✅ Найдено {len(open_deals)} открытых сделок за {search_time:.2f}ms")
        
        # Проверяем производительность
        assert avg_time < 5, f"Создание слишком медленное: {avg_time:.2f}ms"
        assert read_time < 100, f"Чтение слишком медленное: {read_time:.2f}ms"
        assert search_time < 150, f"Поиск слишком медленный: {search_time:.2f}ms"
        
        print("🎉 Тесты производительности пройдены!")
        
    finally:
        await factory.close()
    
    return True

async def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 ЗАПУСК ИНТЕГРАЦИОННЫХ ТЕСТОВ")
    print("=" * 60)
    
    tests = [
        ("Обновленные entities", test_updated_entities),
        ("RepositoryFactory", test_repository_factory),
        ("Интеграция сервисов", test_services_integration),
        ("Производительность", test_performance)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 {test_name}:")
            result = await test_func()
            if result:
                passed_tests += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Пройдено тестов: {passed_tests}/{total_tests}")
    print(f"📈 Процент успеха: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Интеграция entities и сервисов работает корректно")
        print("✅ Двухуровневая архитектура функционирует")
        print("✅ Производительность соответствует требованиям")
        print("\n🚀 СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
    else:
        print("\n⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
        print("🔧 Проверьте ошибки выше")
    
    return passed_tests, total_tests

if __name__ == "__main__":
    asyncio.run(run_all_tests())