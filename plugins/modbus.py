"""Game extension that adds a bard character."""

from dataclasses import dataclass

import minimalmodbus

from protocol import factory


@dataclass
class Modbus(minimalmodbus.Instrument):

    name: str
    port: str
    address: int
    baudrate: int
    bytesize: int
    parity: str
    stopbits: int
    timeout: float
    mode: str
    clearbuffers: bool

    def connect(self) -> None:
        """I/O connection to device"""
        minimalmodbus.Instrument.__init__(self, self.port, self.address)
        self.serial.baudrate = self.baudrate
        self.serial.bytesize = self.bytesize
        self.serial.parity = getattr(minimalmodbus.serial, self.parity)
        self.serial.stopbits = self.stopbits
        self.serial.timeout = self.timeout
        self.mode = getattr(minimalmodbus, self.mode)
        self.clear_buffers_before_each_transaction = self.clearbuffers

    def query(self, registeraddress: int, number_of_decimals: int, value: int | float | None = None) -> tuple[int, str, int | float | None]:
        """Send command to device"""
        if value is not None:
            try:
                self.write_register(registeraddress, number_of_decimals, value)
                return 0, f"Write successful. Instrument: {self.name}, Register: {registeraddress}, Value: {value}", None
            except IOError:
                return 1, f"Write failed. Instrument: {self.name}, Register: {registeraddress}, Value: {value}", None
        try:
            value = self.read_register(registeraddress, number_of_decimals)
            return 0, f"Read successful. Instrument: {self.name}, Register: {registeraddress}, Value: {value}", value
        except IOError:
            return 1, f"Read failed. Instrument: {self.name}, Register: {registeraddress}, Value: {value}", None


def register() -> None:
    factory.register("modbus", Modbus)
