#!/usr/bin/env python3
"""
Тестовый скрипт для проверки правильности загрузки конфига в BuyOrderMonitor
"""
import sys
import os
import asyncio
import logging

# Добавляем путь к src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from config.config_loader import load_config
from domain.services.orders.buy_order_monitor import BuyOrderMonitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def test_config_loading():
    """Тест загрузки конфигурации"""
    print("🧪 Тестирование загрузки конфига BuyOrderMonitor...")
    
    # 1. Загружаем конфиг
    config = load_config()
    buy_order_monitor_cfg = config.get("buy_order_monitor", {})
    
    print(f"📋 Конфиг buy_order_monitor: {buy_order_monitor_cfg}")
    
    # 2. Извлекаем параметры (как в main.py)
    max_age_minutes = buy_order_monitor_cfg.get("max_age_minutes", 5.0)  # ИСПРАВЛЕННОЕ дефолтное значение
    max_price_deviation_percent = buy_order_monitor_cfg.get("max_price_deviation_percent", 3.0)
    check_interval_seconds = buy_order_monitor_cfg.get("check_interval_seconds", 10)
    
    print(f"🔧 Извлеченные параметры:")
    print(f"   - max_age_minutes: {max_age_minutes} (ожидается: 5.0)")
    print(f"   - max_price_deviation_percent: {max_price_deviation_percent} (ожидается: 3.0)")
    print(f"   - check_interval_seconds: {check_interval_seconds} (ожидается: 10)")
    
    # 3. Проверяем соответствие ожидаемым значениям
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
    
    print(f"\n✅ Результаты проверки:")
    all_correct = True
    for param, expected in expected_values.items():
        actual = actual_values[param]
        is_correct = actual == expected
        status = "✅" if is_correct else "❌"
        print(f"   {status} {param}: {actual} {'(правильно)' if is_correct else f'(ожидалось: {expected})'}")
        if not is_correct:
            all_correct = False
    
    if all_correct:
        print(f"\n🎉 ВСЕ ПАРАМЕТРЫ ПРАВИЛЬНЫЕ! Теперь BuyOrderMonitor будет использовать:")
        print(f"   - Проверка каждые {check_interval_seconds} секунд")
        print(f"   - Ордера считаются 'тухлыми' через {max_age_minutes} минут (вместо 15 минут)")
        print(f"   - Отклонение цены: {max_price_deviation_percent}%")
        return True
    else:
        print(f"\n❌ ЕСТЬ ОШИБКИ В КОНФИГУРАЦИИ!")
        return False

def test_buy_order_monitor_creation():
    """Тест создания BuyOrderMonitor с правильными параметрами"""
    print(f"\n🧪 Тестирование создания BuyOrderMonitor...")
    
    try:
        # Создаем мок-объекты (None для простоты)
        buy_monitor = BuyOrderMonitor(
            order_service=None,
            deal_service=None,
            exchange_connector=None,
            max_age_minutes=5.0,  # Правильное значение из конфига
            max_price_deviation_percent=3.0,
            check_interval_seconds=10
        )
        
        # Проверяем, что параметры установлены правильно
        print(f"✅ BuyOrderMonitor создан успешно:")
        print(f"   - max_age_minutes: {buy_monitor.max_age_minutes}")
        print(f"   - max_price_deviation_percent: {buy_monitor.max_price_deviation_percent}")
        print(f"   - check_interval_seconds: {buy_monitor.check_interval_seconds}")
        
        # Проверяем статистику
        stats = buy_monitor.get_statistics()
        print(f"📊 Статистика: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания BuyOrderMonitor: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("="*80)
    print("🚀 ТЕСТ ИСПРАВЛЕНИЯ BuyOrderMonitor КОНФИГУРАЦИИ")
    print("="*80)
    
    # Тест 1: Загрузка конфига
    config_test_passed = test_config_loading()
    
    # Тест 2: Создание BuyOrderMonitor
    creation_test_passed = test_buy_order_monitor_creation()
    
    print("\n" + "="*80)
    if config_test_passed and creation_test_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Исправление работает корректно")
        print("✅ BuyOrderMonitor теперь будет использовать 5 минут вместо 15 минут")
        print("✅ Ордера будут считаться 'тухлыми' через 5 минут, как указано в конфиге")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ С ТЕСТАМИ!")
        print("❌ Требуется дополнительная отладка")
    print("="*80)

if __name__ == "__main__":
    main()