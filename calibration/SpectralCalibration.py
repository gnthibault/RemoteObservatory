# Generic stuff
from threading import Event
from threading import Thread

# Numerical stuff
import numpy as np

# Local stuff
from Base.Base import Base

class SpectralCalibration(Base):
    def __init__(self,
                 camera=None,
                 config=None,
                 *args, **kwargs):
        super().__init__(self, args, kwargs)

        if config is None:
            config = dict(
                module = "SpectralCalibration",
                controller = dict(
                    module = 'IndiSpectroController',
                    controller_name = "spox")
            )

        # Get info from config
        self.gpsCoordinates = dict(latitude = config['latitude'],
                                   longitude = config['longitude'])
        self.spectral_calib_exp_sec = config["spectral_calib_sec"]
        self.flat_exp_sec = config["flat_sec"]
 
        # If controller is specified in the config, load
        try:
            cfg = config['controller']
            controller_name = cfg['module']
            controller = load_module('Spectro.'+controller_name)
            self.controller = getattr(controller,
                                            controller_name)(cfg)
        except Exception as e:
            self.controller = None
            msg = f"Cannot instantiate controller properly: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg)

        self.camera = camera
        self.logger.debug(f"SpectralCalibration successfully created with camera"
                          f"{self.camera.device_name} and controller "
                          f"{self.controller.device_name}")

    def calibrate(self, observed_list):
        for seq_time, observation in self.observed_list.items():
        pass
    def switch_on_spectro_light(self):
        self.logger("Switching-on spectro light")

    def switch_off_spectro_light(self):
        self.logger("Switching-off spectro light")

    def switch_on_flat_light(self):
        self.logger("Switching-on flat light")

    def switch_off_flat_light(self):

