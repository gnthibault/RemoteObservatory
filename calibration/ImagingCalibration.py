# Generic stuff
from threading import Event
from threading import Thread

# Numerical stuff
import numpy as np

# Local stuff
from Base.Base import Base

class ImagingCalibration(Base):
    def __init__(self,
                 camera=None,
                 controller=None,
                 *args, **kwargs):
        super().__init__(self, args, kwargs)

        self.camera = camera
        self.controller = camera

        self.logger.debug(f"ImagingCalibration successfully created with camera"
                          f"{self.camera.device_name} and controller "
                          f"{self.controller.device_name}")

