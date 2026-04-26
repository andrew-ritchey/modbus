import minimalmodbus
import serial

def connect(port, address):
    instrument = minimalmodbus.Instrument(port, address, debug=False)
    instrument.serial.baudrate = 9600 # 38400 # 
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE # serial.PARITY_EVEN # 
    instrument.serial.stopbits = 1
    instrument.serial.timeout = 0.5
    instrument.mode = minimalmodbus.MODE_RTU
    instrument.clear_buffers_before_each_transaction = True
    return instrument


def query_register(instrument, register_id):
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


def update_register(instrument, register_id, entry_widget):
    """Write a numeric value to a register.

    `value` should be a number (int or float).

    Returns a tuple (code, payload).
    - On success: (0, None)
    - On error: (1, error_message)
    """
    try:
        # Expect caller to validate/convert input to a numeric value
        instrument.write_register(register_id, entry_widget)
        return 0, None
    except Exception as exc:
        return 1, str(exc)
