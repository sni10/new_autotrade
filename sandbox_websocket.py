import asyncio
import ccxt.pro as pro
import sys
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 🛠 Фикс для Windows: устанавливаем совместимый event loop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def websocket_price_monitor(exchange, symbol):
    """Подписка на поток цен (тикер) с отображением времени и разницы между обновлениями."""
    last_timestamp = None

    while True:
        try:
            ticker = await exchange.watch_ticker(symbol)

            timestamp = ticker['timestamp'] or time.time() * 1000  # Если нет таймстампа, берем текущее время

            # Разница во времени между обновлениями
            time_diff = (timestamp - last_timestamp) / 1000 if last_timestamp else 0
            last_timestamp = timestamp  # Обновляем таймстамп

            output = (f"{symbol} | Price: {ticker['last']:.2f} |"
                      f" Time: {ticker['timestamp']} |"
                      f" open: {ticker['open']:.2f} |"
                      f" close: {ticker['close']:.2f} |"
                      f" Δt: {time_diff:.3f}s")

            logger.info(output)

        except Exception as e:
            logger.exception("WebSocket Error: %s", e)


async def main():
    exchange = pro.binance({
        "rateLimit": 10,
        "enableRateLimit": True,
        "newUpdates": True,
    })

    symbol = "BTC/USDT"
    await websocket_price_monitor(exchange, symbol)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
