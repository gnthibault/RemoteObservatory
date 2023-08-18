# Basic stuff
import io
import json
import logging

# Local utilities
from Base.Base import Base

class DummySpectroController(Base):
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
        self.device_name = config["device_name"]

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
        self.logger.debug("Switching-on spectro light")

    def switch_off_spectro_light(self):
        self.logger.debug("Switching-off spectro light")
        self.open_optical_path()

    def switch_on_flat_light(self):
        self.logger.debug("Switching-on flat light")

    def switch_off_flat_light(self):
        self.logger.debug("Switching-off flat light")
        self.open_optical_path()

    def close_optical_path_for_dark(self):
        self.logger.debug("Close optical path for dark")

    def open_optical_path(self):
        self.logger.debug("Open optical path")

    def __str__(self):
        return f"Spectro controller: {self.device_name}"

    def __repr__(self):
        return self.__str__()
