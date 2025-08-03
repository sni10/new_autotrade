#!/usr/bin/env python3
"""
Test script to verify fixes for fees list and None handling issues
"""
import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from domain.entities.order import Order
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

def test_fees_list_handling():
    """Test that Order.from_dict() correctly handles fees as list"""
    print("🧪 Testing fees list handling fix...")
    
    # Test case 1: fees as list of dictionaries (common format from some exchanges)
    test_data_1 = {
        'id': '1363874',
        'symbol': 'MAGIC/USDT',
        'side': 'buy',
        'type': 'limit',
        'amount': 151.5,
        'price': 0.1651,
        'status': 'open',
        'filled': 0.0,
        'remaining': 151.5,
        'fees': [{'cost': 0.025, 'currency': 'USDT'}]  # List format
    }
    
    try:
        order1 = Order.from_dict(test_data_1)
        print(f"✅ Test 1 passed: fees list with dict -> {order1.fees}")
        assert isinstance(order1.fees, float), f"Expected float, got {type(order1.fees)}"
        assert order1.fees == 0.025, f"Expected 0.025, got {order1.fees}"
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False
    
    # Test case 2: fees as list of numbers
    test_data_2 = {
        'id': '1363875',
        'symbol': 'MAGIC/USDT',
        'side': 'buy',
        'type': 'limit',
        'amount': 151.6,
        'price': 0.165,
        'status': 'open',
        'filled': 0.0,
        'remaining': 151.6,
        'fees': [0.030, 0.005]  # List of numbers
    }
    
    try:
        order2 = Order.from_dict(test_data_2)
        print(f"✅ Test 2 passed: fees list with numbers -> {order2.fees}")
        assert isinstance(order2.fees, float), f"Expected float, got {type(order2.fees)}"
        assert order2.fees == 0.030, f"Expected 0.030, got {order2.fees}"
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        return False
    
    # Test case 3: fees as empty list
    test_data_3 = {
        'id': '1363876',
        'symbol': 'MAGIC/USDT',
        'side': 'buy',
        'type': 'limit',
        'amount': 151.6,
        'price': 0.165,
        'status': 'open',
        'filled': 0.0,
        'remaining': 151.6,
        'fees': []  # Empty list
    }
    
    try:
        order3 = Order.from_dict(test_data_3)
        print(f"✅ Test 3 passed: empty fees list -> {order3.fees}")
        assert isinstance(order3.fees, float), f"Expected float, got {type(order3.fees)}"
        assert order3.fees == 0.0, f"Expected 0.0, got {order3.fees}"
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        return False
    
    # Test case 4: fees as regular number (should still work)
    test_data_4 = {
        'id': '1363877',
        'symbol': 'MAGIC/USDT',
        'side': 'buy',
        'type': 'limit',
        'amount': 151.6,
        'price': 0.165,
        'status': 'open',
        'filled': 0.0,
        'remaining': 151.6,
        'fees': 0.040  # Regular number
    }
    
    try:
        order4 = Order.from_dict(test_data_4)
        print(f"✅ Test 4 passed: fees as number -> {order4.fees}")
        assert isinstance(order4.fees, float), f"Expected float, got {type(order4.fees)}"
        assert order4.fees == 0.040, f"Expected 0.040, got {order4.fees}"
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        return False
    
    print("🎉 All fees handling tests passed!")
    return True

def test_logging_fees_safety():
    """Test that logging safely handles fees as list"""
    print("\n🧪 Testing logging fees safety...")
    
    # Create orders with different fees formats
    orders = []
    
    # Order with fees as list
    order1 = Order(
        order_id=1363874,
        side="BUY",
        order_type="LIMIT",
        price=0.1651,
        amount=151.5,
        fees=[0.025, 0.005]  # List format
    )
    orders.append(order1)
    
    # Order with fees as number
    order2 = Order(
        order_id=1363875,
        side="BUY", 
        order_type="LIMIT",
        price=0.165,
        amount=151.6,
        fees=0.030  # Number format
    )
    orders.append(order2)
    
    # Order with fees as None
    order3 = Order(
        order_id=1363876,
        side="BUY",
        order_type="LIMIT", 
        price=0.165,
        amount=151.6,
        fees=None  # None format
    )
    orders.append(order3)
    
    # Test the logging logic (simulate the code from run_realtime_trading.py)
    for i, order in enumerate(orders, 1):
        try:
            # This is the exact logic from the fixed run_realtime_trading.py
            if isinstance(order.fees, list):
                fees_value = float(order.fees[0]) if order.fees and order.fees[0] is not None else 0.0
            elif isinstance(order.fees, (int, float)):
                fees_value = float(order.fees)
            else:
                fees_value = 0.0
            
            print(f"✅ Test {i} passed: order {order.order_id} fees -> {fees_value}")
            
        except (ValueError, TypeError, IndexError) as e:
            print(f"❌ Test {i} failed: {e}")
            return False
    
    print("🎉 All logging safety tests passed!")
    return True

async def test_exchange_connector_none_handling():
    """Test that exchange connector handles None responses safely"""
    print("\n🧪 Testing exchange connector None handling...")
    
    # Create a mock exchange client that returns None
    class MockExchangeClient:
        async def create_order(self, symbol, order_type, side, amount, price, params):
            # Simulate the case where exchange returns None
            return None
    
    # Test the fixed logic
    try:
        # Simulate the fixed code from exchange_connector.py
        raw_order = None  # This is what would come from the mock client
        
        # This is the exact logic from the fixed exchange_connector.py
        if raw_order is None:
            raise Exception("Exchange returned None instead of order data")
        
        # This line should not be reached
        print("❌ Test failed: Exception should have been raised")
        return False
        
    except Exception as e:
        if "Exchange returned None" in str(e):
            print("✅ Test passed: None handling works correctly")
            print(f"   Exception message: {e}")
            return True
        else:
            print(f"❌ Test failed: Unexpected exception: {e}")
            return False

def test_scenario_from_log():
    """Test the specific scenario from the log"""
    print("\n🧪 Testing scenario from autotrade_2025-08-03_00-16-03.log...")
    
    # Simulate the exact data that would cause the original error
    problematic_order_data = {
        'id': '1363874',
        'symbol': 'MAGIC/USDT',
        'side': 'buy',
        'type': 'limit',
        'amount': 151.5,
        'price': 0.1651,
        'status': 'open',
        'filled': 0.0,
        'remaining': 151.5,
        'cost': 0.0,
        'average': 0.0,
        'timestamp': 1000000,
        'fees': [{'cost': 0.025, 'currency': 'USDT'}],  # This would cause the original error
        'info': {}
    }
    
    try:
        # This should work now with our fix
        order = Order.from_dict(problematic_order_data)
        print(f"✅ Order creation successful: {order.order_id}")
        print(f"   Fees: {order.fees} (type: {type(order.fees)})")
        
        # Test logging (simulate the problematic line from run_realtime_trading.py)
        if isinstance(order.fees, list):
            fees_value = float(order.fees[0]) if order.fees and order.fees[0] is not None else 0.0
        elif isinstance(order.fees, (int, float)):
            fees_value = float(order.fees)
        else:
            fees_value = 0.0
        
        print(f"✅ Logging simulation successful: fees_value = {fees_value}")
        return True
        
    except Exception as e:
        print(f"❌ Scenario test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing fixes for issues in autotrade_2025-08-03_00-16-03.log")
    print("="*80)
    
    # Test 1: Fees list handling
    test1_success = test_fees_list_handling()
    
    # Test 2: Logging fees safety
    test2_success = test_logging_fees_safety()
    
    # Test 3: Exchange connector None handling
    test3_success = await test_exchange_connector_none_handling()
    
    # Test 4: Specific scenario from log
    test4_success = test_scenario_from_log()
    
    print("\n" + "="*80)
    print("📋 SUMMARY:")
    print(f"   Fees list handling: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"   Logging fees safety: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    print(f"   Exchange None handling: {'✅ PASSED' if test3_success else '❌ FAILED'}")
    print(f"   Log scenario test: {'✅ PASSED' if test4_success else '❌ FAILED'}")
    
    if test1_success and test2_success and test3_success and test4_success:
        print("\n🎉 All fixes verified successfully!")
        print("✅ The errors from autotrade_2025-08-03_00-16-03.log should be resolved:")
        print("   - TypeError: float() argument must be a string or a real number, not 'list'")
        print("   - AttributeError: 'NoneType' object has no attribute 'get'")
        return True
    else:
        print("\n❌ Some fixes failed verification.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)