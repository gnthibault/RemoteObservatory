# Basic stuff
import io
import json
import logging

# Numerical stuff
import numpy as np

class IndiSpectroController:
    """

    """
    def __init__(self, logger=None, config=None):
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                module="DummypectroController",
                controller_name="dummy",
                )

        logger.debug(f"Indi Spectro Controller, controller name is: "
                     f"{config['controller_name']}")

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
