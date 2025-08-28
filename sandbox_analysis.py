

import asyncio
import os
import sys
import ccxt.pro
import logging
from pprint import pprint

# --- Настройка путей и логирования ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from config.config_loader import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Функции для анализа API ---

async def analyze_exchange_object(exchange):
    """Анализирует сам объект биржи, его свойства и возможности."""
    print("\n" + "="*40)
    print("--- 1. Анализ объекта биржи ---")
    print("="*40)
    print(f"ID Биржи: {exchange.id}")
    print(f"Название: {exchange.name}")
    print("Поддерживаемые возможности (has):")
    # Выводим только те возможности, которые включены (True)
    enabled_features = {key: value for key, value in exchange.has.items() if value}
    pprint(enabled_features)
    print("\n")

async def analyze_markets(exchange, symbol='ETH/USDT'):
    """Загружает и анализирует рынки (список валютных пар)."""
    print("="*40)
    print("--- 2. Анализ рынков (валютных пар) ---")
    print("="*40)
    try:
        markets = await exchange.load_markets()
        print(f"Всего загружено рынков: {len(markets)}")
        print(f"\nАнализ конкретного рынка: {symbol}")
        market_details = markets.get(symbol)
        if market_details:
            pprint(market_details)
        else:
            print(f"Рынок {symbol} не найден!")
    except Exception as e:
        logger.error(f"Ошибка при загрузке рынков: {e}")
    print("\n")

async def analyze_balance(exchange):
    """Загружает и анализирует баланс в песочнице."""
    print("="*40)
    print("--- 3. Анализ баланса ---")
    print("="*40)
    try:
        balance = await exchange.fetch_balance()
        print("Структура объекта баланса:")
        # Выводим только валюты с ненулевым балансом
        active_balances = {key: value for key, value in balance.items() if isinstance(value, dict) and value.get('total', 0) > 0}
        pprint(active_balances)
        print("\nПримечание: В песочнице балансы могут быть стандартными или нулевыми.")
    except Exception as e:
        logger.error(f"Ошибка при получении баланса: {e}")
    print("\n")

async def analyze_ticker(exchange, symbol='ETH/USDT'):
    """Получает и анализирует тикер для указанной пары."""
    print("="*40)
    print(f"--- 4. Анализ тикера ({symbol}) ---")
    print("="*40)
    try:
        print(f"Ожидание первого тикера для {symbol}...")
        ticker = await exchange.watch_ticker(symbol)
        print("Структура объекта тикера:")
        pprint(ticker)
    except Exception as e:
        logger.error(f"Ошибка при получении тикера: {e}")
    print("\n")

async def analyze_order_book(exchange, symbol='ETH/USDT'):
    """Получает и анализирует стакан ордеров."""
    print("="*40)
    print(f"--- 5. Анализ стакана ордеров ({symbol}) ---")
    print("="*40)
    try:
        print(f"Ожидание первого обновления стакана для {symbol}...")
        order_book = await exchange.watch_order_book(symbol)
        print("Структура объекта стакана:")
        # Выводим только общую структуру и по 2 примера бидов/асков
        pprint({
            'symbol': order_book.get('symbol'),
            'timestamp': order_book.get('timestamp'),
            'datetime': order_book.get('datetime'),
            'nonce': order_book.get('nonce'),
            'bids_count': len(order_book.get('bids', [])),
            'asks_count': len(order_book.get('asks', [])),
            'sample_bids': order_book.get('bids', [])[:2],
            'sample_asks': order_book.get('asks', [])[:2],
        })
    except Exception as e:
        logger.error(f"Ошибка при получении стакана: {e}")
    print("\n")


async def main():
    """Основная функция для инициализации и запуска анализа."""
    # --- Настройка вывода в файл ---
    original_stdout = sys.stdout
    with open('exchange_analysis_report.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f

        logger.info("Загрузка конфигурации для подключения к песочнице Binance...")
        
        try:
            config = load_config()
            sandbox_config = config.get('binance', {}).get('sandbox', {})
            api_key = sandbox_config.get('apiKey')
            secret = sandbox_config.get('secret')

            if not api_key or not secret:
                logger.error("Ключи API для песочницы не найдены в .env или config.json!")
                return

        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации: {e}")
            return

        exchange = ccxt.pro.binance({
            'apiKey': api_key,
            'secret': secret,
            'options': {
                'defaultType': 'spot',
            },
        })

        try:
            exchange.set_sandbox_mode(True)
            logger.info(f"Подключение к песочнице {exchange.name}...")

            # --- Запуск аналитических функций ---
            await analyze_exchange_object(exchange)
            await analyze_markets(exchange)
            await analyze_balance(exchange)
            await analyze_ticker(exchange)
            await analyze_order_book(exchange)

            logger.info("Анализ завершен.")

        except Exception as e:
            logger.error(f"Произошла ошибка во время анализа: {e}", exc_info=True)
        finally:
            logger.info("Закрытие соединения с биржей.")
            await exchange.close()

    # --- Возвращаем стандартный вывод ---
    sys.stdout = original_stdout
    logger.info("Отчет сохранен в exchange_analysis_report.txt")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем.")
