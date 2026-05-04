"""Schema loading and validation utilities."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from urllib.request import urlopen

logger = logging.getLogger(__name__)


class SchemaLoader:
    """Load and cache JSON schemas from local or remote locations."""

    def __init__(self, registry_url: str, cache_dir: Optional[Path] = None):
        """Initialize schema loader.

        Args:
            registry_url: Schema registry URL (file:// or http/https)
            cache_dir: Optional directory for caching downloaded schemas
        """
        self.registry_url = registry_url
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._schemas: Dict[str, Dict[str, Any]] = {}

        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_schema(self, schema_ref: str) -> Optional[Dict[str, Any]]:
        """Load schema by reference.

        Args:
            schema_ref: Schema reference (e.g., 'com.nats-poc.publisher/greeting/1.0')

        Returns:
            Parsed schema dict or None if not found
        """
        # Check cache first
        if schema_ref in self._schemas:
            return self._schemas[schema_ref]

        # Convert schema reference to path
        # com.nats-poc.publisher/greeting/1.0 -> com/nats-poc/publisher/greeting/1.0/schema.json
        parts = schema_ref.split("/")  # ['com.nats-poc.publisher', 'greeting', '1.0']
        if len(parts) >= 2:
            namespace_parts = parts[0].split(".")  # ['com', 'nats-poc', 'publisher']
            message_type = parts[1]  # 'greeting'
            version = parts[2] if len(parts) > 2 else "1.0"  # '1.0'

            # Build path: com/nats-poc/publisher/greeting/1.0/schema.json
            schema_path = "/".join(namespace_parts) + "/" + message_type + "/" + version + "/schema.json"
        else:
            schema_path = schema_ref.replace(".", "/") + "/schema.json"

        # Try to load from registry
        try:
            schema_data = self._fetch_schema(schema_path)
            if schema_data:
                self._schemas[schema_ref] = schema_data
                return schema_data
        except Exception as e:
            logger.error(f"Failed to load schema {schema_ref}: {e}")

        return None

    def _fetch_schema(self, schema_path: str) -> Optional[Dict[str, Any]]:
        """Fetch schema from registry.

        Args:
            schema_path: Path to schema relative to registry

        Returns:
            Parsed schema dict or None
        """
        # Check cache first
        if self.cache_dir:
            cache_file = self.cache_dir / schema_path.replace("/", "_")
            if cache_file.exists():
                try:
                    return json.loads(cache_file.read_text())
                except Exception as e:
                    logger.warning(f"Failed to load cached schema: {e}")

        # Construct full URL/path
        if self.registry_url.startswith("file://"):
            return self._fetch_local(schema_path)
        else:
            return self._fetch_remote(schema_path)

    def _fetch_local(self, schema_path: str) -> Optional[Dict[str, Any]]:
        """Fetch schema from local file system.

        Args:
            schema_path: Path to schema file

        Returns:
            Parsed schema dict or None
        """
        # Remove file:// prefix and construct path
        base_path = self.registry_url[7:]  # Remove 'file://'
        full_path = Path(base_path) / schema_path

        logger.debug(f"Loading schema from {full_path}")

        try:
            if full_path.exists():
                schema_data = json.loads(full_path.read_text())
                self._cache_schema(schema_path, schema_data)
                return schema_data
            else:
                logger.warning(f"Schema file not found: {full_path}")
                return None
        except Exception as e:
            logger.error(f"Error reading schema file {full_path}: {e}")
            return None

    def _fetch_remote(self, schema_path: str) -> Optional[Dict[str, Any]]:
        """Fetch schema from HTTP/HTTPS registry.

        Args:
            schema_path: Path to schema file

        Returns:
            Parsed schema dict or None
        """
        url = f"{self.registry_url}/{schema_path}".rstrip("/")

        logger.debug(f"Fetching schema from {url}")

        try:
            with urlopen(url) as response:
                schema_data = json.loads(response.read().decode("utf-8"))
                self._cache_schema(schema_path, schema_data)
                return schema_data
        except Exception as e:
            logger.error(f"Failed to fetch schema from {url}: {e}")
            return None

    def _cache_schema(self, schema_path: str, schema_data: Dict[str, Any]) -> None:
        """Cache schema locally.

        Args:
            schema_path: Path to schema
            schema_data: Schema data to cache
        """
        if not self.cache_dir:
            return

        try:
            cache_file = self.cache_dir / schema_path.replace("/", "_")
            cache_file.write_text(json.dumps(schema_data, indent=2))
        except Exception as e:
            logger.warning(f"Failed to cache schema: {e}")

    def validate_message(self, message: Dict[str, Any], schema_ref: str) -> bool:
        """Validate message against schema.

        Args:
            message: Message to validate
            schema_ref: Schema reference

        Returns:
            True if valid, False otherwise
        """
        try:
            import jsonschema
        except ImportError:
            logger.warning("jsonschema not installed, skipping validation")
            return True

        schema = self.load_schema(schema_ref)
        if not schema:
            logger.warning(f"Schema not found: {schema_ref}")
            return False

        try:
            jsonschema.validate(instance=message, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"Schema validation failed: {e.message}")
            return False
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
