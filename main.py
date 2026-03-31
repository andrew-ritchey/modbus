import json
import tkinter as tk
from tkinter import ttk, messagebox
import minimalmodbus
import serial


def connect(port='COM8', slave_address=240):
    instrument = minimalmodbus.Instrument(port, slave_address, debug=False)
    instrument.serial.baudrate = 38400
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_EVEN
    instrument.serial.stopbits = 1
    instrument.serial.timeout = 0.5
    instrument.mode = minimalmodbus.MODE_RTU
    instrument.clear_buffers_before_each_transaction = True
    return instrument


def query_register(instrument, register_id, entry_widget):
    try:
        value = instrument.read_register(register_id)
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, str(value))
    except Exception as exc:
        messagebox.showerror(
            title='Modbus Read Error',
            message=f'Error reading register {register_id}: {exc}'
        )


def update_register(instrument, register_id, entry_widget):
    try:
        text_value = entry_widget.get().strip()
        if text_value == '':
            raise ValueError('Input value cannot be empty')

        value = float(text_value)
        instrument.write_register(register_id, value)
        messagebox.showinfo(
            title='Modbus Write',
            message=f'Successfully wrote {value} to register {register_id}'
        )
    except Exception as exc:
        messagebox.showerror(
            title='Modbus Write Error',
            message=f'Error writing register {register_id}: {exc}'
        )


def build_ui(registers, instrument):
    root = tk.Tk()
    root.title('Modbus Client (Tkinter)')
    root.geometry('850x600')

    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill='both', expand=True)

    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        '<Configure>',
        lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    header_style = {'font': ('Arial', 10, 'bold')}
    ttk.Label(scrollable_frame, text='Description', **header_style).grid(row=0, column=0, padx=5, pady=5)
    ttk.Label(scrollable_frame, text='Register ID', **header_style).grid(row=0, column=1, padx=5, pady=5)
    ttk.Label(scrollable_frame, text='Value', **header_style).grid(row=0, column=2, padx=5, pady=5)
    ttk.Label(scrollable_frame, text='Actions', **header_style).grid(row=0, column=3, padx=5, pady=5)

    print(registers)
    for idx, item in enumerate(registers, start=1):
        register_id = item.get('register_id')
        desc = item.get('description', f'Register {register_id}')

        value_entry = ttk.Entry(scrollable_frame, width=20)

        ttk.Label(scrollable_frame, text=desc).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(scrollable_frame, text=str(register_id)).grid(row=idx, column=1, sticky='w', padx=5, pady=2)
        value_entry.grid(row=idx, column=2, padx=5, pady=2)

        action_frame = ttk.Frame(scrollable_frame)
        action_frame.grid(row=idx, column=3, padx=5, pady=2)

        query_btn = ttk.Button(
            action_frame,
            text='Query',
            command=lambda rid=register_id, entry=value_entry: query_register(instrument, rid, entry)
        )
        query_btn.pack(side='left', padx=(0, 4))
        
        if item.get('writable'):
            update_btn = ttk.Button(
                action_frame,
                text='Update',
                command=lambda rid=register_id, entry=value_entry: update_register(instrument, rid, entry)
            )
            update_btn.pack(side='left')

    root.mainloop()


def main(file_path='redlion_pxu_register.json'):
    try:
        with open(file_path, 'r') as f:
            registers = json.load(f)
    except Exception as exc:
        raise RuntimeError(f'Failed to load register file {file_path}: {exc}')

    instrument = connect(port='COM8', slave_address=240)
    build_ui(registers, instrument)


if __name__ == '__main__':
    register_file = 'redlion_pxu_register.json'
    main(register_file)
