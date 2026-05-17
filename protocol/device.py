"""Represents a basic game character."""

from typing import Protocol
from dataclasses import dataclass

@dataclass
class Device(Protocol):
    """Basic representation of a device."""
    name: str

    def connect(self) -> None:
        """I/O connection to device"""
        pass

    def query(self) -> None:
        """Send command to device"""
        pass

    def ping(self) -> None:
        """Confirm the device has been created"""
        print(f"Successfully created {self.name}")
    
