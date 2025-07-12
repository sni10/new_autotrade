import json
from src.config.config_loader import load_config


def test_load_config_with_env_override(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_data = {"trading": {"orderbook_confidence_threshold": 0.5}}
    config_path.write_text(json.dumps(config_data))

    monkeypatch.setenv("CONFIG_PATH", str(config_path))

    config = load_config()
    assert config["trading"]["orderbook_confidence_threshold"] == 0.6


