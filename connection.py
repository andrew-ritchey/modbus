import json
import minimalmodbus
import serial
from typing import Any


def connect(port: str, address: int, settings: str | dict[str, Any] | None = None) -> minimalmodbus.Instrument:
    instrument = minimalmodbus.Instrument(port, address, debug=True)
    if settings:
        # Handle both file paths (string) and dictionaries
        settings_dict: dict[str, Any]
        if isinstance(settings, str):
            try:
                with open(settings, 'r') as f:
                    settings_dict = json.load(f)
            except Exception as exc:
                raise RuntimeError(f'Failed to load settings file {settings}: {exc}')
        elif isinstance(settings, dict):
            settings_dict = settings
        else:
            raise RuntimeError(f'Settings must be a file path (str) or dict, got {type(settings)}')
        
        # Ensure serial attribute exists and set properties
        if instrument.serial:
            instrument.serial.baudrate = settings_dict.get('baudrate', 9600)
            instrument.serial.bytesize = settings_dict.get('bytesize', 8)
            instrument.serial.parity = getattr(serial, settings_dict.get("parity", "PARITY_NONE"))
            instrument.serial.stopbits = settings_dict.get('stopbits', 1)
            instrument.serial.timeout = settings_dict.get('timeout', 0.5)
        
        instrument.mode = getattr(minimalmodbus, settings_dict.get("mode", "MODE_RTU"))
        instrument.clear_buffers_before_each_transaction = settings_dict.get('clearbuffers', True)
    return instrument


def query_register(instrument: minimalmodbus.Instrument, register_id: int) -> tuple[int, Any]:
    """Read a register value.

    Returns a tuple (code, payload).
    - On success: (0, value)
    - On error: (1, error_message)
    """
    try:
        value = instrument.read_register(register_id)
        return 0, value
    except Exception as exc:
        return 1, str(exc)


def update_register(instrument: minimalmodbus.Instrument, register_id: int, value: float) -> tuple[int, None | str]:
    """Write a numeric value to a register.

    `value` should be a number (int or float).

    Returns a tuple (code, payload).
    - On success: (0, None)
    - On error: (1, error_message)
    """
    try:
        # Expect caller to validate/convert input to a numeric value
        instrument.write_register(register_id, value)
        return 0, None
    except Exception as exc:
        return 1, str(exc)
