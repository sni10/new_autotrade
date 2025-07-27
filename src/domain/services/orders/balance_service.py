import logging
from typing import Dict, List, Optional, Tuple, Any

from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from src.domain.entities.order import Order
from src.domain.repositories.i_statistics_repository import IStatisticsRepository
from src.domain.entities.statistics import Statistics, StatisticCategory, StatisticType

logger = logging.getLogger(__name__)


class BalanceService:
    """
    Сервис для проверки и управления балансами.
    Соблюдает принцип единственной ответственности (SRP).
    Отвечает ТОЛЬКО за проверку балансов перед размещением ордеров.
    """
    
    def __init__(
        self,
        exchange_connector: CcxtExchangeConnector,
        statistics_repo: Optional[IStatisticsRepository] = None,
        initial_balance: Optional[Dict[str, Dict[str, float]]] = None
    ):
        self.exchange_connector = exchange_connector
        self.statistics_repo = statistics_repo
        
        # Кэш балансов для избежания частых запросов к API
        self._balance_cache: Dict[str, Dict[str, float]] = initial_balance or {}
        self._cache_timestamp = self._get_current_timestamp() if initial_balance else 0
        self._cache_ttl = 30  # секунд
        
        self._stats = {
            'balance_checks': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'insufficient_balance_count': 0,
            'errors': 0
        }
    
    async def check_sufficient_balance(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float
    ) -> Tuple[bool, str, float]:
        """
        Проверка достаточности баланса для размещения ордера
        
        Args:
            symbol: Торговая пара (например, BTCUSDT)
            side: Сторона ордера (BUY/SELL)
            amount: Количество
            price: Цена
            
        Returns:
            Tuple[has_sufficient_balance, currency, available_balance]
        """
        try:
            self._stats['balance_checks'] += 1
            
            # Определяем нужную валюту
            base_currency, quote_currency = self._parse_symbol(symbol)
            
            if side == Order.SIDE_BUY:
                # Для покупки нужна квотируемая валюта (например, USDT для BTCUSDT)
                required_currency = quote_currency
                required_amount = amount * price
            else:
                # Для продажи нужна базовая валюта (например, BTC для BTCUSDT)
                required_currency = base_currency
                required_amount = amount
            
            # Получаем баланс
            balance_info = await self._get_balance(required_currency)
            available_balance = balance_info.get('free', 0.0)
            if not isinstance(available_balance, (float, int)):
                raise TypeError(f"available_balance is not a float/int, it is {type(available_balance)}. balance_info was: {balance_info}")
            if not isinstance(available_balance, (float, int)):
                raise TypeError(f"available_balance is not a float/int, it is {type(available_balance)}. balance_info was: {balance_info}")
            
            # Проверяем достаточность
            is_sufficient = available_balance >= required_amount
            
            if not is_sufficient:
                self._stats['insufficient_balance_count'] += 1
                logger.warning(
                    f"💰 Insufficient balance for {side} {amount} {symbol} @ {price}: "
                    f"need {required_amount:.6f} {required_currency}, "
                    f"have {available_balance:.6f}"
                )
            
            # Обновляем статистику
            await self._update_balance_statistics(is_sufficient, symbol, side, required_currency)
            
            return is_sufficient, required_currency, available_balance
            
        except Exception as e:
            logger.error(f"❌ Error checking balance for {side} {symbol}: {e}")
            self._stats['errors'] += 1
            return False, "ERROR", 0.0
    
    async def get_account_balance(self, force_refresh: bool = False) -> Dict[str, Dict[str, float]]:
        """
        Получение полного баланса аккаунта
        
        Args:
            force_refresh: Принудительное обновление кэша
            
        Returns:
            Словарь балансов по валютам
        """
        try:
            # Проверяем кэш
            if not force_refresh and self._is_cache_valid():
                self._stats['cache_hits'] += 1
                return self._balance_cache.copy()
            
            # Запрашиваем баланс с биржи
            self._stats['cache_misses'] += 1
            balance = await self.exchange_connector.fetch_balance()
            
            # Обновляем кэш
            self._balance_cache = balance.copy()
            self._cache_timestamp = self._get_current_timestamp()
            
            logger.debug(f"💰 Retrieved account balance: {len(balance)} currencies")
            
            # Обновляем статистику
            await self._update_balance_refresh_statistics(len(balance))
            
            return balance
            
        except Exception as e:
            logger.error(f"❌ Error getting account balance: {e}")
            self._stats['errors'] += 1
            return {}
    
    async def get_currency_balance(self, currency: str, force_refresh: bool = False) -> Dict[str, float]:
        """
        Получение баланса конкретной валюты
        
        Args:
            currency: Код валюты (например, BTC, USDT)
            force_refresh: Принудительное обновление кэша
            
        Returns:
            Словарь с балансом валюты {free, used, total}
        """
        try:
            full_balance = await self.get_account_balance(force_refresh)
            
            currency_balance = full_balance.get(currency, {
                'free': 0.0,
                'used': 0.0,
                'total': 0.0
            })
            
            return currency_balance
            
        except Exception as e:
            logger.error(f"❌ Error getting balance for {currency}: {e}")
            return {'free': 0.0, 'used': 0.0, 'total': 0.0}
    
    async def get_required_balance_for_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float
    ) -> Tuple[str, float]:
        """
        Рассчитать требуемый баланс для ордера
        
        Args:
            symbol: Торговая пара
            side: Сторона ордера
            amount: Количество
            price: Цена
            
        Returns:
            Tuple[currency, required_amount]
        """
        try:
            base_currency, quote_currency = self._parse_symbol(symbol)
            
            if side == Order.SIDE_BUY:
                return quote_currency, amount * price
            else:
                return base_currency, amount
                
        except Exception as e:
            logger.error(f"❌ Error calculating required balance: {e}")
            return "ERROR", 0.0
    
    async def check_multiple_orders_balance(
        self,
        orders: List[Tuple[str, str, float, float]]  # (symbol, side, amount, price)
    ) -> Dict[str, Tuple[bool, float, float]]:
        """
        Проверка баланса для нескольких ордеров
        
        Args:
            orders: Список ордеров для проверки
            
        Returns:
            Словарь {currency: (is_sufficient, required_total, available)}
        """
        try:
            # Группируем требования по валютам
            currency_requirements: Dict[str, float] = {}
            
            for symbol, side, amount, price in orders:
                currency, required_amount = await self.get_required_balance_for_order(
                    symbol, side, amount, price
                )
                
                if currency in currency_requirements:
                    currency_requirements[currency] += required_amount
                else:
                    currency_requirements[currency] = required_amount
            
            # Проверяем баланс для каждой валюты
            result = {}
            full_balance = await self.get_account_balance()
            
            for currency, required_total in currency_requirements.items():
                available = full_balance.get(currency, {}).get('free', 0.0)
                is_sufficient = available >= required_total
                result[currency] = (is_sufficient, required_total, available)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking multiple orders balance: {e}")
            return {}
    
    async def _get_balance(self, currency: str) -> Dict[str, float]:
        """Получение баланса конкретной валюты с использованием кэша"""
        # Проверяем кэш
        if not self._is_cache_valid():
            # Обновляем весь баланс, если кэш невалиден
            await self.get_account_balance(force_refresh=True)
        else:
            self._stats['cache_hits'] += 1

        # Теперь, когда кэш актуален, извлекаем данные для конкретной валюты
        free = self._balance_cache.get('free', {}).get(currency, 0.0)
        used = self._balance_cache.get('used', {}).get(currency, 0.0)
        total = self._balance_cache.get('total', {}).get(currency, 0.0)

        return {
            'free': free,
            'used': used,
            'total': total
        }
    
    def _parse_symbol(self, symbol: str) -> Tuple[str, str]:
        """
        Парсинг торговой пары на базовую и квотируемую валюты
        
        Args:
            symbol: Торговая пара (BTCUSDT, BTC/USDT, BTC-USDT)
            
        Returns:
            Tuple[base_currency, quote_currency]
        """
        # Обрабатываем различные форматы символов
        if '/' in symbol:
            parts = symbol.split('/')
        elif '-' in symbol:
            parts = symbol.split('-')
        else:
            # Для символов вида BTCUSDT пытаемся угадать разделение
            # Обычно последние 3-4 символа - это квотируемая валюта
            if symbol.endswith('USDT'):
                parts = [symbol[:-4], 'USDT']
            elif symbol.endswith('BTC') or symbol.endswith('ETH'):
                parts = [symbol[:-3], symbol[-3:]]
            elif symbol.endswith('USD'):
                parts = [symbol[:-3], 'USD']
            else:
                # Fallback - делим пополам
                mid = len(symbol) // 2
                parts = [symbol[:mid], symbol[mid:]]
        
        if len(parts) != 2:
            raise ValueError(f"Cannot parse symbol: {symbol}")
        
        return parts[0].upper(), parts[1].upper()
    
    def _is_cache_valid(self) -> bool:
        """Проверка валидности кэша балансов"""
        if not self._balance_cache:
            return False
        
        current_time = self._get_current_timestamp()
        return (current_time - self._cache_timestamp) < self._cache_ttl
    
    def _get_current_timestamp(self) -> int:
        """Получение текущего времени в секундах"""
        import time
        return int(time.time())
    
    def clear_cache(self) -> None:
        """Очистка кэша балансов"""
        self._balance_cache.clear()
        self._cache_timestamp = 0
        logger.debug("💰 Balance cache cleared")
    
    async def _update_balance_statistics(
        self,
        is_sufficient: bool,
        symbol: str,
        side: str,
        currency: str
    ) -> None:
        """Обновление статистики проверки балансов"""
        if not self.statistics_repo:
            return
        
        try:
            await self.statistics_repo.increment_counter(
                "balance_checks_total",
                StatisticCategory.TRADING,
                tags={
                    "symbol": symbol,
                    "side": side.lower(),
                    "currency": currency,
                    "result": "sufficient" if is_sufficient else "insufficient"
                }
            )
            
            if not is_sufficient:
                await self.statistics_repo.increment_counter(
                    "insufficient_balance_count",
                    StatisticCategory.TRADING,
                    tags={"currency": currency}
                )
                
        except Exception as e:
            logger.error(f"Error updating balance statistics: {e}")
    
    async def _update_balance_refresh_statistics(self, currencies_count: int) -> None:
        """Обновление статистики обновления балансов"""
        if not self.statistics_repo:
            return
        
        try:
            await self.statistics_repo.increment_counter(
                "balance_refresh_count",
                StatisticCategory.TRADING
            )
            
            await self.statistics_repo.update_gauge(
                "account_currencies_count",
                StatisticCategory.TRADING,
                currencies_count
            )
            
        except Exception as e:
            logger.error(f"Error updating balance refresh statistics: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики сервиса"""
        return {
            **self._stats,
            'cache_size': len(self._balance_cache),
            'cache_age_seconds': self._get_current_timestamp() - self._cache_timestamp,
            'cache_valid': self._is_cache_valid()
        }
    
    def reset_stats(self) -> None:
        """Сброс статистики"""
        self._stats = {
            'balance_checks': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'insufficient_balance_count': 0,
            'errors': 0
        }