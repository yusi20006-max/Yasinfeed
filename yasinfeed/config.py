import os
import yaml
import logging

DEFAULT_CONFIG = {
    "app": {
        "name": "YasinFeed",
        "env": "production",
    },
    "logging": {
        "level": "INFO",
        "file_path": "yasinfeed.log",
        "console": True,
    },
    "api": {
        "host": "127.0.0.1",
        "port": 8000,
    },
    "fetch": {
        "interval_seconds": 300,
    },
    "rewrite": {
        "provider": "dummy",
    },
    "storage": {
        "type": "sqlite",
        "path": "data/yasinfeed.db",
    },
    "scheduler": {
        "enabled": True,
    },
    "publisher": {
        "eitaa": {
            "enabled": False,
        },
        "pwa": {
            "enabled": False,
        },
        "rss": {
            "enabled": False,
        }
    },
    "models": {
        "provider": "dummy",
    }
}


def cast_value(val, default_val):
    """Cast a string value to the same type as default_val."""
    if default_val is None:
        if isinstance(val, str):
            val_lower = val.lower()
            if val_lower in ("true", "yes", "on"):
                return True
            if val_lower in ("false", "no", "off"):
                return False
            try:
                return int(val)
            except ValueError:
                pass
            try:
                return float(val)
            except ValueError:
                pass
        return val
    if isinstance(default_val, bool):
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes", "on")
        return bool(val)
    if isinstance(default_val, int):
        try:
            return int(val)
        except ValueError:
            return default_val
    if isinstance(default_val, float):
        try:
            return float(val)
        except ValueError:
            return default_val
    return val


def merge_dicts(source, destination):
    """Recursively merges source dict into destination dict."""
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            if isinstance(node, dict):
                merge_dicts(value, node)
            else:
                destination[key] = value
        else:
            destination[key] = value
    return destination


def override_from_env(config, prefix="YASINFEED_"):
    """
    Override configuration values from environment variables.
    Supports both nested overrides via double underscores (e.g., YASINFEED__API__PORT)
    and standard environment variables as fallbacks.
    """
    for env_key, env_val in list(os.environ.items()):
        if not env_key.startswith(prefix):
            continue

        # Strip prefix and strip leading underscores (e.g. YASINFEED__API__PORT becomes API__PORT)
        key_part = env_key[len(prefix):].lstrip("_")
        if not key_part:
            continue

        # Handle specific common direct overrides first for convenience
        direct_mappings = {
            "LOG_LEVEL": ("logging", "level"),
            "PORT": ("api", "port"),
            "HOST": ("api", "host"),
            "ENV": ("app", "env"),
        }

        if key_part in direct_mappings:
            path = direct_mappings[key_part]
            # Navigate to the parent dict
            curr = config
            for step in path[:-1]:
                curr = curr.setdefault(step, {})
            last_key = path[-1]
            curr[last_key] = cast_value(env_val, curr.get(last_key))
            continue

        # Nested keys e.g. YASINFEED__API__PORT -> ["API", "PORT"]
        parts = [p.lower() for p in key_part.split("__") if p]
        if not parts:
            continue

        # Traverse config dict
        curr = config
        found = True
        for i, part in enumerate(parts[:-1]):
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                # If path doesn't exist, we can optionally create it,
                # but to be safe and avoid polluting with random env vars,
                # we only traverse if the key existed or if we decide to allow dynamic keys.
                # Let's create it if it doesn't exist but only for dict structure.
                if isinstance(curr, dict):
                    curr = curr.setdefault(part, {})
                else:
                    found = False
                    break

        if found and isinstance(curr, dict):
            last_key = parts[-1]
            default_v = curr.get(last_key)
            curr[last_key] = cast_value(env_val, default_v)


def load_config(config_path=None) -> dict:
    """
    Loads configuration.
    Path resolution priority:
    1. config_path argument
    2. YASINFEED_CONFIG_PATH env variable
    3. config/config.yaml (default location)

    If no config file is found, falls back to safe default values.
    """
    if not config_path:
        config_path = os.environ.get("YASINFEED_CONFIG_PATH", "config/config.yaml")

    config = {}
    # Start with deep copy of DEFAULT_CONFIG
    import copy
    merged_config = copy.deepcopy(DEFAULT_CONFIG)

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_yaml = yaml.safe_load(f)
                if isinstance(loaded_yaml, dict):
                    merge_dicts(loaded_yaml, merged_config)
        except Exception as e:
            # We don't want to crash on configuration loading if possible,
            # but we should print or log it. Since logging might not be initialized yet,
            # we can print to stderr.
            import sys
            print(f"Warning: Failed to load config from {config_path}: {e}", file=sys.stderr)
    else:
        # File doesn't exist. It is a safe default mode.
        pass

    # Override with environment variables
    override_from_env(merged_config)

    return merged_config
