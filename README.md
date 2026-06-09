# User guide for Red Lion Modbus Interface

## Overview
This module contains a command line script for interrogating COMM port connections and a graphical user interface (GUI) for 
changing settings on a Red Lion PXU controller over Modbus RTU.

## Serial Settings
This program assumes the following serial communcation settings for any connected Red Lion PXU controller.
tyPE - rtU (Default)
bAUd - 9600 (Custom, Setting 2)
dAtA - 8 (Default, Setting 2)
PArb - no (Default, Setting 0)
Addr - 1 (Custom, -)

## Background
The codebase is written in python using the package manager UV.  To ensure the correct python environment is used, all python commands are preceeded with uv run.

## Commandline Tool (port_list.py)
port_list.py: List serial ports COMM address and USB location for connected serial devices

With no arguments, will list device details for all connected serial devices.
Optional arguments:
    '-l', '--location', help='LOCATION string to find port (returns device)'
    '-p', '--port', help='port device to find LOCATION (returns LOCATION)'

Example usage:
    uv run port_list.py -l 1-1.2 => COM2 (Lists comm port for the device connected to USB 1-1.2)
    uv run port_list.py -p COM5 => 1-4.1 (Lists the USB location for the device mapped to COM5)

## GUI Tool (main.py)
main.py: Modbus client GUI launcher

Required arguments:
    '-p', '--port', help='serial port device (e.g. COM3 or /dev/ttyUSB0)'

Optional arguments:
    '-a', '--address', help='Modbus device address (integer)'
        When provided, attempts to connect to a specific Modbus address.  Returns an exception if unable to connect to the provided port and address.  
        
        When omitted, attempts to conncet to each address on the provided COMM port, stopping at the first address where a successful connection is established.

    '-f', '--file', default='redlion_pxu_register.json', help='register JSON file'
        When provided, uses a custom JSON file to define the Modbus register mapping and GUI display.

        When omitted, uses the default JSON file.

## Important Settings/Notes

### PID Settings
The controller can be setup with up to 6 PID settings.  This is useful for tuning the PID parameters to specific set points, loadings, etc. that may affect the thermal behavior of the system.  

PID Set 1 - Auto Tuned at 500 C with an empty Swage reactor

### Ramped Heating/Cooling
1. Set the "Control Mode Transer (Auto/Manual)" to 1.
2. Set "Setpoint 1 (SP1)" to the target value.  (Note input 5000 for 500.0 C)
3. Set "PID parameter set selection" to the PID set that most closely matches the run conditions.
4. Set "SP Ramp Rate" to the target ramp rate.  (Note input 200 for 20.0 C/min)
5. Set "Control Mode Transfer (Auto/Manual)" to 0.
