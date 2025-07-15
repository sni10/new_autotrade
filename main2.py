# main.py.new - ИНТЕГРАЦИЯ Issue #7 OrderExecutionService + BuyOrderMonitor
import asyncio
import sys
import os
import logging
from datetime import datetime
import pytz
import requests
import win32api
import time
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Добавляем src в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# 🆕 НОВЫЕ ИМПОРТЫ для Issue #7
from domain.entities.currency_pair import CurrencyPair
from domain.services.deals.deal_service import DealService

# 🚀 ОБНОВЛЕННЫЕ СЕРВИСЫ
from domain.services.orders.order_service import OrderService  # Используем .new версию
from domain.services.orders.order_execution_service import OrderExecutionService  # НОВЫЙ главный сервис
from domain.services.orders.buy_order_monitor import BuyOrderMonitor  # 🆕 МОНИТОРИНГ ТУХЛЯКОВ
from domain.factories.order_factory import OrderFactory  # Используем .new версию

# 🚀 ОБНОВЛЕННЫЕ РЕПОЗИТОРИИ
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository  # Используем .new версию

# 🚀 ОБНОВЛЕННЫЕ КОННЕКТОРЫ
from infrastructure.connectors.pro_exchange_connector import CcxtProMarketDataConnector
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector  # Используем .new версию
from config.config_loader import load_config

# Use-case запуска торговли
from application.use_cases.run_realtime_trading import run_realtime_trading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    # Для Windows-асинхронного цикла
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def time_sync():
    """Синхронизация времени с серверами Binance"""
    try:
        response = requests.get('https://api.binance.com/api/v3/time')
        server_time = response.json()['serverTime']

        current_time = datetime.fromtimestamp(server_time / 1000)
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
        logger.info("⏰ Time synchronized with Binance servers")

    except Exception as e:
        logger.warning(f"⚠️ Failed to sync time: {e}")


async def main():
    """
    🚀 ГЛАВНАЯ функция с интеграцией OrderExecutionService (Issue #7) + BuyOrderMonitor
    """

    # Синхронизация времени
    time_sync()

    # Настройки торговой пары из конфигурации
    config = load_config()
    pair_cfg = config.get("currency_pair", {})
    base_currency = pair_cfg.get("base_currency", "ETH")
    quote_currency = pair_cfg.get("quote_currency", "USDT")
    symbol_ccxt = f"{base_currency}{quote_currency}"
    symbol_display = f"{base_currency}/{quote_currency}"

    logger.info("🚀 ЗАПУСК AutoTrade v2.2.0+ с OrderExecutionService + BuyOrderMonitor")
    logger.info(f"   💱 Валютная пара: {symbol_display} ({symbol_ccxt})")
    logger.info(f"   📊 Issue #7: Реальная торговля ВКЛЮЧЕНА")
    logger.info(f"   🕒 BuyOrderMonitor: Проверка протухших BUY ордеров ВКЛЮЧЕНА")
    logger.info("="*60)

    # Инициализация переменных для finally блока
    buy_order_monitor = None

    try:
        # 1. 🏗️ СОЗДАНИЕ ВАЛЮТНОЙ ПАРЫ
        currency_pair = CurrencyPair(
            base_currency=base_currency,
            quote_currency=quote_currency,
            symbol=symbol_ccxt,
            order_life_time=pair_cfg.get("order_life_time", 1),
            deal_quota=pair_cfg.get("deal_quota", 15.0),
            min_step=pair_cfg.get("min_step", 0.1),
            price_step=pair_cfg.get("price_step", 0.0001),
            profit_markup=pair_cfg.get("profit_markup", 1.5),
            deal_count=pair_cfg.get("deal_count", 3),
        )
        logger.info(f"✅ Валютная пара создана: {currency_pair.symbol}")

        # 2. 🚀 СОЗДАНИЕ КОННЕКТОРОВ (Production + Sandbox)
        logger.info("🔗 Инициализация коннекторов...")

        # Production коннектор для live данных (тикеры, стаканы)
        pro_exchange_connector_prod = CcxtExchangeConnector(
            exchange_name="binance",
            use_sandbox=False
        )

        # Sandbox коннектор для торговых операций (ордера, балансы)
        pro_exchange_connector_sandbox = CcxtExchangeConnector(
            exchange_name="binance",
            use_sandbox=True
        )

        logger.info("✅ Коннекторы инициализированы")
        logger.info(f"   📡 Production connector: ✅ (live data)")
        logger.info(f"   🧪 Sandbox connector: ✅ (trading operations)")
        logger.info(f"   🚀 Enhanced connector: ✅ (real API calls)")

        # 3. 💾 СОЗДАНИЕ РЕПОЗИТОРИЕВ (Enhanced версии)
        logger.info("💾 Инициализация репозиториев...")

        deals_repo = InMemoryDealsRepository()

        # 🆕 ENHANCED Orders Repository с индексами и поиском
        orders_repo = InMemoryOrdersRepository(max_orders=50000)

        logger.info("✅ Репозитории созданы")
        logger.info(f"   📋 Deals repository: InMemory")
        logger.info(f"   📦 Orders repository: Enhanced InMemory (max: 50K)")

        # 4. 🏭 СОЗДАНИЕ ФАБРИК (Enhanced версии)
        logger.info("🏭 Инициализация фабрик...")

        # 🆕 ENHANCED Order Factory с валидацией
        order_factory = OrderFactory()

        # Загружаем exchange info для фабрики
        try:

            symbol_info = await pro_exchange_connector_prod.get_symbol_info(symbol_ccxt)
            order_factory.update_exchange_info(symbol_ccxt, symbol_info)
            logger.info(f"✅ Exchange info загружена для {symbol_ccxt}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load exchange info: {e}")

        # Deal Factory (остается старой)
        from domain.factories.deal_factory import DealFactory
        deal_factory = DealFactory(order_factory)

        logger.info("✅ Фабрики созданы")
        logger.info(f"   🏭 Order Factory: Enhanced с валидацией")
        logger.info(f"   🏭 Deal Factory: Standard")

        # 5. 🎛️ СОЗДАНИЕ СЕРВИСОВ (Issue #7)
        logger.info("🎛️ Создание торговых сервисов...")

        # 🚀 ENHANCED Order Service с реальным API
        order_service = OrderService(
            orders_repo=orders_repo,
            order_factory=order_factory,
            exchange_connector=pro_exchange_connector_sandbox  # Подключаем реальный API
        )

        # Deal Service (остается старым)
        deal_service = DealService(deals_repo, order_service, deal_factory)

        # 🆕 ГЛАВНЫЙ OrderExecutionService (Issue #7)
        order_execution_service = OrderExecutionService(
            order_service=order_service,
            deal_service=deal_service,
            exchange_connector=pro_exchange_connector_sandbox
        )

        # 🕒 НОВЫЙ BuyOrderMonitor (мониторинг тухляков)
        buy_order_monitor = BuyOrderMonitor(
            order_service=order_service,
            exchange_connector=pro_exchange_connector_sandbox,
            max_age_minutes=15.0,           # 15 минут максимум
            max_price_deviation_percent=3.0, # 3% отклонение цены
            check_interval_seconds=60       # Проверка каждую минуту
        )

        logger.info("✅ Торговые сервисы созданы")
        logger.info(f"   🎛️ OrderService: Enhanced с реальным API")
        logger.info(f"   💼 DealService: Standard")
        logger.info(f"   🚀 OrderExecutionService: НОВЫЙ главный сервис")
        logger.info(f"   🕒 BuyOrderMonitor: Мониторинг протухших BUY ордеров")

        # 6. 🧪 ТЕСТ ПОДКЛЮЧЕНИЯ К БИРЖЕ
        logger.info("🧪 Тестирование подключения к бирже...")

        connection_test = await pro_exchange_connector_sandbox.test_connection()
        if connection_test:
            logger.info("✅ Подключение к бирже успешно")

            # Показываем баланс
            try:
                balance = await pro_exchange_connector_sandbox.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0.0)
                logger.info(f"💰 Доступный баланс: {usdt_balance:.4f} USDT")
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch balance: {e}")
        else:
            logger.error("❌ Подключение к бирже неудачно")
            logger.error("❌ Завершение работы...")
            return

        # 7. ⚙️ НАСТРОЙКА OrderExecutionService
        logger.info("⚙️ Настройка OrderExecutionService...")

        order_execution_service.configure_execution_settings(
            max_execution_time_sec=30.0,       # 30 секунд на выполнение
            enable_risk_checks=True,           # Включить проверки рисков
            enable_balance_checks=True,        # Включить проверки баланса
            enable_slippage_protection=True    # Включить защиту от слиппеджа
        )

        settings = order_execution_service.get_current_settings()
        logger.info("✅ OrderExecutionService настроен:")
        for key, value in settings.items():
            logger.info(f"   📊 {key}: {value}")

        # 8. 🕒 ЗАПУСК МОНИТОРИНГА ТУХЛЯКОВ
        logger.info("🕒 Запуск мониторинга протухших BUY ордеров...")
        asyncio.create_task(buy_order_monitor.start_monitoring())

        monitor_stats = buy_order_monitor.get_statistics()
        logger.info("✅ BuyOrderMonitor запущен:")
        logger.info(f"   ⏱️ Максимальный возраст: {monitor_stats['max_age_minutes']} минут")
        logger.info(f"   📈 Максимальное отклонение цены: {monitor_stats['max_price_deviation_percent']}%")
        logger.info(f"   🔄 Интервал проверки: {monitor_stats['check_interval_seconds']} секунд")

        # 9. 📊 ПОКАЗЫВАЕМ СТАТИСТИКУ СИСТЕМЫ
        logger.info("📊 Статистика системы:")

        # Статистика репозиториев
        orders_stats = orders_repo.get_statistics()
        logger.info(f"   📦 Orders repository: {orders_stats['total_orders']} ордеров")

        # Статистика сервисов
        order_stats = order_service.get_statistics()
        execution_stats = order_execution_service.get_execution_statistics()
        logger.info(f"   🎛️ OrderService: {order_stats['success_rate']:.1f}% success rate")
        logger.info(f"   🚀 OrderExecutionService: {execution_stats['total_executions']} executions")

        # 10. 🚀 ЗАПУСК ТОРГОВЛИ
        logger.info("🚀 СИСТЕМА ГОТОВА К ЗАПУСКУ ТОРГОВЛИ")
        logger.info(f"   💱 Валютная пара: {symbol_display}")
        logger.info(f"   💰 Бюджет на сделку: {currency_pair.deal_quota} USDT")
        logger.info(f"   🎯 Целевая прибыль: {currency_pair.profit_markup}%")
        logger.info(f"   📊 Реальная торговля: ✅ ВКЛЮЧЕНА (Issue #7)")
        logger.info(f"   🕒 Мониторинг тухляков: ✅ ВКЛЮЧЕН")
        logger.info(f"   🧪 Режим: Sandbox (безопасно)")
        logger.info("="*80)

        # Запуск торгового цикла с новыми сервисами
        await run_realtime_trading(
            pro_exchange_connector_prod=pro_exchange_connector_prod,
            pro_exchange_connector_sandbox=pro_exchange_connector_sandbox,
            currency_pair=currency_pair,
            deal_service=deal_service,
            order_execution_service=order_execution_service,  # 🆕 Передаем новый сервис
            buy_order_monitor=buy_order_monitor  # 🕒 Передаем монитор тухляков
        )

    except Exception as e:
        logger.error(f"❌ Критическая ошибка в main(): {e}")
        raise
    finally:
        # Закрываем соединения
        try:
            # Останавливаем мониторинг тухляков
            if buy_order_monitor:
                buy_order_monitor.stop_monitoring()
                logger.info("🔴 BuyOrderMonitor остановлен")

        except Exception as e:
            logger.error(f"❌ Error closing connections: {e}")




if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("🛑 Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        logger.info("👋 AutoTrade завершен")