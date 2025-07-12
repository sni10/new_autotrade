from domain.entities.currency_pair import CurrencyPair


def test_currency_pair_defaults_and_repr():
    pair = CurrencyPair('BTC', 'USDT')
    assert pair.symbol == 'BTC/USDT'
    assert pair.order_life_time == 1
    assert pair.deal_quota == 100.0
    r = repr(pair)
    assert 'BTC/USDT' in r and 'deal_quota=100.0' in r
