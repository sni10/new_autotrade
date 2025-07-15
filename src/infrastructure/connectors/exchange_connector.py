# src/infrastructure/connectors/exchange_connector.py - УНИВЕРСАЛЬНАЯ ВЕРСИЯ
import asyncio
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path
import ccxt.pro as ccxtpro
import ccxt
from config.config_loader import load_config
from domain.entities.order import ExchangeInfo

logger = logging.getLogger(__name__)

class CcxtExchangeConnector:
    """
    УНИВЕРСАЛЬНЫЙ коннектор для биржи, использующий ccxt.pro.
    Поддерживает как RESTful-запросы (создание ордеров, баланс),
    так и WebSocket-стримы (watch_ticker, watch_order_book).
    """

    def __init__(self, exchange_name="binance", use_sandbox=False):
        self.exchange_name = exchange_name
        self.use_sandbox = use_sandbox
        self.config = None
        self.client = None  # Это будет ccxt.pro клиент

        self.exchange_info_cache = {}
        self._load_config()
        self._init_exchange_client()

    def _load_config(self):
        """Загружает конфигурацию API ключей"""
        try:
            full_config = load_config()
            env_key = 'sandbox' if self.use_sandbox else 'production'
            self.config = full_config.get('binance', {}).get(env_key, {})

            private_key_path = self.config.get('privateKeyPath')
            if private_key_path and Path(private_key_path).exists():
                with open(private_key_path, 'r') as f:
                    private_key = f.read()
                self.config['secret'] = private_key
                self.config['privateKey'] = private_key

            logger.info(f"✅ Config loaded for {self.exchange_name} ({'sandbox' if self.use_sandbox else 'production'})")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            raise

    def _init_exchange_client(self):
        """Инициализирует ccxt.pro клиент"""
        try:
            exchange_class = getattr(ccxtpro, self.exchange_name)
            settings = {
                'apiKey': self.config.get('apiKey'),
                'secret': self.config.get('secret'),
                'enableRateLimit': True,
                'newUpdates': True,
                'options': {'defaultType': 'spot'}
            }
            self.client = exchange_class(settings)

            if self.use_sandbox:
                self.client.set_sandbox_mode(True)
                logger.info("🧪 Sandbox mode enabled")

            logger.info(f"✅ CCXT.pro client initialized for {self.exchange_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ccxt.pro client: {e}")
            raise

    def _normalize_symbol(self, symbol: str) -> str:
        """Преобразует 'ETHUSDT' -> 'ETH/USDT'"""
        if not symbol: return None
        if '/' in symbol: return symbol
        if symbol.endswith('USDT'): return f"{symbol[:-4]}/USDT"
        if symbol.endswith('USDC'): return f"{symbol[:-4]}/USDC"
        return symbol

    async def watch_order_book(self, symbol: str):
        return await self.client.watch_order_book(self._normalize_symbol(symbol))

    async def fetch_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Получение стакана заявок (разовый запрос)"""
        normalized_symbol = self._normalize_symbol(symbol)
        return await self.client.fetch_order_book(normalized_symbol, limit)

    async def watch_ticker(self, symbol: str):
        return await self.client.watch_ticker(self._normalize_symbol(symbol))

    async def watch_trades(self, symbol: str):
        return await self.client.watch_trades(self._normalize_symbol(symbol))

    async def watch_ohlcv(self, symbol: str, timeframe='1m'):
        return await self.client.watch_ohlcv(self._normalize_symbol(symbol), timeframe)

    async def load_markets(self, reload=False):
        return await self.client.load_markets(reload)

    async def create_order(self, symbol: str, side: str, order_type: str, amount: float, price: float = None, params: Dict[str, Any] = None):
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"📤 Creating {side.upper()} {order_type} order: {amount} {normalized_symbol} @ {price}")
            result = await self.client.create_order(normalized_symbol, order_type, side, amount, price, params or {})
            logger.info(f"✅ Order created successfully: {result.get('id', 'N/A')}")
            return result
        except ccxt.InsufficientFunds as e:
            logger.error(f"💸 Insufficient funds: {e}")
            raise
        except ccxt.InvalidOrder as e:
            logger.error(f"❌ Invalid order: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error creating order: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"❌ Cancelling order {order_id} for {normalized_symbol}")
            result = await self.client.cancel_order(order_id, normalized_symbol)
            logger.info(f"✅ Order cancelled successfully: {order_id}")
            return result
        except ccxt.OrderNotFound:
            logger.warning(f"⚠️ Order not found on exchange: {order_id}")
            raise  # Пробрасываем исключение дальше
        except Exception as e:
            logger.error(f"❌ Error cancelling order {order_id}: {e}")
            raise

    async def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        result = await self.client.fetch_order(order_id, self._normalize_symbol(symbol))
        return result

    async def fetch_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        return await self.client.fetch_open_orders(self._normalize_symbol(symbol))

    async def fetch_balance(self) -> Dict[str, Any]:
        return await self.client.fetch_balance()

    async def get_available_balance(self, currency: str) -> float:
        balance = await self.fetch_balance()
        return balance.get(currency, {}).get('free', 0.0)

    async def get_balance(self, currency: str) -> float:
        """Для совместимости со старым кодом"""
        return await self.get_available_balance(currency)

    async def check_sufficient_balance(self, symbol: str, side: str, amount: float, price: float = None) -> Tuple[bool, str, float]:
        """Проверка достаточности баланса для ордера"""
        try:
            base_currency, quote_currency = self._normalize_symbol(symbol).split('/')

            if side.lower() == 'buy':
                required_amount = amount * (price or 0)
                available = await self.get_available_balance(quote_currency)
                return available >= required_amount, quote_currency, available
            else:
                available = await self.get_available_balance(base_currency)
                return available >= amount, base_currency, available

        except Exception as e:
            logger.error(f"❌ Error checking balance: {e}")
            return False, "UNKNOWN", 0.0

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        return await self.client.fetch_ticker(self._normalize_symbol(symbol))

    async def get_symbol_info(self, symbol: str) -> ExchangeInfo:
        normalized_symbol = self._normalize_symbol(symbol)
        if normalized_symbol in self.exchange_info_cache:
            return self.exchange_info_cache[normalized_symbol]

        markets = await self.load_markets()
        market_info = markets.get(normalized_symbol)
        if not market_info:
            raise ValueError(f"Symbol {normalized_symbol} not found in markets")

        limits = market_info.get('limits', {})
        precision = market_info.get('precision', {})
        exchange_info = ExchangeInfo(
            symbol=normalized_symbol,
            min_qty=limits.get('amount', {}).get('min'),
            max_qty=limits.get('amount', {}).get('max'),
            step_size=precision.get('amount'),
            min_price=limits.get('price', {}).get('min'),
            max_price=limits.get('price', {}).get('max'),
            tick_size=precision.get('price'),
            min_notional=limits.get('cost', {}).get('min'),
            fees={'maker': market_info.get('maker', 0.001), 'taker': market_info.get('taker', 0.001)},
            precision=precision # ❗️ ДОБАВЛЕНО: сохраняем весь словарь
        )
        self.exchange_info_cache[normalized_symbol] = exchange_info
        return exchange_info

    async def create_market_sell_order(self, symbol: str, amount: float):
        """🚨 Создание маркет-ордера на продажу для стоп-лосса"""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"🚨 Creating MARKET SELL order: {amount} {normalized_symbol}")
            
            # Создаем маркет-ордер на продажу
            result = await self.client.create_market_sell_order(normalized_symbol, amount)
            
            if result:
                logger.info(f"✅ Market SELL order created successfully: {result.get('id', 'N/A')}")
                # Возвращаем результат в стандартном формате
                from domain.entities.order import OrderExecutionResult
                return OrderExecutionResult(
                    success=True,
                    exchange_order_id=result.get('id'),
                    filled_amount=result.get('filled', amount),
                    average_price=result.get('average'),
                    fees=result.get('fee', {}).get('cost', 0.0),
                    timestamp=result.get('timestamp')
                )
            else:
                logger.error("❌ Failed to create market sell order - no result")
                return None
                
        except ccxt.InsufficientFunds as e:
            logger.error(f"💸 Insufficient funds for market sell: {e}")
            return None
        except ccxt.InvalidOrder as e:
            logger.error(f"❌ Invalid market sell order: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error creating market sell order: {e}")
            return None

    async def test_connection(self) -> bool:
        try:
            await self.fetch_balance()
            logger.info(f"✅ Connection test successful for {self.exchange_name} ({'sandbox' if self.use_sandbox else 'production'})")
            return True
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    async def close(self):
        logger.info(f"🔌 Closing connection for {self.exchange_name} ({'sandbox' if self.use_sandbox else 'production'})")
        await self.client.close()