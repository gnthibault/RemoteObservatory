import time

from Spectro.IndiSpectroController import  IndiSpectroController

config = dict(
    module="IndiSpectroController",
    device_name="Shelyak Spox",
    port="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AD0JE0ID-if00-port0",
    indi_client=dict(
        indi_host="localhost",
        indi_port="7625"
    ))
sc = IndiSpectroController(config=config)
sc.close_optical_path_for_dark()
time.sleep(5)
sc.switch_on_flat_light()
time.sleep(5)
sc.switch_off_spectro_light()
time.sleep(5)
sc.open_optical_path()
time.sleep(5)