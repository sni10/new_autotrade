from src.config.config_loader import load_config


def test_load_config_with_env_override():
    """Test that environment variables override config.json values"""
    config = load_config()
    
    # Should get 0.6 from .env file (TRADING_ORDERBOOK_CONFIDENCE_THRESHOLD=0.6)
    # instead of config.json value
    assert config["trading"]["orderbook_confidence_threshold"] == 0.6


