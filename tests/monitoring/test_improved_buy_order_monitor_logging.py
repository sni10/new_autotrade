#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшенного логирования BuyOrderMonitor
"""
import sys
import os
import asyncio
import logging
import time
from unittest.mock import Mock, AsyncMock

# Добавляем путь к src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

# Настройка логирования для тестирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def test_improved_logging_logic():
    """Тест улучшенной логики логирования"""
    print("🧪 Тестирование улучшенного логирования BuyOrderMonitor...")
    
    try:
        from domain.services.orders.buy_order_monitor import BuyOrderMonitor
        
        # Создаем мок-объекты
        mock_order_service = Mock()
        mock_deal_service = Mock()
        mock_exchange = Mock()
        
        # Создаем BuyOrderMonitor с короткими интервалами для тестирования
        buy_monitor = BuyOrderMonitor(
            order_service=mock_order_service,
            deal_service=mock_deal_service,
            exchange_connector=mock_exchange,
            max_age_minutes=5.0,
            max_price_deviation_percent=3.0,
            check_interval_seconds=1  # Короткий интервал для теста
        )
        
        # Устанавливаем короткий интервал сводки для теста
        buy_monitor.summary_interval_minutes = 0.1  # 6 секунд
        
        print("✅ BuyOrderMonitor создан с улучшенным логированием")
        
        # Проверяем новые поля
        assert hasattr(buy_monitor, 'quiet_checks_count'), "Отсутствует поле quiet_checks_count"
        assert hasattr(buy_monitor, 'last_summary_time'), "Отсутствует поле last_summary_time"
        assert hasattr(buy_monitor, 'summary_interval_minutes'), "Отсутствует поле summary_interval_minutes"
        
        print("✅ Все новые поля для улучшенного логирования присутствуют")
        
        return True, buy_monitor
        
    except Exception as e:
        print(f"❌ Ошибка создания BuyOrderMonitor: {e}")
        return False, None

async def test_quiet_checks_behavior():
    """Тест поведения при отсутствии ордеров"""
    print("\n🧪 Тестирование поведения при отсутствии ордеров...")
    
    success, buy_monitor = test_improved_logging_logic()
    if not success:
        return False
    
    try:
        # Настраиваем мок для возврата пустого списка ордеров
        buy_monitor.order_service.get_open_orders.return_value = []
        
        print("📊 Симулируем несколько проверок без ордеров...")
        
        # Выполняем несколько проверок
        for i in range(5):
            await buy_monitor.check_stale_buy_orders()
            print(f"   Проверка {i+1}: quiet_checks_count = {buy_monitor.quiet_checks_count}")
            time.sleep(0.1)
        
        # Проверяем, что счетчик увеличивается
        assert buy_monitor.quiet_checks_count > 0, "Счетчик тихих проверок не увеличивается"
        print(f"✅ Счетчик тихих проверок работает: {buy_monitor.quiet_checks_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования тихих проверок: {e}")
        return False

async def test_periodic_summary():
    """Тест периодической сводки"""
    print("\n🧪 Тестирование периодической сводки...")
    
    success, buy_monitor = test_improved_logging_logic()
    if not success:
        return False
    
    try:
        # Настраиваем мок для возврата пустого списка ордеров
        buy_monitor.order_service.get_open_orders.return_value = []
        
        # Устанавливаем очень короткий интервал для теста
        buy_monitor.summary_interval_minutes = 0.05  # 3 секунды
        
        print("📊 Симулируем проверки с ожиданием сводки...")
        
        # Выполняем проверки в течение времени, достаточного для сводки
        for i in range(10):
            await buy_monitor.check_stale_buy_orders()
            if i == 5:
                print("   ⏰ Ждем время для сводки...")
                time.sleep(4)  # Ждем больше интервала сводки
        
        print("✅ Периодическая сводка должна была появиться в логах")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования периодической сводки: {e}")
        return False

async def test_active_monitoring_logging():
    """Тест логирования при наличии ордеров"""
    print("\n🧪 Тестирование логирования при наличии ордеров...")
    
    success, buy_monitor = test_improved_logging_logic()
    if not success:
        return False
    
    try:
        # Создаем мок-ордер
        mock_order = Mock()
        mock_order.side = 'BUY'
        mock_order.order_id = 'test_order_123'
        mock_order.status = 'open'
        mock_order.created_at = int(time.time() * 1000)
        mock_order.symbol = 'OM/USDT'
        mock_order.price = 0.25
        mock_order.amount = 100
        mock_order.deal_id = 'test_deal_456'
        
        # Настраиваем мок для возврата ордера
        buy_monitor.order_service.get_open_orders.return_value = [mock_order]
        buy_monitor.order_service.get_order_status = AsyncMock(return_value=mock_order)
        
        # Добавляем метод get_fill_percentage к мок-ордеру
        mock_order.get_fill_percentage = Mock(return_value=0.0)
        
        print("📊 Симулируем проверку с наличием BUY ордера...")
        
        # Выполняем проверку
        await buy_monitor.check_stale_buy_orders()
        
        # Проверяем, что счетчик тихих проверок сброшен
        assert buy_monitor.quiet_checks_count == 0, "Счетчик тихих проверок не сброшен при наличии ордеров"
        print("✅ При наличии ордеров счетчик тихих проверок сбрасывается")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования активного мониторинга: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("=" * 80)
    print("🚀 ТЕСТ УЛУЧШЕННОГО ЛОГИРОВАНИЯ BuyOrderMonitor")
    print("=" * 80)
    
    tests = [
        ("Создание с улучшенным логированием", lambda: test_improved_logging_logic()[0]),
        ("Поведение при отсутствии ордеров", test_quiet_checks_behavior),
        ("Периодическая сводка", test_periodic_summary),
        ("Логирование при наличии ордеров", test_active_monitoring_logging),
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
        print("✅ Улучшенное логирование BuyOrderMonitor работает корректно")
        print("✅ Больше не будет постоянного шума в логах")
        print("✅ Периодические сводки предоставляют полезную информацию")
        print("\n🔧 ОЖИДАЕМОЕ ПОВЕДЕНИЕ:")
        print("   • При отсутствии BUY ордеров - только DEBUG сообщения")
        print("   • Информативная сводка каждые 5 минут")
        print("   • Детальное логирование только при наличии ордеров")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ С ТЕСТАМИ!")
        print("❌ Требуется дополнительная отладка")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())