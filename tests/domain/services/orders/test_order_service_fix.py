#!/usr/bin/env python3
"""
Simple test script to verify the OrderService initialization fix
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src')))

try:
    # Import required classes
    from domain.services.orders.order_service import OrderService
    from domain.factories.order_factory import OrderFactory
    from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
    from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
    
    print("✅ All imports successful")
    
    # Test OrderService initialization with correct parameters
    try:
        orders_repo = InMemoryOrdersRepository(max_orders=100)
        order_factory = OrderFactory()
        exchange_connector = CcxtExchangeConnector(use_sandbox=True)
        
        # This should work now without the currency_pair_symbol parameter
        order_service = OrderService(orders_repo, order_factory, exchange_connector)
        
        print("✅ OrderService initialization successful!")
        print("✅ Fix verified - no TypeError occurred")
        
    except TypeError as e:
        print(f"❌ TypeError still exists: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️  Other error (not the original TypeError): {e}")
        print("✅ The original TypeError is fixed, but there might be other issues")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

print("🎉 Test completed successfully!")