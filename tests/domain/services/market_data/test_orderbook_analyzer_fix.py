#!/usr/bin/env python3
"""
Test script to verify orderbook analyzer fix
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from domain.entities.order_book import OrderBook
from domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer

def test_orderbook_analyzer_fix():
    """Test that orderbook analyzer works with both OrderBook objects and dictionaries"""
    print("🧪 Testing OrderBook analyzer fix...")
    
    # Create analyzer
    config = {
        'min_volume_threshold': 1000,
        'big_wall_threshold': 5000,
        'max_spread_percent': 0.3,
        'min_liquidity_depth': 15,
        'typical_order_size': 10
    }
    analyzer = OrderBookAnalyzer(config)
    
    # Test data
    test_bids = [[0.33200, 1000], [0.33190, 1500], [0.33180, 2000]]
    test_asks = [[0.33210, 1200], [0.33220, 1800], [0.33230, 2500]]
    
    # Test 1: OrderBook object
    print("\n📊 Test 1: OrderBook object")
    try:
        orderbook_obj = OrderBook(
            symbol="MAGICUSDT",
            timestamp=1000000,
            bids=test_bids,
            asks=test_asks
        )
        
        metrics = analyzer.analyze_orderbook(orderbook_obj)
        print(f"✅ OrderBook object test passed")
        print(f"   Signal: {metrics.signal}")
        print(f"   Confidence: {metrics.confidence}")
        print(f"   Spread: {metrics.bid_ask_spread:.4f}%")
        
    except Exception as e:
        print(f"❌ OrderBook object test failed: {e}")
        return False
    
    # Test 2: Dictionary format
    print("\n📊 Test 2: Dictionary format")
    try:
        orderbook_dict = {
            'symbol': 'MAGICUSDT',
            'timestamp': 1000000,
            'bids': test_bids,
            'asks': test_asks
        }
        
        metrics = analyzer.analyze_orderbook(orderbook_dict)
        print(f"✅ Dictionary format test passed")
        print(f"   Signal: {metrics.signal}")
        print(f"   Confidence: {metrics.confidence}")
        print(f"   Spread: {metrics.bid_ask_spread:.4f}%")
        
    except Exception as e:
        print(f"❌ Dictionary format test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! The fix works correctly.")
    return True

if __name__ == "__main__":
    test_orderbook_analyzer_fix()