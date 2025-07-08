# application/use_cases/run_realtime_trading.py
import json
from domain.entities.currency_pair import CurrencyPair
from domain.services.deal_service import DealService

from domain.services.ticker_service import TickerService
from infrastructure.connectors.pro_exchange_connector import CcxtProMarketDataConnector
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository
import time
from datetime import datetime
from termcolor import colored  # pip install termcolor
from application.utils.performance_logger import PerformanceLogger
from domain.services.market_analysis_service import MarketAnalysisService

# 🆕 НОВЫЕ ИМПОРТЫ ДЛЯ АНАЛИЗА СТАКАНА
from domain.services.orderbook_analyzer import OrderBookAnalyzer
from domain.services.trading_decision_engine import TradingDecisionEngine
from domain.services.orderbook_service import OrderBookService

# 🆕 НОВЫЙ ИМПОРТ
from domain.services.signal_cooldown_manager import SignalCooldownManager


def now_fmt():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def duration_color(duration):
    if duration < 1:
        return colored(f"{duration:.3f}s", "green")
    elif duration < 5:
        return colored(f"{duration:.3f}s", "yellow")
    else:
        return colored(f"{duration:.3f}s", "red")


async def run_realtime_trading(
        pro_exchange_connector_prod: CcxtProMarketDataConnector,
        pro_exchange_connector_sandbox: CcxtProMarketDataConnector,
        currency_pair: CurrencyPair,
        deal_service: DealService,
):
    repository = InMemoryTickerRepository(max_size=5000)
    ticker_service = TickerService(repository)

    # 🆕 Добавляем логгер производительности
    logger = PerformanceLogger(log_interval_seconds=10)

    # 🆕 ЗАЩИТА ОТ ПОВТОРНЫХ СИГНАЛОВ (только лимит сделок)
    cooldown_manager = SignalCooldownManager()

    # 🆕 ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ АНАЛИЗА СТАКАНА
    # Загружаем конфигурацию
    with open(r'F:\HOME\new_autotrade\config\config.json', 'r') as f:
        config = json.load(f)
    
    orderbook_config = config.get('orderbook_analyzer', {
        'min_volume_threshold': 1000,
        'big_wall_threshold': 5000,
        'max_spread_percent': 0.3,
        'min_liquidity_depth': 15,
        'typical_order_size': 10
    })
    
    trading_config = config.get('trading', {
        'enable_orderbook_validation': True,
        'orderbook_confidence_threshold': 0.6,
        'require_orderbook_support': False,
        'log_orderbook_analysis': True
    })
    
    # Создаем компоненты анализа стакана
    orderbook_analyzer = OrderBookAnalyzer(orderbook_config)
    decision_engine = TradingDecisionEngine(orderbook_analyzer)
    orderbook_service = OrderBookService(orderbook_analyzer)
    
    # Запускаем мониторинг стакана в фоне
    if trading_config.get('enable_orderbook_validation', True):
        await orderbook_service.start_monitoring(
            pro_exchange_connector_sandbox.client,  # Используем sandbox для стакана
            currency_pair.symbol
        )
        print(f"🔍 Запущен анализ стакана для {currency_pair.symbol}")

    # 🆕 Убираем лишние переменные и принты
    counter = 0

    market_analyzer = MarketAnalysisService()

    print(f"🚀 ЗАПУСК ТОРГОВЛИ: {currency_pair.symbol}")
    print(f"   💰 Бюджет на сделку: {currency_pair.deal_quota} USDT")
    print(f"   🎯 Максимум сделок: {currency_pair.deal_count}")
    print(f"   📊 Анализ стакана: {'✅ ВКЛЮЧЕН' if trading_config.get('enable_orderbook_validation') else '❌ ОТКЛЮЧЕН'}")
    print("="*80)

    try:
        while True:
            try:
                # 🚀 УБИРАЕМ ЛИШНИЕ ПРИНТЫ!
                # print(colored(f"\n⏳ [{now_fmt()}] Start Ticker_data.watch_ticker", "cyan"))
                start_watch = time.time()

                ticker_data = await pro_exchange_connector_prod.client.watch_ticker(currency_pair.symbol)

                # 🚀 ОПТИМИЗИРОВАННАЯ ОБРАБОТКА
                start_process = time.time()
                await ticker_service.process_ticker(ticker_data)
                end_process = time.time()

                processing_time = end_process - start_process
                counter += 1

                # 🚀 УБИРАЕМ get_last_n каждый тик!
                # repos_tickers = await ticker_service.repository.get_last_n(50)  # УДАЛИТЬ!

                # Проверяем достаточно ли данных БЕЗ get_last_n
                if len(repository.tickers) < 50:
                    # Логируем только изредка
                    if counter % 100 == 0:
                        print(f"🟡 Накоплено {len(repository.tickers)} тиков, нужно 50")
                    continue

                # 🚀 УПРОЩЕННОЕ получение сигнала
                ticker_signal = await ticker_service.get_signal()

                # 🚀 МИНИМАЛЬНАЯ ОБРАБОТКА ОТОБРАЖЕНИЯ
                if len(repository.tickers) > 0:
                    last_ticker = repository.tickers[-1]

                    # Логируем через PerformanceLogger
                    signals_count = len(last_ticker.signals) if last_ticker.signals else 0
                    logger.log_tick(
                        price=float(last_ticker.close),
                        processing_time=processing_time,
                        signals_count=signals_count
                    )

                    # УБИРАЕМ ВСЕ ПРИНТЫ С ИНДИКАТОРАМИ!
                    # Показываем индикаторы только при логировании
                    if logger.should_log() and last_ticker.signals:
                        hist = last_ticker.signals.get('histogram', 0.0)
                        macd = last_ticker.signals.get('macd', 0.0)
                        signal = last_ticker.signals.get('signal', 0.0)

                        print(f"📈 Индикаторы: HIST={hist:.6f} | MACD={macd:.6f} | SIGNAL={signal:.6f}")

                # 🆕 АНАЛИЗ РЫНКА каждые 50 тиков
                if counter % 50 == 0 and len(repository.tickers) > 20:
                    # ВАРИАНТ 1: Через TickerService
                    volatility_info = ticker_service.analyze_market_conditions()
                    trend_info = ticker_service.get_price_trend()
                    should_trade = ticker_service.should_trade_by_volatility()

                    print(f"\n🔍 АНАЛИЗ РЫНКА (тик {counter}):")
                    print(f"   {volatility_info}")
                    print(f"   {trend_info}")
                    print(f"   🤖 Торговать: {'✅ ДА' if should_trade else '❌ НЕТ'}")

                    # ВАРИАНТ 2: Через MarketAnalysisService (более подробно)
                    prices = [float(t.close) for t in repository.tickers[-50:]]
                    volatility_analysis = market_analyzer.analyze_volatility(prices)
                    trend_analysis = market_analyzer.analyze_trend(prices)

                    print(f"\n📊 ПОДРОБНЫЙ АНАЛИЗ:")
                    print(f"   Волатильность: {volatility_analysis['avg_volatility']}% "
                          f"({volatility_analysis['risk_level']})")
                    print(f"   Рекомендация: {volatility_analysis['trading_recommendation']}")
                    print(f"   Тренд: {trend_analysis['trend_direction']} "
                          f"({trend_analysis['strength']}) {trend_analysis['change_percent']}%")

                    # Показываем статус активных сделок
                    active_deals_count = len(deal_service.get_open_deals())
                    print(f"   {cooldown_manager.get_status(active_deals_count, currency_pair.deal_count)}")
                    
                    # 🆕 СТАТУС СТАКАНА
                    if trading_config.get('enable_orderbook_validation'):
                        orderbook_health = "✅ Здоров" if orderbook_service.is_orderbook_healthy() else "⚠️ Проблемы"
                        print(f"   📊 Стакан: {orderbook_health}")

                # 🎯 ОБРАБОТКА СИГНАЛА ПОКУПКИ С АНАЛИЗОМ СТАКАНА
                if ticker_signal == "BUY":
                    if len(repository.tickers) > 0:
                        last_ticker = repository.tickers[-1]
                        if last_ticker.signals:
                            # Получаем текущие индикаторы MACD
                            macd = last_ticker.signals.get('macd', 0.0)
                            signal = last_ticker.signals.get('signal', 0.0)
                            hist = last_ticker.signals.get('histogram', 0.0)
                            current_price = float(last_ticker.close)

                            # 🛡️ ПРОВЕРКА ЛИМИТА АКТИВНЫХ СДЕЛОК
                            active_deals_count = len(deal_service.get_open_deals())
                            can_buy, reason = cooldown_manager.can_buy(
                                active_deals_count=active_deals_count,
                                max_deals=currency_pair.deal_count
                            )

                            if not can_buy:
                                # 🚫 СИГНАЛ ЗАБЛОКИРОВАН
                                if counter % 20 == 0:  # Показываем блокировку каждые 20 тиков
                                    print(f"🚫 BUY заблокирован: {reason} | Цена: {current_price}")
                                continue

                            # ✅ СИГНАЛ РАЗРЕШЕН - АНАЛИЗИРУЕМ С УЧЕТОМ СТАКАНА
                            print("\n" + "="*80)
                            print("🟢🔥 MACD СИГНАЛ ПОКУПКИ ОБНАРУЖЕН! ПРОВЕРЯЕМ СТАКАН...")
                            print("="*80)
                            print(f"   📈 MACD > Signal: {macd:.6f} > {signal:.6f}")
                            print(f"   📊 Histogram: {hist:.6f}")
                            print(f"   💰 Текущая цена: {current_price} USDT")
                            print(f"   🎯 Активных сделок: {active_deals_count}/{currency_pair.deal_count}")

                            # 🆕 АНАЛИЗ СТАКАНА
                            orderbook_decision = None
                            if trading_config.get('enable_orderbook_validation'):
                                # Получаем данные MACD для анализа
                                macd_data = ticker_service.get_macd_signal_data()
                                macd_bullish = macd_data['is_bullish'] if macd_data else False
                                
                                # Получаем метрики стакана
                                orderbook_metrics = orderbook_service.get_latest_metrics()
                                
                                if orderbook_metrics:
                                    # Принимаем решение на основе MACD + стакан
                                    orderbook_decision = decision_engine.should_execute_trade(
                                        macd_bullish, orderbook_metrics
                                    )
                                    
                                    # Показываем анализ стакана
                                    print(decision_engine.format_orderbook_info(orderbook_metrics))
                                    
                                    if orderbook_decision['execute']:
                                        print(f"\n✅ {orderbook_decision['reason']}")
                                        print(f"   🎯 Уверенность: {orderbook_decision['confidence']:.1%}")
                                        
                                        if orderbook_decision['modifications']:
                                            print(f"   🔧 МОДИФИКАЦИИ СТАКАНА:")
                                            for key, value in orderbook_decision['modifications'].items():
                                                if key == 'entry_price_hint':
                                                    print(f"      💡 Рекомендуемая цена входа: {value:.4f}")
                                                elif key == 'exit_price_hint':
                                                    print(f"      💡 Рекомендуемая цена выхода: {value:.4f}")
                                                elif key == 'reduce_position_size':
                                                    print(f"      ⚠️ Уменьшить размер позиции на: {(1-value)*100:.0f}%")
                                    else:
                                        print(f"\n❌ {orderbook_decision['reason']}")
                                        print("="*80)
                                        print("🔄 Продолжаем мониторинг...\n")
                                        continue
                                else:
                                    print("\n⚠️ Нет данных стакана, используем только MACD")

                            # 🧮 ВЫЗОВ КАЛЬКУЛЯТОРА СТРАТЕГИИ
                            try:
                                # Применяем модификации от стакана если есть
                                orderbook_modifications = None
                                if orderbook_decision and orderbook_decision.get('execute'):
                                    # Преобразуем модификации стакана
                                    modifications = orderbook_decision.get('modifications', {})
                                    if modifications:
                                        orderbook_mods = decision_engine.apply_orderbook_modifications(
                                            current_price, currency_pair.deal_quota, modifications
                                        )
                                        
                                        # Показываем применённые модификации
                                        if orderbook_mods['modifications_applied']:
                                            print("\n🔧 ПРИМЕНЯЕМЫЕ МОДИФИКАЦИИ:")
                                            for mod in orderbook_mods['modifications_applied']:
                                                print(f"   {mod}")
                                        
                                        orderbook_modifications = {
                                            'entry_price': orderbook_mods['entry_price'],
                                            'budget_multiplier': orderbook_mods['budget_multiplier'],
                                            'exit_price_hint': orderbook_mods['exit_price_hint']
                                        }

                                # Вызываем калькулятор с учетом стакана
                                if orderbook_modifications:
                                    strategy_result = ticker_service.calculate_strategy_with_orderbook(
                                        buy_price=current_price,
                                        budget=currency_pair.deal_quota,
                                        min_step=currency_pair.min_step,
                                        price_step=currency_pair.price_step,
                                        buy_fee_percent=0.1,
                                        sell_fee_percent=0.1,
                                        profit_percent=currency_pair.profit_markup,
                                        orderbook_modifications=orderbook_modifications
                                    )
                                else:
                                    # Обычный калькулятор без модификаций
                                    strategy_result = ticker_service.calculate_strategy(
                                        buy_price=current_price,
                                        budget=currency_pair.deal_quota,
                                        min_step=currency_pair.min_step,
                                        price_step=currency_pair.price_step,
                                        buy_fee_percent=0.1,
                                        sell_fee_percent=0.1,
                                        profit_percent=currency_pair.profit_markup
                                    )
                                
                                # Проверяем результат
                                if isinstance(strategy_result, dict) and "comment" in strategy_result:
                                    # Ошибка в расчетах
                                    print(f"\n❌ {strategy_result['comment']}")
                                else:
                                    # Успешный расчет - распаковываем результат
                                    buy_price_calc, total_coins_needed, sell_price_calc, coins_to_sell, info_dict = strategy_result
                                    
                                    calc_title = "✅ РАСЧЕТ С УЧЕТОМ СТАКАНА:" if orderbook_modifications else "✅ РАСЧЕТ УСПЕШЕН:"
                                    print(f"\n{calc_title}")
                                    print(f"   🛒 Купить: {total_coins_needed} {currency_pair.base_currency} по {buy_price_calc} USDT")
                                    print(f"   💵 Потратим: {float(total_coins_needed) * float(buy_price_calc):.4f} USDT")
                                    print(f"   🏷️ Продать: {coins_to_sell} {currency_pair.base_currency} по {sell_price_calc} USDT")
                                    print(f"   💰 Выручим: {float(coins_to_sell) * float(sell_price_calc):.4f} USDT")
                                    print(f"   📊 Чистая прибыль: {info_dict.get('🔹 Чистая прибыль', 'N/A')}")
                                    
                                    if trading_config.get('log_orderbook_analysis'):
                                        print("\n📋 ПОДРОБНАЯ ИНФОРМАЦИЯ:")
                                        for key, value in info_dict.items():
                                            if key != "comment":
                                                print(f"   {key}: {value}")

                                    # 🆕 СОЗДАЕМ СДЕЛКУ
                                    new_deal = deal_service.create_new_deal(currency_pair)

                                    # 🆕 СОЗДАЕМ BUY ОРДЕР
                                    buy_order = deal_service.open_buy_order(
                                        price=float(buy_price_calc),
                                        amount=float(total_coins_needed),
                                        deal_id=new_deal.deal_id
                                    )

                                    # 🆕 СОЗДАЕМ SELL ОРДЕР
                                    sell_order = deal_service.open_sell_order(
                                        price=float(sell_price_calc),
                                        amount=float(coins_to_sell),
                                        deal_id=new_deal.deal_id
                                    )

                                    # 🆕 ПРИВЯЗЫВАЕМ ОРДЕРА К СДЕЛКЕ
                                    new_deal.attach_orders(buy_order, sell_order)

                                    print(f"\n🆕 Создана сделка #{new_deal.deal_id}")
                                    print(f"   🛒 BUY: {buy_order}")
                                    print(f"   🏷️ SELL: {sell_order}")

                            except Exception as calc_error:
                                print(f"❌ Ошибка в калькуляторе: {calc_error}")
                            
                            print("="*80)
                            print("🔄 Продолжаем мониторинг...\n")
                        else:
                            # Раз в 100 тиков показываем почему не покупаем (без изменений)
                            if counter % 100 == 0:
                                if len(repository.tickers) > 0:
                                    last_ticker = repository.tickers[-1]
                                    if last_ticker.signals:
                                        macd = last_ticker.signals.get('macd', 0.0)
                                        signal = last_ticker.signals.get('signal', 0.0)
                                        hist = last_ticker.signals.get('histogram', 0.0)
                                        print(f"🟡 Ожидание сигнала. MACD: {macd:.6f}, Signal: {signal:.6f}, Hist: {hist:.6f}")

            except Exception as e:
                print(f"❌ Error: {e}")
    
    finally:
        # Останавливаем мониторинг стакана при завершении
        if trading_config.get('enable_orderbook_validation'):
            await orderbook_service.stop_monitoring()
            print("🔴 Мониторинг стакана остановлен")
