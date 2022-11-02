# Basic stuff

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

    def prepare_shoot(self):
        self.set_number("SIMULATOR_SETTINGS", self.indi_camera_config["SIMULATOR_SETTINGS"])
        self.set_number("SCOPE_INFO", self.indi_camera_config["SCOPE_INFO"])
        super().prepare_shoot()
