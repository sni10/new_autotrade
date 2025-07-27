
# main.py - Полностью исправленная версия с особым запуском для Windows
import asyncio
import sys
import os
import logging
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv

# --- Условная настройка для Windows ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        import win32api
    except ImportError:
        win32api = None
        print("ПРЕДУПРЕЖДЕНИЕ: Модуль 'pywin32' не найден. Синхронизация времени будет пропущена.")
else:
    win32api = None

# --- Основные импорты проекта ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.domain.entities.currency_pair import CurrencyPair
from src.domain.services.deals.deal_service import DealService
from src.domain.services.orders.order_service import OrderService
from src.domain.services.orders.order_execution_service import OrderExecutionService
from src.domain.services.orders.buy_order_monitor import BuyOrderMonitor
from src.domain.factories.order_factory import OrderFactory
from src.domain.factories.deal_factory import DealFactory
from src.infrastructure.repositories.deals_repository import InMemoryDealsRepository
from src.infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from src.infrastructure.repositories.in_memory_state_repository import InMemoryStateRepository
from src.domain.services.state.state_management_service import StateManagementService
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from src.config.config_loader import load_config
from src.application.use_cases.run_realtime_trading import run_realtime_trading
from src.domain.services.risk.stop_loss_monitor import StopLossMonitor
from src.domain.services.deals.deal_completion_monitor import DealCompletionMonitor
from src.domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer

load_dotenv()

# Настройка логирования
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_filename = f"autotrade_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
log_filepath = os.path.join(log_dir, log_filename)
file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])
logger = logging.getLogger(__name__)

def time_sync_windows():
    if not win32api:
        return
    try:
        logger.info("Попытка синхронизации времени для Windows...")
        response = requests.get('https://api.binance.com/api/v3/time')
        server_time = response.json()['serverTime']
        utc_dt = datetime.fromtimestamp(server_time / 1000, tz=pytz.utc)
        day_of_week = (utc_dt.weekday() + 1) % 7
        win32api.SetSystemTime(utc_dt.year, utc_dt.month, day_of_week, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second, int(utc_dt.microsecond / 1000))
        logger.info(f"⏰ Время успешно синхронизировано: {utc_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось синхронизировать время: {e}")

async def main():
    if sys.platform == "win32":
        time_sync_windows()

    config = load_config()
    pair_cfg = config.get("currency_pair", {})
    base_currency = pair_cfg.get("base_currency", "ETH")
    quote_currency = pair_cfg.get("quote_currency", "USDT")
    symbol_ccxt = f"{base_currency}{quote_currency}"
    symbol_display = f"{base_currency}/{quote_currency}"

    logger.info(f"🚀 ЗАПУСК AutoTrade v2.4.0 для {symbol_display}")
    
    state_service = None
    buy_order_monitor = None
    stop_loss_monitor = None
    pro_exchange_connector_prod = None
    pro_exchange_connector_sandbox = None

    try:
        # 1. Инициализация репозиториев
        db_manager = DatabaseManager(config['database'])
        await db_manager.connect()
        deals_repo = PostgreSQLDealsRepository(db_manager)
        orders_repo = PostgreSQLOrdersRepository(db_manager)
        state_repo = InMemoryStateRepository() # Оставляем InMemory для состояния сессии
        logger.info("✅ Репозитории созданы (PostgreSQL, InMemoryState)")

        # 2. Инициализация StateManagementService
        state_service = StateManagementService(state_repo, deals_repo, orders_repo)
        await state_service.initialize()
        logger.info("✅ StateManagementService инициализирован")

        # 3. Инициализация коннекторов
        pro_exchange_connector_prod = CcxtExchangeConnector(use_sandbox=False)
        pro_exchange_connector_sandbox = CcxtExchangeConnector(use_sandbox=True)
        logger.info("✅ Коннекторы инициализированы (Production, Sandbox)")

        # 4. Инициализация фабрик
        order_factory = OrderFactory()
        symbol_info = await pro_exchange_connector_prod.get_symbol_info(symbol_ccxt)
        order_factory.update_exchange_info(symbol_ccxt, symbol_info)
        deal_factory = DealFactory(order_factory)
        logger.info(f"✅ Фабрики созданы, Exchange info для {symbol_ccxt} загружена")

        # 5. Инициализация сервисов
        order_service = OrderService(orders_repo, order_factory, pro_exchange_connector_sandbox, currency_pair_symbol=symbol_ccxt)
        deal_service = DealService(deals_repo, order_service, deal_factory, pro_exchange_connector_sandbox)
        order_execution_service = OrderExecutionService(order_service, deal_service, pro_exchange_connector_sandbox)
        orderbook_analyzer = OrderBookAnalyzer(config.get("orderbook_analyzer", {}))
        logger.info("✅ Основные сервисы созданы")

        # 6. Инициализация мониторинга
        buy_order_monitor_cfg = config.get("buy_order_monitor", {})
        buy_order_monitor = BuyOrderMonitor(
            order_service=order_service,
            deal_service=deal_service,
            exchange_connector=pro_exchange_connector_sandbox,
            max_age_minutes=buy_order_monitor_cfg.get("max_age_minutes", 15.0),
            max_price_deviation_percent=buy_order_monitor_cfg.get("max_price_deviation_percent", 3.0),
            check_interval_seconds=buy_order_monitor_cfg.get("check_interval_seconds", 60)
        )
        asyncio.create_task(buy_order_monitor.start_monitoring())
        logger.info("✅ BuyOrderMonitor запущен")

        deal_completion_monitor = DealCompletionMonitor(deal_service=deal_service, order_service=order_service, check_interval_seconds=30)
        asyncio.create_task(deal_completion_monitor.start_monitoring())
        logger.info("✅ DealCompletionMonitor запущен")

        risk_config = config.get("risk_management", {})
        if risk_config.get("enable_stop_loss", False):
            smart_config = risk_config.get("smart_stop_loss", {})
            stop_loss_monitor = StopLossMonitor(
                deal_service=deal_service,
                order_execution_service=order_execution_service,
                exchange_connector=pro_exchange_connector_sandbox,
                orderbook_analyzer=orderbook_analyzer,
                stop_loss_percent=risk_config.get("stop_loss_percent", 2.0),
                check_interval_seconds=risk_config.get("stop_loss_check_interval_seconds", 60),
                warning_percent=smart_config.get("warning_percent", 5.0),
                critical_percent=smart_config.get("critical_percent", 10.0),
                emergency_percent=smart_config.get("emergency_percent", 15.0)
            )
            asyncio.create_task(stop_loss_monitor.start_monitoring())
            logger.info("✅ StopLossMonitor запущен с умным анализом стакана")

        # 7. Проверка подключения и баланса
        if not await pro_exchange_connector_sandbox.test_connection():
            logger.error("❌ Подключение к бирже неудачно. Завершение работы...")
            return
        
        balance = await pro_exchange_connector_sandbox.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0.0)
        logger.info(f"💰 Доступный баланс в песочнице: {usdt_balance:.4f} USDT")

        # 8. Создание объекта CurrencyPair
        currency_pair = CurrencyPair(
            base_currency=base_currency,
            quote_currency=quote_currency,
            symbol=symbol_ccxt,
            deal_quota=pair_cfg.get("deal_quota", 100.0),
            deal_count=pair_cfg.get("deal_count", 1),
            profit_markup=pair_cfg.get("profit_markup", 0.005)
        )
        markets = await pro_exchange_connector_prod.load_markets()
        market_details = markets.get(currency_pair.symbol)
        if market_details:
            currency_pair.update_exchange_info(market_details)
            logger.info(f"✅ Config updated with precision and limits for {currency_pair.symbol}")

        # 9. Запуск основного цикла торговли
        logger.info("="*80)
        logger.info("🚀 СИСТЕМА ГОТОВА К ЗАПУСКУ ТОРГОВЛИ")
        logger.info(f'   - Валютная пара: {symbol_display}')
        logger.info(f'   - Бюджет на сделку: {currency_pair.deal_quota} USDT')
        logger.info(f'   - Режим: Sandbox (безопасно)')
        logger.info("="*80)

        await state_service.start_trading_session(symbol_ccxt)

        await run_realtime_trading(
            pro_exchange_connector_prod=pro_exchange_connector_prod,
            pro_exchange_connector_sandbox=pro_exchange_connector_sandbox,
            currency_pair=currency_pair,
            deal_service=deal_service,
            order_execution_service=order_execution_service,
            buy_order_monitor=buy_order_monitor,
            orderbook_analyzer=orderbook_analyzer,
            deal_completion_monitor=deal_completion_monitor,
            stop_loss_monitor=stop_loss_monitor
        )

    except Exception as e:
        logger.error(f"❌ Критическая ошибка в main(): {e}", exc_info=True)
        if state_service:
            await state_service.emergency_shutdown()
    finally:
        logger.info("🔴 Завершение работы, закрытие соединений...")
        if state_service:
            await state_service.request_graceful_shutdown()
        if buy_order_monitor:
            buy_order_monitor.stop_monitoring()
        if stop_loss_monitor:
            stop_loss_monitor.stop_monitoring()
        if pro_exchange_connector_prod:
            await pro_exchange_connector_prod.close()
        if pro_exchange_connector_sandbox:
            await pro_exchange_connector_sandbox.close()
        logger.info("👋 AutoTrade завершен")

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("🛑 Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}", exc_info=True)
    finally:
        logger.info("👋 AutoTrade завершен")
