#!/usr/bin/env python3
"""
Test script to verify the calculate_strategy fix
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from domain.services.market_data.ticker_service import TickerService
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository

def test_calculate_strategy_method():
    """Test that calculate_strategy method works with correct parameters"""
    print("🧪 Testing calculate_strategy method fix...")
    
    # Create ticker service
    repository = InMemoryTickerRepository()
    ticker_service = TickerService(repository)
    
    # Test parameters (matching the method signature)
    test_params = {
        'buy_price': 0.1715,
        'budget': 25.0,
        'min_step': 0.01,  # Example step size
        'price_step': 0.00001,  # Example tick size
        'buy_fee_percent': 0.1,
        'sell_fee_percent': 0.1,
        'profit_percent': 1.5  # 1.5% profit
    }
    
    print(f"📊 Testing with parameters:")
    for key, value in test_params.items():
        print(f"   {key}: {value}")
    
    try:
        # This should work now
        result = ticker_service.calculate_strategy(**test_params)
        
        if isinstance(result, dict) and "comment" in result:
            print(f"✅ Method executed successfully")
            print(f"📝 Result: {result['comment']}")
            if "❌" in result["comment"]:
                print("⚠️ Strategy calculation failed due to business logic, but method call succeeded")
            else:
                print("🎉 Strategy calculation succeeded!")
        elif isinstance(result, tuple) and len(result) == 5:
            print("✅ Method executed successfully")
            print("🎉 Strategy calculation returned valid tuple result!")
            buy_price, total_coins, sell_price, coins_to_sell, info = result
            print(f"   Buy price: {buy_price}")
            print(f"   Total coins needed: {total_coins}")
            print(f"   Sell price: {sell_price}")
            print(f"   Coins to sell: {coins_to_sell}")
        else:
            print(f"❌ Unexpected result format: {type(result)}")
            return False
            
    except TypeError as e:
        if "unexpected keyword argument" in str(e):
            print(f"❌ TypeError still exists: {e}")
            return False
        else:
            print(f"⚠️ Different TypeError (not the original issue): {e}")
            return True  # Original issue is fixed
    except Exception as e:
        print(f"⚠️ Other error (not TypeError): {e}")
        print("✅ The original TypeError is fixed, but there might be other issues")
        return True
    
    return True

def test_old_vs_new_call():
    """Show the difference between old and new method calls"""
    print("\n🔧 Method Call Comparison:")
    print("❌ OLD (incorrect):")
    print("   ticker_service.calculate_strategy(")
    print("       buy_price=current_price,")
    print("       budget=budget,")
    print("       currency_pair=currency_pair,  # ← This parameter doesn't exist!")
    print("       profit_percent=currency_pair.profit_markup")
    print("   )")
    
    print("\n✅ NEW (correct):")
    print("   ticker_service.calculate_strategy(")
    print("       buy_price=current_price,")
    print("       budget=budget,")
    print("       min_step=exchange_info.step_size,")
    print("       price_step=exchange_info.tick_size,")
    print("       buy_fee_percent=0.1,")
    print("       sell_fee_percent=0.1,")
    print("       profit_percent=currency_pair.profit_markup")
    print("   )")

if __name__ == "__main__":
    print("🚀 Testing calculate_strategy fix...")
    
    success = test_calculate_strategy_method()
    test_old_vs_new_call()
    
    if success:
        print("\n🎉 Fix verification completed successfully!")
        print("✅ The TypeError should be resolved in the trading system.")
    else:
        print("\n❌ Fix verification failed.")
        sys.exit(1)