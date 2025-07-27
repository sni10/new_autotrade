from src.domain.factories.order_factory import OrderFactory
from src.domain.entities.order import ExchangeInfo, Order


def _make_info():
    return ExchangeInfo(
        symbol="BTCUSDT",
        min_qty=0.001,
        max_qty=100,
        step_size=0.001,
        min_price=10,
        max_price=100000,
        tick_size=0.01,
        min_notional=10,
        fees={"maker": 0.001},
        precision={'amount': 0.001, 'price': 0.01}
    )


def test_create_orders_and_metadata():
    factory = OrderFactory()
    buy = factory.create_buy_order(symbol="BTCUSDT", amount=0.5, price=20000)
    sell = factory.create_sell_order(symbol="BTCUSDT", amount=0.5, price=21000)
    assert buy.side == Order.SIDE_BUY
    assert sell.side == Order.SIDE_SELL
    assert buy.metadata["order_direction"] == "entry"
    assert sell.metadata["order_direction"] == "exit"
    assert buy.order_id != sell.order_id


def test_precision_adjustment():
    factory = OrderFactory()
    factory.update_exchange_info("BTCUSDT", _make_info())
    # amount precision
    assert factory.adjust_amount_precision("BTCUSDT", 0.00123) == 0.001
    assert factory.adjust_amount_precision("BTCUSDT", 0.00123, round_up=True) == 0.002
    # price precision
    assert factory.adjust_price_precision("BTCUSDT", 1234.56789) == 1234.56