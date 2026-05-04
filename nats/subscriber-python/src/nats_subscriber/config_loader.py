"""Configuration loading from YAML files."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml (or None to use default)

    Returns:
        Configuration dictionary
    """
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not installed, using default configuration")
        return get_default_config()

    # Determine config file path
    if config_path:
        config_file = Path(config_path)
    else:
        # Look for config.yaml in common locations
        candidates = [
            Path("config.yaml"),
            Path("../config.yaml"),
            Path("../../config.yaml"),
        ]
        config_file = None
        for candidate in candidates:
            if candidate.exists():
                config_file = candidate
                break

    if not config_file or not config_file.exists():
        logger.warning("Config file not found, using default configuration")
        return get_default_config()

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"Loaded configuration from {config_file}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config file {config_file}: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Get default configuration.

    Returns:
        Default configuration dictionary
    """
    return {
        "schemas": {
            "registry": "file://./schemas",
            "validate": True,
            "cache_enabled": True,
            "cache_dir": "./.schema_cache",
        },
        "broker": {
            "nats_server": "localhost:4222",
            "input_topic": "pipeline.message.input",
            "output_topic": "pipeline.message.output",
        },
        "message_dir": "/tmp/nats-poc-messages",
        "publisher": {
            "producer": "com.nats-poc.publisher/1.0",
            "message_type": "greeting",
            "schema": "com.nats-poc.publisher/greeting/1.0",
            "timeout": 10,
        },
        "subscriber": {
            "producer": "com.nats-poc.subscriber/1.0",
            "response_schema": "com.nats-poc.subscriber/response/1.0",
            "poll_interval": 0.5,
        },
        "logging": {
            "level": "INFO",
            "format": "[%(levelname)s] %(message)s",
        },
    }


def merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge override config into base config.

    Args:
        base: Base configuration
        override: Override configuration

    Returns:
        Merged configuration
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value

    return result
