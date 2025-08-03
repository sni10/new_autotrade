#!/usr/bin/env python3
"""
Test script to debug the Order .get() error
"""
import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from domain.entities.order import Order
from domain.entities.currency_pair import CurrencyPair
from domain.services.orders.order_service import OrderService
from domain.services.orders.order_execution_service import OrderExecutionService
from domain.services.deals.deal_service import DealService
from domain.factories.order_factory import OrderFactory
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from infrastructure.repositories.deals_repository import InMemoryDealsRepository

async def test_order_creation_error():
    """Test to reproduce the Order .get() error"""
    print("🧪 Testing Order creation error...")
    
    try:
        # Create test repositories
        orders_repo = InMemoryOrdersRepository()
        deals_repo = InMemoryDealsRepository()
        
        # Create factories
        order_factory = OrderFactory()
        deal_factory = DealFactory(order_factory)
        
        # Create currency pair
        currency_pair = CurrencyPair(
            base_currency="MAGIC",
            quote_currency="USDT",
            symbol="MAGIC/USDT"
        )
        
        # Set precision from log data
        currency_pair.precision = {
            'amount': 0.1,
            'price': 0.0001,
            'cost': None,
            'base': 1e-08,
            'quote': 1e-08
        }
        currency_pair.limits = {
            'amount': {'min': 0.1, 'max': 92141578.0},
            'price': {'min': 0.0001, 'max': 1000.0},
            'cost': {'min': 5.0}
        }
        currency_pair.taker_fee = 0.001
        
        # Create a mock exchange connector that returns Order object
        class MockExchangeConnector:
            async def create_order(self, symbol, side, order_type, amount, price):
                # This should return an Order object like the real connector
                raw_order = {
                    'id': '1361272',
                    'symbol': symbol,
                    'side': side,
                    'type': order_type,
                    'amount': amount,
                    'price': price,
                    'status': 'open',
                    'filled': 0.0,
                    'remaining': amount,
                    'cost': 0.0,
                    'average': 0.0,
                    'timestamp': 1000000,
                    'fee': {'cost': 0.0, 'currency': 'USDT'}
                }
                return Order.from_dict(raw_order)
            
            async def check_sufficient_balance(self, symbol, side, amount, price):
                return True, "OK", 1000.0
        
        mock_connector = MockExchangeConnector()
        
        # Create services
        order_service = OrderService(orders_repo, order_factory, mock_connector)
        deal_service = DealService(deals_repo, order_service, deal_factory, mock_connector)
        order_execution_service = OrderExecutionService(order_service, deal_service, mock_connector)
        
        # Test strategy result (from log)
        strategy_result = (0.1662, 150.5, 0.1687, 150.4, {"comment": "✅ Сделка возможна."})
        
        # Try to execute the strategy
        print("📊 Executing trading strategy...")
        result = await order_execution_service.execute_trading_strategy(currency_pair, strategy_result)
        
        if result.success:
            print("✅ Strategy executed successfully!")
            print(f"   Deal ID: {result.deal_id}")
            print(f"   Buy Order: {result.buy_order}")
            print(f"   Sell Order: {result.sell_order}")
        else:
            print(f"❌ Strategy failed: {result.error_message}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_order_creation_error())