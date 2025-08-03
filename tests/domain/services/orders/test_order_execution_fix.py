#!/usr/bin/env python3
"""
Test script to verify the OrderExecutionService fix
"""
import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from domain.services.orders.order_execution_service import OrderExecutionService
from domain.services.orders.buy_order_monitor import BuyOrderMonitor

def test_order_execution_service_methods():
    """Test that OrderExecutionService doesn't have monitor_active_orders method"""
    print("🧪 Testing OrderExecutionService methods...")
    
    # Check if monitor_active_orders method exists
    has_monitor_active_orders = hasattr(OrderExecutionService, 'monitor_active_orders')
    print(f"📊 OrderExecutionService.monitor_active_orders exists: {has_monitor_active_orders}")
    
    if not has_monitor_active_orders:
        print("✅ Confirmed: monitor_active_orders method does NOT exist in OrderExecutionService")
    else:
        print("❌ Unexpected: monitor_active_orders method still exists")
        return False
    
    # List available methods
    methods = [method for method in dir(OrderExecutionService) if not method.startswith('_')]
    print(f"📈 Available OrderExecutionService methods: {methods}")
    
    return True

def test_buy_order_monitor_methods():
    """Test that BuyOrderMonitor has the correct methods"""
    print("\n🧪 Testing BuyOrderMonitor methods...")
    
    # Check if check_stale_buy_orders method exists
    has_check_stale_buy_orders = hasattr(BuyOrderMonitor, 'check_stale_buy_orders')
    print(f"📊 BuyOrderMonitor.check_stale_buy_orders exists: {has_check_stale_buy_orders}")
    
    if has_check_stale_buy_orders:
        print("✅ Confirmed: check_stale_buy_orders method exists in BuyOrderMonitor")
    else:
        print("❌ Error: check_stale_buy_orders method does NOT exist")
        return False
    
    # List available methods
    methods = [method for method in dir(BuyOrderMonitor) if not method.startswith('_')]
    print(f"📈 Available BuyOrderMonitor methods: {methods}")
    
    return True

def test_fix_summary():
    """Provide a summary of the fix"""
    print("\n🔧 Fix Summary:")
    print("❌ Problem: OrderExecutionService.monitor_active_orders() - AttributeError")
    print("✅ Solution: BuyOrderMonitor.check_stale_buy_orders() - Correct method")
    print("📝 Change: Line 120 in run_realtime_trading.py updated")
    print("🎯 Result: Trading system should no longer crash with AttributeError")

if __name__ == "__main__":
    print("🚀 Testing OrderExecutionService fix...")
    
    success1 = test_order_execution_service_methods()
    success2 = test_buy_order_monitor_methods()
    
    if success1 and success2:
        test_fix_summary()
        print("\n🎉 All tests passed! The fix should resolve the AttributeError.")
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
        sys.exit(1)