# infrastructure/connectors/exchange_adapter.py
import logging
from typing import Dict, List, Any, Optional, Tuple
from src.infrastructure.connectors.ccxt_exchange_connector import CCXTExchangeConnector
from src.domain.entities.order import Order, OrderExecutionResult

logger = logging.getLogger(__name__)


class ExchangeAdapter:
    """
    🔄 BACKWARD COMPATIBILITY ADAPTER
    
    Адаптер для обеспечения обратной совместимости между новым CCXT коннектором
    и существующим кодом AutoTrade. Транслирует вызовы старого API в новый CCXT формат.
    """

    def __init__(self, exchange_name: str = "binance", use_sandbox: bool = False):
        self.ccxt_connector = CCXTExchangeConnector(exchange_name, use_sandbox)
        self.exchange_name = exchange_name
        self.use_sandbox = use_sandbox

    # ===== DIRECT DELEGATION METHODS =====

    async def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """Прямая делегация к CCXT connector"""
        return await self.ccxt_connector.load_markets(reload)

    async def fetch_balance(self) -> Dict[str, Any]:
        """Прямая делегация к CCXT connector"""
        return await self.ccxt_connector.fetch_balance()

    async def test_connection(self) -> bool:
        """Прямая делегация к CCXT connector"""
        return await self.ccxt_connector.test_connection()

    async def close(self) -> None:
        """Прямая делегация к CCXT connector"""
        await self.ccxt_connector.close()

    # ===== STREAMING METHODS (прямая делегация) =====

    async def watch_ticker(self, symbol: str) -> Dict[str, Any]:
        """WebSocket стрим тикеров"""
        return await self.ccxt_connector.watch_ticker(symbol)

    async def watch_order_book(self, symbol: str) -> Dict[str, Any]:
        """WebSocket стрим стакана заявок"""
        return await self.ccxt_connector.watch_order_book(symbol)

    async def watch_trades(self, symbol: str) -> List[Dict[str, Any]]:
        """WebSocket стрим сделок"""
        return await self.ccxt_connector.watch_trades(symbol)

    async def watch_ohlcv(self, symbol: str, timeframe: str = '1m') -> List[List]:
        """WebSocket стрим OHLCV"""
        return await self.ccxt_connector.watch_ohlcv(symbol, timeframe)

    # ===== ADAPTED METHODS FOR BACKWARD COMPATIBILITY =====

    def _normalize_symbol(self, symbol: str) -> str:
        """
        LEGACY METHOD: Преобразует 'ETHUSDT' -> 'ETH/USDT'
        Сохранено для обратной совместимости
        """
        if not symbol:
            return None
        if '/' in symbol:
            return symbol
        
        # Обработка популярных пар
        if symbol.endswith('USDT'):
            return f"{symbol[:-4]}/USDT"
        elif symbol.endswith('USDC'):
            return f"{symbol[:-4]}/USDC"
        elif symbol.endswith('BTC'):
            return f"{symbol[:-3]}/BTC"
        elif symbol.endswith('ETH'):
            return f"{symbol[:-3]}/ETH"
        
        return symbol

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """LEGACY: Получение тикера с нормализацией символа"""
        normalized_symbol = self._normalize_symbol(symbol)
        return await self.ccxt_connector.fetch_ticker(normalized_symbol)

    async def fetch_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """LEGACY: Получение стакана с нормализацией символа"""
        normalized_symbol = self._normalize_symbol(symbol)
        return await self.ccxt_connector.fetch_order_book(normalized_symbol, limit)

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
        LEGACY: Создание ордера с адаптацией параметров
        """
        # Нормализуем символ
        normalized_symbol = self._normalize_symbol(symbol)
        
        # Конвертируем старые типы в CCXT стандарт
        ccxt_type = self._convert_order_type_to_ccxt(order_type)
        ccxt_side = side.lower()
        
        return await self.ccxt_connector.create_order(
            symbol=normalized_symbol,
            type=ccxt_type,
            side=ccxt_side,
            amount=amount,
            price=price,
            params=params
        )

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """LEGACY: Отмена ордера с нормализацией символа"""
        normalized_symbol = self._normalize_symbol(symbol)
        return await self.ccxt_connector.cancel_order(order_id, normalized_symbol)

    async def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """LEGACY: Получение ордера с нормализацией символа"""
        normalized_symbol = self._normalize_symbol(symbol)
        return await self.ccxt_connector.fetch_order(order_id, normalized_symbol)

    async def fetch_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """LEGACY: Получение открытых ордеров"""
        normalized_symbol = self._normalize_symbol(symbol) if symbol else None
        return await self.ccxt_connector.fetch_open_orders(normalized_symbol)

    # ===== LEGACY BALANCE METHODS =====

    async def get_available_balance(self, currency: str) -> float:
        """LEGACY: Получение доступного баланса"""
        return await self.ccxt_connector.get_available_balance(currency.upper())

    async def get_balance(self, currency: str) -> float:
        """LEGACY: Алиас для get_available_balance"""
        return await self.get_available_balance(currency)

    async def check_sufficient_balance(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float = None
    ) -> Tuple[bool, str, float]:
        """LEGACY: Проверка достаточности баланса"""
        normalized_symbol = self._normalize_symbol(symbol)
        return await self.ccxt_connector.check_sufficient_balance(
            normalized_symbol, side.lower(), amount, price
        )

    # ===== LEGACY SPECIFIC METHODS =====

    async def create_market_sell_order(self, symbol: str, amount: float) -> Optional[OrderExecutionResult]:
        """
        LEGACY: Создание маркет ордера на продажу для стоп-лосса
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            
            # Создаем маркет ордер через CCXT
            result = await self.ccxt_connector.create_market_order(
                symbol=normalized_symbol,
                side='sell',
                amount=amount
            )
            
            if result:
                logger.info(f"✅ Market SELL order created: {result.get('id', 'N/A')}")
                
                # Возвращаем в старом формате для совместимости
                return OrderExecutionResult(
                    success=True,
                    order=Order.from_ccxt_response(result),
                    exchange_response=result
                )
            else:
                logger.error("❌ Failed to create market sell order - no result")
                return OrderExecutionResult(
                    success=False,
                    error_message="No result from exchange"
                )
                
        except Exception as e:
            logger.error(f"❌ Error creating market sell order: {e}")
            return OrderExecutionResult(
                success=False,
                error_message=str(e)
            )

    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        LEGACY: Получение информации о торговой паре в старом формате
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            market = await self.ccxt_connector.get_market_info(normalized_symbol)
            
            # Конвертируем в старый формат ExchangeInfo
            limits = market.get('limits', {})
            precision = market.get('precision', {})
            
            return {
                'symbol': normalized_symbol,
                'min_qty': limits.get('amount', {}).get('min'),
                'max_qty': limits.get('amount', {}).get('max'),
                'step_size': precision.get('amount'),
                'min_price': limits.get('price', {}).get('min'),
                'max_price': limits.get('price', {}).get('max'),
                'tick_size': precision.get('price'),
                'min_notional': limits.get('cost', {}).get('min'),
                'fees': {
                    'maker': market.get('maker', 0.001),
                    'taker': market.get('taker', 0.001)
                },
                'precision': precision
            }
            
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            raise

    # ===== AUTOTRADE INTEGRATION METHODS =====

    async def place_order_from_autotrade(self, order: Order) -> OrderExecutionResult:
        """
        Размещает AutoTrade Order на бирже через CCXT
        """
        try:
            # Валидируем ордер
            is_valid, error_msg = order.validate_for_exchange_placement()
            if not is_valid:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Order validation failed: {error_msg}"
                )

            # Создаем ордер через CCXT
            ccxt_result = await self.ccxt_connector.create_order(
                symbol=order.symbol,
                type=order.type,
                side=order.side,
                amount=order.amount,
                price=order.price,
                params={
                    'timeInForce': order.timeInForce,
                    'clientOrderId': order.clientOrderId
                }
            )

            # Обновляем ордер данными с биржи
            order.update_from_ccxt_response(ccxt_result)
            order.mark_as_placed_on_exchange(
                ccxt_result['id'],
                ccxt_result.get('timestamp')
            )

            return OrderExecutionResult(
                success=True,
                order=order,
                exchange_response=ccxt_result
            )

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            order.mark_as_failed(str(e))
            
            return OrderExecutionResult(
                success=False,
                order=order,
                error_message=str(e)
            )

    async def sync_autotrade_order(self, order: Order) -> Order:
        """
        Синхронизирует AutoTrade Order с биржей
        """
        return await self.ccxt_connector.sync_order_with_exchange(order)

    # ===== UTILITY METHODS =====

    def _convert_order_type_to_ccxt(self, legacy_type: str) -> str:
        """Конвертирует старые типы ордеров в CCXT стандарт"""
        type_mapping = {
            'LIMIT': 'limit',
            'MARKET': 'market',
            'STOP_LOSS': 'stop',
            'TAKE_PROFIT': 'take_profit'
        }
        return type_mapping.get(legacy_type.upper(), legacy_type.lower())

    def _convert_order_status_from_ccxt(self, ccxt_status: str) -> str:
        """Конвертирует CCXT статусы в старый формат"""
        status_mapping = {
            'open': 'OPEN',
            'closed': 'FILLED',
            'canceled': 'CANCELED',
            'expired': 'EXPIRED',
            'rejected': 'FAILED',
            'pending': 'PENDING'
        }
        return status_mapping.get(ccxt_status.lower(), ccxt_status.upper())

    def get_adapter_info(self) -> Dict[str, Any]:
        """Возвращает информацию об адаптере"""
        return {
            'adapter_type': 'ExchangeAdapter',
            'exchange_name': self.exchange_name,
            'use_sandbox': self.use_sandbox,
            'ccxt_connector_info': self.ccxt_connector.get_exchange_info(),
            'backward_compatibility': True
        }

    def __repr__(self):
        return (f"ExchangeAdapter(exchange={self.exchange_name}, "
                f"sandbox={self.use_sandbox}, "
                f"ccxt_connector={self.ccxt_connector})")


# ===== FACTORY FUNCTION FOR LEGACY COMPATIBILITY =====

def create_exchange_connector(exchange_name: str = "binance", use_sandbox: bool = False) -> ExchangeAdapter:
    """
    Factory function для создания адаптера с обратной совместимостью
    """
    return ExchangeAdapter(exchange_name, use_sandbox)


# Алиас для полной обратной совместимости
CcxtExchangeConnector = ExchangeAdapter