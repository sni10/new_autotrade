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
# Этот блок должен быть в самом верху, до любых вызовов asyncio
if sys.platform == "win32":
    # Устанавливаем политику цикла событий ДО его создания
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        import win32api
    except ImportError:
        win32api = None
        print("ПРЕДУПРЕЖДЕНИЕ: Модуль 'pywin32' не найден. Синхронизация времени будет пропущена.")
else:
    win32api = None

# --- Основные импорты проекта ---
# Добавляем src в sys.path ПЕРЕД всеми импортами из проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from domain.entities.currency_pair import CurrencyPair
from domain.services.deals.deal_service import DealService
from domain.services.orders.order_service import OrderService
from domain.services.orders.order_execution_service import OrderExecutionService
from domain.services.orders.buy_order_monitor import BuyOrderMonitor
from domain.factories.order_factory import OrderFactory
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from config.config_loader import load_config
from application.use_cases.run_realtime_trading import run_realtime_trading
from domain.services.risk.stop_loss_monitor import StopLossMonitor
from domain.services.deals.deal_completion_monitor import DealCompletionMonitor
from domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Имя файла лога с временной меткой
log_filename = f"autotrade_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
log_filepath = os.path.join(log_dir, log_filename)

# Создаем обработчики с явным указанием кодировки UTF-8
file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
stream_handler = logging.StreamHandler(sys.stdout) # Используем sys.stdout для лучшей совместимости

# Устанавливаем форматтер для обоих обработчиков
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Настраиваем корневой логгер
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        stream_handler
    ]
)
logger = logging.getLogger(__name__)

def time_sync_windows():
    """Синхронизация времени с серверами Binance для Windows."""
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
    """🚀 ГЛАВНАЯ функция с интеграцией OrderExecutionService и мониторинга"""
    if sys.platform == "win32":
        time_sync_windows()

    config = load_config()
    pair_cfg = config.get("currency_pair", {})
    base_currency = pair_cfg.get("base_currency", "ETH")
    quote_currency = pair_cfg.get("quote_currency", "USDT")
    symbol_ccxt = f"{base_currency}{quote_currency}"
    symbol_display = f"{base_currency}/{quote_currency}"

    logger.info(f"🚀 ЗАПУСК AutoTrade v2.3.0 для {symbol_display}")
    
    buy_order_monitor = None
    stop_loss_monitor = None
    pro_exchange_connector_prod = None
    pro_exchange_connector_sandbox = None

    try:
        # 1. Инициализация коннекторов
        pro_exchange_connector_prod = CcxtExchangeConnector(use_sandbox=False)
        pro_exchange_connector_sandbox = CcxtExchangeConnector(use_sandbox=True)
        logger.info("✅ Коннекторы инициализированы (Production, Sandbox)")

        # 2. Инициализация репозиториев
        deals_repo = InMemoryDealsRepository()
        orders_repo = InMemoryOrdersRepository(max_orders=50000)
        logger.info("✅ Репозитории созданы (InMemory)")

        # 3. Инициализация фабрик
        order_factory = OrderFactory()
        symbol_info = await pro_exchange_connector_prod.get_symbol_info(symbol_ccxt)
        order_factory.update_exchange_info(symbol_ccxt, symbol_info)
        deal_factory = DealFactory(order_factory)
        logger.info(f"✅ Фабрики созданы, Exchange info для {symbol_ccxt} загружена")

        # 4. Инициализация сервисов
        order_service = OrderService(orders_repo, order_factory, pro_exchange_connector_sandbox, currency_pair_symbol=symbol_ccxt)
        deal_service = DealService(deals_repo, order_service, deal_factory, pro_exchange_connector_sandbox)
        order_execution_service = OrderExecutionService(order_service, deal_service, pro_exchange_connector_sandbox)
        orderbook_analyzer = OrderBookAnalyzer(config.get("orderbook_analyzer", {}))
        logger.info("✅ Основные сервисы созданы")

        # 5. Инициализация мониторинга
        buy_order_monitor_cfg = config.get("buy_order_monitor", {})
        buy_order_monitor = BuyOrderMonitor(
            order_service=order_service,
            exchange_connector=pro_exchange_connector_sandbox,
            max_age_minutes=buy_order_monitor_cfg.get("max_age_minutes", 15.0),
            max_price_deviation_percent=buy_order_monitor_cfg.get("max_price_deviation_percent", 3.0),
            check_interval_seconds=buy_order_monitor_cfg.get("check_interval_seconds", 60)
        )
        asyncio.create_task(buy_order_monitor.start_monitoring())
        logger.info("✅ BuyOrderMonitor запущен")

        # 5.2. Запуск мониторинга завершения сделок
        deal_completion_monitor = DealCompletionMonitor(
            deal_service=deal_service,
            check_interval_seconds=30  # Проверка каждые 30 секунд
        )
        asyncio.create_task(deal_completion_monitor.start_monitoring())
        logger.info("✅ DealCompletionMonitor запущен")

        risk_config = config.get("risk_management", {})
        if risk_config.get("enable_stop_loss", False):
            # Получаем настройки умного стоп-лосса
            smart_config = risk_config.get("smart_stop_loss", {})
            
            stop_loss_monitor = StopLossMonitor(
                deal_service=deal_service,
                order_execution_service=order_execution_service,
                exchange_connector=pro_exchange_connector_prod,
                orderbook_analyzer=orderbook_analyzer,  # Добавляем анализатор стакана
                stop_loss_percent=risk_config.get("stop_loss_percent", 2.0),
                check_interval_seconds=risk_config.get("stop_loss_check_interval_seconds", 60),
                warning_percent=smart_config.get("warning_percent", 5.0),
                critical_percent=smart_config.get("critical_percent", 10.0),
                emergency_percent=smart_config.get("emergency_percent", 15.0)
            )
            asyncio.create_task(stop_loss_monitor.start_monitoring())
            logger.info("✅ StopLossMonitor запущен с умным анализом стакана")

        # 6. Проверка подключения и баланса
        if not await pro_exchange_connector_sandbox.test_connection():
            logger.error("❌ Подключение к бирже неудачно. Завершение работы...")
            return
        
        balance = await pro_exchange_connector_sandbox.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0.0)
        logger.info(f"💰 Доступный баланс в песочнице: {usdt_balance:.4f} USDT")

        # 7. Создание объекта CurrencyPair
        currency_pair = CurrencyPair(
            base_currency=base_currency,
            quote_currency=quote_currency,
            symbol=symbol_ccxt,
            deal_quota=pair_cfg.get("deal_quota", 100.0),
            deal_count=pair_cfg.get("deal_count", 1),
            profit_markup=pair_cfg.get("profit_markup", 0.005)  # 0.5%
        )
        # ЗАГРУЗКА АКТУАЛЬНЫХ ДАННЫХ С БИРЖИ
        markets = await pro_exchange_connector_prod.load_markets()
        market_details = markets.get(currency_pair.symbol)
        if market_details:
            currency_pair.update_exchange_info(market_details)
            logger.info(f"✅ Config updated with precision and limits for {currency_pair.symbol}")

        # 8. Запуск основного цикла торговли
        logger.info("="*80)
        logger.info("🚀 СИСТЕМА ГОТОВА К ЗАПУСКУ ТОРГОВЛИ")
        logger.info(f'   - Валютная пара: {symbol_display}')
        logger.info(f'   - Бюджет на сделку: {currency_pair.deal_quota} USDT')
        logger.info(f'   - Режим: Sandbox (безопасно)')
        logger.info("="*80)

        await run_realtime_trading(
            pro_exchange_connector_prod=pro_exchange_connector_prod,
            pro_exchange_connector_sandbox=pro_exchange_connector_sandbox,
            currency_pair=currency_pair,
            deal_service=deal_service,
            order_execution_service=order_execution_service,
            buy_order_monitor=buy_order_monitor, # Возвращено
            orderbook_analyzer=orderbook_analyzer,
            deal_completion_monitor=deal_completion_monitor,  # Добавлен новый параметр
            stop_loss_monitor=stop_loss_monitor if 'stop_loss_monitor' in locals() else None  # Передаем StopLossMonitor
        )

    except Exception as e:
        logger.error(f"❌ Критическая ошибка в main(): {e}", exc_info=True)
    finally:
        logger.info("🔴 Завершение работы, закрытие соединений...")
        if buy_order_monitor:
            buy_order_monitor.stop_monitoring()
        if 'deal_completion_monitor' in locals() and deal_completion_monitor:
            deal_completion_monitor.stop_monitoring()
        if 'stop_loss_monitor' in locals() and stop_loss_monitor:
            stop_loss_monitor.stop_monitoring()
        if pro_exchange_connector_prod:
            await pro_exchange_connector_prod.close()
        if pro_exchange_connector_sandbox:
            await pro_exchange_connector_sandbox.close()
        logger.info("👋 AutoTrade завершен")

# --- Специальный запуск для Windows и других систем ---
if __name__ == "__main__":
    try:
        # Этот метод запуска является более надежным в сложных окружениях,
        # таких как запуск под отладчиком в Windows.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("🛑 Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}", exc_info=True)
    finally:
        logger.info("👋 AutoTrade завершен")