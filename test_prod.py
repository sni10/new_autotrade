# full_autotrade_test.py — весь минимум для spot-тестнета Binance
# pip install ccxtpro
import os
import sys
import asyncio
import logging
import ccxt.pro as ccxt
import pytest

if not (os.getenv("BINANCE_SANDBOX_API_KEY") and os.getenv("BINANCE_SANDBOX_SECRET")):
    pytest.skip("Binance sandbox credentials not configured", allow_module_level=True)

# 👉 Windows-цикл, чтобы WS не падал
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

PAIR = "OMNI/USDT"
API_KEY = os.getenv("BINANCE_SANDBOX_API_KEY", "")
API_SECRET = os.getenv("BINANCE_SANDBOX_SECRET", "")
RUN_S = 600  # держим WS 10 мин


class EX:
    def __init__(self):
        self.c = ccxt.binance(
            {
                "apiKey": API_KEY,
                "secret": API_SECRET,
                "options": {"defaultType": "spot"},
            }
        )
        self.c.set_sandbox_mode(True)  # тестнет
        self._orders_task = self._keep_task = None

    # ---------- REST ----------
    async def markets(self):
        return await self.c.load_markets()

    async def price(self):
        return (await self.c.fetch_ticker(PAIR))["last"]

    async def balance(self):
        return (await self.c.fetch_balance())["total"]

    async def opens(self):
        return await self.c.fetch_open_orders(PAIR)

    async def trades(self):
        return await self.c.fetch_my_trades(PAIR)

    async def buy(self):
        ticker = await self.c.fetch_ticker(PAIR)
        price = ticker["last"]
        min_notional = 10  # допустим, бинанс требует >= 10 USDT

        amount = min_notional / price
        amount = round(amount, 4)  # округляем, Binance требует точность

        return await self.c.create_order(PAIR, "market", "buy", amount)

    # ---------- WS ----------
    async def _watch_orders(self):
        while True:
            upd = await self.c.watch_orders()
            log.info(f'🔔 {upd["id"]} {upd["status"]}')

    async def _keep_alive(self):
        while True:
            await self.c.privatePutUserDataStream(
                {"listenKey": self.c.options["listenKey"]}
            )
            await asyncio.sleep(1500)  # 25 мин

    async def start_ws(self):
        self._orders_task = asyncio.create_task(self._watch_orders())
        self._keep_task = asyncio.create_task(self._keep_alive())

    async def min_notional(self):
        mkt = self.c.markets[PAIR]
        for f in mkt.get("info", {}).get("filters", []):
            if f["filterType"] == "MIN_NOTIONAL":
                return float(f["minNotional"])

    async def close(self):
        for t in (self._orders_task, self._keep_task):
            if t:
                t.cancel()
        await self.c.close()


# ---------- MAIN ----------
async def main():
    ex = EX()
    log.info("🚀 START")

    mkts = await ex.markets()
    log.info(f"🌐 markets: {len(mkts)} пар")

    log.info(f"📈 price {PAIR}: {await ex.price()}")

    bal = await ex.balance()
    log.info(f'💰 USDT free: {bal.get("USDT", 0)}')
    log.info(f'💰 BTC free: {bal.get("BTC", 0)}')
    log.info(f'💰 ETH free: {bal.get("ETH", 0)}')
    log.info(f'💰 OMNI free: {bal.get("OMNI", 0)}')

    order = await ex.buy()
    log.info(f'📝 buy id: {order["id"]}')

    log.info(f"📦 open orders: {await ex.opens()}")
    log.info(f"📑 my trades:  {await ex.trades()}")

    await ex.start_ws()
    await asyncio.sleep(RUN_S)
    await ex.close()
    log.info("👋 STOP")


# ---------- RUN ----------
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(main())
