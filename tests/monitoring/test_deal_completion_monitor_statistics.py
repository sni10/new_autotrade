#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений статистики DealCompletionMonitor
"""
import sys
import os
import asyncio
import logging
from unittest.mock import Mock, AsyncMock

# Добавляем путь к src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG для диагностических сообщений
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def test_statistics_initialization():
    """Тест правильной инициализации статистики"""
    print("🧪 Тестирование инициализации статистики...")
    
    try:
        from domain.services.deals.deal_completion_monitor import DealCompletionMonitor
        
        # Создаем мок-объекты
        mock_deal_service = Mock()
        mock_order_service = Mock()
        mock_exchange_connector = Mock()
        
        # Создаем DealCompletionMonitor
        monitor = DealCompletionMonitor(
            deal_service=mock_deal_service,
            order_service=mock_order_service,
            exchange_connector=mock_exchange_connector,
            check_interval_seconds=30
        )
        
        # Проверяем начальную статистику
        stats = monitor.get_statistics()
        expected_keys = [
            "checks_performed", "deals_monitored", "deals_completed", 
            "sell_orders_placed", "sync_operations"
        ]
        
        print(f"📊 Начальная статистика: {stats}")
        
        for key in expected_keys:
            if key not in stats:
                print(f"❌ Отсутствует ключ '{key}' в статистике")
                return False
            if stats[key] != 0:
                print(f"❌ Ключ '{key}' должен быть 0, но равен {stats[key]}")
                return False
        
        print("✅ Все ключи статистики инициализированы правильно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False

async def test_statistics_counting():
    """Тест правильности подсчета статистики"""
    print("\n🧪 Тестирование подсчета статистики...")
    
    try:
        from domain.services.deals.deal_completion_monitor import DealCompletionMonitor
        
        # Создаем мок-объекты
        mock_deal_service = Mock()
        mock_order_service = Mock()
        mock_exchange_connector = Mock()
        
        # Создаем мок-сделки
        mock_deal1 = Mock()
        mock_deal1.deal_id = "deal_001"
        mock_deal2 = Mock()
        mock_deal2.deal_id = "deal_002"
        mock_deal3 = Mock()
        mock_deal3.deal_id = "deal_003"
        
        # Настраиваем мок для возврата 3 открытых сделок
        mock_deal_service.get_open_deals.return_value = [mock_deal1, mock_deal2, mock_deal3]
        
        # Настраиваем мок для orders_repo
        mock_order_service.orders_repo = Mock()
        mock_order_service.orders_repo.get_orders_by_deal.return_value = []  # Пустой список для простоты
        
        # Создаем DealCompletionMonitor
        monitor = DealCompletionMonitor(
            deal_service=mock_deal_service,
            order_service=mock_order_service,
            exchange_connector=mock_exchange_connector,
            check_interval_seconds=30
        )
        
        # Выполняем несколько проверок
        for i in range(5):
            await monitor.check_deals_completion()
        
        # Проверяем статистику
        stats = monitor.get_statistics()
        print(f"📊 Статистика после 5 проверок: {stats}")
        
        # Проверяем правильность подсчета
        if stats["checks_performed"] != 5:
            print(f"❌ checks_performed должно быть 5, но равно {stats['checks_performed']}")
            return False
        
        if stats["deals_monitored"] != 3:
            print(f"❌ deals_monitored должно быть 3, но равно {stats['deals_monitored']}")
            return False
        
        if "max_deals_monitored" not in stats:
            print("❌ Отсутствует ключ 'max_deals_monitored'")
            return False
        
        if stats["max_deals_monitored"] != 3:
            print(f"❌ max_deals_monitored должно быть 3, но равно {stats['max_deals_monitored']}")
            return False
        
        print("✅ Статистика подсчитывается правильно")
        print(f"   - Проверок выполнено: {stats['checks_performed']}")
        print(f"   - Сделок отслеживается: {stats['deals_monitored']}")
        print(f"   - Максимум сделок одновременно: {stats['max_deals_monitored']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования подсчета: {e}")
        return False

async def test_sell_orders_placement_counting():
    """Тест подсчета размещенных SELL ордеров"""
    print("\n🧪 Тестирование подсчета размещенных SELL ордеров...")
    
    try:
        from domain.services.deals.deal_completion_monitor import DealCompletionMonitor
        
        # Создаем мок-объекты
        mock_deal_service = Mock()
        mock_order_service = Mock()
        mock_exchange_connector = Mock()
        
        # Создаем мок-сделку
        mock_deal = Mock()
        mock_deal.deal_id = "deal_001"
        
        # Создаем мок-ордера
        mock_buy_order = Mock()
        mock_buy_order.side = "BUY"
        mock_buy_order.order_id = "buy_001"
        mock_buy_order.status = "filled"
        mock_buy_order.is_filled.return_value = True  # BUY ордер исполнен
        mock_buy_order.get_fill_percentage.return_value = 1.0  # 100% заполнен
        
        mock_sell_order = Mock()
        mock_sell_order.side = "SELL"
        mock_sell_order.order_id = "sell_001"
        mock_sell_order.status = "PENDING"  # SELL ордер в статусе PENDING
        mock_sell_order.exchange_id = None  # Не размещен на бирже
        mock_sell_order.is_filled.return_value = False
        mock_sell_order.get_fill_percentage.return_value = 0.0  # 0% заполнен
        
        # Настраиваем моки
        mock_deal_service.get_open_deals.return_value = [mock_deal]
        mock_order_service.orders_repo = Mock()
        mock_order_service.orders_repo.get_orders_by_deal.return_value = [mock_buy_order, mock_sell_order]
        
        # Настраиваем get_order_status
        mock_order_service.get_order_status = AsyncMock()
        mock_order_service.get_order_status.side_effect = lambda order: order  # Возвращаем тот же ордер
        
        # Настраиваем успешное размещение SELL ордера
        mock_result = Mock()
        mock_result.success = True
        mock_order_service.place_existing_order = AsyncMock(return_value=mock_result)
        
        # Создаем DealCompletionMonitor
        monitor = DealCompletionMonitor(
            deal_service=mock_deal_service,
            order_service=mock_order_service,
            exchange_connector=mock_exchange_connector,
            check_interval_seconds=30
        )
        
        # Выполняем проверку
        await monitor.check_deals_completion()
        
        # Проверяем статистику
        stats = monitor.get_statistics()
        print(f"📊 Статистика после размещения SELL ордера: {stats}")
        
        if stats["sell_orders_placed"] != 1:
            print(f"❌ sell_orders_placed должно быть 1, но равно {stats['sell_orders_placed']}")
            return False
        
        print("✅ Подсчет размещенных SELL ордеров работает правильно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования размещения SELL ордеров: {e}")
        return False

async def test_diagnostic_logging():
    """Тест диагностического логирования"""
    print("\n🧪 Тестирование диагностического логирования...")
    
    try:
        from domain.services.deals.deal_completion_monitor import DealCompletionMonitor
        
        # Создаем мок-объекты
        mock_deal_service = Mock()
        mock_order_service = Mock()
        mock_exchange_connector = Mock()
        
        # Создаем мок-сделку
        mock_deal = Mock()
        mock_deal.deal_id = "deal_001"
        
        # Создаем мок-ордера (оба НЕ исполнены)
        mock_buy_order = Mock()
        mock_buy_order.side = "BUY"
        mock_buy_order.order_id = "buy_001"
        mock_buy_order.status = "open"
        mock_buy_order.is_filled.return_value = False  # НЕ исполнен
        mock_buy_order.filled = 0.5
        
        mock_sell_order = Mock()
        mock_sell_order.side = "SELL"
        mock_sell_order.order_id = "sell_001"
        mock_sell_order.status = "open"
        mock_sell_order.exchange_id = "exchange_123"
        mock_sell_order.is_filled.return_value = False  # НЕ исполнен
        mock_sell_order.filled = 0.3
        
        # Настраиваем моки
        mock_deal_service.get_open_deals.return_value = [mock_deal]
        mock_order_service.orders_repo = Mock()
        mock_order_service.orders_repo.get_orders_by_deal.return_value = [mock_buy_order, mock_sell_order]
        
        # Настраиваем get_order_status
        mock_order_service.get_order_status = AsyncMock()
        mock_order_service.get_order_status.side_effect = lambda order: order
        
        # Добавляем get_fill_percentage
        mock_buy_order.get_fill_percentage.return_value = 0.5
        mock_sell_order.get_fill_percentage.return_value = 0.3
        
        # Создаем DealCompletionMonitor
        monitor = DealCompletionMonitor(
            deal_service=mock_deal_service,
            order_service=mock_order_service,
            exchange_connector=mock_exchange_connector,
            check_interval_seconds=30
        )
        
        print("📊 Выполняем проверку с неисполненными ордерами (должны появиться DEBUG сообщения)...")
        
        # Выполняем проверку
        await monitor.check_deals_completion()
        
        print("✅ Диагностическое логирование должно было появиться в логах выше")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования диагностики: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("=" * 80)
    print("🚀 ТЕСТ ИСПРАВЛЕНИЙ СТАТИСТИКИ DealCompletionMonitor")
    print("=" * 80)
    
    tests = [
        ("Инициализация статистики", test_statistics_initialization),
        ("Подсчет статистики", test_statistics_counting),
        ("Подсчет размещенных SELL ордеров", test_sell_orders_placement_counting),
        ("Диагностическое логирование", test_diagnostic_logging),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            if result:
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
        print("✅ Исправления статистики DealCompletionMonitor работают корректно")
        print("✅ Добавлена диагностика для понимания проблем с завершением сделок")
        print("✅ Статистика теперь считается правильно")
        print("\n🔧 ОЖИДАЕМЫЕ УЛУЧШЕНИЯ:")
        print("   • Правильный подсчет deals_monitored (текущее количество)")
        print("   • Добавлен max_deals_monitored (максимум одновременно)")
        print("   • Исправлен подсчет sell_orders_placed")
        print("   • Добавлена диагностика незавершенных сделок")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ С ТЕСТАМИ!")
        print("❌ Требуется дополнительная отладка")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())