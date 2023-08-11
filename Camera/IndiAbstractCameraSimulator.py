# Basic stuff

# Numerical stuff
import numpy as np

# Local stuff
from Camera.IndiAbstractCamera import IndiAbstractCamera

class IndiAbstractCameraSimulator(IndiAbstractCamera):
    def __init__(self, serv_time, config=None,
                 connect_on_create=True):

        # Parent initialization
        super().__init__(
            serv_time=serv_time,
            config=config,
            connect_on_create=connect_on_create)
        self.sampling_arcsec = self.compute_sampling_arcsec(config)

    def compute_sampling_arcsec(self, config):
        px_size = np.mean([
            config["SIMULATOR_SETTINGS"]["SIM_XSIZE"],
            config["SIMULATOR_SETTINGS"]["SIM_YSIZE"]])
        focal_length_mm = config["SCOPE_INFO"]["FOCAL_LENGTH"]
        return 206*px_size/focal_length_mm

    def prepare_shoot(self):
        self.set_number("SIMULATOR_SETTINGS", self.indi_camera_config["SIMULATOR_SETTINGS"])
        self.set_number("SCOPE_INFO", self.indi_camera_config["SCOPE_INFO"])
        super().prepare_shoot()

    def set_cooling_on(self):
        # This feels like a bug from the simulator ...
        self.logger.warning(f"set_cooling_on asynchronously as, there seems to be a bug in simulator implementation")
        self.set_switch('CCD_COOLER', ['COOLER_ON'], sync=False, timeout=self.defaultTimeout)
