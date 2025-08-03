import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair

def make_deal(deal_id, status=Deal.STATUS_OPEN):
    pair = CurrencyPair(symbol="BTC/USDT", base_currency="BTC", quote_currency="USDT")
    return Deal(deal_id=deal_id, currency_pair=pair, status=status)


def test_save_and_get_open():
    repo = InMemoryDealsRepository()
    d1 = make_deal(1)
    d2 = make_deal(2, status=Deal.STATUS_CLOSED)
    repo.save(d1)
    repo.save(d2)
    assert repo.get_by_id(1) == d1
    assert repo.get_open_deals() == [d1]
    assert set(repo.get_all()) == {d1, d2}