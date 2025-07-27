# domain/entities/ccxt_currency_pair.py
import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class CCXTMarketInfo:
    """
    🚀 CCXT Market Information Structure
    
    Содержит полную информацию о торговой паре в формате CCXT market structure
    """
    # CCXT основные поля
    id: str                                    # биржевой идентификатор (BTCUSDT)
    symbol: str                               # стандартизированный символ (BTC/USDT)
    base: str                                 # базовая валюта (BTC)
    quote: str                                # котируемая валюта (USDT)
    base_id: Optional[str] = None             # ID базовой валюты на бирже
    quote_id: Optional[str] = None            # ID котируемой валюты на бирже
    active: bool = True                       # активность торговой пары
    
    # CCXT типы рынков
    type: str = 'spot'                        # тип рынка
    spot: bool = True                         # доступность спот торговли
    margin: bool = False                      # доступность маржинальной торговли
    future: bool = False                      # доступность фьючерсной торговли
    swap: bool = False                        # доступность своп торговли
    option: bool = False                      # доступность опционной торговли
    contract: bool = False                    # контрактная торговля
    linear: Optional[bool] = None             # линейные контракты
    inverse: Optional[bool] = None            # обратные контракты
    
    # CCXT точность (precision)
    precision: Dict[str, Any] = field(default_factory=lambda: {
        'amount': 8,
        'price': 2,
        'cost': 8
    })
    
    # CCXT лимиты (limits)
    limits: Dict[str, Any] = field(default_factory=lambda: {
        'amount': {'min': 0.00001, 'max': None},
        'price': {'min': 0.01, 'max': None},
        'cost': {'min': 10, 'max': None},
        'leverage': {'min': None, 'max': None}
    })
    
    # CCXT комиссии (fees)
    maker: float = 0.001                      # комиссия мейкера
    taker: float = 0.001                      # комиссия тейкера
    
    # CCXT дополнительная информация
    info: Dict[str, Any] = field(default_factory=dict)  # полный ответ от биржи
    
    # AutoTrade дополнительные поля
    last_updated: Optional[int] = None        # время последнего обновления
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = int(time.time() * 1000)


class CCXTCurrencyPair:
    """
    🚀 CCXT COMPLIANT Currency Pair Entity
    
    Полностью совместимая с CCXT сущность торговой пары.
    Интегрируется с CCXT markets и поддерживает все стандартные поля CCXT.
    
    Основные возможности:
    - Загрузка данных из CCXT markets
    - Валидация торговых параметров
    - Расчет торговых размеров с учетом precision
    - Проверка лимитов ордеров
    - Кэширование market data
    """

    def __init__(
        self,
        symbol: str,
        base_currency: Optional[str] = None,
        quote_currency: Optional[str] = None,
        # AutoTrade торговые параметры
        order_life_time: int = 60,              # время жизни ордера в минутах
        deal_quota: float = 100.0,              # размер сделки в quote валюте
        profit_markup: float = 0.015,           # желаемый профит (1.5%)
        deal_count: int = 1,                    # максимальное количество открытых сделок
        # Дополнительные настройки
        enable_auto_update: bool = True,        # автообновление данных с биржи
        cache_ttl_seconds: int = 300           # TTL кэша market data (5 минут)
    ):
        # Парсинг символа
        if '/' in symbol:
            self.symbol = symbol
            if not base_currency or not quote_currency:
                parts = symbol.split('/')
                self.base_currency = base_currency or parts[0]
                self.quote_currency = quote_currency or parts[1]
            else:
                self.base_currency = base_currency
                self.quote_currency = quote_currency
        else:
            # Попытка парсинга без разделителя (BTCUSDT -> BTC/USDT)
            self.base_currency = base_currency
            self.quote_currency = quote_currency
            if base_currency and quote_currency:
                self.symbol = f"{base_currency}/{quote_currency}"
            else:
                # Попытка автоматического парсинга популярных пар
                parsed = self._parse_symbol_without_separator(symbol)
                if parsed:
                    self.base_currency, self.quote_currency = parsed
                    self.symbol = f"{self.base_currency}/{self.quote_currency}"
                else:
                    raise ValueError(f"Cannot parse symbol: {symbol}")

        # AutoTrade параметры
        self.order_life_time = order_life_time
        self.deal_quota = deal_quota
        self.profit_markup = profit_markup
        self.deal_count = deal_count
        
        # Настройки
        self.enable_auto_update = enable_auto_update
        self.cache_ttl_seconds = cache_ttl_seconds
        
        # CCXT market информация
        self.market_info: Optional[CCXTMarketInfo] = None
        self._market_cache_time: float = 0
        
        # Статистика
        self.stats = {
            'market_updates': 0,
            'validation_checks': 0,
            'calculation_operations': 0,
            'last_activity': int(time.time() * 1000)
        }

    # ===== CCXT INTEGRATION METHODS =====

    def update_from_ccxt_market(self, ccxt_market: Dict[str, Any]) -> bool:
        """
        Обновляет торговую пару данными из CCXT market structure
        """
        try:
            # Валидируем CCXT market structure
            if not self._validate_ccxt_market(ccxt_market):
                logger.error(f"Invalid CCXT market structure for {self.symbol}")
                return False

            # Создаем CCXTMarketInfo из CCXT данных
            self.market_info = CCXTMarketInfo(
                id=ccxt_market.get('id', ''),
                symbol=ccxt_market.get('symbol', self.symbol),
                base=ccxt_market.get('base', self.base_currency),
                quote=ccxt_market.get('quote', self.quote_currency),
                base_id=ccxt_market.get('baseId'),
                quote_id=ccxt_market.get('quoteId'),
                active=ccxt_market.get('active', True),
                type=ccxt_market.get('type', 'spot'),
                spot=ccxt_market.get('spot', True),
                margin=ccxt_market.get('margin', False),
                future=ccxt_market.get('future', False),
                swap=ccxt_market.get('swap', False),
                option=ccxt_market.get('option', False),
                contract=ccxt_market.get('contract', False),
                linear=ccxt_market.get('linear'),
                inverse=ccxt_market.get('inverse'),
                precision=ccxt_market.get('precision', {}),
                limits=ccxt_market.get('limits', {}),
                maker=ccxt_market.get('maker', 0.001),
                taker=ccxt_market.get('taker', 0.001),
                info=ccxt_market.get('info', {}),
                last_updated=int(time.time() * 1000)
            )

            # Обновляем кэш
            self._market_cache_time = time.time()
            
            # Обновляем статистику
            self.stats['market_updates'] += 1
            self.stats['last_activity'] = int(time.time() * 1000)

            logger.debug(f"✅ Updated {self.symbol} with CCXT market data")
            logger.debug(f"   Precision: {self.market_info.precision}")
            logger.debug(f"   Limits: {self.market_info.limits}")
            logger.debug(f"   Fees: maker={self.market_info.maker}, taker={self.market_info.taker}")

            return True

        except Exception as e:
            logger.error(f"Failed to update {self.symbol} with CCXT market data: {e}")
            return False

    def is_market_data_fresh(self) -> bool:
        """
        Проверяет актуальность market data
        """
        if not self.market_info:
            return False
        
        age_seconds = time.time() - self._market_cache_time
        return age_seconds < self.cache_ttl_seconds

    def get_ccxt_market_dict(self) -> Optional[Dict[str, Any]]:
        """
        Возвращает market info в формате CCXT market structure
        """
        if not self.market_info:
            return None

        return {
            'id': self.market_info.id,
            'symbol': self.market_info.symbol,
            'base': self.market_info.base,
            'quote': self.market_info.quote,
            'baseId': self.market_info.base_id,
            'quoteId': self.market_info.quote_id,
            'active': self.market_info.active,
            'type': self.market_info.type,
            'spot': self.market_info.spot,
            'margin': self.market_info.margin,
            'future': self.market_info.future,
            'swap': self.market_info.swap,
            'option': self.market_info.option,
            'contract': self.market_info.contract,
            'linear': self.market_info.linear,
            'inverse': self.market_info.inverse,
            'precision': self.market_info.precision,
            'limits': self.market_info.limits,
            'maker': self.market_info.maker,
            'taker': self.market_info.taker,
            'info': self.market_info.info
        }

    # ===== TRADING CALCULATIONS =====

    def calculate_order_amount_precision(self, amount: float) -> float:
        """
        Рассчитывает точное количество с учетом precision amount
        """
        if not self.market_info or 'amount' not in self.market_info.precision:
            return amount

        precision = self.market_info.precision['amount']
        
        if isinstance(precision, int):
            # Количество знаков после запятой
            return round(amount, precision)
        elif isinstance(precision, float):
            # Шаг округления
            return round(amount / precision) * precision
        else:
            return amount

    def calculate_order_price_precision(self, price: float) -> float:
        """
        Рассчитывает точную цену с учетом precision price
        """
        if not self.market_info or 'price' not in self.market_info.precision:
            return price

        precision = self.market_info.precision['price']
        
        if isinstance(precision, int):
            # Количество знаков после запятой
            return round(price, precision)
        elif isinstance(precision, float):
            # Шаг округления
            return round(price / precision) * precision
        else:
            return price

    def calculate_optimal_buy_amount(self, price: float) -> float:
        """
        Рассчитывает оптимальное количество для покупки на основе deal_quota
        """
        try:
            # Базовый расчет количества
            raw_amount = self.deal_quota / price
            
            # Применяем precision
            precise_amount = self.calculate_order_amount_precision(raw_amount)
            
            # Проверяем минимальные лимиты
            if self.market_info and 'amount' in self.market_info.limits:
                min_amount = self.market_info.limits['amount'].get('min', 0)
                if precise_amount < min_amount:
                    logger.warning(f"Calculated amount {precise_amount} below minimum {min_amount}")
                    precise_amount = min_amount
            
            self.stats['calculation_operations'] += 1
            return precise_amount

        except Exception as e:
            logger.error(f"Failed to calculate optimal buy amount: {e}")
            return 0.0

    def calculate_sell_price_with_profit(self, buy_price: float) -> float:
        """
        Рассчитывает цену продажи с учетом желаемого профита и комиссий
        """
        try:
            # Учитываем комиссии при расчете профита
            maker_fee = self.market_info.maker if self.market_info else 0.001
            taker_fee = self.market_info.taker if self.market_info else 0.001
            
            # Общие комиссии (покупка + продажа)
            total_fee_rate = taker_fee + maker_fee
            
            # Цена продажи = цена покупки * (1 + профит + комиссии)
            sell_price = buy_price * (1 + self.profit_markup + total_fee_rate)
            
            # Применяем precision
            precise_sell_price = self.calculate_order_price_precision(sell_price)
            
            self.stats['calculation_operations'] += 1
            return precise_sell_price

        except Exception as e:
            logger.error(f"Failed to calculate sell price: {e}")
            return buy_price * 1.02  # Fallback 2%

    # ===== VALIDATION METHODS =====

    def validate_order_amount(self, amount: float) -> tuple[bool, str]:
        """
        Валидирует количество ордера согласно CCXT limits
        """
        self.stats['validation_checks'] += 1
        
        if not self.market_info:
            return False, "Market info not available"

        try:
            limits = self.market_info.limits.get('amount', {})
            
            # Проверка минимального количества
            min_amount = limits.get('min')
            if min_amount is not None and amount < min_amount:
                return False, f"Amount {amount} below minimum {min_amount}"
            
            # Проверка максимального количества
            max_amount = limits.get('max')
            if max_amount is not None and amount > max_amount:
                return False, f"Amount {amount} above maximum {max_amount}"
            
            return True, "Valid"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_order_price(self, price: float) -> tuple[bool, str]:
        """
        Валидирует цену ордера согласно CCXT limits
        """
        self.stats['validation_checks'] += 1
        
        if not self.market_info:
            return False, "Market info not available"

        try:
            limits = self.market_info.limits.get('price', {})
            
            # Проверка минимальной цены
            min_price = limits.get('min')
            if min_price is not None and price < min_price:
                return False, f"Price {price} below minimum {min_price}"
            
            # Проверка максимальной цены
            max_price = limits.get('max')
            if max_price is not None and price > max_price:
                return False, f"Price {price} above maximum {max_price}"
            
            return True, "Valid"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_order_cost(self, amount: float, price: float) -> tuple[bool, str]:
        """
        Валидирует общую стоимость ордера согласно CCXT limits
        """
        self.stats['validation_checks'] += 1
        
        if not self.market_info:
            return False, "Market info not available"

        try:
            cost = amount * price
            limits = self.market_info.limits.get('cost', {})
            
            # Проверка минимальной стоимости
            min_cost = limits.get('min')
            if min_cost is not None and cost < min_cost:
                return False, f"Order cost {cost} below minimum {min_cost}"
            
            # Проверка максимальной стоимости
            max_cost = limits.get('max')
            if max_cost is not None and cost > max_cost:
                return False, f"Order cost {cost} above maximum {max_cost}"
            
            return True, "Valid"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_trading_pair(self) -> tuple[bool, List[str]]:
        """
        Полная валидация торговой пары
        """
        errors = []

        if not self.market_info:
            errors.append("Market info not loaded")
            return False, errors

        # Проверка активности
        if not self.market_info.active:
            errors.append("Trading pair is not active")

        # Проверка поддержки спот торговли
        if not self.market_info.spot:
            errors.append("Spot trading not supported")

        # Проверка базовых параметров
        if not self.base_currency or not self.quote_currency:
            errors.append("Base or quote currency not defined")

        # Проверка наличия необходимых precision данных
        if not self.market_info.precision:
            errors.append("Precision data missing")

        # Проверка наличия лимитов
        if not self.market_info.limits:
            errors.append("Limits data missing")

        return len(errors) == 0, errors

    # ===== HELPER METHODS =====

    def _parse_symbol_without_separator(self, symbol: str) -> Optional[tuple[str, str]]:
        """
        Парсинг символа без разделителя (BTCUSDT -> (BTC, USDT))
        """
        # Популярные quote валюты в порядке приоритета
        quote_currencies = ['USDT', 'USDC', 'BUSD', 'BTC', 'ETH', 'BNB', 'USD', 'EUR']
        
        for quote in quote_currencies:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                if len(base) >= 2:  # Минимальная длина базовой валюты
                    return base, quote
        
        return None

    def _validate_ccxt_market(self, market_data: Dict[str, Any]) -> bool:
        """
        Валидация CCXT market structure
        """
        required_fields = ['symbol', 'base', 'quote', 'active']
        
        for field in required_fields:
            if field not in market_data:
                logger.error(f"Missing required field in CCXT market: {field}")
                return False
        
        return True

    # ===== INFORMATION METHODS =====

    def get_trading_info(self) -> Dict[str, Any]:
        """
        Получение полной торговой информации
        """
        info = {
            'symbol': self.symbol,
            'base_currency': self.base_currency,
            'quote_currency': self.quote_currency,
            'autotrade_params': {
                'order_life_time': self.order_life_time,
                'deal_quota': self.deal_quota,
                'profit_markup': self.profit_markup,
                'deal_count': self.deal_count
            },
            'market_data_available': self.market_info is not None,
            'market_data_fresh': self.is_market_data_fresh(),
            'stats': self.stats.copy()
        }

        if self.market_info:
            info['ccxt_market_info'] = {
                'id': self.market_info.id,
                'active': self.market_info.active,
                'type': self.market_info.type,
                'precision': self.market_info.precision,
                'limits': self.market_info.limits,
                'maker_fee': self.market_info.maker,
                'taker_fee': self.market_info.taker,
                'last_updated': self.market_info.last_updated
            }

        return info

    def get_fees_info(self) -> Dict[str, float]:
        """
        Получение информации о комиссиях
        """
        if self.market_info:
            return {
                'maker': self.market_info.maker,
                'taker': self.market_info.taker,
                'total_round_trip': self.market_info.maker + self.market_info.taker
            }
        else:
            return {
                'maker': 0.001,
                'taker': 0.001,
                'total_round_trip': 0.002
            }

    def update_autotrade_params(
        self,
        order_life_time: Optional[int] = None,
        deal_quota: Optional[float] = None,
        profit_markup: Optional[float] = None,
        deal_count: Optional[int] = None
    ):
        """
        Обновление параметров торговли AutoTrade
        """
        if order_life_time is not None:
            self.order_life_time = order_life_time
        if deal_quota is not None:
            self.deal_quota = deal_quota
        if profit_markup is not None:
            self.profit_markup = profit_markup
        if deal_count is not None:
            self.deal_count = deal_count

        self.stats['last_activity'] = int(time.time() * 1000)
        logger.info(f"Updated AutoTrade params for {self.symbol}")

    def reset_statistics(self):
        """
        Сброс статистики
        """
        self.stats = {
            'market_updates': 0,
            'validation_checks': 0,
            'calculation_operations': 0,
            'last_activity': int(time.time() * 1000)
        }

    # ===== LEGACY COMPATIBILITY =====

    @property
    def precision(self) -> Dict[str, Any]:
        """LEGACY: Возвращает precision для обратной совместимости"""
        return self.market_info.precision if self.market_info else {}

    @property
    def limits(self) -> Dict[str, Any]:
        """LEGACY: Возвращает limits для обратной совместимости"""
        return self.market_info.limits if self.market_info else {}

    @property
    def taker_fee(self) -> float:
        """LEGACY: Возвращает taker fee для обратной совместимости"""
        return self.market_info.taker if self.market_info else 0.001

    @property
    def maker_fee(self) -> float:
        """LEGACY: Возвращает maker fee для обратной совместимости"""
        return self.market_info.maker if self.market_info else 0.001

    def update_exchange_info(self, market_data: Dict[str, Any]):
        """LEGACY: Для обратной совместимости"""
        self.update_from_ccxt_market(market_data)

    # ===== STRING REPRESENTATIONS =====

    def __repr__(self):
        return (f"CCXTCurrencyPair(symbol={self.symbol}, "
                f"quota={self.deal_quota}, profit={self.profit_markup*100:.1f}%, "
                f"market_data={'✓' if self.market_info else '✗'})")

    def __str__(self):
        return f"{self.symbol} ({self.base_currency}/{self.quote_currency})"


# ===== FACTORY FUNCTIONS =====

def create_ccxt_currency_pair_from_symbol(symbol: str, **kwargs) -> CCXTCurrencyPair:
    """
    Factory function для создания CCXTCurrencyPair из символа
    """
    return CCXTCurrencyPair(symbol=symbol, **kwargs)


def create_ccxt_currency_pair_from_market(ccxt_market: Dict[str, Any], **kwargs) -> CCXTCurrencyPair:
    """
    Factory function для создания CCXTCurrencyPair из CCXT market data
    """
    pair = CCXTCurrencyPair(
        symbol=ccxt_market['symbol'],
        base_currency=ccxt_market['base'],
        quote_currency=ccxt_market['quote'],
        **kwargs
    )
    
    pair.update_from_ccxt_market(ccxt_market)
    return pair