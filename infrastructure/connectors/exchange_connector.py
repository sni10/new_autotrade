# infrastructure/connectors/exchange_connector.py.new - ENHANCED для реальной торговли
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import ccxt
import ccxt.pro as ccxt_async
from domain.entities.order import ExchangeInfo

logger = logging.getLogger(__name__)

class CcxtExchangeConnector:
    """
    🚀 РАСШИРЕННАЯ обёртка над ccxt для полноценной торговли
    Поддерживает все критические операции для реального трейдинга
    """

    def __init__(self, exchange_name="binance", use_sandbox=False, config_path=None):
        self.exchange_name = exchange_name
        self.use_sandbox = use_sandbox
        self.config_path = config_path or "F:\\HOME\\new_autotrade\\config\\config.json"
        self.config = None
        self.client = None
        self.async_client = None

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests

        # Cache для exchange info
        self.exchange_info_cache = {}
        self.symbols_cache = {}

        # Инициализация
        self._load_config()
        self._init_exchange_clients()

    def _load_config(self):
        """Загружает конфигурацию API ключей"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            env_key = 'sandbox' if self.use_sandbox else 'production'
            self.config = config[self.exchange_name][env_key]

            # Загружаем приватный ключ из файла
            private_key_path = self.config.get('privateKeyPath')
            if private_key_path and Path(private_key_path).exists():
                with open(private_key_path, 'r') as f:
                    private_key = f.read()
                self.config['secret'] = private_key

            logger.info(f"✅ Config loaded for {self.exchange_name} ({env_key})")

        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            raise

    def _init_exchange_clients(self):
        """Инициализирует синхронный и асинхронный клиенты"""
        try:
            # Синхронный клиент
            exchange_class = getattr(ccxt, self.exchange_name)
            self.client = exchange_class({
                'apiKey': self.config.get('apiKey'),
                'secret': self.config.get('secret'),
                'enableRateLimit': True,
                'rateLimit': 100,  # мс между запросами
                'options': {
                    'defaultType': 'spot',  # spot торговля
                }
            })

            # Асинхронный клиент
            async_exchange_class = getattr(ccxt_async, self.exchange_name)
            self.async_client = async_exchange_class({
                'apiKey': self.config.get('apiKey'),
                'secret': self.config.get('secret'),
                'enableRateLimit': True,
                'rateLimit': 100,
                'options': {
                    'defaultType': 'spot',
                }
            })

            # Включаем sandbox режим
            if self.use_sandbox:
                if hasattr(self.client, 'set_sandbox_mode'):
                    self.client.set_sandbox_mode(True)
                    self.async_client.set_sandbox_mode(True)
                    logger.info("🧪 Sandbox mode enabled")
                else:
                    logger.warning(f"⚠️ Sandbox mode not supported for {self.exchange_name}")

            logger.info(f"✅ Exchange clients initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize exchange clients: {e}")
            raise

    async def _rate_limit_wait(self):
        """Соблюдает rate limiting"""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    # 🚀 ОСНОВНЫЕ МЕТОДЫ ДЛЯ ТОРГОВЛИ

    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: float = None,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        🛒 Создание ордера на бирже

        Args:
            symbol: Торговая пара (BTCUSDT)
            side: buy или sell
            order_type: limit, market, stop_loss, etc.
            amount: Количество
            price: Цена (для лимитных ордеров)
            params: Дополнительные параметры

        Returns:
            Ответ биржи с информацией об ордере
        """
        await self._rate_limit_wait()

        try:
            logger.info(f"📤 Creating {side.upper()} {order_type} order: {amount} {symbol} @ {price}")

            # Подготавливаем параметры
            order_params = params or {}

            # Создаем ордер через async клиент
            if order_type.lower() == 'limit':
                if price is None:
                    raise ValueError("Price required for limit orders")
                result = await self.async_client.create_order(
                    symbol, order_type, side, amount, price, None, order_params
                )
            elif order_type.lower() == 'market':
                result = await self.async_client.create_order(
                    symbol, order_type, side, amount, None, None, order_params
                )
            else:
                # Для других типов (stop_loss, take_profit)
                result = await self.async_client.create_order(
                    symbol, order_type, side, amount, price, None, order_params
                )

            logger.info(f"✅ Order created successfully: {result.get('id', 'N/A')}")
            return result

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

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        ❌ Отмена ордера на бирже
        """
        await self._rate_limit_wait()

        try:
            logger.info(f"❌ Cancelling order {order_id} for {symbol}")

            result = await self.async_client.cancel_order(order_id, symbol)

            logger.info(f"✅ Order cancelled successfully: {order_id}")
            return result

        except ccxt.OrderNotFound as e:
            logger.warning(f"⚠️ Order not found: {order_id}")
            raise
        except Exception as e:
            logger.error(f"❌ Error cancelling order {order_id}: {e}")
            raise

    async def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        📊 Получение информации об ордере
        """
        await self._rate_limit_wait()

        try:
            result = await self.async_client.fetch_order(order_id, symbol)
            return result
        except Exception as e:
            logger.error(f"❌ Error fetching order {order_id}: {e}")
            raise

    async def fetch_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        📋 Получение всех открытых ордеров
        """
        await self._rate_limit_wait()

        try:
            result = await self.async_client.fetch_open_orders(symbol)
            return result
        except Exception as e:
            logger.error(f"❌ Error fetching open orders: {e}")
            raise

    async def fetch_order_history(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        📚 Получение истории ордеров
        """
        await self._rate_limit_wait()

        try:
            result = await self.async_client.fetch_orders(symbol, None, limit)
            return result
        except Exception as e:
            logger.error(f"❌ Error fetching order history: {e}")
            raise

    # 💰 МЕТОДЫ ДЛЯ РАБОТЫ С БАЛАНСОМ

    async def fetch_balance(self) -> Dict[str, Any]:
        """
        💰 Получение баланса аккаунта
        """
        await self._rate_limit_wait()

        try:
            balance = await self.async_client.fetch_balance()

            # Логируем только основные валюты
            main_currencies = ['USDT', 'BTC', 'ETH', 'BNB']
            for currency in main_currencies:
                if currency in balance and balance[currency]['total'] > 0:
                    total = balance[currency]['total']
                    free = balance[currency]['free']
                    used = balance[currency]['used']
                    logger.info(f"💰 {currency}: {total:.4f} (free: {free:.4f}, used: {used:.4f})")

            return balance

        except Exception as e:
            logger.error(f"❌ Error fetching balance: {e}")
            raise

    async def get_available_balance(self, currency: str) -> float:
        """
        💵 Получение доступного баланса для конкретной валюты
        """
        try:
            balance = await self.fetch_balance()
            return balance.get(currency, {}).get('free', 0.0)
        except Exception as e:
            logger.error(f"❌ Error getting balance for {currency}: {e}")
            return 0.0

    async def check_sufficient_balance(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float = None
    ) -> Tuple[bool, str, float]:
        """
        🔍 Проверка достаточности баланса для ордера

        Returns:
            tuple: (sufficient, currency, available_amount)
        """
        try:
            base_currency, quote_currency = symbol.replace('/', '').split('USDT')[0], 'USDT'
            if '/' in symbol:
                base_currency, quote_currency = symbol.split('/')

            if side.lower() == 'buy':
                # Для покупки нужна quote валюта (USDT)
                required_amount = amount * (price or 0)
                available = await self.get_available_balance(quote_currency)
                return available >= required_amount, quote_currency, available
            else:
                # Для продажи нужна base валюта (BTC)
                available = await self.get_available_balance(base_currency)
                return available >= amount, base_currency, available

        except Exception as e:
            logger.error(f"❌ Error checking balance: {e}")
            return False, "UNKNOWN", 0.0

    # 📊 МЕТОДЫ ДЛЯ ПОЛУЧЕНИЯ РЫНОЧНОЙ ИНФОРМАЦИИ

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        📈 Получение тикера (цена, объем, изменение)
        """
        await self._rate_limit_wait()

        try:
            ticker = await self.async_client.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"❌ Error fetching ticker for {symbol}: {e}")
            raise

    async def fetch_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        📊 Получение стакана заявок
        """
        await self._rate_limit_wait()

        try:
            orderbook = await self.async_client.fetch_order_book(symbol, limit)
            return orderbook
        except Exception as e:
            logger.error(f"❌ Error fetching orderbook for {symbol}: {e}")
            raise

    async def fetch_exchange_info(self, symbol: str = None) -> Dict[str, Any]:
        """
        ℹ️ Получение информации о бирже и торговых парах
        """
        await self._rate_limit_wait()

        try:
            if symbol and symbol in self.exchange_info_cache:
                return self.exchange_info_cache[symbol]

            # Для ccxt используем метод load_markets
            markets = await self.async_client.load_markets()

            if symbol:
                if symbol in markets:
                    info = markets[symbol]
                    self.exchange_info_cache[symbol] = info
                    return info
                else:
                    raise ValueError(f"Symbol {symbol} not found")

            return markets

        except Exception as e:
            logger.error(f"❌ Error fetching exchange info: {e}")
            raise

    async def get_symbol_info(self, symbol: str) -> ExchangeInfo:
        """
        🔍 Получение детальной информации о торговой паре
        """
        try:
            market_info = await self.fetch_exchange_info(symbol)

            # Извлекаем лимиты из ccxt market info
            limits = market_info.get('limits', {})
            precision = market_info.get('precision', {})
            fees = market_info.get('fees', {})

            exchange_info = ExchangeInfo(
                symbol=symbol,
                min_qty=limits.get('amount', {}).get('min', 0.0),
                max_qty=limits.get('amount', {}).get('max', float('inf')),
                step_size=precision.get('amount', 0.00000001),
                min_price=limits.get('price', {}).get('min', 0.0),
                max_price=limits.get('price', {}).get('max', float('inf')),
                tick_size=precision.get('price', 0.00000001),
                min_notional=limits.get('cost', {}).get('min', 0.0),
                fees={
                    'maker': fees.get('trading', {}).get('maker', 0.001),
                    'taker': fees.get('trading', {}).get('taker', 0.001)
                }
            )

            return exchange_info

        except Exception as e:
            logger.error(f"❌ Error getting symbol info for {symbol}: {e}")
            raise

    # 🔧 УТИЛИТНЫЕ МЕТОДЫ

    async def test_connection(self) -> bool:
        """
        🔗 Тест соединения с биржей
        """
        try:
            await self.fetch_balance()
            logger.info("✅ Connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    async def get_server_time(self) -> int:
        """
        ⏰ Получение времени сервера биржи
        """
        try:
            await self._rate_limit_wait()
            # Для ccxt используем fetch_time если доступен
            if hasattr(self.async_client, 'fetch_time'):
                return await self.async_client.fetch_time()
            else:
                # Fallback к текущему времени
                import time
                return int(time.time() * 1000)
        except Exception as e:
            logger.error(f"❌ Error getting server time: {e}")
            import time
            return int(time.time() * 1000)

    async def calculate_fees(self, symbol: str, amount: float, price: float, side: str) -> float:
        """
        💸 Расчет комиссий для ордера
        """
        try:
            symbol_info = await self.get_symbol_info(symbol)
            fee_rate = symbol_info.fees.get('taker', 0.001)  # Используем taker fee

            total_value = amount * price
            fee = total_value * fee_rate

            return fee

        except Exception as e:
            logger.error(f"❌ Error calculating fees: {e}")
            return 0.0

    # 🧹 МЕТОДЫ ОЧИСТКИ

    async def close(self):
        """
        🔚 Закрытие соединений
        """
        try:
            if self.async_client:
                await self.async_client.close()
            logger.info("✅ Exchange connector closed")
        except Exception as e:
            logger.error(f"❌ Error closing connector: {e}")

    def __del__(self):
        """Деструктор для очистки ресурсов"""
        try:
            if self.async_client and hasattr(self.async_client, 'close'):
                import asyncio
                # Попытка закрыть, если event loop еще работает
                try:
                    loop = asyncio.get_event_loop()
                    if not loop.is_closed():
                        loop.create_task(self.async_client.close())
                except:
                    pass
        except:
            pass

    # 🆕 ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ

    async def cancel_all_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        🚨 Отмена всех открытых ордеров (экстренная функция)
        """
        try:
            open_orders = await self.fetch_open_orders(symbol)
            cancelled_orders = []

            for order in open_orders:
                try:
                    result = await self.cancel_order(order['id'], order['symbol'])
                    cancelled_orders.append(result)
                except Exception as e:
                    logger.error(f"❌ Failed to cancel order {order['id']}: {e}")

            logger.info(f"✅ Cancelled {len(cancelled_orders)} orders")
            return cancelled_orders

        except Exception as e:
            logger.error(f"❌ Error cancelling all orders: {e}")
            return []

    async def get_trade_history(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        📜 Получение истории сделок
        """
        await self._rate_limit_wait()

        try:
            trades = await self.async_client.fetch_my_trades(symbol, None, limit)
            return trades
        except Exception as e:
            logger.error(f"❌ Error fetching trade history: {e}")
            return []


# 🆕 СОВМЕСТИМОСТЬ СО СТАРЫМ КОДОМ

class CcxtExchangeConnectorLegacy:
    """Обертка для совместимости со старым кодом"""

    def __init__(self, exchange_name="binance", use_sandbox=False):
        self.connector = CcxtExchangeConnector(exchange_name, use_sandbox)

    async def create_order(self, symbol, side, order_type, amount, price=None):
        """Метод для совместимости"""
        return await self.connector.create_order(symbol, side, order_type, amount, price)

    async def cancel_order(self, order_id, symbol):
        """Метод для совместимости"""
        return await self.connector.cancel_order(order_id, symbol)
