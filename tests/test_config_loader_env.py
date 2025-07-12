import json
import os
from pathlib import Path

from config.config_loader import load_config
from dotenv import load_dotenv


def test_load_config_with_env_override(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_data = {"trading": {"orderbook_confidence_threshold": 0.5}}
    config_path.write_text(json.dumps(config_data))

    env_file = tmp_path / ".env"
    env_file.write_text("TRADING_ORDERBOOK_CONFIDENCE_THRESHOLD=0.9\n")

    monkeypatch.chdir(tmp_path)
    load_dotenv(env_file)
    monkeypatch.setenv("CONFIG_PATH", str(config_path))

    config = load_config()
    assert config["trading"]["orderbook_confidence_threshold"] == 0.9


