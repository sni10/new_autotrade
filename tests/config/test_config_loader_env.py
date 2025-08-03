import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from config.config_loader import load_config


def test_load_config_with_env_override():
    """Test that environment variables override config.json values"""
    config = load_config()
    
    # Should get 0.6 from .env file (TRADING_ORDERBOOK_CONFIDENCE_THRESHOLD=0.6)
    # instead of config.json value
    assert config["trading"]["orderbook_confidence_threshold"] == 0.6


