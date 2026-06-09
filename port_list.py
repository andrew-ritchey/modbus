import serial.tools.list_ports
import re
import argparse
from typing import Optional


def extract_location(hwid: str) -> Optional[str]:
    """Extract the text after 'LOCATION=' from an HWID string.

    Returns the matched value or None if not present.
    Examples it will match: LOCATION=1-1:1.0, LOCATION=0001, LOCATION=1
    """
    if not hwid:
        return None
    # Prefer a match that stops at common separators (space, semicolon, comma)
    m = re.search(r'LOCATION=([^;,\s]+)', hwid, re.IGNORECASE)
    if m:
        return m.group(1)
    # Fallback: capture until end of string
    m = re.search(r'LOCATION=(.+)$', hwid, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def find_port_by_location(location: str) -> Optional[str]:
    """Return the serial port device whose HWID contains the given LOCATION.

    Matching is case-insensitive and requires an exact LOCATION match.
    Returns the port device string (e.g. 'COM3' or '/dev/ttyUSB0') or `None`.
    """
    if not location:
        return None
    for port in serial.tools.list_ports.comports():
        loc = extract_location(port.hwid)
        if loc and loc.lower() == location.lower():
            return port.device
    return None

def find_location_by_port(port: str) -> Optional[str]:
    """Return the LOCATION value from the HWID of the given serial port device.

    Matching is case-insensitive. Returns the LOCATION string or `None`.
    """
    if not port:
        return None
    for p in serial.tools.list_ports.comports():
        if p.device.lower() == port.lower():
            return extract_location(p.hwid)
    return None


def details():
    ports = serial.tools.list_ports.comports()

    for port in ports:
        print(f"Device: {port.device}")
        print(f"Description: {port.description}")
        print(f"HWID: {port.hwid}")
        print("-" * 40)


def main():
    parser = argparse.ArgumentParser(
        description='List serial ports COMM address and USB location for connected serial devices'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l', '--location', help='LOCATION string to find port (returns device)')
    group.add_argument('-p', '--port', help='port device to find LOCATION (returns LOCATION)')

    args = parser.parse_args()

    if args.location:
        device = find_port_by_location(args.location)
        if device:
            print(device)
        else:
            print(f"No port found for LOCATION={args.location}")
        return

    if args.port:
        loc = find_location_by_port(args.port)
        if loc:
            print(loc)
        else:
            print(f"No LOCATION found for port {args.port}")
        return

    details()


if __name__ == '__main__':
    main()