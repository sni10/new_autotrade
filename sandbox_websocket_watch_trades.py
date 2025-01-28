import asyncio
import ccxt.pro as pro
import sys
import time
from datetime import datetime

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def websocket_trade_monitor(exchange, symbol):
    """Подписка на поток сделок (trades), обновления приходят чаще, чем тикер."""
    last_timestamp = None

    if exchange.has['watchTrades']:
        while True:
            try:
                trades = await exchange.watch_trades(symbol)  # Получаем массив трейдов
                for trade in trades:
                    timestamp = trade['timestamp'] or time.time() * 1000

                    time_diff = (timestamp - last_timestamp) / 1000 if last_timestamp else 0
                    last_timestamp = timestamp

                    output = f"{symbol}{trade['id']} | Price: {trade['price']:.2f} | {trade['side']} | Amount: {trade['amount']:.6f}| Cost: {trade['cost']:.6f} | Δt: {time_diff:.3f}s"

                    print(f"\r{output}", end="\n", flush=False)

            except Exception as e:
                print(e)


async def main():
    exchange = pro.binance({
        "rateLimit": 10,
        "enableRateLimit": True,
        "newUpdates": True,
    })

    symbol = "BTC/USDT"
    await websocket_trade_monitor(exchange, symbol)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
