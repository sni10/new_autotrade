import logging
from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_DOWN, ROUND_UP, ROUND_HALF_UP

from src.domain.entities.currency_pair import CurrencyPair
from src.domain.services.market_data.ticker_processor import TickerProcessor
from src.domain.services.indicators.indicator_calculation_service import IndicatorCalculationService
from src.domain.services.signals.signal_generation_service import SignalGenerationService
from src.domain.services.utils.decimal_rounding_service import DecimalRoundingService

logger = logging.getLogger(__name__)


class RefactoredTickerService:
    """
    Рефакторенный TickerService, соблюдающий принцип единственной ответственности (SRP).
    
    Теперь этот сервис ТОЛЬКО координирует работу специализированных сервисов:
    - TickerProcessor: обработка и валидация тикеров
    - IndicatorCalculationService: вычисление индикаторов
    - SignalGenerationService: генерация торговых сигналов
    
    Больше НЕ содержит кэшей, буферов или бизнес-логики вычислений.
    """
    
    def __init__(
        self,
        ticker_processor: TickerProcessor,
        indicator_service: IndicatorCalculationService,
        signal_service: SignalGenerationService
    ):
        self.ticker_processor = ticker_processor
        self.indicator_service = indicator_service
        self.signal_service = signal_service
        
        self._stats = {
            "tickers_processed": 0,
            "indicators_calculated": 0,
            "signals_generated": 0,
            "errors": 0
        }
    
    async def process_ticker(self, symbol: str, ticker_data: Dict[str, Any]) -> bool:
        """
        Координирует полную обработку тикера:
        1. Обработка и сохранение тикера
        2. Вычисление индикаторов
        3. Генерация сигналов
        """
        try:
            # 1. Обработка тикера
            if not await self.ticker_processor.process_ticker(symbol, ticker_data):
                logger.warning(f"Failed to process ticker for {symbol}")
                return False
            
            current_price = float(ticker_data.get('close', 0))
            if current_price <= 0:
                logger.warning(f"Invalid price in ticker for {symbol}: {current_price}")
                return False
            
            # 2. Вычисление индикаторов
            all_indicators = {}
            
            # Быстрые индикаторы (каждый тик)
            fast_indicators = await self.indicator_service.calculate_fast_indicators(symbol, current_price)
            all_indicators.update(fast_indicators)
            
            # Средние индикаторы (каждые 10 тиков)
            if await self.indicator_service.should_update_medium_indicators(symbol):
                medium_indicators = await self.indicator_service.calculate_medium_indicators(symbol)
                all_indicators.update(medium_indicators)
            
            # Тяжелые индикаторы (каждые 50 тиков)
            if await self.indicator_service.should_update_heavy_indicators(symbol):
                heavy_indicators = await self.indicator_service.calculate_heavy_indicators(symbol)
                all_indicators.update(heavy_indicators)
            
            # Получаем все кэшированные индикаторы для полноты
            cached_indicators = await self.indicator_service.get_all_cached_indicators(symbol)
            all_indicators.update(cached_indicators)
            
            # 3. Генерация сигналов
            if all_indicators:
                combined_signal = await self.signal_service.generate_combined_signal(
                    symbol, all_indicators, current_price
                )
                
                if combined_signal:
                    self._stats["signals_generated"] += 1
            
            self._stats["tickers_processed"] += 1
            if all_indicators:
                self._stats["indicators_calculated"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error in process_ticker for {symbol}: {e}")
            self._stats["errors"] += 1
            return False
    
    async def get_signal(self, symbol: str) -> str:
        """
        Получить текущий торговый сигнал для символа.
        Делегирует выполнение SignalGenerationService.
        """
        try:
            return await self.signal_service.get_current_signal(symbol)
        except Exception as e:
            logger.error(f"Error getting signal for {symbol}: {e}")
            return "HOLD"
    
    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Получить последнюю цену для символа.
        Делегирует выполнение TickerProcessor.
        """
        try:
            return await self.ticker_processor.get_latest_price(symbol)
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {e}")
            return None
    
    async def get_all_indicators(self, symbol: str) -> Dict[str, float]:
        """
        Получить все доступные индикаторы для символа.
        Делегирует выполнение IndicatorCalculationService.
        """
        try:
            return await self.indicator_service.get_all_cached_indicators(symbol)
        except Exception as e:
            logger.error(f"Error getting indicators for {symbol}: {e}")
            return {}
    
    def calculate_strategy(
        self,
        buy_price: float,
        budget: float,
        currency_pair: CurrencyPair,
        profit_percent: float
    ):
        """
        Рассчитывает сделку, используя DecimalRoundingService и данные о
        лимитах и точности из объекта currency_pair.
        
        ПРИМЕЧАНИЕ: Этот метод оставлен для обратной совместимости,
        но в будущем должен быть вынесен в отдельный TradingCalculationService.
        """
        try:
            # 1. Получаем правила с биржи (из объекта currency_pair)
            price_step = Decimal(str(currency_pair.precision.get('price', '0.000001')))
            amount_step = Decimal(str(currency_pair.precision.get('amount', '0.0001')))
            
            # Вычисляем количество знаков после запятой из шага
            price_precision = int(price_step.normalize().as_tuple().exponent * -1)
            amount_precision = int(amount_step.normalize().as_tuple().exponent * -1)
            
            min_notional = Decimal(str(currency_pair.limits.get('cost', {}).get('min', 10.0)))
            
            # 2. Конвертируем все в Decimal для точности
            buy_price_dec = Decimal(str(buy_price))
            budget_dec = Decimal(str(budget))
            buy_fee_rate = Decimal(str(currency_pair.taker_fee))
            sell_fee_rate = Decimal(str(currency_pair.taker_fee))
            profit_dec = Decimal(str(profit_percent))
            
            # 3. Проверка на минимальную сумму ордера
            if budget_dec < min_notional:
                return {"comment": f"❌ Бюджет ({budget_dec}) меньше минимально допустимого ({min_notional})"}
            
            # 4. Расчеты с использованием DecimalRoundingService
            coins_to_buy_raw = budget_dec / buy_price_dec
            coins_to_buy = DecimalRoundingService.ceil_to_precision(coins_to_buy_raw, amount_precision)
            
            # Комиссия вычитается из полученного количества монет
            coins_after_buy_fee = coins_to_buy * (1 - buy_fee_rate)
            
            # Цена продажи, которая покрывает обе комиссии и дает желаемую прибыль
            sell_price_raw = buy_price_dec * (1 + profit_dec) / (1 - sell_fee_rate)
            sell_price = DecimalRoundingService.round_to_precision(sell_price_raw, price_precision)
            
            # Что останется для продажи после уплаты комиссии
            coins_to_sell = DecimalRoundingService.floor_to_precision(
                coins_after_buy_fee,
                amount_precision
            )
            
            # 5. Финальные проверки
            total_cost = coins_to_buy * buy_price_dec
            if total_cost < min_notional:
                return {"comment": f"❌ Итоговая сумма ордера ({total_cost:.2f}) меньше минимально допустимой ({min_notional})"}
            
            final_revenue = coins_to_sell * sell_price
            net_profit = final_revenue - total_cost
            
            return (
                buy_price_dec,
                coins_to_buy,
                sell_price,
                coins_to_sell,
                {
                    "comment": "✅ Сделка возможна.",
                    "net_profit": f"{net_profit:.4f} USDT"
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating strategy: {e}")
            return {"comment": f"❌ Ошибка расчета стратегии: {e}"}
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Получить объединенную статистику всех сервисов"""
        try:
            return {
                "coordinator_stats": self._stats.copy(),
                "ticker_processor_stats": self.ticker_processor.get_processing_stats(),
                "indicator_service_stats": self.indicator_service.get_stats(),
                "signal_service_stats": self.signal_service.get_stats()
            }
        except Exception as e:
            logger.error(f"Error getting comprehensive stats: {e}")
            return {"error": str(e)}
    
    def reset_all_stats(self) -> None:
        """Сбросить статистику всех сервисов"""
        try:
            self._stats = {
                "tickers_processed": 0,
                "indicators_calculated": 0,
                "signals_generated": 0,
                "errors": 0
            }
            self.ticker_processor.reset_stats()
            self.indicator_service.reset_stats()
            self.signal_service.reset_stats()
            
        except Exception as e:
            logger.error(f"Error resetting stats: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка состояния всех компонентов"""
        health = {
            "status": "healthy",
            "components": {},
            "timestamp": int(__import__('time').time() * 1000)
        }
        
        try:
            # Проверяем каждый компонент
            components = [
                ("ticker_processor", self.ticker_processor),
                ("indicator_service", self.indicator_service),
                ("signal_service", self.signal_service)
            ]
            
            for name, component in components:
                try:
                    # Простая проверка - попытка получить статистику
                    if hasattr(component, 'get_stats'):
                        stats = component.get_stats()
                        health["components"][name] = {
                            "status": "healthy",
                            "stats": stats
                        }
                    else:
                        health["components"][name] = {"status": "healthy"}
                        
                except Exception as e:
                    health["components"][name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health