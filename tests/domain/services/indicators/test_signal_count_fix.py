#!/usr/bin/env python3
"""
Test script to verify signal count after fixing naming mismatch
"""
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from domain.services.indicators.indicator_calculator_service import IndicatorCalculatorService
from domain.entities.ticker import Ticker
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository
from infrastructure.repositories.indicators_repository import InMemoryIndicatorsRepository
from domain.services.market_data.ticker_service import TickerService

async def test_signal_generation():
    """Test signal generation and count"""
    print("🧪 Testing signal generation...")
    
    # Create test data
    repository = InMemoryTickerRepository()
    indicators_repo = InMemoryIndicatorsRepository()
    ticker_service = TickerService(repository, indicators_repo)
    
    # Generate some test price data
    test_prices = [0.33 + i * 0.001 for i in range(100)]  # 100 price points
    
    # Create test ticker data
    for i, price in enumerate(test_prices):
        ticker_data = {
            'symbol': 'MAGICUSDT',
            'close': str(price),
            'open': str(price - 0.0001),
            'high': str(price + 0.0002),
            'low': str(price - 0.0002),
            'volume': '1000',
            'timestamp': 1000000 + i
        }
        
        # Process ticker
        await ticker_service.process_ticker(ticker_data)
    
    # Check the last ticker's signals
    if repository.tickers:
        last_ticker = repository.tickers[-1]
        if last_ticker.signals:
            print(f"📊 Signal count: {len(last_ticker.signals)}")
            print("📈 Generated signals:")
            for key, value in last_ticker.signals.items():
                print(f"   {key}: {value}")
            
            # Test if the fixed naming works
            hist = last_ticker.signals.get('macdhist', 0)
            macd = last_ticker.signals.get('macd', 0)
            signal = last_ticker.signals.get('macdsignal', 0)
            
            print(f"\n🔍 MACD values after fix:")
            print(f"   MACD: {macd}")
            print(f"   Signal: {signal}")
            print(f"   Histogram: {hist}")
            
            if hist != 0 and signal != 0:
                print("✅ Naming fix successful - MACD values are accessible!")
            else:
                print("❌ Naming fix failed - MACD values still not accessible")
        else:
            print("❌ No signals generated")
    else:
        print("❌ No tickers in repository")

if __name__ == "__main__":
    asyncio.run(test_signal_generation())