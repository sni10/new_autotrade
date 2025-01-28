import asyncio
import ccxt.pro as pro
import sys
import time
from datetime import datetime

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def websocket_order_book_monitor(exchange, symbol):
    """Подписка на обновления ордербука, обновления приходят при каждом изменении книги заявок."""
    last_timestamp = None
    while True:
        try:
            order_book = await exchange.watch_order_book(symbol)
            timestamp = time.time() * 1000
            best_bid = order_book['bids'][0][0] if order_book['bids'] else None
            best_ask = order_book['asks'][0][0] if order_book['asks'] else None
            time_diff = (timestamp - last_timestamp) / 1000 if last_timestamp else 0
            last_timestamp = timestamp

            output = f"{symbol} | Best Bid: {best_bid:.2f} | Best Ask: {best_ask:.2f} | Δt: {time_diff:.3f}s"
            print(f"\r{output}", end="", flush=True)

        except Exception as e:
            print(f"\nWebSocket Error: {e}")


async def main():
    exchange = pro.binance({
        "rateLimit": 10,
        "enableRateLimit": True,
        "newUpdates": True,
    })

    symbol = "BTC/USDT"
    await websocket_order_book_monitor(exchange, symbol)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
