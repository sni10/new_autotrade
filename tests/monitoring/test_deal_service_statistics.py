#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправления метода get_statistics() в DealService
"""
import sys
import os
import logging

# Добавляем путь к src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def test_deal_service_statistics():
    """Тест метода get_statistics() в DealService"""
    print("🧪 Тестирование метода get_statistics() в DealService...")
    
    try:
        from domain.services.deals.deal_service import DealService
        
        # Создаем мок-объекты для тестирования
        class MockDealsRepo:
            def get_all(self):
                # Возвращаем пустой список для теста
                return []
            
            def get_open_deals(self):
                return []
        
        # Создаем DealService с мок-объектами
        deal_service = DealService(
            deals_repo=MockDealsRepo(),
            order_service=None,
            deal_factory=None,
            exchange_connector=None
        )
        
        # Тестируем метод get_statistics()
        stats = deal_service.get_statistics()
        
        print(f"✅ Метод get_statistics() работает!")
        print(f"📊 Полученная статистика: {stats}")
        
        # Проверяем наличие обязательных ключей
        required_keys = ['total_deals', 'completed_deals']
        for key in required_keys:
            if key in stats:
                print(f"✅ Ключ '{key}': {stats[key]}")
            else:
                print(f"❌ Отсутствует ключ '{key}'")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования DealService.get_statistics(): {e}")
        return False

def test_system_stats_monitor_integration():
    """Тест интеграции с SystemStatsMonitor"""
    print("\n🧪 Тестирование интеграции с SystemStatsMonitor...")
    
    try:
        from domain.services.monitoring.system_stats_monitor import SystemStatsMonitor
        from domain.services.deals.deal_service import DealService
        from domain.services.orders.order_service import OrderService
        
        # Создаем мок-объекты
        class MockDealsRepo:
            def get_all(self):
                return []
            def get_open_deals(self):
                return []
        
        class MockOrdersRepo:
            def get_all(self):
                return []
            def get_open_orders(self):
                return []
        
        # Создаем сервисы
        deal_service = DealService(
            deals_repo=MockDealsRepo(),
            order_service=None,
            deal_factory=None,
            exchange_connector=None
        )
        
        order_service = OrderService(
            orders_repo=MockOrdersRepo(),
            order_factory=None,
            exchange_connector=None
        )
        
        # Создаем SystemStatsMonitor
        stats_monitor = SystemStatsMonitor(
            order_service=order_service,
            deal_service=deal_service,
            stats_interval_seconds=60
        )
        
        print("✅ SystemStatsMonitor создан успешно")
        
        # Тестируем метод _log_deals_statistics напрямую
        import asyncio
        
        async def test_deals_stats():
            try:
                await stats_monitor._log_deals_statistics()
                print("✅ Метод _log_deals_statistics() выполнен без ошибок")
                return True
            except Exception as e:
                print(f"❌ Ошибка в _log_deals_statistics(): {e}")
                return False
        
        # Запускаем асинхронный тест
        result = asyncio.run(test_deals_stats())
        return result
        
    except Exception as e:
        print(f"❌ Ошибка тестирования интеграции: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("=" * 80)
    print("🚀 ТЕСТ ИСПРАВЛЕНИЯ DealService.get_statistics()")
    print("=" * 80)
    
    tests = [
        ("Метод get_statistics() в DealService", test_deal_service_statistics),
        ("Интеграция с SystemStatsMonitor", test_system_stats_monitor_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                print(f"✅ {test_name}: ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name}: ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name}: ОШИБКА - {e}")
    
    print("\n" + "=" * 80)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Ошибка 'DealService' object has no attribute 'get_statistics' исправлена")
        print("✅ SystemStatsMonitor теперь может получать статистику сделок")
        print("✅ Система мониторинга работает корректно")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ С ТЕСТАМИ!")
        print("❌ Требуется дополнительная отладка")
    
    print("=" * 80)

if __name__ == "__main__":
    main()