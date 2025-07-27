import logging
import time
from typing import Any, Awaitable, Callable, Optional

from src.domain.repositories.i_statistics_repository import IStatisticsRepository
from src.domain.entities.statistics import StatisticCategory

logger = logging.getLogger(__name__)


class CcxtMonitoring:
    """Utility to monitor CCXT API calls."""

    def __init__(self, statistics_repo: Optional[IStatisticsRepository] = None) -> None:
        self.statistics_repo = statistics_repo
        self.total_calls = 0
        self.total_errors = 0
        self.total_duration_ms = 0.0

    async def record(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        method_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Execute and monitor an async CCXT call."""
        name = method_name or getattr(func, "__name__", "unknown")
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception:
            self.total_errors += 1
            raise
        finally:
            duration_ms = (time.time() - start) * 1000
            self.total_calls += 1
            self.total_duration_ms += duration_ms
            logger.debug("⏱️ CCXT %s took %.2fms", name, duration_ms)
            if self.statistics_repo:
                try:
                    await self.statistics_repo.record_timing(
                        "ccxt_call_duration_ms",
                        StatisticCategory.EXCHANGE,
                        duration_ms,
                        tags={"method": name},
                    )
                except Exception as exc:  # pragma: no cover - optional
                    logger.debug("Failed to record timing: %s", exc)
                if self.total_errors and name in str(func):
                    try:
                        await self.statistics_repo.increment_counter(
                            "ccxt_call_errors",
                            StatisticCategory.EXCHANGE,
                            tags={"method": name},
                        )
                    except Exception as exc:  # pragma: no cover - optional
                        logger.debug("Failed to increment error counter: %s", exc)

    def get_metrics(self) -> dict:
        """Return aggregated metrics."""
        avg_duration = self.total_duration_ms / self.total_calls if self.total_calls else 0.0
        error_rate = self.total_errors / self.total_calls if self.total_calls else 0.0
        return {
            "total_calls": self.total_calls,
            "avg_duration_ms": avg_duration,
            "error_rate": error_rate,
        }
