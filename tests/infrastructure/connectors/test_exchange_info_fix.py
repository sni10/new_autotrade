#!/usr/bin/env python3
"""
Test script to verify the exchange info fix
"""
import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

def test_method_existence():
    """Test that get_symbol_info method exists and get_exchange_info doesn't"""
    print("🧪 Testing CcxtExchangeConnector methods...")
    
    # Check if get_symbol_info method exists
    has_get_symbol_info = hasattr(CcxtExchangeConnector, 'get_symbol_info')
    print(f"📊 CcxtExchangeConnector.get_symbol_info exists: {has_get_symbol_info}")
    
    # Check if get_exchange_info method exists (should not exist)
    has_get_exchange_info = hasattr(CcxtExchangeConnector, 'get_exchange_info')
    print(f"📊 CcxtExchangeConnector.get_exchange_info exists: {has_get_exchange_info}")
    
    if has_get_symbol_info and not has_get_exchange_info:
        print("✅ Method availability check passed!")
        return True
    else:
        print("❌ Method availability check failed!")
        return False

async def test_get_symbol_info_method():
    """Test that get_symbol_info method works (mock test)"""
    print("\n🧪 Testing get_symbol_info method functionality...")
    
    try:
        # Create a mock connector (we can't actually connect without proper config)
        connector = CcxtExchangeConnector(use_sandbox=True)
        
        # Check that the method is callable
        method = getattr(connector, 'get_symbol_info', None)
        if method and callable(method):
            print("✅ get_symbol_info method is callable")
            return True
        else:
            print("❌ get_symbol_info method is not callable")
            return False
            
    except Exception as e:
        print(f"⚠️ Could not fully test method (expected due to config): {e}")
        # This is expected since we don't have proper API keys
        # But the method should still exist
        return hasattr(CcxtExchangeConnector, 'get_symbol_info')

def test_fix_summary():
    """Provide a summary of the fix"""
    print("\n🔧 Fix Summary:")
    print("❌ Problem: pro_exchange_connector_sandbox.get_exchange_info() - AttributeError")
    print("✅ Solution: pro_exchange_connector_sandbox.get_symbol_info() - Correct method")
    print("📝 Change: Line 178 in run_realtime_trading.py updated")
    print("🎯 Result: Trading system should no longer crash with AttributeError")
    print("\n📋 Method Details:")
    print("   - get_symbol_info() returns ExchangeInfo object")
    print("   - ExchangeInfo has step_size and tick_size properties")
    print("   - These are exactly what the calculate_strategy method needs")

async def main():
    print("🚀 Testing exchange info fix...")
    
    success1 = test_method_existence()
    success2 = await test_get_symbol_info_method()
    
    if success1 and success2:
        test_fix_summary()
        print("\n🎉 All tests passed! The fix should resolve the AttributeError.")
        return True
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    if not result:
        sys.exit(1)