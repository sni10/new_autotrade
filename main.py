# main.py.new - ИНТЕГРАЦИЯ Issue #7 OrderExecutionService + BuyOrderMonitor
import asyncio
import sys
import logging
from datetime import datetime
import pytz
import requests
import win32api
import time

# 🆕 НОВЫЕ ИМПОРТЫ для Issue #7
from domain.entities.currency_pair import CurrencyPair
from domain.services.deal_service import DealService

# 🚀 ОБНОВЛЕННЫЕ СЕРВИСЫ
from domain.services.order_service import OrderService  # Используем .new версию
from domain.services.order_execution_service import OrderExecutionService  # НОВЫЙ главный сервис
from domain.services.buy_order_monitor import BuyOrderMonitor  # 🆕 МОНИТОРИНГ ТУХЛЯКОВ
from domain.factories.order_factory import OrderFactory  # Используем .new версию

# 🚀 ОБНОВЛЕННЫЕ РЕПОЗИТОРИИ
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository  # Используем .new версию

# 🚀 ОБНОВЛЕННЫЕ КОННЕКТОРЫ
from infrastructure.connectors.pro_exchange_connector import CcxtProMarketDataConnector
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector  # Используем .new версию

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

    # Настройки торговой пары
    base_currency = "ETH"
    quote_currency = "USDT"
    symbol_ccxt = f"{base_currency}{quote_currency}"  # "MAGICUSDT"
    symbol_display = f"{base_currency}/{quote_currency}"  # "MAGIC/USDT"

    logger.info("🚀 ЗАПУСК AutoTrade v2.2.0+ с OrderExecutionService + BuyOrderMonitor")
    logger.info(f"   💱 Валютная пара: {symbol_display} ({symbol_ccxt})")
    logger.info(f"   📊 Issue #7: Реальная торговля ВКЛЮЧЕНА")
    logger.info(f"   🕒 BuyOrderMonitor: Проверка протухших BUY ордеров ВКЛЮЧЕНА")
    logger.info("="*60)

    # Инициализация переменных для finally блока
    enhanced_exchange_connector = None
    buy_order_monitor = None

    try:
        # 1. 🏗️ СОЗДАНИЕ ВАЛЮТНОЙ ПАРЫ
        currency_pair = CurrencyPair(
            base_currency=base_currency,
            quote_currency=quote_currency,
            symbol=symbol_ccxt,
            order_life_time=1,
            deal_quota=15.0,        # Бюджет на сделку
            min_step=0.1,
            price_step=0.0001,
            profit_markup=1.5,      # Целевая прибыль %
            deal_count=3000         # Макс. активных сделок
        )
        logger.info(f"✅ Валютная пара создана: {currency_pair.symbol}")

        # 2. 🚀 СОЗДАНИЕ КОННЕКТОРОВ (Production + Sandbox)
        logger.info("🔗 Инициализация коннекторов...")

        # Production коннектор для live данных (тикеры, стаканы)
        pro_exchange_connector_prod = CcxtProMarketDataConnector(
            exchange_name="binance",
            use_sandbox=False
        )

        # Sandbox коннектор для торговых операций (ордера, балансы)
        pro_exchange_connector_sandbox = CcxtProMarketDataConnector(
            exchange_name="binance",
            use_sandbox=True
        )

        # 🆕 НОВЫЙ Enhanced Exchange Connector для реальной торговли
        enhanced_exchange_connector = CcxtExchangeConnector(
            exchange_name="binance",
            use_sandbox=True  # ВАЖНО: начинаем с sandbox для безопасности
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
            symbol_info = await enhanced_exchange_connector.get_symbol_info(symbol_ccxt)
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
            exchange_connector=enhanced_exchange_connector  # Подключаем реальный API
        )

        # Deal Service (остается старым)
        deal_service = DealService(deals_repo, order_service, deal_factory)

        # 🆕 ГЛАВНЫЙ OrderExecutionService (Issue #7)
        order_execution_service = OrderExecutionService(
            order_service=order_service,
            deal_service=deal_service,
            exchange_connector=enhanced_exchange_connector
        )

        # 🕒 НОВЫЙ BuyOrderMonitor (мониторинг тухляков)
        buy_order_monitor = BuyOrderMonitor(
            order_service=order_service,
            exchange_connector=enhanced_exchange_connector,
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

        connection_test = await enhanced_exchange_connector.test_connection()
        if connection_test:
            logger.info("✅ Подключение к бирже успешно")

            # Показываем баланс
            try:
                balance = await enhanced_exchange_connector.fetch_balance()
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
        await run_realtime_trading_enhanced(
            pro_exchange_connector_prod=pro_exchange_connector_prod,
            pro_exchange_connector_sandbox=pro_exchange_connector_sandbox,
            enhanced_exchange_connector=enhanced_exchange_connector,
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

            if enhanced_exchange_connector:
                await enhanced_exchange_connector.close()
                logger.info("🔌 Enhanced exchange connector closed")
        except Exception as e:
            logger.error(f"❌ Error closing connections: {e}")


async def run_realtime_trading_enhanced(
        pro_exchange_connector_prod,
        pro_exchange_connector_sandbox,
        enhanced_exchange_connector,
        currency_pair,
        deal_service,
        order_execution_service,
        buy_order_monitor
):
    """
    🚀 АДАПТИРОВАННАЯ версия торгового цикла для Issue #7 + BuyOrderMonitor

    Это упрощенная версия run_realtime_trading.py которая использует
    новый OrderExecutionService вместо прямого создания ордеров
    + мониторинг протухших BUY ордеров
    """

    # Импортируем необходимые сервисы
    from infrastructure.repositories.tickers_repository import InMemoryTickerRepository
    from domain.services.ticker_service import TickerService
    from application.utils.performance_logger import PerformanceLogger
    from domain.services.signal_cooldown_manager import SignalCooldownManager

    # Инициализация сервисов для анализа
    repository = InMemoryTickerRepository(max_size=5000)
    ticker_service = TickerService(repository)
    logger_perf = PerformanceLogger(log_interval_seconds=10)
    cooldown_manager = SignalCooldownManager()

    counter = 0

    logger.info("🚀 Запуск расширенного торгового цикла с OrderExecutionService + BuyOrderMonitor")

    try:
        while True:
            try:
                start_watch = time.time()

                # Получение тикера
                ticker_data = await pro_exchange_connector_prod.client.watch_ticker(currency_pair.symbol)

                # Обработка тикера
                start_process = time.time()
                await ticker_service.process_ticker(ticker_data)
                end_process = time.time()

                processing_time = end_process - start_process
                counter += 1

                # Проверяем достаточно ли данных
                if len(repository.tickers) < 50:
                    if counter % 100 == 0:
                        logger.info(f"🟡 Накоплено {len(repository.tickers)} тиков, нужно 50")
                    continue

                # Получаем сигнал
                ticker_signal = await ticker_service.get_signal()

                # Логирование производительности
                if len(repository.tickers) > 0:
                    last_ticker = repository.tickers[-1]
                    signals_count = len(last_ticker.signals) if last_ticker.signals else 0
                    logger_perf.log_tick(
                        price=float(last_ticker.close),
                        processing_time=processing_time,
                        signals_count=signals_count
                    )

                # 🎯 ОБРАБОТКА СИГНАЛА ПОКУПКИ с OrderExecutionService
                if ticker_signal == "BUY":
                    if len(repository.tickers) > 0:
                        last_ticker = repository.tickers[-1]
                        if last_ticker.signals:
                            # Получаем текущие данные
                            current_price = float(last_ticker.close)

                            # 🛡️ ПРОВЕРКА ЛИМИТА АКТИВНЫХ СДЕЛОК
                            active_deals_count = len(deal_service.get_open_deals())
                            can_buy, reason = cooldown_manager.can_buy(
                                active_deals_count=active_deals_count,
                                max_deals=currency_pair.deal_count
                            )

                            if not can_buy:
                                if counter % 20 == 0:
                                    logger.info(f"🚫 BUY заблокирован: {reason} | Цена: {current_price}")
                                continue

                            # ✅ СИГНАЛ РАЗРЕШЕН
                            logger.info("\n" + "="*80)
                            logger.info("🟢🔥 MACD СИГНАЛ ПОКУПКИ ОБНАРУЖЕН! ВЫПОЛНЯЕМ ЧЕРЕЗ OrderExecutionService...")
                            logger.info("="*80)

                            macd = last_ticker.signals.get('macd', 0.0)
                            signal = last_ticker.signals.get('signal', 0.0)
                            hist = last_ticker.signals.get('histogram', 0.0)

                            logger.info(f"   📈 MACD > Signal: {macd:.6f} > {signal:.6f}")
                            logger.info(f"   📊 Histogram: {hist:.6f}")
                            logger.info(f"   💰 Текущая цена: {current_price} USDT")
                            logger.info(f"   🎯 Активных сделок: {active_deals_count}/{currency_pair.deal_count}")

                            # 🧮 РАСЧЕТ СТРАТЕГИИ
                            try:
                                strategy_result = ticker_service.calculate_strategy(
                                    buy_price=current_price,
                                    budget=currency_pair.deal_quota,
                                    min_step=currency_pair.min_step,
                                    price_step=currency_pair.price_step,
                                    buy_fee_percent=0.1,
                                    sell_fee_percent=0.1,
                                    profit_percent=currency_pair.profit_markup
                                )

                                if isinstance(strategy_result, dict) and "comment" in strategy_result:
                                    logger.warning(f"❌ Ошибка в калькуляторе: {strategy_result['comment']}")
                                    continue

                                # 🚀 ВЫПОЛНЕНИЕ ЧЕРЕЗ OrderExecutionService (Issue #7)
                                logger.info("🚀 Выполнение стратегии через OrderExecutionService...")

                                execution_result = await order_execution_service.execute_trading_strategy(
                                    currency_pair=currency_pair,
                                    strategy_result=strategy_result,
                                    metadata={
                                        'trigger': 'macd_signal',
                                        'macd_data': {
                                            'macd': macd,
                                            'signal': signal,
                                            'histogram': hist
                                        },
                                        'market_price': current_price,
                                        'timestamp': int(time.time() * 1000)
                                    }
                                )

                                if execution_result.success:
                                    logger.info("🎉 СТРАТЕГИЯ ВЫПОЛНЕНА УСПЕШНО!")
                                    logger.info(f"   ✅ Сделка: #{execution_result.deal_id}")
                                    logger.info(f"   🛒 BUY ордер: {execution_result.buy_order.exchange_id}")
                                    logger.info(f"   🏷️ SELL ордер: {execution_result.sell_order.exchange_id}")
                                    logger.info(f"   💰 Общая стоимость: {execution_result.total_cost:.4f} USDT")
                                    logger.info(f"   📈 Ожидаемая прибыль: {execution_result.expected_profit:.4f} USDT")
                                    logger.info(f"   💸 Комиссии: {execution_result.fees:.4f} USDT")
                                    logger.info(f"   ⏱️ Время выполнения: {execution_result.execution_time_ms:.1f}ms")

                                    # Обновляем статистику
                                    execution_stats = order_execution_service.get_execution_statistics()
                                    logger.info(f"   📊 Общая статистика: {execution_stats['successful_executions']}/{execution_stats['total_executions']} успешных")

                                else:
                                    logger.error("❌ СТРАТЕГИЯ НЕ ВЫПОЛНЕНА!")
                                    logger.error(f"   💔 Ошибка: {execution_result.error_message}")
                                    if execution_result.warnings:
                                        for warning in execution_result.warnings:
                                            logger.warning(f"   ⚠️ {warning}")

                                    # Показываем статистику ошибок
                                    execution_stats = order_execution_service.get_execution_statistics()
                                    logger.error(f"   📊 Статистика ошибок: {execution_stats['failed_executions']} неудач")

                            except Exception as calc_error:
                                logger.error(f"❌ Ошибка в стратегии: {calc_error}")

                            logger.info("="*80)
                            logger.info("🔄 Продолжаем мониторинг...\n")

                # 📊 ПЕРИОДИЧЕСКАЯ СТАТИСТИКА (включая BuyOrderMonitor)
                if counter % 100 == 0:
                    # Статистика OrderExecutionService
                    execution_stats = order_execution_service.get_execution_statistics()
                    logger.info(f"\n📊 СТАТИСТИКА OrderExecutionService (тик {counter}):")
                    logger.info(f"   🚀 Всего выполнений: {execution_stats['total_executions']}")
                    logger.info(f"   ✅ Успешных: {execution_stats['successful_executions']}")
                    logger.info(f"   ❌ Неудачных: {execution_stats['failed_executions']}")
                    logger.info(f"   📈 Процент успеха: {execution_stats['success_rate']:.1f}%")
                    logger.info(f"   💰 Общий объем: {execution_stats['total_volume']:.4f} USDT")
                    logger.info(f"   ⏱️ Среднее время: {execution_stats['average_execution_time_ms']:.1f}ms")

                    # Статистика ордеров
                    order_stats = order_execution_service.order_service.get_statistics()
                    logger.info(f"   📦 Всего ордеров: {order_stats['total_orders']}")
                    logger.info(f"   🔄 Открытых ордеров: {order_stats['open_orders']}")

                    # Статистика активных сделок
                    active_deals = len(deal_service.get_open_deals())
                    logger.info(f"   💼 Активных сделок: {active_deals}")

                    # 🕒 СТАТИСТИКА BuyOrderMonitor
                    monitor_stats = buy_order_monitor.get_statistics()
                    logger.info(f"\n🕒 СТАТИСТИКА BuyOrderMonitor:")
                    logger.info(f"   🔍 Проверок выполнено: {monitor_stats['checks_performed']}")
                    logger.info(f"   🚨 Тухляков найдено: {monitor_stats['stale_orders_found']}")
                    logger.info(f"   ❌ Ордеров отменено: {monitor_stats['orders_cancelled']}")
                    logger.info(f"   🔄 Ордеров пересоздано: {monitor_stats['orders_recreated']}")

            except Exception as e:
                logger.error(f"❌ Ошибка в торговом цикле: {e}")
                await asyncio.sleep(1)  # Пауза при ошибке

    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    finally:
        # Экстренная остановка всей торговли
        logger.info("🚨 Выполнение экстренной остановки...")

        emergency_result = await order_execution_service.emergency_stop_all_trading()
        logger.info(f"🚨 Экстренная остановка завершена:")
        logger.info(f"   ❌ Отменено ордеров: {emergency_result.get('cancelled_orders', 0)}")
        logger.info(f"   📊 Осталось открытых: {emergency_result.get('remaining_open_orders', 0)}")
        logger.info(f"   💼 Активных сделок: {emergency_result.get('open_deals', 0)}")

        # 🕒 Финальная статистика BuyOrderMonitor
        final_monitor_stats = buy_order_monitor.get_statistics()
        logger.info("🕒 ФИНАЛЬНАЯ СТАТИСТИКА BuyOrderMonitor:")
        logger.info(f"   🔍 Всего проверок: {final_monitor_stats['checks_performed']}")
        logger.info(f"   🚨 Всего тухляков: {final_monitor_stats['stale_orders_found']}")
        logger.info(f"   ❌ Всего отменено: {final_monitor_stats['orders_cancelled']}")
        logger.info(f"   🔄 Всего пересоздано: {final_monitor_stats['orders_recreated']}")

        # Финальная статистика OrderExecutionService
        final_stats = order_execution_service.get_execution_statistics()
        logger.info("📊 ФИНАЛЬНАЯ СТАТИСТИКА OrderExecutionService:")
        logger.info(f"   🚀 Всего выполнений: {final_stats['total_executions']}")
        logger.info(f"   ✅ Успешных: {final_stats['successful_executions']}")
        logger.info(f"   📈 Процент успеха: {final_stats['success_rate']:.1f}%")
        logger.info(f"   💰 Общий объем: {final_stats['total_volume']:.4f} USDT")
        logger.info(f"   💸 Общие комиссии: {final_stats['total_fees']:.4f} USDT")


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
