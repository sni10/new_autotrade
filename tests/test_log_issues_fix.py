#!/usr/bin/env python3
"""
Test script to verify fixes for issues found in logs/autotrade_2025-08-02_23-49-01.log
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
from domain.services.market_data.ticker_service import TickerService
from domain.entities.ticker import Ticker
from domain.factories.order_factory import OrderFactory
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository
from infrastructure.repositories.indicators_repository import InMemoryIndicatorsRepository

async def test_order_get_error_fix():
    """Test that the Order .get() error is fixed"""
    print("🧪 Testing Order .get() error fix...")
    
    try:
        # Create test repositories
        orders_repo = InMemoryOrdersRepository()
        deals_repo = InMemoryDealsRepository()
        
        # Create factories
        order_factory = OrderFactory()
        deal_factory = DealFactory(order_factory)
        
        # Create currency pair with MAGIC/USDT precision from log
        currency_pair = CurrencyPair(
            base_currency="MAGIC",
            quote_currency="USDT",
            symbol="MAGIC/USDT"
        )
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
        
        # Create a mock exchange connector that returns Order object (like real one)
        class MockExchangeConnector:
            async def create_order(self, symbol, side, order_type, amount, price):
                # Return Order object like the real connector does
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
            
            async def fetch_order(self, order_id, symbol):
                return Order.from_dict({'id': order_id, 'symbol': symbol, 'side': 'buy', 'type': 'limit', 'amount': 100, 'price': 0.1662, 'status': 'open'})
            
            async def cancel_order(self, order_id, symbol):
                return Order.from_dict({'id': order_id, 'symbol': symbol, 'side': 'buy', 'type': 'limit', 'amount': 100, 'price': 0.1662, 'status': 'canceled'})
            
            async def check_sufficient_balance(self, symbol, side, amount, price):
                return True, "OK", 1000.0
        
        mock_connector = MockExchangeConnector()
        
        # Create services
        order_service = OrderService(orders_repo, order_factory, mock_connector)
        deal_service = DealService(deals_repo, order_service, deal_factory, mock_connector)
        order_execution_service = OrderExecutionService(order_service, deal_service, mock_connector)
        
        # Test strategy result (from log: 150.5 MAGIC @ 0.1662)
        strategy_result = (0.1662, 150.5, 0.1687, 150.4, {"comment": "✅ Сделка возможна."})
        
        # Try to execute the strategy - this should NOT fail with Order.get() error
        print("📊 Executing trading strategy...")
        result = await order_execution_service.execute_trading_strategy(currency_pair, strategy_result)
        
        if result.success:
            print("✅ Order .get() error fix successful!")
            print(f"   Deal ID: {result.deal_id}")
            print(f"   Buy Order: {result.buy_order.order_id}")
            print(f"   Sell Order: {result.sell_order.order_id}")
            return True
        else:
            print(f"❌ Strategy failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Error during Order test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_signal_count_fix():
    """Test that signal count stays at 13 across multiple ticks"""
    print("\n🧪 Testing signal count fix...")
    
    try:
        # Create repositories
        tickers_repo = InMemoryTickerRepository()
        indicators_repo = InMemoryIndicatorsRepository()
        ticker_service = TickerService(tickers_repo, indicators_repo)
        
        # Generate test price data
        test_prices = [0.1662 + i * 0.0001 for i in range(100)]
        
        signal_counts = []
        
        # Process multiple tickers to simulate real trading
        for i, price in enumerate(test_prices):
            ticker_data = {
                'symbol': 'MAGIC/USDT',
                'timestamp': 1000000 + i,
                'open': price - 0.0001,
                'high': price + 0.0001,
                'low': price - 0.0002,
                'close': price,
                'last': price,
                'baseVolume': 1000.0,
                'quoteVolume': price * 1000.0
            }
            ticker = Ticker(ticker_data)
            
            # Process ticker asynchronously
            await ticker_service.process_ticker(ticker)
            
            # Check signal count
            if tickers_repo.tickers:
                last_ticker = tickers_repo.tickers[-1]
                if last_ticker.signals:
                    signal_count = len(last_ticker.signals)
                    signal_counts.append(signal_count)
                    
                    # Log signal counts for key ticks
                    if i + 1 in [1, 5, 10, 15, 20, 30, 50]:
                        print(f"   Тик {i + 1}: {signal_count} сигналов")
        
        # Check results
        if len(signal_counts) > 50:  # After enough ticks for all indicators
            final_count = signal_counts[-1]
            if final_count == 13:
                print("✅ Signal count fix successful!")
                print(f"   Final signal count: {final_count}")
                
                # Check that signal count is stable after initial calculation
                stable_counts = signal_counts[50:]  # After heavy indicators are calculated
                if all(count == 13 for count in stable_counts):
                    print("✅ Signal count remains stable at 13!")
                    return True
                else:
                    print(f"❌ Signal count not stable: {set(stable_counts)}")
                    return False
            else:
                print(f"❌ Final signal count is {final_count}, expected 13")
                return False
        else:
            print("❌ Not enough ticks processed")
            return False
            
    except Exception as e:
        print(f"❌ Error during signal count test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests for log issues fixes"""
    print("🚀 Testing fixes for issues in logs/autotrade_2025-08-02_23-49-01.log")
    print("="*80)
    
    # Test 1: Order .get() error fix
    test1_success = await test_order_get_error_fix()
    
    # Test 2: Signal count fix
    test2_success = await test_signal_count_fix()
    
    print("\n" + "="*80)
    print("📋 SUMMARY:")
    print(f"   Order .get() error fix: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"   Signal count fix: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 All fixes verified successfully!")
        print("✅ The trading system should now work without the errors from the log.")
        return True
    else:
        print("\n❌ Some fixes failed verification.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)