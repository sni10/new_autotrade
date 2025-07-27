import time
from typing import Optional
import logging

from .ccxt_monitoring import CcxtMonitoring

logger = logging.getLogger(__name__)


class PerformanceLogger:
    def __init__(self, log_interval_seconds: int = 5, ccxt_monitor: Optional[CcxtMonitoring] = None):
        self.tick_count = 0
        self.last_log_time = time.time()
        self.log_interval = log_interval_seconds
        self.start_time = time.time()

        self.ccxt_monitor = ccxt_monitor

        # Статистика производительности
        self.total_processing_time = 0
        self.min_tick_time = float('inf')
        self.max_tick_time = 0

    def should_log(self) -> bool:
        """Определяет, нужно ли логировать сейчас"""
        current_time = time.time()
        return current_time - self.last_log_time >= self.log_interval

    def log_tick(self, price: float, processing_time: float, signals_count: int = 0):
        """Логирует информацию о тике"""
        self.tick_count += 1
        self.total_processing_time += processing_time
        self.min_tick_time = min(self.min_tick_time, processing_time)
        self.max_tick_time = max(self.max_tick_time, processing_time)

        if self.should_log():
            self._print_performance_stats(price, signals_count)
            self.last_log_time = time.time()

    # В performance_logger.py добавить:
    def log_detailed_signals(self, ticker):
        """Подробный вывод сигналов"""
        if ticker.signals and self.should_log():
            signals = ticker.signals
            logger.info(
                f"📈 MACD: {signals.get('macd', 0):.6f} | "
                f"Signal: {signals.get('signal', 0):.6f} | "
                f"Hist: {signals.get('histogram', 0):.6f}"
            )
            logger.info(
                f"📊 RSI(5): {signals.get('rsi_5', 0):.2f} | "
                f"RSI(15): {signals.get('rsi_15', 0):.2f}"
            )
            logger.info(
                f"📉 SMA(7): {signals.get('sma_7', 0):.8f} | "
                f"SMA(25): {signals.get('sma_25', 0):.8f}"
            )

    def _print_performance_stats(self, price: float, signals_count: int):
        """Выводит статистику производительности"""
        avg_time = self.total_processing_time / self.tick_count if self.tick_count > 0 else 0
        uptime = time.time() - self.start_time
        tps = self.tick_count / uptime if uptime > 0 else 0  # Ticks per second

        message = (
            f"📊 Тик {self.tick_count} | Цена: {price:.8f} | "
            f"Сигналов: {signals_count} | TPS: {tps:.1f} | "
            f"Среднее время: {avg_time*1000:.1f}ms | "
            f"Мин/Макс: {self.min_tick_time*1000:.1f}/{self.max_tick_time*1000:.1f}ms"
        )

        if self.ccxt_monitor:
            ccxt_stats = self.ccxt_monitor.get_metrics()
            message += (
                f" | CCXT: {ccxt_stats['avg_duration_ms']:.1f}ms avg, "
                f"{ccxt_stats['error_rate']*100:.1f}% errors"
            )

        logger.info(message)

    def log_cache_update(self, cache_type: str, tick_count: int):
        """Логирует обновления кеша"""
        logger.info(f"🔄 {cache_type} кеш обновлен на тике {tick_count}")
