# domain/services/market_data/ccxt_market_service.py
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

from src.domain.entities.ccxt_currency_pair import CCXTCurrencyPair, create_ccxt_currency_pair_from_market
from src.infrastructure.connectors.ccxt_exchange_connector import CCXTExchangeConnector

logger = logging.getLogger(__name__)


class CCXTMarketService:
    """
    🚀 CCXT Market Data Service
    
    Сервис для работы с рыночными данными через CCXT.
    Управляет торговыми парами, загружает market data, предоставляет unified интерфейс.
    
    Основные возможности:
    - Загрузка и кэширование CCXT markets
    - Создание CCXTCurrencyPair из market data
    - Автоматическое обновление market information
    - Валидация торговых пар
    - Поиск и фильтрация рынков
    """

    def __init__(
        self,
        exchange_connector: CCXTExchangeConnector,
        auto_update_enabled: bool = True,
        update_interval_seconds: int = 3600,  # 1 час
        cache_ttl_seconds: int = 1800         # 30 минут
    ):
        self.exchange_connector = exchange_connector
        self.auto_update_enabled = auto_update_enabled
        self.update_interval_seconds = update_interval_seconds
        self.cache_ttl_seconds = cache_ttl_seconds
        
        # Кэши
        self._markets_cache: Dict[str, Dict[str, Any]] = {}
        self._currency_pairs_cache: Dict[str, CCXTCurrencyPair] = {}
        self._cache_timestamp: float = 0
        
        # Статистика
        self.stats = {
            'markets_loaded': 0,
            'currency_pairs_created': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'update_operations': 0,
            'last_update': None
        }
        
        # Автообновление
        self._update_task: Optional[asyncio.Task] = None

    # ===== CORE MARKET OPERATIONS =====

    async def load_markets(self, reload: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Загрузка рынков с биржи через CCXT
        """
        try:
            # Проверяем кэш
            if not reload and self._is_cache_fresh():
                self.stats['cache_hits'] += 1
                return self._markets_cache

            logger.info("Loading markets from exchange...")
            
            # Загружаем с биржи
            markets = await self.exchange_connector.load_markets(reload)
            
            # Обновляем кэш
            self._markets_cache = markets
            self._cache_timestamp = time.time()
            
            # Обновляем статистику
            self.stats['markets_loaded'] = len(markets)
            self.stats['update_operations'] += 1
            self.stats['last_update'] = datetime.now(timezone.utc).isoformat()
            self.stats['cache_misses'] += 1
            
            logger.info(f"✅ Loaded {len(markets)} markets from {self.exchange_connector.exchange_name}")
            
            return markets

        except Exception as e:
            logger.error(f"Failed to load markets: {e}")
            raise

    async def get_market_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о конкретном рынке
        """
        try:
            markets = await self.load_markets()
            return markets.get(symbol)

        except Exception as e:
            logger.error(f"Failed to get market info for {symbol}: {e}")
            return None

    async def create_currency_pair(
        self,
        symbol: str,
        **autotrade_params
    ) -> Optional[CCXTCurrencyPair]:
        """
        Создание CCXTCurrencyPair с загрузкой market data
        """
        try:
            # Проверяем кэш currency pairs
            if symbol in self._currency_pairs_cache:
                cached_pair = self._currency_pairs_cache[symbol]
                if cached_pair.is_market_data_fresh():
                    self.stats['cache_hits'] += 1
                    return cached_pair

            # Получаем market data
            market_data = await self.get_market_info(symbol)
            if not market_data:
                logger.error(f"Market data not found for symbol: {symbol}")
                return None

            # Создаем currency pair
            currency_pair = create_ccxt_currency_pair_from_market(
                market_data,
                **autotrade_params
            )

            # Кэшируем
            self._currency_pairs_cache[symbol] = currency_pair
            
            # Обновляем статистику
            self.stats['currency_pairs_created'] += 1
            self.stats['cache_misses'] += 1

            logger.info(f"✅ Created CCXTCurrencyPair for {symbol}")
            return currency_pair

        except Exception as e:
            logger.error(f"Failed to create currency pair for {symbol}: {e}")
            return None

    async def update_currency_pair_market_data(self, currency_pair: CCXTCurrencyPair) -> bool:
        """
        Обновление market data для currency pair
        """
        try:
            market_data = await self.get_market_info(currency_pair.symbol)
            if not market_data:
                return False

            success = currency_pair.update_from_ccxt_market(market_data)
            
            if success:
                # Обновляем кэш
                self._currency_pairs_cache[currency_pair.symbol] = currency_pair
                logger.debug(f"Updated market data for {currency_pair.symbol}")

            return success

        except Exception as e:
            logger.error(f"Failed to update market data for {currency_pair.symbol}: {e}")
            return False

    # ===== SEARCH AND FILTER METHODS =====

    async def find_markets_by_base(self, base_currency: str) -> List[Dict[str, Any]]:
        """
        Поиск рынков по базовой валюте
        """
        try:
            markets = await self.load_markets()
            
            matching_markets = []
            for market_data in markets.values():
                if market_data.get('base', '').upper() == base_currency.upper():
                    matching_markets.append(market_data)
            
            logger.debug(f"Found {len(matching_markets)} markets for base currency {base_currency}")
            return matching_markets

        except Exception as e:
            logger.error(f"Failed to find markets by base {base_currency}: {e}")
            return []

    async def find_markets_by_quote(self, quote_currency: str) -> List[Dict[str, Any]]:
        """
        Поиск рынков по котируемой валюте
        """
        try:
            markets = await self.load_markets()
            
            matching_markets = []
            for market_data in markets.values():
                if market_data.get('quote', '').upper() == quote_currency.upper():
                    matching_markets.append(market_data)
            
            logger.debug(f"Found {len(matching_markets)} markets for quote currency {quote_currency}")
            return matching_markets

        except Exception as e:
            logger.error(f"Failed to find markets by quote {quote_currency}: {e}")
            return []

    async def get_active_spot_markets(self) -> List[Dict[str, Any]]:
        """
        Получение активных спот рынков
        """
        try:
            markets = await self.load_markets()
            
            active_spot_markets = []
            for market_data in markets.values():
                if (market_data.get('active', False) and 
                    market_data.get('spot', False) and
                    market_data.get('type') == 'spot'):
                    active_spot_markets.append(market_data)
            
            logger.debug(f"Found {len(active_spot_markets)} active spot markets")
            return active_spot_markets

        except Exception as e:
            logger.error(f"Failed to get active spot markets: {e}")
            return []

    async def search_markets(
        self,
        query: str,
        active_only: bool = True,
        spot_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск рынков по запросу
        """
        try:
            markets = await self.load_markets()
            
            matching_markets = []
            query_upper = query.upper()
            
            for market_data in markets.values():
                # Фильтрация по активности
                if active_only and not market_data.get('active', False):
                    continue
                
                # Фильтрация по типу (спот)
                if spot_only and not market_data.get('spot', False):
                    continue
                
                # Поиск по символу, базовой или котируемой валюте
                symbol = market_data.get('symbol', '').upper()
                base = market_data.get('base', '').upper()
                quote = market_data.get('quote', '').upper()
                
                if (query_upper in symbol or 
                    query_upper in base or 
                    query_upper in quote):
                    matching_markets.append(market_data)
                
                # Ограничение количества результатов
                if limit and len(matching_markets) >= limit:
                    break
            
            logger.debug(f"Found {len(matching_markets)} markets matching query '{query}'")
            return matching_markets

        except Exception as e:
            logger.error(f"Failed to search markets with query '{query}': {e}")
            return []

    # ===== CURRENCY PAIR MANAGEMENT =====

    async def create_currency_pairs_batch(
        self,
        symbols: List[str],
        **common_autotrade_params
    ) -> Dict[str, Optional[CCXTCurrencyPair]]:
        """
        Массовое создание currency pairs
        """
        results = {}
        
        try:
            # Предзагружаем markets для оптимизации
            await self.load_markets()
            
            # Создаем currency pairs
            for symbol in symbols:
                try:
                    currency_pair = await self.create_currency_pair(
                        symbol,
                        **common_autotrade_params
                    )
                    results[symbol] = currency_pair
                    
                except Exception as e:
                    logger.error(f"Failed to create currency pair for {symbol}: {e}")
                    results[symbol] = None
            
            success_count = sum(1 for pair in results.values() if pair is not None)
            logger.info(f"Created {success_count}/{len(symbols)} currency pairs")
            
            return results

        except Exception as e:
            logger.error(f"Failed to create currency pairs batch: {e}")
            return {symbol: None for symbol in symbols}

    async def update_all_currency_pairs(self) -> int:
        """
        Обновление market data для всех кэшированных currency pairs
        """
        updated_count = 0
        
        try:
            # Предзагружаем markets
            await self.load_markets()
            
            # Обновляем каждую currency pair
            for currency_pair in self._currency_pairs_cache.values():
                if await self.update_currency_pair_market_data(currency_pair):
                    updated_count += 1
            
            logger.info(f"Updated market data for {updated_count} currency pairs")
            return updated_count

        except Exception as e:
            logger.error(f"Failed to update currency pairs: {e}")
            return 0

    def get_cached_currency_pairs(self) -> Dict[str, CCXTCurrencyPair]:
        """
        Получение всех кэшированных currency pairs
        """
        return self._currency_pairs_cache.copy()

    def remove_currency_pair_from_cache(self, symbol: str) -> bool:
        """
        Удаление currency pair из кэша
        """
        if symbol in self._currency_pairs_cache:
            del self._currency_pairs_cache[symbol]
            logger.debug(f"Removed {symbol} from currency pairs cache")
            return True
        return False

    def clear_currency_pairs_cache(self):
        """
        Очистка кэша currency pairs
        """
        cleared_count = len(self._currency_pairs_cache)
        self._currency_pairs_cache.clear()
        logger.info(f"Cleared {cleared_count} currency pairs from cache")

    # ===== VALIDATION METHODS =====

    async def validate_symbol(self, symbol: str) -> Tuple[bool, str]:
        """
        Валидация символа торговой пары
        """
        try:
            market_data = await self.get_market_info(symbol)
            
            if not market_data:
                return False, f"Symbol {symbol} not found on exchange"
            
            if not market_data.get('active', False):
                return False, f"Symbol {symbol} is not active"
            
            if not market_data.get('spot', False):
                return False, f"Symbol {symbol} does not support spot trading"
            
            return True, "Valid"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def validate_trading_requirements(
        self,
        symbol: str,
        min_amount: Optional[float] = None,
        min_cost: Optional[float] = None
    ) -> Tuple[bool, List[str]]:
        """
        Валидация торговых требований
        """
        errors = []
        
        try:
            market_data = await self.get_market_info(symbol)
            
            if not market_data:
                errors.append(f"Market data not found for {symbol}")
                return False, errors
            
            limits = market_data.get('limits', {})
            
            # Проверка минимального количества
            if min_amount is not None:
                amount_limits = limits.get('amount', {})
                market_min_amount = amount_limits.get('min')
                
                if market_min_amount and min_amount < market_min_amount:
                    errors.append(f"Minimum amount {min_amount} below market minimum {market_min_amount}")
            
            # Проверка минимальной стоимости
            if min_cost is not None:
                cost_limits = limits.get('cost', {})
                market_min_cost = cost_limits.get('min')
                
                if market_min_cost and min_cost < market_min_cost:
                    errors.append(f"Minimum cost {min_cost} below market minimum {market_min_cost}")
            
            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors

    # ===== AUTO UPDATE METHODS =====

    async def start_auto_update(self):
        """
        Запуск автоматического обновления market data
        """
        if not self.auto_update_enabled:
            logger.warning("Auto update disabled")
            return

        if self._update_task and not self._update_task.done():
            logger.warning("Auto update already running")
            return

        logger.info(f"Starting auto market update with interval {self.update_interval_seconds}s")
        self._update_task = asyncio.create_task(self._auto_update_loop())

    async def stop_auto_update(self):
        """
        Остановка автоматического обновления
        """
        if self._update_task and not self._update_task.done():
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            logger.info("Auto market update stopped")

    async def _auto_update_loop(self):
        """
        Цикл автоматического обновления
        """
        try:
            while True:
                try:
                    # Обновляем markets
                    await self.load_markets(reload=True)
                    
                    # Обновляем currency pairs
                    await self.update_all_currency_pairs()
                    
                    await asyncio.sleep(self.update_interval_seconds)
                    
                except Exception as e:
                    logger.error(f"Error in auto update loop: {e}")
                    await asyncio.sleep(60)  # Короткая пауза при ошибке
                    
        except asyncio.CancelledError:
            logger.info("Auto update loop cancelled")

    # ===== HELPER METHODS =====

    def _is_cache_fresh(self) -> bool:
        """
        Проверка актуальности кэша markets
        """
        if not self._markets_cache:
            return False
        
        age_seconds = time.time() - self._cache_timestamp
        return age_seconds < self.cache_ttl_seconds

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Информация о состоянии кэша
        """
        cache_age = time.time() - self._cache_timestamp if self._cache_timestamp else 0
        
        return {
            'markets_cached': len(self._markets_cache),
            'currency_pairs_cached': len(self._currency_pairs_cache),
            'cache_age_seconds': cache_age,
            'cache_fresh': self._is_cache_fresh(),
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'last_update': self.stats['last_update']
        }

    # ===== STATISTICS AND MONITORING =====

    def get_service_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики сервиса
        """
        return {
            'stats': self.stats.copy(),
            'cache_info': self.get_cache_info(),
            'settings': {
                'auto_update_enabled': self.auto_update_enabled,
                'update_interval_seconds': self.update_interval_seconds,
                'cache_ttl_seconds': self.cache_ttl_seconds
            },
            'auto_update_running': self._update_task and not self._update_task.done() if self._update_task else False
        }

    def reset_statistics(self):
        """
        Сброс статистики
        """
        self.stats = {
            'markets_loaded': 0,
            'currency_pairs_created': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'update_operations': 0,
            'last_update': None
        }
        logger.info("Market service statistics reset")

    # ===== CONFIGURATION =====

    def configure_service(
        self,
        auto_update_enabled: Optional[bool] = None,
        update_interval_seconds: Optional[int] = None,
        cache_ttl_seconds: Optional[int] = None
    ):
        """
        Настройка сервиса
        """
        if auto_update_enabled is not None:
            self.auto_update_enabled = auto_update_enabled
            
        if update_interval_seconds is not None:
            self.update_interval_seconds = update_interval_seconds
            
        if cache_ttl_seconds is not None:
            self.cache_ttl_seconds = cache_ttl_seconds

        logger.info(f"Market service configured: auto_update={self.auto_update_enabled}")

    # ===== CLEANUP =====

    async def close(self):
        """
        Закрытие сервиса и освобождение ресурсов
        """
        await self.stop_auto_update()
        self.clear_currency_pairs_cache()
        self._markets_cache.clear()
        logger.info("CCXT Market Service closed")

    def __repr__(self):
        return (f"CCXTMarketService("
                f"exchange={self.exchange_connector.exchange_name}, "
                f"markets={len(self._markets_cache)}, "
                f"pairs={len(self._currency_pairs_cache)}, "
                f"auto_update={'ON' if self.auto_update_enabled else 'OFF'})")


# ===== FACTORY FUNCTION =====

def create_ccxt_market_service(
    exchange_connector: CCXTExchangeConnector,
    **kwargs
) -> CCXTMarketService:
    """
    Factory function для создания CCXT Market Service
    """
    return CCXTMarketService(
        exchange_connector=exchange_connector,
        **kwargs
    )