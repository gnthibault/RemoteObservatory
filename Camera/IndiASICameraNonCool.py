# Basic stuff

# Local stuff
from Camera.IndiAbstractCamera import IndiASICamera

class IndiASICameraNonCool(IndiASICamera):
    def __init__(self, serv_time, config=None,
                 connect_on_create=True):

        # Parent initialization
        super().__init__(
            serv_time=serv_time,
            config=config,
            connect_on_create=connect_on_create)

    def set_cooling_on(self):
        pass

    def set_cooling_off(self):
        pass

    def get_temperature(self):
        return np.nan

    def set_temperature(self, temperature):
        pass
