import dearpygui.dearpygui as dpg


def query_callback():
    """Callback for query button"""
    text_value = dpg.get_value("text_input")
    print(f"Query: {text_value}")


def update_callback():
    """Callback for update button"""
    text_value = dpg.get_value("text_input")
    print(f"Update: {text_value}")


def make_row():
    with dpg.group(horizontal=True):
        dpg.add_text("Example:")
        dpg.add_input_text(
            id="text_input",
            width=200,
            default_value=""
        )
        dpg.add_button(
            label="Query",
            callback=query_callback,
            width=80
        )
        dpg.add_button(
            label="Update",
            callback=update_callback,
            width=80
        )

def make_window():
    with dpg.window(label="Modbus", tag="main_window", no_title_bar=True, no_move=True, no_resize=True, pos=(0, 0), width=600, height=150):
        make_row()

def main():
    dpg.create_context()
    make_window()
    dpg.create_viewport(title="Modbus", width=600, height=150)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    main()
