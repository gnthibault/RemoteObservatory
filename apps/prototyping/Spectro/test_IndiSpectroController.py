import time

from Spectro.IndiSpectroController import  IndiSpectroController

config = dict(
    module="IndiSpectroController",
    device_name="Shelyak SPOX",
    port="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AD0JE0ID-if00-port0",
    indi_client=dict(
        indi_host="192.168.0.194",
        indi_port="7624"
    ))
time.sleep(5)
sc = IndiSpectroController(config=config)
sc.close_optical_path_for_dark()
time.sleep(5)
sc.switch_on_flat_light()
time.sleep(5)
sc.switch_on_spectro_light()
time.sleep(5)
sc.open_optical_path()
time.sleep(5)