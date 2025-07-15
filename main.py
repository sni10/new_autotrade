# main.py
import asyncio
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# --- Настройка путей и логирования ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
load_dotenv()

log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_filename = f"autotrade_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(os.path.join(log_dir, log_filename), encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Основные импорты проекта ---
from src.config.config_loader import load_config
from src.domain.entities.currency_pair import CurrencyPair
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from src.infrastructure.database.postgres_provider import PostgresPersistenceProvider
# Репозитории
from src.infrastructure.repositories.persistent_deals_repository import PersistentDealsRepository
from src.infrastructure.repositories.persistent_orders_repository import PersistentOrdersRepository
from src.infrastructure.repositories.persistent_tickers_repository import PersistentTickersRepository
from src.infrastructure.repositories.persistent_order_books_repository import PersistentOrderBooksRepository
from src.infrastructure.repositories.persistent_indicators_repository import PersistentIndicatorsRepository
# Фабрики
from src.domain.factories.order_factory import OrderFactory
from src.domain.factories.deal_factory import DealFactory
# Сервисы
from src.domain.services.orders.order_service import OrderService
from src.domain.services.deals.deal_service import DealService
from src.domain.services.orders.order_execution_service import OrderExecutionService
from src.domain.services.market_data.ticker_service import TickerService
from src.domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer
from src.domain.services.orders.buy_order_monitor import BuyOrderMonitor
from src.domain.services.deals.deal_completion_monitor import DealCompletionMonitor
from src.domain.services.risk.stop_loss_monitor import StopLossMonitor
from src.application.services.persistence_sync_service import PersistenceSyncService
# Use Case
from src.application.use_cases.run_realtime_trading import run_realtime_trading

async def main():
    config = load_config()
    db_provider = None
    sync_service = None
    exchange_connector = None

    try:
        # 1. --- Инициализация базовых компонентов ---
        logger.info("--- 1. Initializing Components ---")
        db_provider = PostgresPersistenceProvider(config.get("database", {}))
        await db_provider.connect()

        schema_dir = Path(__file__).resolve().parent / "src" / "infrastructure" / "database" / "schemas"
        for schema_file in sorted(schema_dir.glob("*.sql")):
            await db_provider.execute_schema(str(schema_file))
        logger.info("✅ Database schemas applied.")

        exchange_connector = CcxtExchangeConnector(use_sandbox=True)
        await exchange_connector.load_markets()
        logger.info("✅ Exchange connector initialized.")

        # 2. --- Инициализация репозиториев и загрузка состояния ---
        logger.info("--- 2. Initializing Repositories & Loading State ---")
        orders_repo = PersistentOrdersRepository(db_provider)
        await orders_repo.load()
        logger.info(f"✅ Orders repository initialized. Loaded {len(orders_repo.get_all())} orders.")

        all_orders_map = {o.order_id: o for o in orders_repo.get_all()}
        
        pair_cfg = config.get("currency_pair", {})
        currency_pair = CurrencyPair(
            base_currency=pair_cfg.get("base_currency", "ETH"),
            quote_currency=pair_cfg.get("quote_currency", "USDT"),
            symbol=f"{pair_cfg.get('base_currency', 'ETH')}/{pair_cfg.get('quote_currency', 'USDT')}",
            deal_quota=pair_cfg.get("deal_quota", 100.0),
            deal_count=pair_cfg.get("deal_count", 1),
            profit_markup=pair_cfg.get("profit_markup", 0.005)
        )
        symbol_info = await exchange_connector.get_symbol_info(currency_pair.symbol)
        currency_pair.update_exchange_info(symbol_info)
        all_currency_pairs = {currency_pair.symbol: currency_pair}

        deals_repo = PersistentDealsRepository(db_provider)
        await deals_repo.load(all_currency_pairs, all_orders_map)
        logger.info(f"✅ Deals repository initialized. Loaded {len(deals_repo.get_all())} deals.")

        tickers_repo = PersistentTickersRepository(db_provider)
        indicators_repo = PersistentIndicatorsRepository(db_provider)
        order_books_repo = PersistentOrderBooksRepository(db_provider)
        logger.info("✅ Market data repositories initialized.")

        # 3. --- И��ициализация фабрик и сервисов ---
        logger.info("--- 3. Initializing Factories & Services ---")
        order_factory = OrderFactory()
        order_factory.update_exchange_info(currency_pair.symbol, symbol_info)
        deal_factory = DealFactory(order_factory)

        order_service = OrderService(orders_repo, order_factory, exchange_connector)
        deal_service = DealService(deals_repo, order_service, deal_factory, exchange_connector)
        order_execution_service = OrderExecutionService(order_service, deal_service, exchange_connector)
        ticker_service = TickerService(tickers_repo, indicators_repo)
        orderbook_analyzer = OrderBookAnalyzer(config.get("orderbook_analyzer", {}))
        logger.info("✅ Core services initialized.")

        # 4. --- Запуск фоновых задач (Мониторы и Синхронизация) ---
        logger.info("--- 4. Starting Background Tasks ---")
        buy_monitor_config = config.get("buy_order_monitor", {})
        # Фильтруем только поддерживаемые параметры
        supported_params = {k: v for k, v in buy_monitor_config.items() 
                          if k in ['max_age_minutes', 'max_price_deviation_percent', 'check_interval_seconds']}
        buy_monitor = BuyOrderMonitor(order_service, deal_service, exchange_connector, **supported_params)
        deal_completion_monitor = DealCompletionMonitor(deal_service, order_service, check_interval_seconds=30)
        risk_config = config.get("risk_management", {})
        # Фильтруем и адаптируем параметры StopLossMonitor
        stop_loss_params = {}
        if 'stop_loss_percent' in risk_config:
            stop_loss_params['stop_loss_percent'] = risk_config['stop_loss_percent']
        if 'stop_loss_check_interval_seconds' in risk_config:
            stop_loss_params['check_interval_seconds'] = risk_config['stop_loss_check_interval_seconds']
        for param in ['warning_percent', 'critical_percent', 'emergency_percent']:
            if param in risk_config:
                stop_loss_params[param] = risk_config[param]
        stop_loss_monitor = StopLossMonitor(deal_service, order_execution_service, exchange_connector, orderbook_analyzer, **stop_loss_params)
        
        asyncio.create_task(buy_monitor.start_monitoring())
        asyncio.create_task(deal_completion_monitor.start_monitoring())
        if config.get("risk_management", {}).get("enable_stop_loss"):
            asyncio.create_task(stop_loss_monitor.start_monitoring())
        logger.info("✅ All monitors started.")

        sync_service = PersistenceSyncService(
            repositories=[deals_repo, orders_repo, tickers_repo, order_books_repo, indicators_repo],
            sync_interval_seconds=config.get("database", {}).get("sync_interval", 60)
        )
        asyncio.create_task(sync_service.start())

        # 5. --- Запуск основного торгового цикла ---
        logger.info("--- 5. Starting Main Trading Loop ---")
        # В run_realtime_trading нужно будет передать новые репозитории, если они там нужны
        # Пока что оставляем как есть, предполагая, что он работает через сервисы
        await run_realtime_trading(
            pro_exchange_connector_prod=exchange_connector,
            pro_exchange_connector_sandbox=None, # Убрали дублирующий коннектор
            currency_pair=currency_pair,
            deal_service=deal_service,
            order_execution_service=order_execution_service,
            buy_order_monitor=buy_monitor,
            orderbook_analyzer=orderbook_analyzer,
            deal_completion_monitor=deal_completion_monitor,
            stop_loss_monitor=stop_loss_monitor
        )

    except Exception as e:
        logger.critical(f"🔥🔥🔥 A critical error occurred in main: {e}", exc_info=True)
    finally:
        logger.info("--- Shutting Down ---")
        if sync_service:
            await sync_service.stop()
        if exchange_connector:
            await exchange_connector.close()
        if db_provider:
            await db_provider.close()
        logger.info("👋 Application shut down gracefully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 User interrupted the program.")
    except Exception as e:
        logger.critical(f"🔥🔥🔥 Unhandled exception at the top level: {e}", exc_info=True)
