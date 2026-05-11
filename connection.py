import json
import minimalmodbus
import serial
from typing import Any


def connect(
    port: str,
    address: int,
    settings: str | dict[str, Any] | None = None,
) -> minimalmodbus.Instrument:
    """Open a Modbus RTU/ASCII instrument on *port* at slave *address*.

    *settings* may be:
    - a file path (str) pointing to a JSON object, or
    - a plain dict.

    Recognised keys (all optional, defaults shown):
        baudrate      int   9600
        bytesize      int   8
        parity        str   "PARITY_NONE"   (serial.PARITY_* constant name)
        stopbits      int   1
        timeout       float 0.5
        mode          str   "MODE_RTU"      (minimalmodbus.MODE_* constant name)
        clearbuffers  bool  True
    """
    instrument = minimalmodbus.Instrument(port, address, debug=True)
    if settings:
        settings_dict: dict[str, Any]
        if isinstance(settings, str):
            try:
                with open(settings, 'r') as f:
                    settings_dict = json.load(f)
            except Exception as exc:
                raise RuntimeError(
                    f'Failed to load settings file {settings}: {exc}'
                ) from exc
        elif isinstance(settings, dict):
            settings_dict = settings
        else:
            raise TypeError(
                f'settings must be a file path (str) or dict, got {type(settings)}'
            )

        if instrument.serial:
            instrument.serial.baudrate = settings_dict.get('baudrate', 9600)
            instrument.serial.bytesize = settings_dict.get('bytesize', 8)
            instrument.serial.parity = getattr(
                serial, settings_dict.get('parity', 'PARITY_NONE')
            )
            instrument.serial.stopbits = settings_dict.get('stopbits', 1)
            instrument.serial.timeout = settings_dict.get('timeout', 0.5)

        instrument.mode = getattr(
            minimalmodbus, settings_dict.get('mode', 'MODE_RTU')
        )
        instrument.clear_buffers_before_each_transaction = settings_dict.get(
            'clearbuffers', True
        )
    return instrument


def query_register(
    instrument: minimalmodbus.Instrument,
    register_id: int,
) -> tuple[int, Any]:
    """Read a holding register.

    Returns ``(0, value)`` on success or ``(1, error_message)`` on failure.
    The raw integer value is returned unchanged; any scaling (e.g. ÷10) is
    the caller's responsibility.
    """
    try:
        value = instrument.read_register(register_id)
        return 0, value
    except Exception as exc:
        return 1, str(exc)


def update_register(
    instrument: minimalmodbus.Instrument,
    register_id: int,
    value: int,
) -> tuple[int, None | str]:
    """Write an integer value to a holding register.

    *value* must already be scaled to the controller's fixed-point
    representation before calling this function (e.g. pass ``int(celsius * 10)``
    for a controller that stores tenths of a degree).

    Returns ``(0, None)`` on success or ``(1, error_message)`` on failure.
    """
    try:
        instrument.write_register(register_id, int(value))
        return 0, None
    except Exception as exc:
        return 1, str(exc)
