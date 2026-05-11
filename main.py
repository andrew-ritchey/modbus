import json
import argparse
import tkinter as tk
from tkinter import ttk, messagebox

import connection as conn
import threading
import time
from collections import deque
from typing import Any

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Maximum number of (timestamp, value) samples kept per series.
MAX_PLOT_POINTS = 500
# How often the plot thread triggers a redraw (seconds).
PLOT_REFRESH_INTERVAL = 0.5


# ---------------------------------------------------------------------------
# PlotBuffer — thread-safe sample store for one plotted series
# ---------------------------------------------------------------------------
class PlotBuffer:
    """A fixed-length, thread-safe circular buffer of (datetime, float) pairs."""

    def __init__(self, label: str, maxlen: int = MAX_PLOT_POINTS) -> None:
        self.label = label
        self._lock = threading.Lock()
        self._times: deque[datetime] = deque(maxlen=maxlen)
        self._values: deque[float] = deque(maxlen=maxlen)

    def append(self, timestamp: datetime, value: float) -> None:
        with self._lock:
            self._times.append(timestamp)
            self._values.append(value)

    def snapshot(self) -> tuple[list[datetime], list[float]]:
        """Return a consistent copy of current data (safe to call from any thread)."""
        with self._lock:
            return list(self._times), list(self._values)


# ---------------------------------------------------------------------------
# DevicePlotWindow — one Toplevel + Figure per device
#
# Created on the main thread.  All figure mutations happen on the main thread
# too, dispatched via root.after() from the plot thread — Tk's single-thread
# rule is never violated.
# ---------------------------------------------------------------------------
class DevicePlotWindow:
    def __init__(self, root: tk.Tk, device_name: str,
                 buffers: list[PlotBuffer]) -> None:
        self._root = root
        self._buffers = buffers
        self._alive = True

        self._win = tk.Toplevel(root)
        self._win.title(f'{device_name} — Live Plot')
        self._win.protocol('WM_DELETE_WINDOW', self._on_close)

        self._fig, self._ax = plt.subplots(figsize=(6, 3), tight_layout=True)
        self._ax.set_xlabel('Time')
        self._ax.set_ylabel('Value')
        self._ax.set_title(device_name)

        # One Line2D per series — data updated in-place to avoid legend churn.
        self._lines = {
            buf.label: self._ax.plot([], [], label=buf.label)[0]
            for buf in buffers
        }
        if len(buffers) > 1:
            self._ax.legend(loc='upper left', fontsize=8)

        self._canvas = FigureCanvasTkAgg(self._fig, master=self._win)
        self._canvas.get_tk_widget().pack(fill='both', expand=True)
        self._canvas.draw()

    # Called from the plot thread — schedules the actual redraw on the main thread.
    def request_redraw(self) -> None:
        if self._alive:
            self._root.after(0, self._redraw)

    # Runs on the main thread only (scheduled via root.after).
    def _redraw(self) -> None:
        if not self._alive:
            return
        any_data = False
        for buf in self._buffers:
            times, values = buf.snapshot()
            if times:
                any_data = True
                line = self._lines[buf.label]
                line.set_xdata(times)
                line.set_ydata(values)

        if any_data:
            self._ax.relim()
            self._ax.autoscale_view()
            self._ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self._fig.autofmt_xdate(rotation=30, ha='right')

        self._canvas.draw_idle()

    def _on_close(self) -> None:
        self._alive = False
        self._win.destroy()

    def destroy(self) -> None:
        self._alive = False
        try:
            self._win.destroy()
        except tk.TclError:
            pass


# ---------------------------------------------------------------------------
# PlotThread — wakes periodically and asks each window to redraw.
# Never calls Tk widget methods directly; all Tk work is dispatched through
# root.after() inside DevicePlotWindow.request_redraw().
# ---------------------------------------------------------------------------
class PlotThread(threading.Thread):
    def __init__(self, plot_windows: list[DevicePlotWindow],
                 stop_event: threading.Event) -> None:
        super().__init__(daemon=True, name='PlotThread')
        self._windows = plot_windows
        self._stop = stop_event

    def run(self) -> None:
        while not self._stop.is_set():
            for win in self._windows:
                win.request_redraw()
            self._stop.wait(timeout=PLOT_REFRESH_INTERVAL)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _connect_all(devices_config: dict[str, Any]) -> dict[str, Any]:
    """Attempt to connect to every device in the config."""
    instruments: dict[str, Any] = {}
    for device_key, device_config in devices_config.items():
        try:
            port = device_config.get('port', '/dev/ttyUSB0')
            address = device_config['address']
            settings_dict = {
                k: v for k, v in device_config.items()
                if k not in ('name', 'register', 'address', 'port')
            }
            instruments[device_key] = conn.connect(
                port=port, address=address, settings=settings_dict
            )
        except Exception as e:
            messagebox.showerror(
                'Connection Error',
                f'Failed to connect to device {device_key}: {e}'
            )
            instruments[device_key] = None
    return instruments


# ---------------------------------------------------------------------------
# build_ui
# ---------------------------------------------------------------------------
def build_ui(devices_config: dict[str, Any]) -> None:
    root = tk.Tk()
    root.title('Modbus Client (Tkinter)')
    root.geometry('1400x600')

    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill='both', expand=True)

    canvas = tk.Canvas(main_frame)
    v_scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
    h_scrollbar = ttk.Scrollbar(main_frame, orient='horizontal', command=canvas.xview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        '<Configure>',
        lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    canvas.grid(row=0, column=0, sticky='nsew')
    v_scrollbar.grid(row=0, column=1, sticky='ns')
    h_scrollbar.grid(row=1, column=0, sticky='ew')

    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    instruments = _connect_all(devices_config)

    # --- Top controls ---
    controls_frame = ttk.Frame(scrollable_frame)
    controls_frame.grid(
        row=0, column=0, columnspan=len(devices_config) * 4,
        sticky='ew', padx=5, pady=(0, 8)
    )

    controls_inner = ttk.Frame(controls_frame)
    controls_inner.pack(anchor='center')

    auto_query_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(controls_inner, text='Auto-Query', variable=auto_query_var).pack(
        side='left', padx=(0, 12)
    )

    ttk.Label(controls_inner, text='Rate (Hz):').pack(side='left')

    def validate_float(p: str) -> bool:
        if p == '':
            return True
        try:
            float(p)
            return True
        except ValueError:
            return False

    vcmd = controls_inner.register(validate_float)
    rate_entry = ttk.Entry(controls_inner, width=10, validate='key',
                           validatecommand=(vcmd, '%P'))
    rate_entry.pack(side='left', padx=(4, 0))
    rate_entry.insert(0, '1')

    # --- Build plot buffers for every register marked "plot": true ---
    # Keyed by (device_key, register_id); written by I/O thread, read by plot thread.
    plot_buffers: dict[tuple[str, int], PlotBuffer] = {}
    for device_key, device_config in devices_config.items():
        for item in device_config.get('register', []):
            if item.get('plot'):
                key = (device_key, item['register_id'])
                plot_buffers[key] = PlotBuffer(
                    label=item.get('description', f'reg{item["register_id"]}')
                )

    # --- Shared read helper (called by both Q button and auto-query worker) ---
    def read_register_into_label(device_key: str, register_id: int,
                                 label_widget: ttk.Label,
                                 show_errors: bool = True) -> None:
        """Read one register, update the label, and feed any plot buffer.

        When show_errors is False (auto-query path) read errors are silently
        dropped to avoid modal-box storms during continuous polling.
        """
        instrument = instruments.get(device_key)
        if instrument is None:
            if show_errors:
                messagebox.showerror(
                    'Connection Error',
                    f'Not connected to device {device_key}'
                )
            return
        code, payload = conn.query_register(instrument, register_id)
        if code == 0:
            scaled = payload / 10
            # Label update must happen on the main thread.
            root.after(0, lambda lbl=label_widget, v=scaled: lbl.config(text=str(v)))
            # Feed plot buffer — PlotBuffer.append() is thread-safe.
            buf = plot_buffers.get((device_key, register_id))
            if buf is not None:
                buf.append(datetime.now(), scaled)
        elif show_errors:
            messagebox.showerror(
                'Modbus Read Error',
                f'Error reading register {register_id}: {payload}'
            )

    # --- Write helper ---
    def do_update(device_key: str, register_id: int,
                  entry_widget: ttk.Entry) -> None:
        instrument = instruments.get(device_key)
        if instrument is None:
            messagebox.showerror('Connection Error',
                                 f'Not connected to device {device_key}')
            return
        text_value = entry_widget.get().strip()
        if not text_value:
            messagebox.showerror('Modbus Write Error',
                                 'Input value cannot be empty')
            return
        try:
            # Scale by 10 to match the controller's fixed-point representation.
            raw_value = int(float(text_value) * 10)
        except ValueError:
            messagebox.showerror('Modbus Write Error',
                                 'Input value must be numeric')
            return

        code, payload = conn.update_register(instrument, register_id, raw_value)
        if code == 0:
            messagebox.showinfo('Modbus Write',
                                f'Successfully wrote {raw_value} to register {register_id}')
        else:
            messagebox.showerror('Modbus Write Error',
                                 f'Error writing register {register_id}: {payload}')

    # --- Build per-device columns and spawn plot windows ---
    labels_list: list[tuple[str, int, ttk.Label]] = []
    plot_windows: list[DevicePlotWindow] = []
    header_font = ('Arial', 10, 'bold')
    device_column_offset = 0

    for device_key, device_config in devices_config.items():
        device_name = device_config.get('name', device_key)
        registers = device_config.get('register', [])

        tk.Label(scrollable_frame, text=device_name, font=header_font).grid(
            row=1, column=device_column_offset, columnspan=4,
            padx=5, pady=5, sticky='n'
        )

        for row_idx, item in enumerate(registers, start=2):
            register_id = item['register_id']
            desc = item.get('description', f'Register {register_id}')

            value_entry = ttk.Entry(scrollable_frame, width=12)
            read_label = ttk.Label(scrollable_frame, text='-', width=10)
            labels_list.append((device_key, register_id, read_label))

            ttk.Label(scrollable_frame, text=desc, width=20).grid(
                row=row_idx, column=device_column_offset,
                sticky='w', padx=2, pady=2
            )
            read_label.grid(row=row_idx, column=device_column_offset + 1,
                            padx=2, pady=2)
            value_entry.grid(row=row_idx, column=device_column_offset + 2,
                             padx=2, pady=2)

            action_frame = ttk.Frame(scrollable_frame)
            action_frame.grid(row=row_idx, column=device_column_offset + 3,
                               padx=2, pady=2)

            ttk.Button(
                action_frame, text='Q', width=5,
                command=lambda dk=device_key, rid=register_id, lbl=read_label:
                    read_register_into_label(dk, rid, lbl, show_errors=True)
            ).pack(side='left', padx=1)

            if item.get('writable'):
                ttk.Button(
                    action_frame, text='U', width=5,
                    command=lambda dk=device_key, rid=register_id, ent=value_entry:
                        do_update(dk, rid, ent)
                ).pack(side='left', padx=1)

        # One plot window per device, containing all its "plot": true series.
        device_plot_bufs = [
            plot_buffers[(device_key, item['register_id'])]
            for item in registers
            if item.get('plot') and (device_key, item['register_id']) in plot_buffers
        ]
        if device_plot_bufs:
            plot_windows.append(DevicePlotWindow(root, device_name, device_plot_bufs))

        device_column_offset += 4

    # --- Serial I/O background thread ---
    stop_event = threading.Event()
    worker_thread: list[threading.Thread | None] = [None]

    def worker() -> None:
        while not stop_event.is_set() and auto_query_var.get():
            try:
                rate = float(rate_entry.get().strip() or '1')
            except ValueError:
                rate = 1.0
            interval = 1.0 / max(rate, 1e-6)

            start_time = time.monotonic()
            for device_key, rid, lbl in labels_list:
                if stop_event.is_set() or not auto_query_var.get():
                    break
                read_register_into_label(device_key, rid, lbl, show_errors=False)

            elapsed = time.monotonic() - start_time
            end_time = time.monotonic() + max(0.0, interval - elapsed)
            while time.monotonic() < end_time:
                if stop_event.is_set() or not auto_query_var.get():
                    break
                time.sleep(0.05)

    def start_worker() -> None:
        if worker_thread[0] is None or not worker_thread[0].is_alive():
            stop_event.clear()
            worker_thread[0] = threading.Thread(target=worker, daemon=True,
                                                name='ModbusIOThread')
            worker_thread[0].start()

    def stop_worker() -> None:
        stop_event.set()
        if worker_thread[0] is not None:
            worker_thread[0].join(timeout=0.2)
            worker_thread[0] = None

    def _on_auto_change(*_: Any) -> None:
        if auto_query_var.get():
            start_worker()
        else:
            stop_worker()

    auto_query_var.trace_add('write', _on_auto_change)

    # --- Plot thread (independent of serial I/O and main GUI thread) ---
    plot_stop_event = threading.Event()
    plot_thread: PlotThread | None = None
    if plot_windows:
        plot_thread = PlotThread(plot_windows, plot_stop_event)
        plot_thread.start()

    # --- Shutdown ---
    def on_close() -> None:
        stop_worker()                       # stop serial I/O thread
        plot_stop_event.set()               # stop plot thread
        if plot_thread is not None:
            plot_thread.join(timeout=1.0)
        for win in plot_windows:
            win.destroy()
        plt.close('all')
        root.destroy()

    root.protocol('WM_DELETE_WINDOW', on_close)
    root.mainloop()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(config_file: str = 'devices.json', port: str | None = None) -> None:
    try:
        with open(config_file, 'r') as f:
            devices_config = json.load(f)
    except Exception as exc:
        raise RuntimeError(f'Failed to load config file {config_file}: {exc}')

    if port is not None:
        for device_key in devices_config:
            devices_config[device_key]['port'] = port

    build_ui(devices_config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Modbus client GUI launcher')
    parser.add_argument('-c', '--config', default='devices.json',
                        help='JSON config file with device definitions (default: devices.json)')
    parser.add_argument('-p', '--port',
                        help='Serial port (e.g. COM3 or /dev/ttyUSB0) — overrides config file')
    args = parser.parse_args()
    main(config_file=args.config, port=args.port)
