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

    """
    def __init__(self,
                 config=None,
                 connect_on_create=True):

        if config is None:
            config = dict(
                module="IndiSpectroController",
                device_name="spox",
                port="/dev/ttyUSB0",
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"
                ))

        self.port = config['port']

        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config['device_name'],
                            indi_client_config=config["indi_client"])
        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('Indi spectro controller configured successfully')

    def initialize(self):
        self._setup_indi_client()
        self.connect_client()
        self.set_port()
        self.connect_device()

    def set_port(self):
        self.set_text("DEVICE_PORT", {"PORT": self.port})

    def on_emergency(self):
        self.logger.debug("Indi spectro controller: on emergency routine started...")
        self.switch_off_spectro_light()
        self.switch_off_flat_light()
        self.logger.debug("Indi spectro controller: on emergency routine finished")

    def switch_on_spectro_light(self):
        self.logger("Switching-on spectro light")

    def switch_off_spectro_light(self):
        self.logger("Switching-off spectro light")
        self.open_optical_path()

    def switch_on_flat_light(self):
        self.logger("Switching-on flat light")

    def switch_off_flat_light(self):
        self.logger("Switching-off flat light")
        self.open_optical_path()

    def close_optical_path_for_dark(self):
        self.logger("Close optical path for dark")

    def open_optical_path(self):
        self.logger("Open optical path")

    def __str__(self):
        return f"Spectro controller: {self.device_name}"

    def __repr__(self):
        return self.__str__()
