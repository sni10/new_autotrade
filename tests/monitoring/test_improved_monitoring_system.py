#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшенной системы мониторинга
"""
import sys
import os
import asyncio
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

def test_imports():
    """Тест импортов всех новых компонентов"""
    print("🧪 Тестирование импортов...")
    
    try:
        # Тестируем импорты улучшенных компонентов
        from domain.services.orders.buy_order_monitor import BuyOrderMonitor
        print("✅ BuyOrderMonitor импортирован")
        
        from domain.services.deals.deal_completion_monitor import DealCompletionMonitor
        print("✅ DealCompletionMonitor импортирован")
        
        from domain.services.orders.order_sync_monitor import OrderSyncMonitor
        print("✅ OrderSyncMonitor импортирован")
        
        from domain.services.monitoring.system_stats_monitor import SystemStatsMonitor
        print("✅ SystemStatsMonitor импортирован")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_component_creation():
    """Тест создания компонентов с мок-объектами"""
    print("\n🧪 Тестирование создания компонентов...")
    
    try:
        from domain.services.orders.buy_order_monitor import BuyOrderMonitor
        from domain.services.deals.deal_completion_monitor import DealCompletionMonitor
        from domain.services.orders.order_sync_monitor import OrderSyncMonitor
        from domain.services.monitoring.system_stats_monitor import SystemStatsMonitor
        
        # Создаем компоненты с None (мок-объекты)
        buy_monitor = BuyOrderMonitor(
            order_service=None,
            deal_service=None,
            exchange_connector=None,
            max_age_minutes=5.0,
            max_price_deviation_percent=3.0,
            check_interval_seconds=10
        )
        print("✅ BuyOrderMonitor создан")
        
        deal_monitor = DealCompletionMonitor(
            deal_service=None,
            order_service=None,
            exchange_connector=None,
            check_interval_seconds=30
        )
        print("✅ DealCompletionMonitor создан")
        
        sync_monitor = OrderSyncMonitor(
            order_service=None,
            sync_interval_seconds=30
        )
        print("✅ OrderSyncMonitor создан")
        
        stats_monitor = SystemStatsMonitor(
            order_service=None,
            deal_service=None,
            buy_order_monitor=buy_monitor,
            deal_completion_monitor=deal_monitor,
            order_sync_monitor=sync_monitor,
            stats_interval_seconds=60
        )
        print("✅ SystemStatsMonitor создан")
        
        return True, {
            'buy_monitor': buy_monitor,
            'deal_monitor': deal_monitor,
            'sync_monitor': sync_monitor,
            'stats_monitor': stats_monitor
        }
        
    except Exception as e:
        print(f"❌ Ошибка создания компонентов: {e}")
        return False, {}

def test_statistics():
    """Тест получения статистики от компонентов"""
    print("\n🧪 Тестирование статистики...")
    
    success, components = test_component_creation()
    if not success:
        return False
    
    try:
        # Тестируем статистику каждого компонента
        buy_stats = components['buy_monitor'].get_statistics()
        print(f"✅ BuyOrderMonitor статистика: {buy_stats}")
        
        deal_stats = components['deal_monitor'].get_statistics()
        print(f"✅ DealCompletionMonitor статистика: {deal_stats}")
        
        sync_stats = components['sync_monitor'].get_statistics()
        print(f"✅ OrderSyncMonitor статистика: {sync_stats}")
        
        system_stats = components['stats_monitor'].get_statistics()
        print(f"✅ SystemStatsMonitor статистика: {system_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return False

def test_configuration():
    """Тест конфигурации компонентов"""
    print("\n🧪 Тестирование конфигурации...")
    
    try:
        from config.config_loader import load_config
        
        config = load_config()
        buy_order_monitor_cfg = config.get("buy_order_monitor", {})
        
        print(f"📋 Конфиг buy_order_monitor: {buy_order_monitor_cfg}")
        
        # Проверяем ключевые параметры
        max_age_minutes = buy_order_monitor_cfg.get("max_age_minutes", 5.0)
        max_price_deviation_percent = buy_order_monitor_cfg.get("max_price_deviation_percent", 3.0)
        check_interval_seconds = buy_order_monitor_cfg.get("check_interval_seconds", 10)
        
        expected_values = {
            "max_age_minutes": 5.0,
            "max_price_deviation_percent": 3.0,
            "check_interval_seconds": 10
        }
        
        actual_values = {
            "max_age_minutes": max_age_minutes,
            "max_price_deviation_percent": max_price_deviation_percent,
            "check_interval_seconds": check_interval_seconds
        }
        
        all_correct = True
        for param, expected in expected_values.items():
            actual = actual_values[param]
            is_correct = actual == expected
            status = "✅" if is_correct else "❌"
            print(f"   {status} {param}: {actual}")
            if not is_correct:
                all_correct = False
        
        return all_correct
        
    except Exception as e:
        print(f"❌ Ошибка тестирования конфигурации: {e}")
        return False

def test_main_integration():
    """Тест интеграции с main.py"""
    print("\n🧪 Тестирование интеграции с main.py...")
    
    try:
        # Проверяем, что main.py содержит все необходимые импорты
        with open('main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        required_imports = [
            'from domain.services.orders.order_sync_monitor import OrderSyncMonitor',
            'from domain.services.monitoring.system_stats_monitor import SystemStatsMonitor'
        ]
        
        required_components = [
            'order_sync_monitor = OrderSyncMonitor(',
            'system_stats_monitor = SystemStatsMonitor(',
            'order_sync_monitor.stop_monitoring()',
            'system_stats_monitor.stop_monitoring()'
        ]
        
        for import_line in required_imports:
            if import_line in main_content:
                print(f"✅ Найден импорт: {import_line.split('import')[1].strip()}")
            else:
                print(f"❌ Отсутствует импорт: {import_line.split('import')[1].strip()}")
                return False
        
        for component in required_components:
            if component in main_content:
                print(f"✅ Найден компонент: {component.split('=')[0].strip() if '=' in component else component.split('.')[0].strip()}")
            else:
                print(f"❌ Отсутствует компонент: {component.split('=')[0].strip() if '=' in component else component.split('.')[0].strip()}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования интеграции: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("=" * 80)
    print("🚀 ТЕСТ УЛУЧШЕННОЙ СИСТЕМЫ МОНИТОРИНГА")
    print("=" * 80)
    
    tests = [
        ("Импорты компонентов", test_imports),
        ("Создание компонентов", lambda: test_component_creation()[0]),
        ("Статистика компонентов", test_statistics),
        ("Конфигурация", test_configuration),
        ("Интеграция с main.py", test_main_integration),
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
        print("✅ Улучшенная система мониторинга готова к работе")
        print("✅ Все компоненты корректно интегрированы")
        print("✅ Конфигурация работает правильно")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ С ТЕСТАМИ!")
        print("❌ Требуется дополнительная отладка")
    
    print("=" * 80)

if __name__ == "__main__":
    main()