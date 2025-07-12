import pandas as pd
import pytest
from unittest.mock import MagicMock

from domain.services.order_execution_service import OrderExecutionService
from domain.services.order_service import OrderService
from domain.services.deal_service import DealService
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from domain.factories.order_factory import OrderFactory
from domain.factories.deal_factory import DealFactory


def create_service():
    order_factory = OrderFactory()
    orders_repo = InMemoryOrdersRepository()
    order_service = OrderService(orders_repo, order_factory, exchange_connector=MagicMock())
    deal_factory = DealFactory(order_factory)
    deal_service = DealService(InMemoryDealsRepository(), order_service, deal_factory)
    return OrderExecutionService(order_service, deal_service, MagicMock())


def test_update_execution_stats_dataframe():
    svc = create_service()

    data = pd.DataFrame({
        "success": [True, False, True, True],
        "volume": [10.0, 0.0, 5.0, 15.0],
        "fees": [0.1, 0.0, 0.05, 0.15],
        "time": [100.0, 150.0, 120.0, 110.0],
    })

    for _, row in data.iterrows():
        svc._update_execution_stats(row.success, row.volume, row.fees, row.time)

    stats = svc.get_execution_statistics()

    assert stats["total_executions"] == len(data)
    assert stats["successful_executions"] == data[data.success].shape[0]
    assert stats["failed_executions"] == data[~data.success].shape[0]
    assert stats["total_volume"] == pytest.approx(data[data.success].volume.sum())
    assert stats["total_fees"] == pytest.approx(data[data.success].fees.sum())
    assert stats["average_execution_time_ms"] == pytest.approx(data.time.mean())

