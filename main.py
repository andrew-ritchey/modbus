import json
import argparse
import tkinter as tk
from tkinter import ttk, messagebox

import connection as conn
import threading
import time
from typing import Any

def build_ui(devices_config: dict[str, Any]):
    root = tk.Tk()
    root.title('Modbus Client (Tkinter)')
    root.geometry('1400x600')

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

    # Connect to all devices
    instruments: dict[str, Any] = {}
    for device_key, device_config in devices_config.items():
        try:
            address = device_config.get('address')
            port = device_config.get('port', '/dev/ttyUSB0')  # Default port
            settings_dict = {k: v for k, v in device_config.items() if k not in ['name', 'register', 'address', 'port']}
            instruments[device_key] = conn.connect(port=port, address=address, settings=settings_dict)
        except Exception as e:
            messagebox.showerror('Connection Error', f"Failed to connect to device {device_key}: {e}")
            instruments[device_key] = None

    # Top controls: Auto-Query checkbox and Rate input (Hz)
    controls_frame = ttk.Frame(scrollable_frame)
    controls_frame.grid(row=0, column=0, columnspan=len(devices_config), sticky='ew', padx=5, pady=(0, 8))

    controls_inner = ttk.Frame(controls_frame)
    controls_inner.pack(anchor='center')

    auto_query_var = tk.BooleanVar(value=False)
    auto_query_chk = ttk.Checkbutton(controls_inner, text='Auto-Query', variable=auto_query_var)
    auto_query_chk.pack(side='left', padx=(0, 12))

    ttk.Label(controls_inner, text='Rate (Hz):').pack(side='left')

    def validate_float(p):
        if p == '':
            return True
        try:
            float(p)
            return True
        except Exception:
            return False

    vcmd = controls_inner.register(validate_float)
    rate_entry = ttk.Entry(controls_inner, width=10, validate='key', validatecommand=(vcmd, '%P'))
    rate_entry.pack(side='left', padx=(4, 0))
    rate_entry.insert(0, '1')

    def do_query(device_key: str, rid: int, label_widget: ttk.Label):
        instrument = instruments.get(device_key)
        if instrument is None:
            messagebox.showerror('Connection Error', f'Not connected to device {device_key}')
            return
        code, payload = conn.query_register(instrument, rid)
        if code == 0:
            label_widget.config(text=str(payload))
        else:
            messagebox.showerror(
                title='Modbus Read Error',
                message=f'Error reading register {rid}: {payload}'
            )

    def do_update(device_key: str, rid: int, entry_widget: ttk.Entry):
        instrument = instruments.get(device_key)
        if instrument is None:
            messagebox.showerror('Connection Error', f'Not connected to device {device_key}')
            return
        text_value = entry_widget.get().strip()
        if text_value == '':
            messagebox.showerror(
                title='Modbus Write Error',
                message='Input value cannot be empty'
            )
            return
        try:
            value = float(text_value)
        except ValueError:
            messagebox.showerror(
                title='Modbus Write Error',
                message='Input value must be numeric'
            )
            return

        code, payload = conn.update_register(instrument, rid, value)
        if code == 0:
            messagebox.showinfo(
                title='Modbus Write',
                message=f'Successfully wrote {value} to register {rid}'
            )
        else:
            messagebox.showerror(
                title='Modbus Write Error',
                message=f'Error writing register {rid}: {payload}'
            )


    # keep list of entries and labels for auto-query
    entries_list: list[tuple[str, int, ttk.Entry]] = []
    labels_list: list[tuple[str, int, ttk.Label]] = []

    header_font = ('Arial', 10, 'bold')
    device_column_offset = 0

    for device_key, device_config in devices_config.items():
        device_name = device_config.get('name', device_key)
        registers = device_config.get('register', [])

        # Device name header (spans multiple columns for this device)
        tk.Label(scrollable_frame, text=device_name, font=header_font).grid(
            row=1, column=device_column_offset, columnspan=4, padx=5, pady=5, sticky='n'
        )

        # Create widgets for each register
        for row_idx, item in enumerate(registers, start=2):
            register_id = item.get('register_id')
            desc = item.get('description', f'Register {register_id}')

            # editable entry for manual updates
            value_entry = ttk.Entry(scrollable_frame, width=12)

            # label to display read/query results (auto-updated)
            read_label = ttk.Label(scrollable_frame, text='-', width=10)

            entries_list.append((device_key, register_id, value_entry))
            labels_list.append((device_key, register_id, read_label))

            # Description column
            ttk.Label(scrollable_frame, text=desc, width=20).grid(
                row=row_idx, column=device_column_offset, sticky='w', padx=2, pady=2
            )

            # Read value column
            read_label.grid(row=row_idx, column=device_column_offset + 1, padx=2, pady=2)

            # Entry column
            value_entry.grid(row=row_idx, column=device_column_offset + 2, padx=2, pady=2)

            # Actions column
            action_frame = ttk.Frame(scrollable_frame)
            action_frame.grid(row=row_idx, column=device_column_offset + 3, padx=2, pady=2)

            query_btn = ttk.Button(
                action_frame,
                text='Q',
                command=lambda dk=device_key, rid=register_id, lbl=read_label: do_query(dk, rid, lbl)
            )
            query_btn.pack(side='left', padx=1)

            if item.get('writable'):
                update_btn = ttk.Button(
                    action_frame,
                    text='U',
                    command=lambda dk=device_key, rid=register_id, entry=value_entry: do_update(dk, rid, entry)
                )
                update_btn.pack(side='left', padx=1)

        device_column_offset += 4  # Move to next device (4 columns per device)

    # Auto-query using a background thread to avoid blocking the UI
    stop_event: list[threading.Event] = [threading.Event()]
    worker_thread: list[threading.Thread | None] = [None]

    def worker():
        while not stop_event[0].is_set() and auto_query_var.get():
            try:
                rate_text = rate_entry.get().strip()
                rate = float(rate_text) if rate_text != '' else 1.0
            except Exception:
                rate = 1.0
            if rate <= 0:
                rate = 1.0
            interval = 1.0 / rate

            start_time = time.time()
            for device_key, rid, lbl in labels_list:
                if stop_event[0].is_set() or not auto_query_var.get():
                    break
                try:
                    instrument = instruments.get(device_key)
                    if instrument is not None:
                        code, payload = conn.query_register(instrument, rid)
                        if code == 0:
                            # schedule GUI update on main thread to update label text
                            root.after(0, lambda label=lbl, p=payload: label.config(text=str(p)))
                except Exception:
                    # ignore individual read errors during auto-query
                    pass

            elapsed = time.time() - start_time
            sleep_time = max(0.0, interval - elapsed)
            # Sleep in small increments so stop_event can interrupt sooner
            end_time = time.time() + sleep_time
            while time.time() < end_time:
                if stop_event[0].is_set() or not auto_query_var.get():
                    break
                time.sleep(0.05)

    def start_auto_query_thread():
        if worker_thread[0] is None or not worker_thread[0].is_alive():
            stop_event[0].clear()
            worker_thread[0] = threading.Thread(target=worker, daemon=True)
            worker_thread[0].start()

    def stop_auto_query_thread():
        stop_event[0].set()
        # don't block UI extensively; give thread a moment to exit
        if worker_thread[0] is not None:
            worker_thread[0].join(timeout=0.2)
            worker_thread[0] = None

    # start/stop when checkbox changes
    def _on_auto_change(*_):
        if auto_query_var.get():
            start_auto_query_thread()
        else:
            stop_auto_query_thread()

    auto_query_var.trace_add('write', _on_auto_change)

    def on_close():
        stop_auto_query_thread()
        root.destroy()

    root.protocol('WM_DELETE_WINDOW', on_close)

    root.mainloop()
    


def main(config_file: str = 'devices.json', port: str | None = None):
    try:
        with open(config_file, 'r') as f:
            devices_config = json.load(f)
    except Exception as exc:
        raise RuntimeError(f'Failed to load config file {config_file}: {exc}')

    # Override port if provided via command line
    if port is not None:
        for device_key in devices_config:
            devices_config[device_key]['port'] = port

    build_ui(devices_config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Modbus client GUI launcher')
    parser.add_argument('-c', '--config', default='devices.json', help='JSON config file with device definitions (default: devices.json)')
    parser.add_argument('-p', '--port', help='serial port device (e.g. COM3 or /dev/ttyUSB0) - overrides config file port')

    args = parser.parse_args()

    main(config_file=args.config, port=args.port)
