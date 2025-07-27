import asyncio
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..', 'src')))

from src.application.utils.ccxt_monitoring import CcxtMonitoring


@pytest.mark.asyncio
async def test_record_successful_call():
    monitor = CcxtMonitoring()

    async def dummy():
        await asyncio.sleep(0)
        return 42

    result = await monitor.record(dummy)
    assert result == 42
    metrics = monitor.get_metrics()
    assert metrics['total_calls'] == 1
    assert metrics['error_rate'] == 0


@pytest.mark.asyncio
async def test_record_failed_call():
    monitor = CcxtMonitoring()

    async def failing():
        await asyncio.sleep(0)
        raise ValueError("boom")

    with pytest.raises(ValueError):
        await monitor.record(failing)

    metrics = monitor.get_metrics()
    assert metrics['total_calls'] == 1
    assert metrics['error_rate'] == 1

