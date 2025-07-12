import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from infrastructure.repositories.tickers_repository import InMemoryTickerRepository
from domain.entities.ticker import Ticker


def test_save_and_get_last_n_with_cache():
    repo = InMemoryTickerRepository(max_size=5)
    for i in range(7):
        t = Ticker({'timestamp': i, 'symbol': 'BTCUSDT', 'last': i})
        repo.save(t)
    last_two = repo.get_last_n(2)
    assert len(last_two) == 2
    # repository currently does not prune when max_size exceeded
    assert last_two[0].timestamp == 5
    assert last_two[-1].timestamp == 6
    # cache should return same objects without modification
    cached = repo.get_last_n(2)
    assert cached is last_two