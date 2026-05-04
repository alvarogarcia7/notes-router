"""NATS Subscriber - Message processing application."""

__version__ = "0.1.0"
__author__ = "NATS PoC Team"

from nats_subscriber.subscriber import Subscriber
from nats_subscriber.nats_client import NATSClient

__all__ = ["Subscriber", "NATSClient"]
