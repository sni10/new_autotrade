import json
import os
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

# Default path to config.json inside this package
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", Path(__file__).resolve().parent / "config.json"))


def _camel_to_env(name: str) -> str:
    """Convert camelCase or PascalCase to ENV_VAR_STYLE"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.upper()


def _override_with_env(config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    for key, value in config.items():
        env_key = f"{prefix}_{_camel_to_env(key)}" if prefix else _camel_to_env(key)
        if isinstance(value, dict):
            config[key] = _override_with_env(value, env_key)
        else:
            env_val = os.getenv(env_key)
            if env_val is not None:
                if isinstance(value, bool):
                    config[key] = env_val.lower() in {"1", "true", "yes", "on"}
                elif isinstance(value, int):
                    config[key] = int(env_val)
                elif isinstance(value, float):
                    config[key] = float(env_val)
                else:
                    config[key] = env_val
    return config


def load_config() -> Dict[str, Any]:
    """Load configuration from JSON and override with environment variables."""
    load_dotenv()
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
    return _override_with_env(data)

