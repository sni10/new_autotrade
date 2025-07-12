import json
import os
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

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
    # Load .env from the current directory, overriding existing env vars.
    load_dotenv(override=True)

    # Get config path from env, with a fallback to the default location.
    config_path_str = os.getenv("CONFIG_PATH", str(Path(__file__).resolve().parent / "config.json"))
    config_path = Path(config_path_str)

    with open(config_path, "r") as f:
        data = json.load(f)
    return _override_with_env(data)