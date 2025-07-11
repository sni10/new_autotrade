from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from domain.entities.deal import Deal


def make_deal(deal_id, status=Deal.STATUS_OPEN):
    return Deal(deal_id=deal_id, currency_pair_id='BTCUSDT', status=status)


def test_save_and_get_open():
    repo = InMemoryDealsRepository()
    d1 = make_deal(1)
    d2 = make_deal(2, status=Deal.STATUS_CLOSED)
    repo.save(d1)
    repo.save(d2)
    assert repo.get_by_id(1) == d1
    assert repo.get_open_deals() == [d1]
    assert set(repo.get_all()) == {d1, d2}
