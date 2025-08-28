# quick_swap.py (версия 4, с исправлением для Windows)
import asyncio
import sys
import os
import logging
from decimal import Decimal

# --- Исправление для Windows ---
# Этот блок должен быть в самом верху, до любых вызовов asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Добавляем src в sys.path для доступа к модулям проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

# --- НАСТРОЙКИ ОПЕРАЦИИ ---
# ====================================================================
SIDE = "sell"  # Укажите 'buy' для покупки или 'sell' для продажи
SYMBOL = "TURBO/USDT"  # Укажите торговую пару, например 'ETH/USDT'
AMOUNT = "0"  # Количество в БАЗОВОЙ валюте. Если 0, покажет только баланс.
EXCHANGE_NAME = "binance" # Биржа (используется только секция sandbox)
# ====================================================================

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    """
    Основная функция для выполнения рыночного обмена или показа баланса.
    """
    logger.info(f"🚀 Запуск скрипта quick_swap.py")
    amount_dec = Decimal(AMOUNT)
    connector = None
    
    try:
        # --- Инициализация коннектора ---
        connector = CcxtExchangeConnector(exchange_name=EXCHANGE_NAME, use_sandbox=True)
        logger.info("✅ Коннектор к песочнице инициализирован.")

        # --- Загрузка рынков и определение валют ---
        await connector.load_markets(reload=True)
        market = connector.client.markets.get(SYMBOL)
        if not market:
            logger.error(f"❌ Символ '{SYMBOL}' не найден на бирже '{EXCHANGE_NAME}'.")
            return

        base_currency = market['base']
        quote_currency = market['quote']

        # --- Проверка и вывод баланса ---
        logger.info("🔍 Получение баланса...")
        balance = await connector.fetch_balance()
        base_balance = Decimal(str(balance.get(base_currency, {}).get('free', 0.0)))
        quote_balance = Decimal(str(balance.get(quote_currency, {}).get('free', 0.0)))

        logger.info(f"💰 Баланс: {base_balance:.8f} {base_currency}")
        logger.info(f"💰 Баланс: {quote_balance:.4f} {quote_currency}")

        # --- Если количество 0, выходим после показа баланса ---
        if amount_dec == 0:
            logger.info("🟡 Количество для обмена равно нулю. Показан только баланс.")
            return

        # --- Логика обмена (если количество > 0) ---
        logger.info(f"▶️ Подготовка к операции: {SIDE.upper()} {AMOUNT} {SYMBOL}")
        
        # Проверка достаточности средств для сделки
        if SIDE == 'sell':
            if amount_dec > base_balance:
                logger.error(f"❌ Недостаточно средств. Нужно: {amount_dec} {base_currency}, доступно: {base_balance}")
                return
        else:  # buy
            ticker = await connector.fetch_ticker(SYMBOL)
            current_price = Decimal(str(ticker.last))
            required_quote_amount = amount_dec * current_price

            if required_quote_amount > quote_balance:
                logger.error(f"❌ Недостаточно средств. Нужно ~{required_quote_amount:.4f} {quote_currency}, доступно: {quote_balance:.4f}")
                return

        # Создание ордера
        logger.info(f"📤 Создание рыночного ({SIDE.upper()}) ордера на {amount_dec} {base_currency}...")
        order_result = await connector.create_order(
            symbol=SYMBOL,
            side=SIDE,
            order_type='market',
            amount=float(amount_dec)
        )
        
        logger.info("🎉 Ордер успешно выполнен!")
        logger.info("--- РЕЗУЛЬТАТ ---")
        logger.info(f"  ID ордера: {order_result.get('id')}")
        logger.info(f"  Статус: {order_result.get('status')}")
        logger.info(f"  Символ: {order_result.get('symbol')}")
        logger.info(f"  Сторона: {order_result.get('side')}")
        logger.info(f"  Количество: {order_result.get('filled')} {base_currency}")
        logger.info(f"  Средняя цена: {order_result.get('average')} {quote_currency}")
        logger.info(f"  Общая стоимость: {order_result.get('cost')} {quote_currency}")
        fee_info = order_result.get('fee', {})
        if fee_info and fee_info.get('cost') is not None:
                logger.info(f"  Комиссия: {fee_info.get('cost')} {fee_info.get('currency')}")
        logger.info("-----------------")

    except Exception as e:
        logger.error(f"❌ Произошла критическая ошибка: {e}", exc_info=True)
    finally:
        if connector:
            await connector.close()
            logger.info("🔌 Соединение с биржей закрыто.")

if __name__ == "__main__":
    try:
        # Используем более надежный метод запуска asyncio для совместимости с отладчиками
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("🛑 Операция прервана пользователем.")