from Spectro.IndiSpectroController import  IndiSpectroController

config = dict(
    module="IndiSpectroController",
    device_name="spox",
    port="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AD0JE0ID-if00-port0",
    indi_client=dict(
        indi_host="localhost",
        indi_port="7625"
    ))
sc = IndiSpectroController(config=config)