"""Reusable async NATS client with connection retry."""

import asyncio
import ssl
import sys
import nats


class NATSClient:
    """Async NATS client with built-in retry on connect."""

    def __init__(
        self,
        url: str,
        max_attempts: int = 5,
        retry_interval: float = 1.0,
        connect_timeout: int = 2,
        tls: ssl.SSLContext | None = None,
    ):
        self.url = url
        self.max_attempts = max_attempts
        self.retry_interval = retry_interval
        self.connect_timeout = connect_timeout
        self.tls = tls
        self._nc = None

    async def connect(self) -> None:
        """Connect to NATS with retry logic."""
        for attempt in range(self.max_attempts):
            try:
                self._nc = await nats.connect(
                    self.url, tls=self.tls, connect_timeout=self.connect_timeout
                )
                return
            except Exception as e:
                if attempt < self.max_attempts - 1:
                    print(
                        f"Connection attempt {attempt + 1}/{self.max_attempts} failed, "
                        f"retrying in {self.retry_interval}s..."
                    )
                    await asyncio.sleep(self.retry_interval)
                else:
                    print(
                        f"Error: Could not connect to NATS at {self.url} "
                        f"after {self.max_attempts} attempts"
                    )
                    print(f"Make sure NATS server is running: {e}")
                    sys.exit(1)

    async def publish(self, topic: str, data: bytes) -> None:
        """Publish bytes to a topic."""
        await self._nc.publish(topic, data)

    async def subscribe(self, topic: str, cb) -> None:
        """Subscribe to a topic with a callback."""
        await self._nc.subscribe(topic, cb=cb)

    async def close(self) -> None:
        """Close the connection."""
        if self._nc:
            await self._nc.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *_):
        await self.close()
