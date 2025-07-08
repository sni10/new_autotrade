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

    base_currency = "FIS"
    quote_currency = "USDT"

    # ИСПРАВЛЕНИЕ: используем формат без слэша для Binance
    symbol_ccxt = f"{base_currency}{quote_currency}"  # "VICUSDT"
    symbol_display = f"{base_currency}/{quote_currency}"  # "VIC/USDT"

    # 1. Репозитории
    currency_pair = CurrencyPair(
        base_currency=base_currency,
        quote_currency=quote_currency,
        symbol=symbol_ccxt,  # ИСПОЛЬЗУЕМ VICUSDT для API
        order_life_time=1,
        deal_quota=10.0,
        min_step=1.0,
        price_step=0.0001,
        profit_markup=1.5,
        deal_count=3
    )

    deals_repo = InMemoryDealsRepository()

    orders_repo = InMemoryOrdersRepository()

    # 2. Фабрики
    order_factory = OrderFactory()
    deal_factory = DealFactory(order_factory)

    # MarketDataConnector (WebSocket)
    pro_exchange_connector_prod = CcxtProMarketDataConnector(
        exchange_name="binance",
        use_sandbox=False
    )

    pro_exchange_connector_sandbox = CcxtProMarketDataConnector(
        exchange_name="binance",
        use_sandbox=True
    )

    # 4. Сервисы
    order_service = OrderService(orders_repo, order_factory)

    # TradingService сам решает, открывать ли сделку и т.д.
    # trading_service = TradingService(deals_repo, order_service, deal_factory)
    # signal_service = SignalService()

    deal_service = DealService(deals_repo, order_service, deal_factory)

    print("🚀 СИСТЕМА ГОТОВА К ЗАПУСКУ")
    print(f"   💱 Валютная пара: {symbol_display} ({symbol_ccxt})")
    print(f"   📊 Анализ стакана: Включен")
    print(f"   🔗 Подключения: Prod + Sandbox")
    print("="*60)

    # 5. Запуск use-case: "run_realtime_trading"
    await run_realtime_trading(
        pro_exchange_connector_prod=pro_exchange_connector_prod,
        pro_exchange_connector_sandbox=pro_exchange_connector_sandbox,
        currency_pair=currency_pair,
        deal_service=deal_service
    )


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
