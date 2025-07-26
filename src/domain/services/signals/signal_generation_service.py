import logging
from typing import Dict, List, Optional, Any
import time

from src.domain.entities.trading_signal import TradingSignal, SignalType, SignalSource
from src.domain.repositories.i_trading_signal_repository import ITradingSignalRepository
from src.domain.repositories.i_cache_repository import ICacheRepository

logger = logging.getLogger(__name__)


class SignalGenerationService:
    """
    Сервис для генерации торговых сигналов.
    Соблюдает принцип единственной ответственности (SRP).
    Отвечает ТОЛЬКО за создание торговых сигналов на основе индикаторов.
    """
    
    def __init__(
        self,
        signal_repository: ITradingSignalRepository,
        cache_repository: Optional[ICacheRepository] = None
    ):
        self.signal_repository = signal_repository
        self.cache_repository = cache_repository
        
        self._stats = {
            "signals_generated": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "hold_signals": 0,
            "combined_signals": 0,
            "errors": 0
        }
    
    async def generate_macd_signal(self, symbol: str, indicators: Dict[str, float]) -> Optional[TradingSignal]:
        """Генерировать сигнал на основе MACD"""
        try:
            macd = indicators.get('macd', 0)
            signal = indicators.get('macd_signal', 0)
            histogram = indicators.get('macd_histogram', 0)
            
            if macd == 0 or signal == 0:
                return None
            
            # Определяем тип сигнала
            if macd > signal and histogram > 0:
                signal_type = SignalType.BUY
                strength = min(abs(histogram) / 100, 1.0)  # Нормализация
            elif macd < signal and histogram < 0:
                signal_type = SignalType.SELL
                strength = min(abs(histogram) / 100, 1.0)
            else:
                signal_type = SignalType.HOLD
                strength = 0.1
            
            # Уверенность основана на силе дивергенции
            confidence = min(abs(macd - signal) / max(abs(macd), abs(signal), 0.001), 0.95)
            
            trading_signal = TradingSignal(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                signal_type=signal_type,
                source=SignalSource.MACD,
                strength=strength,
                confidence=confidence,
                metadata={
                    "macd": macd,
                    "signal": signal,
                    "histogram": histogram
                }
            )
            
            await self._save_signal(trading_signal)
            return trading_signal
            
        except Exception as e:
            logger.error(f"Error generating MACD signal for {symbol}: {e}")
            self._stats["errors"] += 1
            return None
    
    async def generate_sma_crossover_signal(self, symbol: str, indicators: Dict[str, float]) -> Optional[TradingSignal]:
        """Генерировать сигнал на основе пересечения SMA"""
        try:
            sma_7 = indicators.get('sma_7', 0)
            sma_25 = indicators.get('sma_25', 0)
            
            if sma_7 == 0 or sma_25 == 0:
                return None
            
            # Определяем силу сигнала на основе разности SMA
            price_diff_percent = abs(sma_7 - sma_25) / sma_25 * 100
            
            if sma_7 > sma_25:
                signal_type = SignalType.BUY
                strength = min(price_diff_percent / 5.0, 1.0)  # 5% = максимальная сила
            elif sma_7 < sma_25:
                signal_type = SignalType.SELL  
                strength = min(price_diff_percent / 5.0, 1.0)
            else:
                signal_type = SignalType.HOLD
                strength = 0.1
            
            # Уверенность зависит от величины разрыва
            confidence = min(price_diff_percent / 2.0, 0.9)  # 2% = высокая уверенность
            
            trading_signal = TradingSignal(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                signal_type=signal_type,
                source=SignalSource.SMA_CROSSOVER,
                strength=strength,
                confidence=confidence,
                metadata={
                    "sma_7": sma_7,
                    "sma_25": sma_25,
                    "price_diff_percent": price_diff_percent
                }
            )
            
            await self._save_signal(trading_signal)
            return trading_signal
            
        except Exception as e:
            logger.error(f"Error generating SMA crossover signal for {symbol}: {e}")
            self._stats["errors"] += 1
            return None
    
    async def generate_rsi_signal(self, symbol: str, indicators: Dict[str, float]) -> Optional[TradingSignal]:
        """Генерировать сигнал на основе RSI"""
        try:
            rsi_5 = indicators.get('rsi_5', 50)
            rsi_15 = indicators.get('rsi_15', 50)
            
            # Средний RSI для более стабильного сигнала
            avg_rsi = (rsi_5 + rsi_15) / 2
            
            # Определяем сигнал
            if avg_rsi < 30:  # Перепроданность
                signal_type = SignalType.BUY
                strength = (30 - avg_rsi) / 30  # Чем ниже, тем сильнее
            elif avg_rsi > 70:  # Перекупленность
                signal_type = SignalType.SELL
                strength = (avg_rsi - 70) / 30  # Чем выше, тем сильнее
            else:
                signal_type = SignalType.HOLD
                strength = 0.1
            
            # Уверенность зависит от экстремальности значения
            if avg_rsi < 30 or avg_rsi > 70:
                confidence = min(abs(avg_rsi - 50) / 50, 0.9)
            else:
                confidence = 0.3
            
            trading_signal = TradingSignal(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                signal_type=signal_type,
                source=SignalSource.RSI,
                strength=strength,
                confidence=confidence,
                metadata={
                    "rsi_5": rsi_5,
                    "rsi_15": rsi_15,
                    "avg_rsi": avg_rsi
                }
            )
            
            await self._save_signal(trading_signal)
            return trading_signal
            
        except Exception as e:
            logger.error(f"Error generating RSI signal for {symbol}: {e}")
            self._stats["errors"] += 1
            return None
    
    async def generate_bollinger_signal(self, symbol: str, indicators: Dict[str, float], current_price: float) -> Optional[TradingSignal]:
        """Генерировать сигнал на основе Bollinger Bands"""
        try:
            bb_upper = indicators.get('bb_upper', 0)
            bb_middle = indicators.get('bb_middle', 0)
            bb_lower = indicators.get('bb_lower', 0)
            
            if bb_upper == 0 or bb_lower == 0 or bb_middle == 0:
                return None
            
            # Определяем положение цены относительно полос
            bb_range = bb_upper - bb_lower
            if bb_range == 0:
                return None
            
            # Позиция в процентах (0 = нижняя полоса, 1 = верхняя полоса)
            bb_position = (current_price - bb_lower) / bb_range
            
            if bb_position < 0.2:  # Близко к нижней полосе
                signal_type = SignalType.BUY
                strength = 1.0 - bb_position / 0.2  # Чем ближе к низу, тем сильнее
            elif bb_position > 0.8:  # Близко к верхней полосе
                signal_type = SignalType.SELL
                strength = (bb_position - 0.8) / 0.2  # Чем ближе к верху, тем сильнее
            else:
                signal_type = SignalType.HOLD
                strength = 0.1
            
            # Уверенность зависит от ширины полос (узкие полосы = выше уверенность)
            bb_width_percent = bb_range / bb_middle * 100
            confidence = max(0.3, min(0.9, 5.0 / bb_width_percent))  # 5% ширина = высокая уверенность
            
            trading_signal = TradingSignal(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                signal_type=signal_type,
                source=SignalSource.BOLLINGER_BANDS,
                strength=strength,
                confidence=confidence,
                price=current_price,
                metadata={
                    "bb_upper": bb_upper,
                    "bb_middle": bb_middle,
                    "bb_lower": bb_lower,
                    "bb_position": bb_position,
                    "bb_width_percent": bb_width_percent
                }
            )
            
            await self._save_signal(trading_signal)
            return trading_signal
            
        except Exception as e:
            logger.error(f"Error generating Bollinger signal for {symbol}: {e}")
            self._stats["errors"] += 1
            return None
    
    async def generate_combined_signal(self, symbol: str, indicators: Dict[str, float], current_price: float) -> Optional[TradingSignal]:
        """Генерировать комбинированный сигнал на основе всех индикаторов"""
        try:
            # Генерируем все отдельные сигналы
            signals = []
            
            macd_signal = await self.generate_macd_signal(symbol, indicators)
            if macd_signal:
                signals.append(macd_signal)
            
            sma_signal = await self.generate_sma_crossover_signal(symbol, indicators)
            if sma_signal:
                signals.append(sma_signal)
            
            rsi_signal = await self.generate_rsi_signal(symbol, indicators)
            if rsi_signal:
                signals.append(rsi_signal)
            
            bollinger_signal = await self.generate_bollinger_signal(symbol, indicators, current_price)
            if bollinger_signal:
                signals.append(bollinger_signal)
            
            if not signals:
                return None
            
            # Комбинируем сигналы
            buy_signals = [s for s in signals if s.is_bullish]
            sell_signals = [s for s in signals if s.is_bearish]
            
            # Определяем итоговый сигнал
            if len(buy_signals) > len(sell_signals):
                signal_type = SignalType.STRONG_BUY if len(buy_signals) >= 3 else SignalType.BUY
                relevant_signals = buy_signals
            elif len(sell_signals) > len(buy_signals):
                signal_type = SignalType.STRONG_SELL if len(sell_signals) >= 3 else SignalType.SELL
                relevant_signals = sell_signals
            else:
                signal_type = SignalType.HOLD
                relevant_signals = signals
            
            # Средние значения силы и уверенности
            avg_strength = sum(s.strength for s in relevant_signals) / len(relevant_signals)
            avg_confidence = sum(s.confidence for s in relevant_signals) / len(relevant_signals)
            
            # Бонус за согласованность
            if len(relevant_signals) >= 3:
                avg_confidence = min(avg_confidence * 1.2, 0.95)
            
            combined_signal = TradingSignal(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                signal_type=signal_type,
                source=SignalSource.COMBINED,
                strength=avg_strength,
                confidence=avg_confidence,
                price=current_price,
                metadata={
                    "component_signals": [s.signal_id for s in signals],
                    "buy_count": len(buy_signals),
                    "sell_count": len(sell_signals),
                    "total_signals": len(signals)
                }
            )
            
            await self._save_signal(combined_signal)
            self._stats["combined_signals"] += 1
            
            return combined_signal
            
        except Exception as e:
            logger.error(f"Error generating combined signal for {symbol}: {e}")
            self._stats["errors"] += 1
            return None
    
    async def get_current_signal(self, symbol: str) -> str:
        """Получить текущий торговый сигнал в простом формате"""
        try:
            # Получаем последний комбинированный сигнал
            latest_signal = await self.signal_repository.get_latest(symbol)
            
            if not latest_signal or not latest_signal.is_actionable:
                return "HOLD"
            
            if latest_signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                return "BUY"
            elif latest_signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                return "SELL"
            else:
                return "HOLD"
                
        except Exception as e:
            logger.error(f"Error getting current signal for {symbol}: {e}")
            return "HOLD"
    
    async def _save_signal(self, signal: TradingSignal) -> None:
        """Сохранить сигнал в репозиторий и кэш"""
        try:
            # Сохраняем в репозиторий
            await self.signal_repository.save(signal)
            
            # Кэшируем если есть кэш-репозиторий
            if self.cache_repository:
                signal_data = {
                    "signal_type": signal.signal_type.value,
                    "strength": signal.strength,
                    "confidence": signal.confidence,
                    "timestamp": signal.timestamp,
                    "is_actionable": signal.is_actionable
                }
                await self.cache_repository.cache_signal(
                    signal.symbol, signal.source.value, signal_data, 60
                )
            
            # Обновляем статистику
            self._stats["signals_generated"] += 1
            if signal.is_bullish:
                self._stats["buy_signals"] += 1
            elif signal.is_bearish:
                self._stats["sell_signals"] += 1
            else:
                self._stats["hold_signals"] += 1
                
        except Exception as e:
            logger.error(f"Error saving signal {signal.signal_id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику сервиса"""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Сбросить статистику"""
        self._stats = {
            "signals_generated": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "hold_signals": 0,
            "combined_signals": 0,
            "errors": 0
        }