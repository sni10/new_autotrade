import time
from typing import Dict, List, Optional, Any, Tuple

from src.domain.entities.order import ExchangeInfo


class MockCcxtExchangeConnector:
    def __init__(self, market_info: Dict[str, Any]):
        self._market_info = market_info
        self._balances = {
            'free': {"USDT": 10000.0, "BTC": 10.0, "ETH": 100.0, "THE": 5000.0},
            'used': {"USDT": 0.0, "BTC": 0.0, "ETH": 0.0, "THE": 0.0},
            'total': {"USDT": 10000.0, "BTC": 10.0, "ETH": 100.0, "THE": 5000.0}
        }
        self._open_orders: List[Dict[str, Any]] = []
        self._filled_orders: Dict[str, Dict[str, Any]] = {}
        self._canceled_orders: Dict[str, Dict[str, Any]] = {}
        self._order_id_counter = 1

    async def fetch_balance(self) -> Dict[str, Any]:
        return self._balances.copy()

    async def get_symbol_info(self, symbol: str) -> ExchangeInfo:
        info = self._market_info[symbol]
        return ExchangeInfo(
            symbol=symbol,
            min_qty=info['limits']['amount']['min'],
            max_qty=info['limits']['amount']['max'],
            step_size=info['precision']['amount'],
            min_price=info['limits']['price']['min'],
            max_price=info['limits']['price']['max'],
            tick_size=info['precision']['price'],
            min_notional=info['limits']['cost']['min'],
            fees=info.get('fees', {'maker': 0.001, 'taker': 0.001}),
            precision=info['precision']
        )

    async def create_order(self, symbol: str, side: str, order_type: str, amount: float, price: Optional[float] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        order_id = f"mock_{self._order_id_counter}"
        self._order_id_counter += 1
        
        order_data = {
            'id': order_id,
            'clientOrderId': None,
            'datetime': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime()),
            'timestamp': int(time.time() * 1000),
            'lastTradeTimestamp': None,
            'status': 'open',
            'symbol': symbol,
            'type': order_type,
            'timeInForce': 'GTC',
            'side': side,
            'price': price,
            'average': None,
            'amount': amount,
            'filled': 0.0,
            'remaining': amount,
            'cost': 0.0,
            'trades': [],
            'fee': None,
            'info': {}
        }
        self._open_orders.append(order_data)
        
        base_currency, quote_currency = symbol.split('/')
        if side == 'buy':
            cost = amount * price
            self._balances['free'][quote_currency] -= cost
            self._balances['used'][quote_currency] += cost
        else: # sell
            self._balances['free'][base_currency] -= amount
            self._balances['used'][base_currency] += amount
            
        return order_data

    async def fetch_ticker(self, symbol: str) -> Dict[str, float]:
        return {'last': self._market_info[symbol]['info']['last_price']}

    def get_open_orders(self) -> List[Dict[str, Any]]:
        return self._open_orders

    def fill_order(self, order_id: str, fill_price: Optional[float] = None):
        order_to_fill = next((o for o in self._open_orders if o['id'] == order_id), None)
        if order_to_fill:
            self._open_orders = [o for o in self._open_orders if o['id'] != order_id]
            order_to_fill['status'] = 'closed'
            order_to_fill['filled'] = order_to_fill['amount']
            order_to_fill['remaining'] = 0
            order_to_fill['average'] = fill_price or order_to_fill['price']
            order_to_fill['lastTradeTimestamp'] = int(time.time() * 1000)
            self._filled_orders[order_id] = order_to_fill

            symbol = order_to_fill['symbol']
            side = order_to_fill['side']
            amount = order_to_fill['amount']
            price = order_to_fill['average']
            base_currency, quote_currency = symbol.split('/')

            if side == 'buy':
                cost = amount * price
                self._balances['used'][quote_currency] -= cost
                self._balances['free'][base_currency] += amount
            else: # sell
                self._balances['used'][base_currency] -= amount
                self._balances['free'][quote_currency] += amount * price


    def set_market_price(self, symbol: str, price: float):
        self._market_info[symbol]['info']['last_price'] = price

    def set_balance(self, currency: str, amount: float):
        self._balances['free'][currency] = amount
        self._balances['total'][currency] = amount

    async def check_sufficient_balance(self, symbol: str, side: str, amount: float, price: float = None) -> Tuple[bool, str, float]:
        base_currency, quote_currency = symbol.split('/')
        if side == 'buy':
            cost = amount * price
            available = self._balances['free'][quote_currency]
            return available >= cost, quote_currency, available
        else: # sell
            available = self._balances['free'][base_currency]
            return available >= amount, base_currency, available

    async def fetch_order(self, order_id: str, symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if order_id in self._filled_orders:
            return self._filled_orders[order_id]
        if order_id in self._canceled_orders:
            return self._canceled_orders[order_id]
        return next((o for o in self._open_orders if o['id'] == order_id), None)

    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        order_to_cancel = next((o for o in self._open_orders if o['id'] == order_id), None)
        if order_to_cancel:
            self._open_orders = [o for o in self._open_orders if o['id'] != order_id]
            order_to_cancel['status'] = 'canceled'
            self._canceled_orders[order_id] = order_to_cancel
            return order_to_cancel
        return {}
