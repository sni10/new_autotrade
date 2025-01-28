# domain/services/signal_service.py
import pandas as pd
import talib

class SignalService:
    """
    Пример сервиса, считающего технические индикаторы.
    """

    def __init__(self):
        self.history = pd.DataFrame(columns=['timestamp','price','volume'])

    def update_history(self, trades):
        # trades - массив сделок
        for trade in trades:
            row = {
                'timestamp': trade['timestamp'],
                'price': trade['price'],
                'volume': trade['amount'],
            }
            self.history = pd.concat([self.history, pd.DataFrame([row])])

        # Очищаем слишком старые данные, если нужно
        # self.history = self.history[self.history['timestamp'] > ...]

    def calculate_indicators(self):
        """
        Например, формируем свечи 1m и считаем MACD/RSI.
        Возвращаем dict со значениями сигналов.
        """
        # Пример, если у нас есть DataFrame с 'price'
        close = self.history['price'].values
        if len(close) < 20:
            return {}

        rsi = talib.RSI(close, timeperiod=14)
        macd, signal, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

        return {
            'rsi': rsi[-1],
            'macd': macd[-1],
            'macd_signal': signal[-1],
            'macd_hist': hist[-1],
        }

    def generate_signal(self, indicators):
        """
        Пример принятия решения.
        """
        if not indicators:
            return None
        if indicators['rsi'] < 30 and indicators['macd_hist'] > 0:
            return "BUY"
        elif indicators['rsi'] > 70 and indicators['macd_hist'] < 0:
            return "SELL"
        return "HOLD"
