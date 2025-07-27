# infrastructure/connectors/ccxt_exchange_connector.py
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import ccxt.pro as ccxtpro
import ccxt

from src.domain.entities.order import Order
from src.config.config_loader import load_config

logger = logging.getLogger(__name__)


class CCXTExchangeConnector:
    """
    🚀 CCXT COMPLIANT Exchange Connector
    
    Полностью совместимая с CCXT Unified API реализация коннектора к бирже.
    Все методы возвращают данные в стандартном CCXT формате.
    Поддерживает как WebSocket streams, так и REST API.
    """

    def __init__(self, exchange_name: str = "binance", use_sandbox: bool = False):
        self.exchange_name = exchange_name.lower()
        self.use_sandbox = use_sandbox
        self.config = None
        self.rest_client: Optional[ccxt.Exchange] = None      # REST API клиент
        self.stream_client: Optional[ccxtpro.Exchange] = None  # WebSocket клиент
        
        # Кэши для производительности
        self._markets_cache: Optional[Dict[str, Any]] = None
        self._markets_cache_time: float = 0
        self._markets_cache_ttl: float = 3600  # 1 час
        
        self._tickers_cache: Dict[str, Dict[str, Any]] = {}
        self._tickers_cache_ttl: float = 10  # 10 секунд
        
        # Инициализация
        self._load_config()
        self._init_clients()

    def _load_config(self) -> None:
        """Загружает конфигурацию API ключей"""
        try:
            full_config = load_config()
            env_key = 'sandbox' if self.use_sandbox else 'production'
            self.config = full_config.get(self.exchange_name, {}).get(env_key, {})

            # Загружаем приватный ключ из файла если указан
            private_key_path = self.config.get('privateKeyPath')
            if private_key_path and Path(private_key_path).exists():
                with open(private_key_path, 'r', encoding='utf-8') as f:
                    private_key = f.read().strip()
                self.config['secret'] = private_key
                self.config['privateKey'] = private_key

            logger.info(f"✅ Config loaded for {self.exchange_name} ({'sandbox' if self.use_sandbox else 'production'})")
            
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            raise

    def _init_clients(self) -> None:
        """Инициализирует CCXT клиенты (REST и WebSocket)"""
        try:
            # Базовые настройки CCXT
            base_settings = {
                'apiKey': self.config.get('apiKey'),
                'secret': self.config.get('secret'),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True
                },
                'timeout': 30000,  # 30 секунд
                'rateLimit': 50,   # 50ms между запросами
            }

            # Инициализируем REST клиент
            rest_class = getattr(ccxt, self.exchange_name)
            self.rest_client = rest_class(base_settings.copy())

            # Инициализируем WebSocket клиент
            stream_settings = base_settings.copy()
            stream_settings['newUpdates'] = True
            stream_class = getattr(ccxtpro, self.exchange_name)
            self.stream_client = stream_class(stream_settings)

            # Настраиваем sandbox mode
            if self.use_sandbox:
                self.rest_client.set_sandbox_mode(True)
                self.stream_client.set_sandbox_mode(True)
                logger.info("🧪 Sandbox mode enabled")

            logger.info(f"✅ CCXT clients initialized for {self.exchange_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize CCXT clients: {e}")
            raise

    # ===== MARKET DATA METHODS =====

    async def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """
        Загружает информацию о торговых парах (CCXT markets)
        """
        current_time = time.time()
        
        # Проверяем кэш
        if (not reload and 
            self._markets_cache and 
            (current_time - self._markets_cache_time) < self._markets_cache_ttl):
            return self._markets_cache

        try:
            markets = await self.rest_client.load_markets(reload)
            
            # Обновляем кэш
            self._markets_cache = markets
            self._markets_cache_time = current_time
            
            logger.debug(f"Loaded {len(markets)} markets from {self.exchange_name}")
            return markets
            
        except Exception as e:
            logger.error(f"Failed to load markets: {e}")
            raise

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Получает тикер для торговой пары (CCXT ticker structure)
        """
        try:
            ticker = await self.rest_client.fetch_ticker(symbol)
            
            # Кэшируем тикер
            current_time = time.time()
            self._tickers_cache[symbol] = {
                'data': ticker,
                'timestamp': current_time
            }
            
            return ticker
            
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            raise

    async def fetch_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Получает стакан заявок (CCXT order book structure)
        """
        try:
            order_book = await self.rest_client.fetch_order_book(symbol, limit)
            return order_book
            
        except Exception as e:
            logger.error(f"Failed to fetch order book for {symbol}: {e}")
            raise

    async def fetch_trades(self, symbol: str, since: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает последние сделки (CCXT trades structure)
        """
        try:
            trades = await self.rest_client.fetch_trades(symbol, since, limit)
            return trades
            
        except Exception as e:
            logger.error(f"Failed to fetch trades for {symbol}: {e}")
            raise

    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1m', since: Optional[int] = None, limit: int = 100) -> List[List]:
        """
        Получает OHLCV данные (CCXT OHLCV structure)
        """
        try:
            ohlcv = await self.rest_client.fetch_ohlcv(symbol, timeframe, since, limit)
            return ohlcv
            
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            raise

    # ===== STREAMING METHODS =====

    async def watch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        WebSocket стрим тикеров (CCXT ticker structure)
        """
        try:
            ticker = await self.stream_client.watch_ticker(symbol)
            return ticker
            
        except Exception as e:
            logger.error(f"Failed to watch ticker for {symbol}: {e}")
            raise

    async def watch_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        WebSocket стрим стакана заявок (CCXT order book structure)
        """
        try:
            order_book = await self.stream_client.watch_order_book(symbol, limit)
            return order_book
            
        except Exception as e:
            logger.error(f"Failed to watch order book for {symbol}: {e}")
            raise

    async def watch_trades(self, symbol: str) -> List[Dict[str, Any]]:
        """
        WebSocket стрим сделок (CCXT trades structure)
        """
        try:
            trades = await self.stream_client.watch_trades(symbol)
            return trades
            
        except Exception as e:
            logger.error(f"Failed to watch trades for {symbol}: {e}")
            raise

    async def watch_ohlcv(self, symbol: str, timeframe: str = '1m') -> List[List]:
        """
        WebSocket стрим OHLCV (CCXT OHLCV structure)
        """
        try:
            ohlcv = await self.stream_client.watch_ohlcv(symbol, timeframe)
            return ohlcv
            
        except Exception as e:
            logger.error(f"Failed to watch OHLCV for {symbol}: {e}")
            raise

    # ===== ORDER MANAGEMENT METHODS =====

    async def create_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Создает ордер (возвращает CCXT order structure)
        """
        try:
            logger.info(f"📤 Creating {side.upper()} {type.upper()} order: {amount} {symbol} @ {price}")
            
            # Создаем ордер через CCXT
            order_result = await self.rest_client.create_order(
                symbol=symbol,
                type=type,
                side=side,
                amount=amount,
                price=price,
                params=params or {}
            )
            
            logger.info(f"✅ Order created successfully: {order_result.get('id', 'N/A')}")
            return order_result
            
        except ccxt.InsufficientFunds as e:
            logger.error(f"💸 Insufficient funds: {e}")
            raise
        except ccxt.InvalidOrder as e:
            logger.error(f"❌ Invalid order: {e}")
            raise
        except ccxt.NetworkError as e:
            logger.error(f"🌐 Network error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error creating order: {e}")
            raise

    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Создает лимитный ордер
        """
        return await self.create_order(symbol, 'limit', side, amount, price, params)

    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Создает маркет ордер
        """
        return await self.create_order(symbol, 'market', side, amount, None, params)

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Отменяет ордер (возвращает CCXT order structure)
        """
        try:
            logger.info(f"❌ Cancelling order {order_id} for {symbol}")
            
            result = await self.rest_client.cancel_order(order_id, symbol)
            
            logger.info(f"✅ Order cancelled successfully: {order_id}")
            return result
            
        except ccxt.OrderNotFound as e:
            logger.warning(f"⚠️ Order not found on exchange: {order_id}")
            raise
        except Exception as e:
            logger.error(f"❌ Error cancelling order {order_id}: {e}")
            raise

    async def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Получает информацию об ордере (CCXT order structure)
        """
        try:
            order = await self.rest_client.fetch_order(order_id, symbol)
            return order
            
        except ccxt.OrderNotFound as e:
            logger.warning(f"⚠️ Order not found: {order_id}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch order {order_id}: {e}")
            raise

    async def fetch_orders(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получает список ордеров (CCXT orders structure)
        """
        try:
            orders = await self.rest_client.fetch_orders(symbol, since, limit)
            return orders
            
        except Exception as e:
            logger.error(f"Failed to fetch orders: {e}")
            raise

    async def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получает открытые ордера (CCXT orders structure)
        """
        try:
            orders = await self.rest_client.fetch_open_orders(symbol)
            return orders
            
        except Exception as e:
            logger.error(f"Failed to fetch open orders: {e}")
            raise

    async def fetch_closed_orders(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получает закрытые ордера (CCXT orders structure)
        """
        try:
            orders = await self.rest_client.fetch_closed_orders(symbol, since, limit)
            return orders
            
        except Exception as e:
            logger.error(f"Failed to fetch closed orders: {e}")
            raise

    # ===== BALANCE METHODS =====

    async def fetch_balance(self) -> Dict[str, Any]:
        """
        Получает баланс аккаунта (CCXT balance structure)
        """
        try:
            balance = await self.rest_client.fetch_balance()
            return balance
            
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise

    async def get_available_balance(self, currency: str) -> float:
        """
        Получает доступный баланс по валюте
        """
        try:
            balance = await self.fetch_balance()
            return balance.get(currency, {}).get('free', 0.0)
            
        except Exception as e:
            logger.error(f"Failed to get available balance for {currency}: {e}")
            return 0.0

    async def get_total_balance(self, currency: str) -> float:
        """
        Получает общий баланс по валюте
        """
        try:
            balance = await self.fetch_balance()
            return balance.get(currency, {}).get('total', 0.0)
            
        except Exception as e:
            logger.error(f"Failed to get total balance for {currency}: {e}")
            return 0.0

    # ===== TRADING HELPER METHODS =====

    async def check_sufficient_balance(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: Optional[float] = None
    ) -> Tuple[bool, str, float]:
        """
        Проверяет достаточность баланса для создания ордера
        """
        try:
            # Получаем информацию о рынке
            markets = await self.load_markets()
            market = markets.get(symbol)
            if not market:
                logger.error(f"Market {symbol} not found")
                return False, "UNKNOWN", 0.0

            base_currency = market['base']
            quote_currency = market['quote']

            if side.lower() == 'buy':
                # Для покупки нужна котируемая валюта
                if not price:
                    # Для маркет ордера получаем текущую цену
                    ticker = await self.fetch_ticker(symbol)
                    price = ticker.get('ask', ticker.get('last', 0))
                
                required_amount = amount * price
                available = await self.get_available_balance(quote_currency)
                return available >= required_amount, quote_currency, available
                
            else:
                # Для продажи нужна базовая валюта
                available = await self.get_available_balance(base_currency)
                return available >= amount, base_currency, available

        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return False, "UNKNOWN", 0.0

    async def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        Получает полную информацию о рынке (CCXT market structure)
        """
        try:
            markets = await self.load_markets()
            market = markets.get(symbol)
            if not market:
                raise ValueError(f"Symbol {symbol} not found in markets")
            
            return market
            
        except Exception as e:
            logger.error(f"Failed to get market info for {symbol}: {e}")
            raise

    async def get_trading_fees(self, symbol: str) -> Dict[str, float]:
        """
        Получает торговые комиссии для символа
        """
        try:
            market = await self.get_market_info(symbol)
            return {
                'maker': market.get('maker', 0.001),
                'taker': market.get('taker', 0.001)
            }
            
        except Exception as e:
            logger.error(f"Failed to get trading fees for {symbol}: {e}")
            return {'maker': 0.001, 'taker': 0.001}

    async def calculate_order_cost(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Рассчитывает стоимость ордера с учетом комиссий
        """
        try:
            # Получаем цену если не указана
            if not price:
                ticker = await self.fetch_ticker(symbol)
                if side.lower() == 'buy':
                    price = ticker.get('ask', ticker.get('last', 0))
                else:
                    price = ticker.get('bid', ticker.get('last', 0))

            # Базовая стоимость
            base_cost = amount * price

            # Получаем комиссии
            fees = await self.get_trading_fees(symbol)
            fee_rate = fees.get('taker', 0.001)  # Используем taker fee как более консервативную оценку
            fee_cost = base_cost * fee_rate

            return {
                'base_cost': base_cost,
                'fee_cost': fee_cost,
                'total_cost': base_cost + fee_cost,
                'fee_rate': fee_rate,
                'price': price,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate order cost: {e}")
            raise

    # ===== AUTOTRADE INTEGRATION METHODS =====

    def create_order_from_autotrade(self, order: Order) -> Dict[str, Any]:
        """
        Преобразует AutoTrade Order в CCXT параметры
        """
        # Валидируем Order
        is_valid, errors = order.validate_ccxt_compliance()
        if not is_valid:
            raise ValueError(f"Order validation failed: {'; '.join(errors)}")

        # Возвращаем CCXT-совместимые параметры
        return {
            'symbol': order.symbol,
            'type': order.type,
            'side': order.side,
            'amount': order.amount,
            'price': order.price,
            'params': {
                'timeInForce': order.timeInForce,
                'clientOrderId': order.clientOrderId
            }
        }

    async def sync_order_with_exchange(self, order: Order) -> Order:
        """
        Синхронизирует AutoTrade Order с биржей
        """
        if not order.id:
            logger.warning("Cannot sync order without exchange ID")
            return order

        try:
            # Получаем актуальную информацию с биржи
            ccxt_order = await self.fetch_order(order.id, order.symbol)
            
            # Обновляем Order данными с биржи
            order.update_from_ccxt_response(ccxt_order)
            
            logger.debug(f"Synced order {order.id} with exchange")
            return order
            
        except ccxt.OrderNotFound:
            # Ордер не найден на бирже - помечаем как rejected
            order.status = Order.STATUS_REJECTED
            order.error_message = "Order not found on exchange"
            logger.warning(f"Order {order.id} not found on exchange")
            return order
            
        except Exception as e:
            logger.error(f"Failed to sync order {order.id}: {e}")
            raise

    # ===== CONNECTION MANAGEMENT =====

    async def test_connection(self) -> bool:
        """
        Тестирует подключение к бирже
        """
        try:
            # Тестируем REST API
            await self.fetch_balance()
            
            # Тестируем WebSocket (пытаемся загрузить рынки)
            await self.load_markets()
            
            logger.info(f"✅ Connection test successful for {self.exchange_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    async def get_server_time(self) -> int:
        """
        Получает время сервера биржи (Unix timestamp в миллисекундах)
        """
        try:
            if hasattr(self.rest_client, 'fetch_time'):
                return await self.rest_client.fetch_time()
            else:
                # Fallback - используем текущее время
                return int(time.time() * 1000)
                
        except Exception as e:
            logger.warning(f"Failed to get server time: {e}")
            return int(time.time() * 1000)

    async def get_exchange_status(self) -> Dict[str, Any]:
        """
        Получает статус биржи
        """
        try:
            if hasattr(self.rest_client, 'fetch_status'):
                status = await self.rest_client.fetch_status()
                return status
            else:
                # Fallback - проверяем через balance
                await self.fetch_balance()
                return {
                    'status': 'ok',
                    'updated': int(time.time() * 1000)
                }
                
        except Exception as e:
            logger.error(f"Failed to get exchange status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'updated': int(time.time() * 1000)
            }

    async def close(self) -> None:
        """
        Закрывает соединения с биржей
        """
        try:
            if self.rest_client:
                await self.rest_client.close()
                logger.debug("Closed REST client connection")
                
            if self.stream_client:
                await self.stream_client.close()
                logger.debug("Closed WebSocket client connection")
                
            logger.info(f"🔌 Closed all connections for {self.exchange_name}")
            
        except Exception as e:
            logger.error(f"Error closing connections: {e}")

    # ===== UTILITY METHODS =====

    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о коннекторе
        """
        return {
            'exchange_name': self.exchange_name,
            'use_sandbox': self.use_sandbox,
            'has_rest_client': self.rest_client is not None,
            'has_stream_client': self.stream_client is not None,
            'markets_cached': self._markets_cache is not None,
            'markets_cache_age': time.time() - self._markets_cache_time if self._markets_cache else None,
            'ccxt_version': ccxt.__version__
        }

    def __repr__(self):
        return (f"CCXTExchangeConnector(exchange={self.exchange_name}, "
                f"sandbox={self.use_sandbox}, "
                f"rest_client={'✓' if self.rest_client else '✗'}, "
                f"stream_client={'✓' if self.stream_client else '✗'})")


# ===== FACTORY FUNCTION =====

def create_ccxt_connector(
    exchange_name: str = "binance",
    use_sandbox: bool = False
) -> CCXTExchangeConnector:
    """
    Factory function для создания CCXT коннектора
    """
    return CCXTExchangeConnector(exchange_name, use_sandbox)


# ===== EXAMPLE USAGE =====

if __name__ == "__main__":
    async def example_usage():
        # Создание коннектора
        connector = create_ccxt_connector("binance", use_sandbox=True)
        
        try:
            # Тест соединения
            if await connector.test_connection():
                print("✅ Connection successful!")
                
                # Загрузка рынков
                markets = await connector.load_markets()
                print(f"📊 Loaded {len(markets)} markets")
                
                # Получение тикера
                ticker = await connector.fetch_ticker("BTC/USDT")
                print(f"💰 BTC/USDT: {ticker['last']}")
                
                # Получение баланса
                balance = await connector.fetch_balance()
                print(f"💳 USDT balance: {balance.get('USDT', {}).get('free', 0)}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
        finally:
            # Закрытие соединений
            await connector.close()
    
    asyncio.run(example_usage())