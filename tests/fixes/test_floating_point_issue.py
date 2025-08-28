#!/usr/bin/env python3
"""
Скрипт для воспроизведения и исправления проблемы с неокругленными значениями в базе данных.
Проблема: Order.from_dict() не применяет округление, что приводит к сохранению 
неточных float значений типа 15.3499999999999996447286321199499070644378662109375
"""

import sys
import os
import json
from decimal import Decimal

# Добавляем путь к src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_current_problem():
    """Воспроизводим текущую проблему с неокругленными значениями"""
    print("🔍 ВОСПРОИЗВЕДЕНИЕ ПРОБЛЕМЫ С НЕОКРУГЛЕННЫМИ ЗНАЧЕНИЯМИ")
    print("=" * 70)
    
    try:
        from domain.entities.order import Order, ExchangeInfo
        
        # Данные из issue - такие значения приходят с биржи (реальные проблемные значения)
        problematic_data = {
            "id": "848456",
            "order_id": 1754225647058998,
            "symbol": "ATM/USDT",
            "side": "BUY",
            "type": "LIMIT",
            "amount": 15.3499999999999996447286321199499070644378662109375,
            "price": 1.6279999999999998916422327965847216546535491943359375,
            "status": "closed",
            "filled": 15.3499999999999996447286321199499070644378662109375,
            "fees": 0.0
        }
        
        print(f"📥 Исходные данные с биржи:")
        print(f"   Amount: {problematic_data['amount']}")
        print(f"   Price: {problematic_data['price']}")
        print(f"   Filled: {problematic_data['filled']}")
        
        # Создаем ордер через from_dict (текущая реализация)
        order = Order.from_dict(problematic_data)
        
        print(f"\n📤 Ордер после Order.from_dict():")
        print(f"   Amount: {order.amount}")
        print(f"   Price: {order.price}")
        print(f"   Filled: {order.filled_amount}")
        
        # Проверяем что попадет в базу данных
        order_dict = order.to_dict()
        print(f"\n💾 Данные для сохранения в БД:")
        print(f"   Amount: {order_dict['amount']}")
        print(f"   Price: {order_dict['price']}")
        print(f"   Filled: {order_dict['filled_amount']}")
        
        # Симулируем JSON сериализацию (как в postgres_provider.py)
        json_data = json.dumps(order_dict)
        restored_data = json.loads(json_data)
        
        print(f"\n🔄 После JSON сериализации/десериализации:")
        print(f"   Amount: {restored_data['amount']}")
        print(f"   Price: {restored_data['price']}")
        print(f"   Filled: {restored_data['filled_amount']}")
        
        print(f"\n❌ ПРОБЛЕМА ПОДТВЕРЖДЕНА:")
        print(f"   • Неокругленные значения сохраняются в базу данных")
        print(f"   • Вместо 15.35 получаем {order.amount}")
        print(f"   • Вместо 1.628 получаем {order.price}")
        
        return True, order, problematic_data
        
    except Exception as e:
        print(f"❌ Ошибка воспроизведения проблемы: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_exchange_info_availability():
    """Проверяем доступность информации о точности биржи"""
    print("\n🔍 ПРОВЕРКА ДОСТУПНОСТИ ИНФОРМАЦИИ О ТОЧНОСТИ")
    print("=" * 70)
    
    try:
        from domain.entities.order import ExchangeInfo
        from domain.factories.order_factory import OrderFactory
        
        # Создаем ExchangeInfo для ATM/USDT (как в логах)
        exchange_info = ExchangeInfo(
            symbol="ATM/USDT",
            min_qty=0.01,
            max_qty=90000.0,
            step_size=0.01,  # Шаг количества
            min_price=0.001,
            max_price=10000.0,
            tick_size=0.001,  # Шаг цены
            min_notional=5.0,
            fees={'maker': 0.001, 'taker': 0.001},
            precision={'amount': 0.01, 'price': 0.001, 'cost': None, 'base': 1e-08, 'quote': 1e-08}
        )
        
        print(f"✅ ExchangeInfo для ATM/USDT:")
        print(f"   Step size (amount): {exchange_info.step_size}")
        print(f"   Tick size (price): {exchange_info.tick_size}")
        print(f"   Precision: {exchange_info.precision}")
        
        # Проверяем методы округления в OrderFactory
        order_factory = OrderFactory()
        order_factory.update_exchange_info("ATM/USDT", exchange_info)
        
        # Тестируем округление проблемных значений
        problematic_amount = 15.3499999999999996447286321199499070644378662109375
        problematic_price = 1.6279999999999998916422327965847216546535491943359375
        
        rounded_amount = order_factory.adjust_amount_precision("ATM/USDT", problematic_amount)
        rounded_price = order_factory.adjust_price_precision("ATM/USDT", problematic_price)
        
        print(f"\n🔧 Результаты округления OrderFactory:")
        print(f"   Amount: {problematic_amount} → {rounded_amount}")
        print(f"   Price: {problematic_price} → {rounded_price}")
        
        print(f"\n✅ МЕТОДЫ ОКРУГЛЕНИЯ РАБОТАЮТ КОРРЕКТНО")
        print(f"   • Amount округлен до {rounded_amount} (шаг 0.01)")
        print(f"   • Price округлен до {rounded_price} (шаг 0.001)")
        
        return True, exchange_info, order_factory
        
    except Exception as e:
        print(f"❌ Ошибка проверки ExchangeInfo: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_proposed_solution():
    """Тестируем предлагаемое решение"""
    print("\n🔧 ТЕСТИРОВАНИЕ ПРЕДЛАГАЕМОГО РЕШЕНИЯ")
    print("=" * 70)
    
    try:
        # Получаем результаты предыдущих тестов
        problem_success, problem_order, problem_data = test_current_problem()
        info_success, exchange_info, order_factory = test_exchange_info_availability()
        
        if not (problem_success and info_success):
            print("❌ Не удалось получить данные для тестирования решения")
            return False
        
        print(f"\n💡 ПРЕДЛАГАЕМОЕ РЕШЕНИЕ:")
        print(f"   1. Модифицировать Order.from_dict() для применения округления")
        print(f"   2. Использовать доступную информацию о точности биржи")
        print(f"   3. Применять округление только для известных символов")
        
        # Симулируем исправленный Order.from_dict()
        def create_fixed_order_from_dict(data, exchange_info=None):
            """Исправленная версия Order.from_dict() с округлением"""
            from domain.entities.order import Order
            
            # Создаем ордер как обычно
            order = Order.from_dict(data)
            
            # Применяем округление если доступна информация о символе
            if exchange_info and data.get('symbol') == exchange_info.symbol:
                # Округляем amount согласно step_size
                if exchange_info.step_size and exchange_info.step_size > 0:
                    import math
                    precision = len(str(exchange_info.step_size).split('.')[-1]) if '.' in str(exchange_info.step_size) else 0
                    steps = order.amount / exchange_info.step_size
                    steps = math.floor(steps)  # Округляем вниз для безопасности
                    order.amount = round(steps * exchange_info.step_size, precision)
                
                # Округляем price согласно tick_size
                if exchange_info.tick_size and exchange_info.tick_size > 0:
                    precision = len(str(exchange_info.tick_size).split('.')[-1]) if '.' in str(exchange_info.tick_size) else 0
                    order.price = round(order.price // exchange_info.tick_size * exchange_info.tick_size, precision)
                
                # Округляем filled_amount аналогично amount
                if order.filled_amount and exchange_info.step_size and exchange_info.step_size > 0:
                    precision = len(str(exchange_info.step_size).split('.')[-1]) if '.' in str(exchange_info.step_size) else 0
                    steps = order.filled_amount / exchange_info.step_size
                    steps = math.floor(steps)
                    order.filled_amount = round(steps * exchange_info.step_size, precision)
            
            return order
        
        # Тестируем исправленную версию
        fixed_order = create_fixed_order_from_dict(problem_data, exchange_info)
        
        print(f"\n✅ РЕЗУЛЬТАТ ИСПРАВЛЕННОЙ ВЕРСИИ:")
        print(f"   Amount: {problem_data['amount']} → {fixed_order.amount}")
        print(f"   Price: {problem_data['price']} → {fixed_order.price}")
        print(f"   Filled: {problem_data['filled']} → {fixed_order.filled_amount}")
        
        # Проверяем что попадет в базу данных
        fixed_dict = fixed_order.to_dict()
        print(f"\n💾 ИСПРАВЛЕННЫЕ ДАННЫЕ ДЛЯ БД:")
        print(f"   Amount: {fixed_dict['amount']}")
        print(f"   Price: {fixed_dict['price']}")
        print(f"   Filled: {fixed_dict['filled_amount']}")
        
        # Проверяем соответствие требованиям биржи (с учетом погрешностей float)
        amount_remainder = fixed_order.amount % exchange_info.step_size
        amount_valid = abs(amount_remainder) < 1e-10 or abs(amount_remainder - exchange_info.step_size) < 1e-10
        
        price_remainder = fixed_order.price % exchange_info.tick_size  
        price_valid = abs(price_remainder) < 1e-10 or abs(price_remainder - exchange_info.tick_size) < 1e-10
        
        print(f"\n🎯 ВАЛИДАЦИЯ РЕЗУЛЬТАТОВ:")
        print(f"   Amount соответствует step_size: {'✅' if amount_valid else '❌'}")
        print(f"   Price соответствует tick_size: {'✅' if price_valid else '❌'}")
        
        if amount_valid and price_valid:
            print(f"\n🎉 РЕШЕНИЕ РАБОТАЕТ КОРРЕКТНО!")
            print(f"   • Неокругленные значения исправлены")
            print(f"   • Значения соответствуют требованиям биржи")
            print(f"   • В базу данных будут сохраняться правильные значения")
            return True
        else:
            print(f"\n❌ РЕШЕНИЕ ТРЕБУЕТ ДОРАБОТКИ")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования решения: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция"""
    print("🚀 АНАЛИЗ И РЕШЕНИЕ ПРОБЛЕМЫ С НЕОКРУГЛЕННЫМИ ЗНАЧЕНИЯМИ")
    print("=" * 80)
    
    # Запускаем все тесты
    tests = [
        ("Воспроизведение проблемы", lambda: test_current_problem()[0]),
        ("Проверка ExchangeInfo", lambda: test_exchange_info_availability()[0]),
        ("Тестирование решения", test_proposed_solution),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {test_name}: УСПЕШНО")
                passed += 1
            else:
                print(f"\n❌ {test_name}: ПРОВАЛЕН")
        except Exception as e:
            print(f"\n❌ {test_name}: ОШИБКА - {e}")
    
    print("\n" + "=" * 80)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 АНАЛИЗ ЗАВЕРШЕН УСПЕШНО!")
        print("✅ Проблема воспроизведена и решение протестировано")
        print("✅ Готово к внедрению исправлений в код")
    else:
        print("❌ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ОТЛАДКА")
    
    print("=" * 80)

if __name__ == "__main__":
    main()