# application/use_cases/run_realtime_trading.py
import math
import time
import domain.services.ticker_service
from domain.entities.currency_pair import CurrencyPair
from domain.services.deal_service import DealService

from domain.services.ticker_service import TickerService
from infrastructure.connectors.pro_exchange_connector import CcxtProMarketDataConnector
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository


# Если нужна логика расчёта индикаторов/сигналов
# from domain.services.signal_service import SignalService

# run_realtime_trading.py (примерно)

async def run_realtime_trading(
        pro_exchange_connector: CcxtProMarketDataConnector,
        currency_pair: CurrencyPair,
        deal_service: DealService,
):
    repository = InMemoryTickerRepository(max_size=5000)
    ticker_service = TickerService(repository)

    # await pro_exchange_connector.subscribe(symbol)

    # ANSI escape code
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    HIST_ANALYSIS_POINTS = 3
    ANALYSIS_POINTS = 5
    last_timestamp = 0
    counter = 0

    while True:
        try:
            # Получаем новые сделки
            ticker_data = await pro_exchange_connector.client.watch_ticker(currency_pair.symbol)

            # """
            # ticker = {dict: 22} {'ask': 0.05515, 'askVolume': 5850.0, 'average': 0.04824, 'baseVolume': 791854721.0, 'bid': 0.0551, 'bidVolume': 1080.0, 'change': 0.01374, 'close': 0.05511, 'datetime': '2025-01-26T11:42:58.462Z', 'high': 0.064, 'indexPrice': None, 'info': {'A': '5850.000
            #  'symbol' = {str} 'SKL/USDT'
            #  'timestamp' = {int} 1737891778462
            #  'datetime' = {str} '2025-01-26T11:42:58.462Z'
            #  'high' = {float} 0.064
            #  'low' = {float} 0.04104
            #  'bid' = {float} 0.0551
            #  'bidVolume' = {float} 1080.0
            #  'ask' = {float} 0.05515
            #  'askVolume' = {float} 5850.0
            #  'vwap' = {float} 0.05083828
            #  'open' = {float} 0.04137
            #  'close' = {float} 0.05511
            #  'last' = {float} 0.05511
            #  'previousClose' = {float} 0.04137
            #  'change' = {float} 0.01374
            #  'percentage' = {float} 33.212
            #  'average' = {float} 0.04824
            #  'baseVolume' = {float} 791854721.0
            #  'quoteVolume' = {float} 40256532.6071
            #  'info' = {dict: 23} {'A': '5850.00000000', 'B': '1080.00000000', 'C': 1737891778462, 'E': 1737891778462, 'F': 60734052, 'L': 61010891, 'O': 1737805378462, 'P': '33.212', 'Q': '27481.00000000', 'a': '0.05515000', 'b': '0.05510000', 'c': '0.05511000', 'e': '24hrTicker', 'h': '0
            #   'e' = {str} '24hrTicker'
            #   'E' = {int} 1737891778462
            #   's' = {str} 'SKLUSDT'
            #   'p' = {str} '0.01374000'
            #   'P' = {str} '33.212'
            #   'w' = {str} '0.05083828'
            #   'x' = {str} '0.04137000'
            #   'c' = {str} '0.05511000'
            #   'Q' = {str} '27481.00000000'
            #   'b' = {str} '0.05510000'
            #   'B' = {str} '1080.00000000'
            #   'a' = {str} '0.05515000'
            #   'A' = {str} '5850.00000000'
            #   'o' = {str} '0.04137000'
            #   'h' = {str} '0.06400000'
            #   'l' = {str} '0.04104000'
            #   'v' = {str} '791854721.00000000'
            #   'q' = {str} '40256532.60710000'
            #   'O' = {int} 1737805378462
            #   'C' = {int} 1737891778462
            #   'F' = {int} 60734052
            #   'L' = {int} 61010891
            #   'n' = {int} 276840
            #   __len__ = {int} 23
            #  'indexPrice' = {NoneType} None
            #  'markPrice' = {NoneType} None
            #  __len__ = {int} 22
            # """

            counter += 1
            ticker_service.process_ticker(ticker_data)
            ticker_signal = ticker_service.get_signal()

            """
            ТОЛЬКО ДЛЯ ВЫЧИСЛЕНИЯ ДЕЛЬТЫ Δt: {time_diff:.3f}  В ПРОДЕ УДАЛИТЬ
            """
            timestamp = ticker_data['timestamp'] or time.time() * 1000
            time_diff = (timestamp - last_timestamp) / 1000 if last_timestamp else 0
            last_timestamp = timestamp
            """
            ТОЛЬКО ДЛЯ ВЫЧИСЛЕНИЯ ДЕЛЬТЫ Δt: {time_diff:.3f}  В ПРОДЕ УДАЛИТЬ
            """

            repos_tickers = ticker_service.repository.get_last_n(50)

            if len(repos_tickers) < 5:
                continue

            if repos_tickers:
                last_ticker = repos_tickers[-1] if repos_tickers else None  # Исправлено условие

                if last_ticker and hasattr(last_ticker, 'symbol') and hasattr(last_ticker, 'close'):
                    print(f"🟢 Обработан тикер #{counter}: {str(last_ticker.symbol)} |"
                          f" Цена: {float(last_ticker.close):.7f} |"
                          f" Δt: {time_diff:.3f}s")
                else:
                    print(f"🟡 Обработан тикер #{counter}: Данные недоступны")
                    continue

                if last_ticker and last_ticker.signals:
                    hist_values = [t.signals.get('histogram', 0.0) for t in repos_tickers[-HIST_ANALYSIS_POINTS:]]
                    hist = last_ticker.signals.get('histogram', 0.0)
                    macd = last_ticker.signals.get('macd', 0.0)
                    signal = last_ticker.signals.get('signal', 0.0)
                    bb_upper = last_ticker.signals.get('bb_upper', 0.0)
                    bb_lower = last_ticker.signals.get('bb_lower', 0.0)
                    price = float(last_ticker.close) if last_ticker else 0.0

                    # Определяем цвет MACD vs SIGNAL
                    macd_signal_color = GREEN if macd > signal else RED

                    # Подсветка Bollinger Bands
                    bb_color = GREEN if price > bb_upper else RED if price < bb_lower else RESET

                    # Подсветка гистограммы (HIST) - либо растет, либо падает
                    # Подсветка гистограммы (HIST) по вектору с `n` значениями
                    if len(hist_values) >= HIST_ANALYSIS_POINTS:
                        hist_trend = [hist_values[i] - hist_values[i - 1] for i in range(1, HIST_ANALYSIS_POINTS)]
                        hist_color = GREEN if all(diff > 0 for diff in hist_trend) else RED
                    else:
                        hist_color = YELLOW  # Недостаточно данных

                    if len(repos_tickers) >= ANALYSIS_POINTS:

                        sma_7_values = [t.signals.get("sma_7", 0) for t in repos_tickers[-ANALYSIS_POINTS:]]
                        sma_25_values = [t.signals.get("sma_25", 0) for t in repos_tickers[-ANALYSIS_POINTS:]]
                        sma_99_values = [t.signals.get("sma_99", 0) for t in repos_tickers[-ANALYSIS_POINTS:]]

                        sma_7_trend = [sma_7_values[i] - sma_7_values[i - 1] for i in range(1, ANALYSIS_POINTS)]
                        sma_25_trend = [sma_25_values[i] - sma_25_values[i - 1] for i in range(1, ANALYSIS_POINTS)]
                        sma_99_trend = [sma_99_values[i] - sma_99_values[i - 1] for i in range(1, ANALYSIS_POINTS)]

                        sma_7_color = GREEN if all(diff > 0 for diff in sma_7_trend) else RED
                        sma_25_color = GREEN if all(diff > 0 for diff in sma_25_trend) else RED
                        sma_99_color = GREEN if all(diff > 0 for diff in sma_99_trend) else RED

                        print(f"🟩 Сигналы база |"
                              f" HIST: {hist_color}{hist:.8f}{RESET} |"
                              f" MACD: {macd_signal_color}{macd:.8f}{RESET} |"
                              f" SIGNAL: {macd_signal_color}{signal:.8f}{RESET} |"
                              f" BB_UPPER: {bb_color}{bb_upper:.8f}{RESET} |"
                              f" BB_MIDDLE: {last_ticker.signals.get('bb_middle', 0):.8f} |"
                              f" BB_LOWER: {bb_color}{bb_lower:.8f}{RESET} |"
                              f" SMA_7: {sma_7_color}{last_ticker.signals.get('sma_7', 0):.8f}{RESET} |"
                              f" SMA_25: {sma_25_color}{last_ticker.signals.get('sma_25', 0):.8f}{RESET} |"
                              f" SMA_99: {sma_99_color}{last_ticker.signals.get('sma_99', 0):.8f}{RESET}"
                              )

                else:
                    print("🟡 Нет данных сигналов для анализа")

            if ticker_signal == "BUY":
                print("🟢 Сигнал на покупку! 🔥🚀 Расчет сделки... ")

                # 1) Создаём сделку
                deal = deal_service.deal_factory.create_new_deal(currency_pair)
                deal_service.deals_repo.save(deal)
                print("New Deal:", deal)

                if deal.buy_order:
                    deal_service.order_service.orders_repo.save(deal.buy_order)
                if deal.sell_order:
                    deal_service.order_service.orders_repo.save(deal.sell_order)

                # Устанавливаем параметры сделки
                buy_price = ticker_data['close']
                budget = currency_pair.deal_quota  # Условный бюджет в USDT
                min_step = currency_pair.min_step  # Минимальный шаг монеты
                price_step = currency_pair.price_step  # Минимальный шаг юсдт цены wмонеты
                buy_fee_percent = 0.1  # Комиссия при покупке (%)
                sell_fee_percent = 0.1  # Комиссия при продаже (%)
                profit_percent = currency_pair.profit_markup  # Желаемая прибыль (%)

                # Вызываем расчет торговой стратегии
                buy_price_with_fee_factor, total_coins_needed, sell_price, X_adjusted, trade_result = ticker_service.calculate_strategy(
                    buy_price, budget, min_step, price_step,
                    buy_fee_percent, sell_fee_percent,
                    profit_percent
                )

                deal.buy_order.price = buy_price_with_fee_factor
                deal.buy_order.amount = total_coins_needed
                deal_service.order_service.orders_repo.save(deal.buy_order)

                deal.sell_order.price = sell_price
                deal.sell_order.amount = X_adjusted
                deal_service.order_service.orders_repo.save(deal.sell_order)

                # Выводим детальную информацию о сделке
                print("\n🔹 **РЕЗУЛЬТАТ РАСЧЁТА СДЕЛКИ** 🔹\n")
                for key, value in trade_result.items():
                    print(f"🟢 {key.ljust(50)} ➜ {value}")
            else:
                print("🟡 Пока ждем, сигналов на покупку нет.")


        except Exception as e:
            print(f"Error: {e}")
