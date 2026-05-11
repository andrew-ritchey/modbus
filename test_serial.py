import serial
import time

# Configuration (Update these to match your specific device and OS)
SERIAL_PORT = '/dev/tty.usbserial-BG03AAQB'  # Windows: 'COM3', Linux/Mac: '/dev/ttyUSB0'
BAUD_RATE = 19200

def send_serial_command():
    try:
        # 1. Initialize connection (pyserial defaults to 8N1)
        with serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2  # 2-second timeout for reading responses
        ) as ser:
            
            print(f"Successfully connected to {ser.name}...")
            ser.flush()
            ser.reset_output_buffer()
            command = "a\r\n" 
            ser.write(command.encode('ascii'))
            response = None
            while not response:
                response = ser.read_all().decode('ascii').strip()
                ser.reset_input_buffer()
                print(response)

    except serial.SerialException as e:
        print(f"Error communicating with the serial port: {e}")

if __name__ == "__main__":
    send_serial_command()