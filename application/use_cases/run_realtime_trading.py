# application/use_cases/run_realtime_trading.py
"""Trading loop using OrderExecutionService and BuyOrderMonitor."""

import asyncio
import time

from domain.entities.currency_pair import CurrencyPair
from domain.services.deal_service import DealService
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository
from domain.services.ticker_service import TickerService
from application.utils.performance_logger import PerformanceLogger
from domain.services.signal_cooldown_manager import SignalCooldownManager


async def run_realtime_trading(
    pro_exchange_connector_prod: CcxtExchangeConnector,
    pro_exchange_connector_sandbox: CcxtExchangeConnector,
    currency_pair: CurrencyPair,
    deal_service: DealService,
    order_execution_service,
    buy_order_monitor,
):
    """Simplified trading loop using OrderExecutionService and BuyOrderMonitor."""

    repository = InMemoryTickerRepository(max_size=5000)
    ticker_service = TickerService(repository)
    logger_perf = PerformanceLogger(log_interval_seconds=10)
    cooldown_manager = SignalCooldownManager()

    counter = 0

    print("🚀 Запуск расширенного торгового цикла с OrderExecutionService + BuyOrderMonitor")

    try:
        while True:
            try:
                ticker_data = await pro_exchange_connector_prod.async_client.watch_ticker(currency_pair.symbol)

                start_process = time.time()
                await ticker_service.process_ticker(ticker_data)
                end_process = time.time()

                processing_time = end_process - start_process
                counter += 1

                if len(repository.tickers) < 50:
                    if counter % 100 == 0:
                        print(f"🟡 Накоплено {len(repository.tickers)} тиков, нужно 50")
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
                                    print(f"🚫 BUY заблокирован: {reason} | Цена: {current_price}")
                                continue

                            print("\n" + "="*80)
                            print("🟢🔥 MACD СИГНАЛ ПОКУПКИ ОБНАРУЖЕН! ВЫПОЛНЯЕМ ЧЕРЕЗ OrderExecutionService...")
                            print("="*80)

                            macd = last_ticker.signals.get('macd', 0.0)
                            signal = last_ticker.signals.get('signal', 0.0)
                            hist = last_ticker.signals.get('histogram', 0.0)

                            print(f"   📈 MACD > Signal: {macd:.6f} > {signal:.6f}")
                            print(f"   📊 Histogram: {hist:.6f}")
                            print(f"   💰 Текущая цена: {current_price} USDT")
                            print(f"   🎯 Активных сделок: {active_deals_count}/{currency_pair.deal_count}")

                            try:
                                strategy_result = ticker_service.calculate_strategy(
                                    buy_price=current_price,
                                    budget=currency_pair.deal_quota,
                                    min_step=currency_pair.min_step,
                                    price_step=currency_pair.price_step,
                                    buy_fee_percent=0.1,
                                    sell_fee_percent=0.1,
                                    profit_percent=currency_pair.profit_markup,
                                )

                                if isinstance(strategy_result, dict) and "comment" in strategy_result:
                                    print(f"❌ Ошибка в калькуляторе: {strategy_result['comment']}")
                                    continue

                                print("🚀 Выполнение стратегии через OrderExecutionService...")
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
                                    print("🎉 СТРАТЕГИЯ ВЫПОЛНЕНА УСПЕШНО!")
                                else:
                                    print(f"❌ СТРАТЕГИЯ НЕ ВЫПОЛНЕНА: {execution_result.error_message}")

                            except Exception as calc_error:
                                print(f"❌ Ошибка в стратегии: {calc_error}")

                            print("="*80)
                            print("🔄 Продолжаем мониторинг...\n")

                if counter % 100 == 0:
                    execution_stats = order_execution_service.get_execution_statistics()
                    print(f"\n📊 СТАТИСТИКА OrderExecutionService (тик {counter}):")
                    print(f"   🚀 Всего выполнений: {execution_stats['total_executions']}")
                    print(f"   ✅ Успешных: {execution_stats['successful_executions']}")
                    print(f"   ❌ Неудачных: {execution_stats['failed_executions']}")

                    order_stats = order_execution_service.order_service.get_statistics()
                    print(f"   📦 Всего ордеров: {order_stats['total_orders']}")
                    print(f"   🔄 Открытых ордеров: {order_stats['open_orders']}")

                    active_deals = len(deal_service.get_open_deals())
                    print(f"   💼 Активных сделок: {active_deals}")

                    monitor_stats = buy_order_monitor.get_statistics()
                    print(f"\n🕒 СТАТИСТИКА BuyOrderMonitor:")
                    print(f"   🔍 Проверок выполнено: {monitor_stats['checks_performed']}")
                    print(f"   🚨 Тухляков найдено: {monitor_stats['stale_orders_found']}")
                    print(f"   ❌ Ордеров отменено: {monitor_stats['orders_cancelled']}")
                    print(f"   🔄 Ордеров пересоздано: {monitor_stats['orders_recreated']}")

            except Exception as e:
                print(f"❌ Ошибка в торговом цикле: {e}")
                await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("🛑 Получен сигнал остановки...")
    finally:
        print("🚨 Выполнение экстренной остановки...")
        emergency_result = await order_execution_service.emergency_stop_all_trading()
        print(f"🚨 Экстренная остановка завершена: {emergency_result}")

        final_monitor_stats = buy_order_monitor.get_statistics()
        print("🕒 ФИНАЛЬНАЯ СТАТИСТИКА BuyOrderMonitor:")
        print(f"   🔍 Всего проверок: {final_monitor_stats['checks_performed']}")
        print(f"   🚨 Всего тухляков: {final_monitor_stats['stale_orders_found']}")
        print(f"   ❌ Всего отменено: {final_monitor_stats['orders_cancelled']}")
        print(f"   🔄 Всего пересоздано: {final_monitor_stats['orders_recreated']}")

        final_stats = order_execution_service.get_execution_statistics()
        print("📊 ФИНАЛЬНАЯ СТАТИСТИКА OrderExecutionService:")
        print(f"   🚀 Всего выполнений: {final_stats['total_executions']}")
        print(f"   ✅ Успешных: {final_stats['successful_executions']}")
        print(f"   📈 Процент успеха: {final_stats['success_rate']:.1f}%")
        print(f"   💰 Общий объем: {final_stats['total_volume']:.4f} USDT")
        print(f"   💸 Общие комиссии: {final_stats['total_fees']:.4f} USDT")
