# main.py
import asyncio
import sys
from datetime import datetime, timedelta
import pytz
import requests
import win32api
import time

from domain.entities.currency_pair import CurrencyPair
from domain.services.deal_service import DealService
from domain.services.signal_service import SignalService
from domain.services.trading_service import TradingService
from domain.services.order_service import OrderService
from domain.factories.deal_factory import DealFactory
from domain.factories.order_factory import OrderFactory
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository

# Пример коннекторов (WebSocket + REST):
# (Предположим, что вы реализуете их)
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from infrastructure.connectors.pro_exchange_connector import CcxtProMarketDataConnector

# Use-case запуска торговли
from application.use_cases.run_realtime_trading import run_realtime_trading

if sys.platform == "win32":
    # Для Windows-асинхронного цикла
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def time_sync():
    # PowerShell добавить разницу. Разница два вида спешка и отставание
    # $currentTime = Get-Date
    # $newTime = $currentTime.AddMilliseconds(7000)   time_diff = 7000 example
    # Set-Date $newTime
    #
    # PowerShell
    # $currentTime = Get-Date
    # $newTime = $currentTime.AddMilliseconds(-4384) time_diff = -7000 example
    # Set-Date $newTime
    response = requests.get('https://api.binance.com/api/v3/time')
    server_time = response.json()['serverTime']
    server_timezone = pytz.timezone('UTC')
    # Calculate the time difference
    local_time = int(time.time() * 1000)

    current_time = datetime.fromtimestamp(server_time / 1000)  # Divide by 1000 to convert milliseconds to seconds
    tz = pytz.timezone('Europe/Kiev')
    current_time = tz.localize(current_time)

    # Convert to UTC
    utc_dt = current_time.astimezone(pytz.utc)

    # Use the UTC datetime to set the system time
    win32api.SetSystemTime(
        utc_dt.year,
        utc_dt.month,
        utc_dt.weekday(),
        utc_dt.day,
        utc_dt.hour,
        utc_dt.minute,
        utc_dt.second,
        utc_dt.microsecond // 1000
    )


async def main():

    time_sync()

    base_currency = "SPELL"

    quote_currency = "USDT"

    symbol = f"{base_currency}/{quote_currency}"

    # 1. Репозитории
    currency_pair = CurrencyPair(
        base_currency=base_currency,
        quote_currency=quote_currency,
        symbol=symbol,
        order_life_time=1,
        deal_quota=12.0,
        min_step=1.0,
        price_step=0.0000001,
        profit_markup=0.5,
        deal_count=1
    )

    deals_repo = InMemoryDealsRepository()

    orders_repo = InMemoryOrdersRepository()

    # 2. Фабрики
    order_factory = OrderFactory()
    deal_factory = DealFactory(order_factory)

    # ExchangeConnector (REST)
    # exchange_connector = CcxtExchangeConnector(
    #     exchange_name="binance",
    #     use_sandbox=True
    # )

    # MarketDataConnector (WebSocket)
    pro_exchange_connector = CcxtProMarketDataConnector(
        exchange_name="binance",
        use_sandbox=False
    )

    # 4. Сервисы
    order_service = OrderService(orders_repo, order_factory)

    # TradingService сам решает, открывать ли сделку и т.д.
    # trading_service = TradingService(deals_repo, order_service, deal_factory)

    # signal_service = SignalService()

    deal_service = DealService(deals_repo, order_service, deal_factory)

    # 5. Запуск use-case: "run_realtime_trading"

    await run_realtime_trading(
        pro_exchange_connector=pro_exchange_connector,
        currency_pair=currency_pair,
        deal_service=deal_service
    )


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
