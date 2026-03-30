import json
import dearpygui.dearpygui as dpg
import minimalmodbus
import serial

def connect(port='COM1'):
    instrument = minimalmodbus.Instrument(port, 240, debug=False)  # port name, slave address (in decimal)
    instrument.serial.baudrate = 38400  # baudrate
    instrument.serial.bytesize = 8
    instrument.serial.parity   = serial.PARITY_EVEN
    instrument.serial.stopbits = 1
    instrument.serial.timeout  = 0.1      # seconds
    instrument.mode = minimalmodbus.MODE_RTU # rtu or ascii mode
    instrument.clear_buffers_before_each_transaction = True

    return instrument


def query_callback(sender, app_data, user_data):
    """Callback for query button, read from register"""
    value = user_data['instrument'].read_register(user_data['id'])
    dpg.set_value(f'text_{user_data["row_id"]}', value=value)


def update_callback(sender, app_data, user_data):
    """Callback for update button, write to register"""
    value = dpg.get_value(f'text_{user_data["row_id"]}')
    user_data['instrument'].write_register(user_data['id'], value)


def make_row(instrument, title, id):
    row_id = dpg.generate_uuid()
    with dpg.group(horizontal=True, parent="main_window"):
        dpg.add_button(
            tag=f'query_{row_id}',
            label="Query",
            callback=query_callback,
            user_data={'row_id':row_id, 'instrument':instrument, 'id':id},
            width=80
        )
        dpg.add_button(
            tag=f'update_{row_id}',
            label="Update",
            callback=update_callback,
            user_data={'row_id':row_id, 'instrument':instrument, 'id':id},
            width=80
        )
        dpg.add_input_text(
            tag=f'text_{row_id}',
            width=200,
            default_value="",
            label=title
        )

def make_window():
    dpg.add_window(label="Modbus",
                   tag="main_window",
                   no_title_bar=True)
    dpg.set_primary_window("main_window", True)

def main(file_path):
    with open(file_path, 'r') as f:
        register = json.load(f)

    instrument = connect(port='COM8')

    dpg.create_context()
    make_window()

    for item in register:
        make_row(instrument=instrument,
                 title=item['description'],
                 id=item['register_id'])

    # Calculate height based on number of items
    dpg.create_viewport(title="Modbus", width=800, height=1000)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    register_file = "redlion_pxu_register.json"
    main(register_file)
