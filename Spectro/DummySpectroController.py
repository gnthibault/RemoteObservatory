# Basic stuff
import io
import json
import logging

# Local utilities
from Base import Base

class DummySpectroController:
    """

    """
    def __init__(self,
                 config=None,
                 connect_on_create=True):

        if config is None:
            config = dict(
                module="DummypectroController",
                device_name="dummy",
                )

        super().__init__()


        # Finished configuring
        self.logger.debug('Indi Spectro controller configured successfully')

    def initialize(self):
        pass

    def on_emergency(self):
        self.logger.debug("Indi spectro controller: on emergency routine "
                          "started...")
        self.switch_off_spectro_light()
        self.switch_off_flat_light()
        self.logger.debug("Indi spectro controller: on emergency routine "
                          "finished")

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
