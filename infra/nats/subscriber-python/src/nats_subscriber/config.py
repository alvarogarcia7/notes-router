"""Configuration module for NATS Subscriber."""

import os
from pathlib import Path
from typing import Any, Dict

from nats_subscriber.config_loader import get_default_config, load_config, merge_config


class Config:
    """Application configuration."""

    def __init__(self, config_dict: Dict[str, Any] = None):
        """Initialize configuration.

        Args:
            config_dict: Configuration dictionary (loaded from YAML or defaults)
        """
        if config_dict is None:
            config_dict = {}

        # Load base config from YAML
        base_config = load_config()

        # Merge with provided config
        if config_dict:
            self.config = merge_config(base_config, config_dict)
        else:
            self.config = base_config

        # Allow environment variables to override
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        if "NATS_SERVER" in os.environ:
            self.config["broker"]["nats_server"] = os.environ["NATS_SERVER"]
        if "MESSAGE_DIR" in os.environ:
            self.config["message_dir"] = os.environ["MESSAGE_DIR"]
        if "POLL_INTERVAL" in os.environ:
            self.config["subscriber"]["poll_interval"] = float(os.environ["POLL_INTERVAL"])
        if "LOG_LEVEL" in os.environ:
            self.config["logging"]["level"] = os.environ["LOG_LEVEL"]

    # NATS Configuration
    @property
    def NATS_SERVER(self) -> str:
        """Get NATS server address."""
        return self.config["broker"]["nats_server"]

    @property
    def INPUT_TOPIC(self) -> str:
        """Get input topic."""
        return self.config["broker"]["input_topic"]

    @property
    def OUTPUT_TOPIC(self) -> str:
        """Get output topic."""
        return self.config["broker"]["output_topic"]

    # Message Directory
    @property
    def MESSAGE_DIR(self) -> Path:
        """Get message directory."""
        return Path(self.config["message_dir"])

    @property
    def COUNTER_FILE(self) -> Path:
        """Get counter file path."""
        return self.MESSAGE_DIR / ".message_counter"

    # Polling Configuration
    @property
    def POLL_INTERVAL(self) -> float:
        """Get polling interval."""
        return self.config["subscriber"]["poll_interval"]

    @property
    def CHECK_INTERVAL(self) -> float:
        """Get check interval."""
        return 0.1  # Fixed value

    # Logging
    @property
    def LOG_LEVEL(self) -> str:
        """Get log level."""
        return self.config["logging"]["level"]

    @property
    def LOG_FORMAT(self) -> str:
        """Get log format."""
        return self.config["logging"]["format"]

    # Schema Configuration
    @property
    def SCHEMA_REGISTRY(self) -> str:
        """Get schema registry URL."""
        return self.config["schemas"]["registry"]

    @property
    def SCHEMA_VALIDATION(self) -> bool:
        """Get schema validation enabled flag."""
        return self.config["schemas"]["validate"]

    @property
    def SCHEMA_CACHE_DIR(self) -> Path:
        """Get schema cache directory."""
        return Path(self.config["schemas"]["cache_dir"])


_config_instance = None


def get_config(config_dict: Dict[str, Any] = None) -> Config:
    """Get application configuration.

    Args:
        config_dict: Optional config dictionary to use

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_dict)
    return _config_instance
