# application/use_cases/run_realtime_trading.py
"""Trading loop using OrderExecutionService and BuyOrderMonitor."""

import asyncio
import time
import logging
from decimal import Decimal

from domain.entities.currency_pair import CurrencyPair
from domain.services.deals.deal_service import DealService
from domain.services.market_data.orderbook_analyzer import OrderBookSignal
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository
from domain.services.market_data.ticker_service import TickerService
from application.utils.performance_logger import PerformanceLogger
from domain.services.trading.signal_cooldown_manager import SignalCooldownManager

logger = logging.getLogger(__name__)


async def run_realtime_trading(
    pro_exchange_connector_prod: CcxtExchangeConnector,
    pro_exchange_connector_sandbox: CcxtExchangeConnector,
    currency_pair: CurrencyPair,
    deal_service: DealService,
    order_execution_service,
    buy_order_monitor, # Возвращено
    orderbook_analyzer,
    deal_completion_monitor=None,  # Добавлен новый параметр
):
    """Simplified trading loop using OrderExecutionService and BuyOrderMonitor."""

    repository = InMemoryTickerRepository(max_size=5000)
    ticker_service = TickerService(repository)
    logger_perf = PerformanceLogger(log_interval_seconds=10)
    cooldown_manager = SignalCooldownManager()

    counter = 0

    logger.info("🚀 Запуск расширенного торгового цикла с OrderExecutionService + BuyOrderMonitor")

    try:
        while True:
            try:
                ticker_data = await pro_exchange_connector_prod.watch_ticker(currency_pair.symbol)

                start_process = time.time()
                await ticker_service.process_ticker(ticker_data)
                end_process = time.time()

                processing_time = end_process - start_process
                counter += 1

                if len(repository.tickers) < 50:
                    if counter % 100 == 0:
                        logger.info(
                            "🟡 Накоплено %s тиков, нужно 50",
                            len(repository.tickers),
                        )
                    continue

                ticker_signal = await ticker_service.get_signal()

                if len(repository.tickers) > 0:
                    last_ticker = repository.tickers[-1]
                    signals_count = len(last_ticker.signals) if last_ticker.signals else 0
                    logger_perf.log_tick(
                        price=float(last_ticker.close),
                        processing_time=processing_time,
                        signals_count=signals_count,
                    )

                if ticker_signal == "BUY":
                    # Анализ стакана
                    orderbook_metrics = orderbook_analyzer.analyze_orderbook(
                        await pro_exchange_connector_prod.watch_order_book(currency_pair.symbol)
                    )

                    if orderbook_metrics.signal in [OrderBookSignal.REJECT, OrderBookSignal.WEAK_SELL, OrderBookSignal.STRONG_SELL]:
                        logger.info(f"🚫 Сигнал MACD отклонен анализатором стакана: {orderbook_metrics.signal.value}")
                        continue
                    
                    # Синхронизация ордеров перед принятием решения
                    await order_execution_service.monitor_active_orders()

                    if len(repository.tickers) > 0:
                        last_ticker = repository.tickers[-1]
                        if last_ticker.signals:
                            current_price = float(last_ticker.close)

                            active_deals_count = len(deal_service.get_open_deals())
                            can_buy, reason = cooldown_manager.can_buy(
                                active_deals_count=active_deals_count,
                                max_deals=currency_pair.deal_count,
                            )

                            if not can_buy:
                                if counter % 20 == 0:
                                    logger.info(
                                        "🚫 BUY заблокирован: %s | Цена: %s",
                                        reason,
                                        current_price,
                                    )
                                continue

                            logger.info("\n" + "=" * 80)
                            logger.info(
                                "🟢🔥 MACD СИГНАЛ ПОКУПКИ ОБНАРУЖЕН! ВЫПОЛНЯЕМ ЧЕРЕЗ OrderExecutionService..."
                            )
                            logger.info("=" * 80)

                            macd = last_ticker.signals.get('macd', 0.0)
                            signal = last_ticker.signals.get('signal', 0.0)
                            hist = last_ticker.signals.get('histogram', 0.0)

                            logger.info("   📈 MACD > Signal: %.6f > %.6f", macd, signal)
                            logger.info("   📊 Histogram: %.6f", hist)
                            logger.info("   💰 Текущая цена: %s USDT", current_price)
                            logger.info(
                                "   🎯 Активных сделок: %s/%s",
                                active_deals_count,
                                currency_pair.deal_count,
                            )

                            try:
                                # Используем бюджет из currency_pair
                                budget = currency_pair.deal_quota

                                # Проверка баланса перед выполнением
                                balance_ok, balance_reason = await deal_service.check_balance_before_deal(
                                    quote_currency=currency_pair.quote_currency,
                                    required_amount=budget
                                )
                                if not balance_ok:
                                    logger.error(f"❌ Недостаточно средств: {balance_reason}")
                                    continue

                                strategy_result = ticker_service.calculate_strategy(
                                    buy_price=current_price,
                                    budget=budget,
                                    currency_pair=currency_pair,
                                    profit_percent=currency_pair.profit_markup,
                                )

                                if isinstance(strategy_result, dict) and "comment" in strategy_result:
                                    logger.error(
                                        "❌ Ошибка в калькуляторе: %s",
                                        strategy_result["comment"],
                                    )
                                    continue

                                logger.info("🚀 Выполнение стратегии через OrderExecutionService...")
                                execution_result = await order_execution_service.execute_trading_strategy(
                                    currency_pair=currency_pair,
                                    strategy_result=strategy_result,
                                    metadata={
                                        'trigger': 'macd_signal',
                                        'macd_data': {
                                            'macd': macd,
                                            'signal': signal,
                                            'histogram': hist,
                                        },
                                        'market_price': current_price,
                                        'timestamp': int(time.time() * 1000),
                                    },
                                )

                                if execution_result.success:
                                    logger.info("🎉 СТРАТЕГИЯ ВЫПОЛНЕНА УСПЕШНО!")
                                else:
                                    logger.error(
                                        "❌ СТРАТЕГИЯ НЕ ВЫПОЛНЕНА: %s",
                                        execution_result.error_message,
                                    )

                            except Exception as calc_error:
                                logger.exception(
                                    "❌ Ошибка в стратегии: %s",
                                    calc_error,
                                )

                            logger.info("=" * 80)
                            logger.info("🔄 Продолжаем мониторинг...\n")

                if counter % 50 == 0:  # Изменено с 100 на 50 для более частого вывода
                    execution_stats = order_execution_service.get_execution_statistics()
                    logger.info("\n📊 СТАТИСТИКА OrderExecutionService (тик %s):", counter)
                    logger.info("   🚀 Всего выполнений: %s", execution_stats["total_executions"])
                    logger.info("   ✅ Успешных: %s", execution_stats["successful_executions"])
                    logger.info("   ❌ Неудачных: %s", execution_stats["failed_executions"])

                    order_stats = order_execution_service.order_service.get_statistics()
                    logger.info("   📦 Всего ордеров: %s", order_stats["total_orders"])
                    logger.info("   🔄 Открытых ордеров: %s", order_stats["open_orders"])

                    all_orders = order_execution_service.order_service.orders_repo.get_all()
                    if all_orders:
                        logger.info("   🔍 ДЕТАЛИ ПО ОРДЕРАМ:")
                        # Получаем шаг цены и количества для корректного ВЫЧИСЛЕНИЯ точности
                        price_step = Decimal(str(currency_pair.precision.get('price', '0.000001')))
                        amount_step = Decimal(str(currency_pair.precision.get('amount', '0.0001')))
                        price_precision = int(price_step.normalize().as_tuple().exponent * -1)
                        amount_precision = int(amount_step.normalize().as_tuple().exponent * -1)

                        # Динамическое создание строки формата
                        log_format = (
                            f"     - ID: %s | DealID: %s | %s | %s | %s | "
                            f"Цена: %s | Кол-во: %s | ExchangeID: %s | Filled: %s | AvgPrice: %s | Fees: %s"
                        )

                        for order in all_orders:
                            # Форматируем цену и количество с правильной точностью
                            formatted_price = f"{order.price:.{price_precision}f}"
                            formatted_amount = f"{order.amount:.{amount_precision}f}"
                            
                            # Форматируем исполненное количество, среднюю цену и комиссии
                            formatted_filled_amount = f"{order.filled_amount:.{amount_precision}f}"
                            formatted_average_price = f"{order.average_price:.{price_precision}f}"
                            formatted_fees = f"{order.fees:.{price_precision}f}" # Комиссии тоже с точностью цены

                            logger.info(
                                log_format,
                                order.order_id,
                                order.deal_id,
                                order.symbol,
                                order.side.upper(),
                                order.status,
                                formatted_price,
                                formatted_amount,
                                order.exchange_id,
                                formatted_filled_amount,
                                formatted_average_price,
                                formatted_fees
                            )

                    active_deals = len(deal_service.get_open_deals())
                    logger.info("   💼 Активных сделок: %s", active_deals)

                    # Получение и отображение баланса
                    balance = await pro_exchange_connector_sandbox.fetch_balance()
                    base_currency_balance = balance.get(currency_pair.base_currency, {}).get('free', 0.0)
                    quote_currency_balance = balance.get(currency_pair.quote_currency, {}).get('free', 0.0)
                    logger.info(f"   💰 Баланс: {base_currency_balance:.6f} {currency_pair.base_currency} | {quote_currency_balance:.2f} {currency_pair.quote_currency}")

                    monitor_stats = buy_order_monitor.get_statistics()
                    logger.info("\n🕒 СТАТИСТИКА BuyOrderMonitor:")
                    logger.info("   🔍 Проверок выполнено: %s", monitor_stats["checks_performed"])
                    logger.info("   🚨 Тухляков найдено: %s", monitor_stats["stale_orders_found"])
                    logger.info("   ❌ Ордеров отменено: %s", monitor_stats["orders_cancelled"])
                    logger.info("   🔄 Ордеров пересоздано: %s", monitor_stats["orders_recreated"])
                    
                    # Добавляем статистику для нашего нового DealCompletionMonitor
                    if deal_completion_monitor:
                        try:
                            completion_stats = deal_completion_monitor.get_statistics()
                            logger.info("\n🎯 СТАТИСТИКА DealCompletionMonitor:")
                            logger.info("   🔍 Проверок выполнено: %s", completion_stats["checks_performed"])
                            logger.info("   💼 Сделок отслеживается: %s", completion_stats["deals_monitored"])
                            logger.info("   ✅ Сделок завершено: %s", completion_stats["deals_completed"])
                        except Exception as e:
                            logger.debug("⚠️ DealCompletionMonitor статистика недоступна: %s", e)

            except Exception as e:
                logger.exception("❌ Ошибка в торговом цикле: %s", e)
                await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    finally:
        logger.info("🚨 Выполнение экстренной остановки...")
        emergency_result = await order_execution_service.emergency_stop_all_trading()
        logger.info("🚨 Экстренная остановка завершена: %s", emergency_result)

        final_monitor_stats = buy_order_monitor.get_statistics()
        logger.info("🕒 ФИНАЛЬНАЯ СТАТИСТИКА BuyOrderMonitor:")
        logger.info("   🔍 Всего проверок: %s", final_monitor_stats["checks_performed"])
        logger.info("   🚨 Всего тухляков: %s", final_monitor_stats["stale_orders_found"])
        logger.info("   ❌ Всего отменено: %s", final_monitor_stats["orders_cancelled"])
        logger.info("   🔄 Всего пересоздано: %s", final_monitor_stats["orders_recreated"])

        final_stats = order_execution_service.get_execution_statistics()
        logger.info("📊 ФИНАЛЬНАЯ СТАТИСТИКА OrderExecutionService:")
        logger.info("   🚀 Всего выполнений: %s", final_stats["total_executions"])
        logger.info("   ✅ Успешных: %s", final_stats["successful_executions"])
        logger.info("   📈 Процент успеха: %.1f%%", final_stats["success_rate"])
        logger.info("   💰 Общий объем: %.4f USDT", final_stats["total_volume"])
        logger.info("   💸 Общие комиссии: %.4f USDT", final_stats["total_fees"])
