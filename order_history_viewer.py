#!/usr/bin/env python3
"""
Скрипт для просмотра истории ордеров на бирже
Показывает все ордера (открытые, исполненные, отмененные)
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Добавляем src в путь для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.config_loader import load_config
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Основная функция для просмотра ордеров"""
    
    # Выбор режима
    print("🔍 ПРОСМОТР ИСТОРИИ ОРДЕРОВ")
    print("1. Sandbox (тестовый режим)")
    print("2. Production (реальные ордера)")
    
    choice = input("Выберите режим (1 или 2): ").strip()
    use_sandbox = choice == "1"
    mode_name = "SANDBOX" if use_sandbox else "PRODUCTION"
    
    print(f"\n📊 Загружаем данные из режима: {mode_name}")
    
    # Создаем коннектор
    connector = CcxtExchangeConnector("binance", use_sandbox=use_sandbox)
    
    try:
        # Проверяем подключение
        if not await connector.test_connection():
            logger.error("❌ Не удалось подключиться к бирже")
            return
        
        print(f"✅ Подключение к Binance {mode_name} успешно")
        
        # Символ для поиска
        symbol = input("\n🎯 Введите символ (например, TURBOUSDT) или Enter для всех: ").strip().upper()
        if not symbol:
            symbol = None
        
        print("\n" + "="*80)
        print(f"📋 ИСТОРИЯ ОРДЕРОВ {f'ДЛЯ {symbol}' if symbol else '(ВСЕ СИМВОЛЫ)'}")
        print("="*80)
        
        # 1. Открытые ордера
        print("\n🟢 ОТКРЫТЫЕ ОРДЕРА:")
        print("-" * 40)
        open_orders = await connector.fetch_open_orders(symbol)
        
        if open_orders:
            for order in open_orders:
                print_order_info(order, "ОТКРЫТ")
        else:
            print("   Нет открытых ордеров")
        
        # 2. Недавние ордера (последние 100)
        print(f"\n📜 ИСТОРИЯ ОРДЕРОВ (последние):")
        print("-" * 40)
        
        try:
            # Для истории ордеров нужен конкретный символ
            if symbol:
                # Получаем закрытые ордера (за последние 7 дней по умолчанию)
                closed_orders = await connector.client.fetch_closed_orders(symbol, limit=100)
                
                if closed_orders:
                    # Сортируем по времени (новые сначала)
                    closed_orders.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                    
                    for order in closed_orders:
                        print_order_info(order, order.get('status', 'UNKNOWN'))
                else:
                    print("   Нет истории ордеров")
            else:
                print("   ⚠️ Для просмотра истории укажите конкретный символ")
        
        except Exception as e:
            logger.warning(f"Не удалось получить историю ордеров: {e}")
            print("   ⚠️ История недоступна (возможно, нужны дополнительные права)")
        
        # 3. Статистика по балансу
        print(f"\n💰 ТЕКУЩИЙ БАЛАНС:")
        print("-" * 40)
        
        balance = await connector.fetch_balance()
        
        # Показываем только ненулевые балансы
        for currency, data in balance.items():
            if currency not in ['info', 'free', 'used', 'total']:
                free_balance = data.get('free', 0)
                used_balance = data.get('used', 0)
                total_balance = data.get('total', 0)
                
                if total_balance > 0:
                    print(f"   {currency}: {total_balance:.8f} (свободно: {free_balance:.8f}, в ордерах: {used_balance:.8f})")
    
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    finally:
        await connector.close()
        print(f"\n🔌 Соединение с {mode_name} закрыто")

def print_order_info(order, status_override=None):
    """Красивый вывод информации об ордере"""
    
    # Извлекаем основные данные
    order_id = order.get('id', 'N/A')
    symbol = order.get('symbol', 'N/A')
    side = order.get('side', 'N/A').upper()
    order_type = order.get('type', 'N/A').upper()
    amount = order.get('amount', 0)
    price = order.get('price', 0)
    filled = order.get('filled', 0)
    remaining = order.get('remaining', 0)
    status = status_override or order.get('status', 'UNKNOWN').upper()
    timestamp = order.get('timestamp')
    
    # Форматируем время
    time_str = "N/A"
    if timestamp:
        try:
            dt = datetime.fromtimestamp(timestamp / 1000)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = str(timestamp)
    
    # Выбираем эмодзи для статуса
    status_emoji = {
        'ОТКРЫТ': '🟢',
        'OPEN': '🟢',
        'FILLED': '✅',
        'CANCELED': '❌',
        'CANCELLED': '❌',
        'EXPIRED': '⏰',
        'REJECTED': '🚫',
        'PARTIALLY_FILLED': '🟡'
    }.get(status, '❓')
    
    # Форматируем цены
    price_str = f"{price:.8f}" if price else "MARKET"
    filled_percent = (filled / amount * 100) if amount > 0 else 0
    
    # Выводим информацию
    print(f"   {status_emoji} ID: {order_id}")
    print(f"      📊 {symbol} | {side} {order_type} | {status}")
    print(f"      💰 Цена: {price_str} | Количество: {amount:.8f}")
    print(f"      ✅ Исполнено: {filled:.8f} ({filled_percent:.1f}%) | Остаток: {remaining:.8f}")
    print(f"      🕐 Время: {time_str}")
    
    # Дополнительная информация если есть
    cost = order.get('cost', 0)
    if cost > 0:
        print(f"      💵 Стоимость: {cost:.8f}")
    
    fee = order.get('fee')
    if fee and fee.get('cost', 0) > 0:
        print(f"      💸 Комиссия: {fee['cost']:.8f} {fee.get('currency', '')}")
    
    print()

if __name__ == "__main__":
    asyncio.run(main())