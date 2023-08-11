# Basic stuff
import io
import json
import logging

# Numerical stuff
import numpy as np

# Indi stuff
from helper.IndiDevice import IndiDevice


class IndiSpectroController(IndiDevice):
    """
        Return of indi_getprop -p 7625 "Shelyak Spox.*.*"
            Shelyak Spox.CONNECTION.CONNECT=On
            Shelyak Spox.CONNECTION.DISCONNECT=Off
            Shelyak Spox.DRIVER_INFO.DRIVER_NAME=Shelyak Spox
            Shelyak Spox.DRIVER_INFO.DRIVER_EXEC=indi_shelyakspox_spectrograph
            Shelyak Spox.DRIVER_INFO.DRIVER_VERSION=1.0
            Shelyak Spox.DRIVER_INFO.DRIVER_INTERFACE=0
            Shelyak Spox.CONFIG_PROCESS.CONFIG_LOAD=Off
            Shelyak Spox.CONFIG_PROCESS.CONFIG_SAVE=Off
            Shelyak Spox.CONFIG_PROCESS.CONFIG_DEFAULT=Off
            Shelyak Spox.CONFIG_PROCESS.CONFIG_PURGE=Off
            Shelyak Spox.DEVICE_PORT.PORT=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AD0JE0ID-if00-port0
            Shelyak Spox.CALIBRATION.DARK=Off
            Shelyak Spox.CALIBRATION.FLAT=Off
            Shelyak Spox.CALIBRATION.CALIBRATION=Off
            Shelyak Spox.CALIBRATION.SKY=Off
    """
    def __init__(self,
                 config=None,
                 connect_on_create=True):

        if config is None:
            config = dict(
                module="IndiSpectroController",
                device_name="Shelyak Spox",
                port="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AD0JE0ID-if00-port0",
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7625"
                ))

        self.port = config['port']

        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config['device_name'],
                            indi_driver_name=config.get('indi_driver_name', None),
                            indi_client_config=config["indi_client"])
        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('Indi spectro controller configured successfully')

    def initialize(self):
        self.connect(connect_device=False) #TODO TN Urgent check if this is ok
        self.set_port()
        self.connect_device()
        self.initialize_calibration()

    def set_port(self):
        self.set_text("DEVICE_PORT", {"PORT": self.port})

    def initialize_calibration(self):
        self.open_optical_path()

    def on_emergency(self):
        self.logger.debug("Indi spectro controller: on emergency routine started...")
        self.open_optical_path()
        self.logger.debug("Indi spectro controller: on emergency routine finished")

    def switch_on_spectro_light(self):
        self.set_switch("CALIBRATION", ["CALIBRATION"])
        self.logger.debug("Switching-on spectro light")

    def switch_off_spectro_light(self):
        self.logger.debug("Switching-off spectro light")
        self.open_optical_path()

    def switch_on_flat_light(self):
        self.set_switch("CALIBRATION", ["FLAT"])
        self.logger.debug("Switching-on flat light")

    def switch_off_flat_light(self):
        self.logger.debug("Switching-off flat light")
        self.open_optical_path()

    def close_optical_path_for_dark(self):
        self.set_switch("CALIBRATION", ["DARK"])
        self.logger.debug("Close optical path for dark")

    def open_optical_path(self):
        self.set_switch("CALIBRATION", ["SKY"])
        self.logger.debug("Open optical path")

    def __str__(self):
        return f"Spectro controller: {self.device_name} with current calibration {self.get_switch('CALIBRATION')}"

    def __repr__(self):
        return self.__str__()
