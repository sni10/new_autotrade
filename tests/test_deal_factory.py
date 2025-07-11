from domain.factories.deal_factory import DealFactory
from domain.entities.currency_pair import CurrencyPair
from domain.factories.order_factory import OrderFactory


def test_create_new_deal_assigns_deal_id_to_orders():
    of = OrderFactory()
    df = DealFactory(of)
    pair = CurrencyPair('BTC', 'USDT', 'BTCUSDT')
    # DealFactory uses order_factory.create_buy_order without symbol, patch it
    import functools
    df.order_factory.create_buy_order = functools.partial(of.create_buy_order, symbol=pair.symbol)
    df.order_factory.create_sell_order = functools.partial(of.create_sell_order, symbol=pair.symbol)
    deal = df.create_new_deal(pair)
    assert deal.buy_order.deal_id == deal.deal_id
    assert deal.sell_order.deal_id == deal.deal_id
    assert deal.currency_pair_id == 'BTCUSDT'
