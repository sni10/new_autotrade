import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from domain.entities.ticker import Ticker


def test_ticker_dict_conversion_and_signals():
    data = {
        'timestamp': 1234567890,
        'symbol': 'BTC/USDT',
        'last': 100.0,
        'open': 95.0,
        'close': 100.0,
        'baseVolume': 10.5,
        'high': 101.0,
        'low': 94.0,
        'bid': 99.5,
        'ask': 100.5
    }
    ticker = Ticker(data)
    ticker.update_signals({'macd': 1.2, 'rsi': 55})
    d = ticker.to_dict()
    assert d['timestamp'] == 1234567890
    assert d['symbol'] == 'BTC/USDT'
    assert d['price'] == 100.0
    assert d['macd'] == 1.2
    assert d['rsi'] == 55
    # repr should contain symbol and price
    rep = repr(ticker)
    assert 'BTC/USDT' in rep and '100.0' in rep