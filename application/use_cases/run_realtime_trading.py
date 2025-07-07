# application/use_cases/run_realtime_trading.py
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


def now_fmt():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def duration_color(duration):
    if duration < 1:
        return colored(f"{duration:.3f}s", "green")
    elif duration < 5:
        return colored(f"{duration:.3f}s", "yellow")
    else:
        return colored(f"{duration:.3f}s", "red")


# Если нужна логика расчёта индикаторов/сигналов
# from domain.services.signal_service import SignalService

# run_realtime_trading.py (примерно)


# Добавить в импорты:


async def run_realtime_trading(
        pro_exchange_connector: CcxtProMarketDataConnector,
        currency_pair: CurrencyPair,
        deal_service: DealService,
):
    repository = InMemoryTickerRepository(max_size=5000)
    ticker_service = TickerService(repository)

    # 🆕 Добавляем логгер производительности
    logger = PerformanceLogger(log_interval_seconds=10)

    # 🆕 Убираем лишние переменные и принты
    counter = 0

    market_analyzer = MarketAnalysisService()

    while True:
        try:
            # 🚀 УБИРАЕМ ЛИШНИЕ ПРИНТЫ!
            # print(colored(f"\n⏳ [{now_fmt()}] Start Ticker_data.watch_ticker", "cyan"))
            start_watch = time.time()

            ticker_data = await pro_exchange_connector.client.watch_ticker(currency_pair.symbol)

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

            # Обработка сигнала покупки (без изменений)
            # Добавить в run_realtime_trading.py:
            if ticker_signal == "BUY":
                # 🔧 ИСПРАВЛЯЕМ - получаем переменные ПЕРЕД использованием
                if len(repository.tickers) > 0:
                    last_ticker = repository.tickers[-1]
                    if last_ticker.signals:
                        macd = last_ticker.signals.get('macd', 0.0)
                        signal = last_ticker.signals.get('signal', 0.0)
                        hist = last_ticker.signals.get('histogram', 0.0)

                        print("🟢🔥 СИГНАЛ ПОКУПКИ! Условия:")
                        print(f"   📈 MACD > Signal: {macd:.6f} > {signal:.6f}")
                        print(f"   📊 Histogram положительная: {hist:.6f}")
                        print(f"   📉 SMA тренд восходящий")

                        # Здесь логика создания сделки...
                    else:
                        # Раз в 100 тиков показываем почему не покупаем
                        if counter % 100 == 0:
                            # 🔧 ДОБАВИТЬ проверку наличия данных:
                            if len(repository.tickers) > 0:
                                last_ticker = repository.tickers[-1]
                                if last_ticker.signals:
                                    macd = last_ticker.signals.get('macd', 0.0)
                                    signal = last_ticker.signals.get('signal', 0.0)
                                    hist = last_ticker.signals.get('histogram', 0.0)
                                    print(f"🟡 Ожидание. MACD: {macd:.6f}, Signal: {signal:.6f}, Hist: {hist:.6f}")

        except Exception as e:
            print(f"❌ Error: {e}")
