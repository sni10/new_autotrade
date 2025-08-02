from decimal import Decimal
import pytest

from domain.services.market_data.ticker_service import TickerService
from domain.entities.currency_pair import CurrencyPair
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository
from infrastructure.repositories.indicators_repository import InMemoryIndicatorsRepository


@pytest.fixture
def ticker_service():
    """Фикстура для создания экземпляра TickerService."""
    tickers_repo = InMemoryTickerRepository()
    indicators_repo = InMemoryIndicatorsRepository()
    return TickerService(tickers_repo, indicators_repo)

@pytest.fixture
def eth_usdt_pair():
    """Фикстура, имитирующая реальные данные для ETH/USDT."""
    pair = CurrencyPair('ETH', 'USDT', 'ETH/USDT')
    # Данные, полученные из анализа API
    pair.precision = {'amount': 4, 'price': 2}
    pair.limits = {'amount': {'min': 0.0001}, 'cost': {'min': 10.0}}
    return pair

def test_calculate_strategy_success(ticker_service, eth_usdt_pair):
    """Тест успешного расчета стратегии с достаточным бюджетом."""
    result = ticker_service.calculate_strategy(
        buy_price=3000.0,
        budget=100.0,
        currency_pair=eth_usdt_pair,
        profit_percent=1.0
    )
    assert isinstance(result, tuple), f"Ожидался tuple, получили: {getattr(result, 'comment', result)}"
    assert result[0] == Decimal('3000.0')
    assert result[1] > 0  # Должны купить какое-то количество монет

def test_calculate_strategy_insufficient_budget(ticker_service, eth_usdt_pair):
    """Тест, когда бюджет меньше минимально допустимого биржей."""
    result = ticker_service.calculate_strategy(
        buy_price=3000.0,
        budget=5.0,  # Меньше, чем limits['cost']['min'] = 10.0
        currency_pair=eth_usdt_pair,
        profit_percent=1.0
    )
    assert isinstance(result, dict)
    assert "Бюджет (5.0) меньше минимально допустимого (10.0)" in result['comment']

def test_calculate_strategy_very_low_price(ticker_service, eth_usdt_pair):
    """Тест, когда цена настолько низкая, что на бюджет можно купить очень много, 
       но итоговая сумма все равно проходит."""
    result = ticker_service.calculate_strategy(
        buy_price=0.02,
        budget=20.0, # Больше минимального
        currency_pair=eth_usdt_pair,
        profit_percent=5.0
    )
    assert isinstance(result, tuple), f"Ожидался tuple, получили: {getattr(result, 'comment', result)}"
    assert result[1] > 0

def test_calculate_strategy_budget_just_above_minimum(ticker_service, eth_usdt_pair):
    """Тест, когда бюджет чуть выше минимального."""
    result = ticker_service.calculate_strategy(
        buy_price=3000.0,
        budget=11.0, # Чуть больше минимального
        currency_pair=eth_usdt_pair,
        profit_percent=1.0
    )
    assert isinstance(result, tuple), f"Ожидался tuple, получили: {getattr(result, 'comment', result)}"