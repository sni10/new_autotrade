# main.py - Clean version for AutoTrade v2.3.4
import asyncio
import sys
import os
import logging
import requests
import pytz
from datetime import datetime
try:
    import win32api
except ImportError:
    win32api = None
import time
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

from domain.entities.currency_pair import CurrencyPair
from domain.services.deals.deal_service import DealService
from domain.services.orders.order_service import OrderService
from domain.services.orders.order_execution_service import OrderExecutionService
from domain.services.orders.buy_order_monitor import BuyOrderMonitor
from domain.factories.order_factory import OrderFactory
from domain.factories.deal_factory import DealFactory
from domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer
from domain.services.risk.stop_loss_monitor import StopLossMonitor
from domain.services.deals.deal_completion_monitor import DealCompletionMonitor

# Репозитории (память, кеш, файлы - НЕ база данных)
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from config.config_loader import load_config
from application.use_cases.run_realtime_trading import run_realtime_trading

# Настройка логирования с поддержкой Unicode
import sys

# Создаем обработчики с правильной кодировкой
file_handler = logging.FileHandler(
    f'logs/autotrade_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log',
    encoding='utf-8'
)

# Для консоли используем UTF-8 с обработкой ошибок
console_handler = logging.StreamHandler(sys.stdout)
if sys.platform == "win32":
    # На Windows устанавливаем UTF-8 для stdout
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        # Для старых версий Python
        pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

def sync_time():
    """Синхронизация времени для Windows"""
    if win32api is None:
        logger.warning("⚠️ win32api недоступен, синхронизация времени пропущена")
        return
    
    try:
        logger.info("Попытка синхронизации времени для Windows...")
        response = requests.get('http://worldtimeapi.org/api/timezone/UTC', timeout=5)
        if response.status_code == 200:
            utc_time = datetime.fromisoformat(response.json()['datetime'].replace('Z', '+00:00'))
            win32api.SetSystemTime(utc_time.timetuple()[:8])
            logger.info("✅ Время синхронизировано с UTC")
        else:
            logger.warning("⚠️ Не удалось получить время с сервера")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось синхронизировать время: {e}")

async def main():
    """Главная функция запуска AutoTrade"""
    
    # Синхронизация времени
    sync_time()
    
    # Загрузка конфигурации
    config = load_config()
    pair_cfg = config.get("currency_pair", {})
    
    base_currency = pair_cfg.get("base_currency", "MAGIC")
    quote_currency = pair_cfg.get("quote_currency", "USDT")
    symbol_ccxt = f"{base_currency}/{quote_currency}"
    symbol_display = f"{base_currency}/{quote_currency}"
    
    logger.info(f"🚀 ЗАПУСК AutoTrade v2.3.4 для {symbol_display}")
    
    buy_order_monitor = None
    stop_loss_monitor = None
    deal_completion_monitor = None
    pro_exchange_connector_prod = None
    pro_exchange_connector_sandbox = None
    
    try:
        # 1. Инициализация коннекторов
        pro_exchange_connector_prod = CcxtExchangeConnector(use_sandbox=False)
        pro_exchange_connector_sandbox = CcxtExchangeConnector(use_sandbox=True)
        logger.info("✅ Коннекторы инициализированы (Production, Sandbox)")
        
        # 2. Инициализация репозиториев (память, НЕ база данных)
        deals_repo = InMemoryDealsRepository()
        orders_repo = InMemoryOrdersRepository(max_orders=50000)
        logger.info("✅ Репозитории созданы (InMemory)")
        
        # 3. Инициализация фабрик с exchange info
        order_factory = OrderFactory()
        symbol_info = await pro_exchange_connector_prod.get_symbol_info(symbol_ccxt)
        order_factory.update_exchange_info(symbol_ccxt, symbol_info)
        deal_factory = DealFactory(order_factory)
        logger.info(f"✅ Фабрики созданы, Exchange info для {symbol_ccxt} загружена")
        
        # 4. Создание CurrencyPair с правильными данными биржи
        currency_pair = CurrencyPair(
            base_currency=base_currency,
            quote_currency=quote_currency,
            symbol=symbol_ccxt,
            order_life_time=pair_cfg.get("order_life_time", 1),
            deal_quota=pair_cfg.get("deal_quota", 25.0),
            profit_markup=pair_cfg.get("profit_markup", 0.015),  # 1.5%
            deal_count=pair_cfg.get("deal_count", 3),
        )
        
        # КРИТИЧЕСКИ ВАЖНО: Обновляем CurrencyPair данными с биржи
        currency_pair.update_exchange_info(symbol_info)
        logger.info(f"✅ CurrencyPair создан и обновлен данными биржи для {currency_pair.symbol}")
        
        # 5. Инициализация сервисов
        order_service = OrderService(orders_repo, order_factory, pro_exchange_connector_sandbox)
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
            check_interval_seconds=buy_order_monitor_cfg.get("check_interval_seconds", 10)
        )
        asyncio.create_task(buy_order_monitor.start_monitoring())
        logger.info("✅ BuyOrderMonitor запущен")
        
        # 7. Запуск мониторинга завершения сделок
        deal_completion_monitor = DealCompletionMonitor(
            deal_service=deal_service,
            order_service=order_service,
            check_interval_seconds=30
        )
        asyncio.create_task(deal_completion_monitor.start_monitoring())
        logger.info("✅ DealCompletionMonitor запущен")
        
        # 8. Настройка стоп-лосса (если включен)
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
        
        # 9. Проверка подключения и баланса
        if not await pro_exchange_connector_sandbox.test_connection():
            logger.error("❌ Подключение к бирже неудачно. Завершение работы...")
            return
        
        balance = await pro_exchange_connector_sandbox.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0.0)
        logger.info(f"💰 Доступный баланс в песочнице: {usdt_balance:.4f} USDT")
        
        # 10. Информация о готовности системы
        logger.info("="*80)
        logger.info("🚀 СИСТЕМА ГОТОВА К ЗАПУСКУ ТОРГОВЛИ")
        logger.info(f"   - Валютная пара: {currency_pair.symbol}")
        logger.info(f"   - Бюджет на сделку: {currency_pair.deal_quota} USDT")
        logger.info(f"   - Режим: Sandbox (безопасно)")
        logger.info("="*80)
        
        # 11. Запуск торгового цикла
        await run_realtime_trading(
            pro_exchange_connector_prod=pro_exchange_connector_prod,
            pro_exchange_connector_sandbox=pro_exchange_connector_sandbox,
            currency_pair=currency_pair,
            deal_service=deal_service,
            order_execution_service=order_execution_service,
            buy_order_monitor=buy_order_monitor,
            orderbook_analyzer=orderbook_analyzer,
            deal_completion_monitor=deal_completion_monitor,
            stop_loss_monitor=stop_loss_monitor if 'stop_loss_monitor' in locals() else None
        )
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в main(): {e}", exc_info=True)
    finally:
        logger.info("🔴 Завершение работы, закрытие соединений...")
        if buy_order_monitor:
            buy_order_monitor.stop_monitoring()
        if deal_completion_monitor:
            deal_completion_monitor.stop_monitoring()
        if 'stop_loss_monitor' in locals() and stop_loss_monitor:
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