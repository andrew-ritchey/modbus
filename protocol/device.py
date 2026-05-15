"""Represents a basic game character."""

from typing import Protocol


class Device(Protocol):
    """Basic representation of a device."""

    def connect(self) -> None:
        """I/O connection to device"""
        pass

    def query(self) -> None:
        """Send command to device"""
        pass
    
