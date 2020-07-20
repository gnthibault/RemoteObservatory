# Generic stuff
from threading import Event
from threading import Thread

# Numerical stuff
import numpy as np

# Astropy stuff
import astropy.units as u

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
        self.spectral_calib_nb = config["spectral_calib_nb"]
        self.flat_exp_sec = config["flat_sec"]
        self.flat_nb = config["flat_nb"]
        self.dark_exp_sec = []
        self.dark_nb = config["dark_nb"]
 
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
        self.dark_exp_sec = []
        for seq_time, observation in self.observed_list.items():
            self.dark_exp_sec.append(
                observation.time_per_exposure.to(u.second).value)
        
        self.dark_exp_sec = np.unique(self.dark_exp_sec).tolist()
        self.take_flat()
        self.take_spectral_calib()
        self.take_dark()

    def take_flat(self):
        self.controller.switch_on_flat_light()
        self.flat_exp_sec
        self.flat_nb
        self.controller.switch_on_flat_light()

    def take_spectral_calib(self):
        self.controller.switch_on_spectro_light()
        self.spectral_calib_exp_sec
        self.spectral_calib_nb
        self.controller.switch_off_spectro_light()

    def take_dark(self):
        self.controller.close_optical_path_for_dark()
        self.dark_exp_sec = []
        self.dark_nb
        self.controller.open_optical_path()

