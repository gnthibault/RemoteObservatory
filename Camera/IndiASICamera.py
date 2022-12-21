# Basic stuff

# Local stuff
from Camera.IndiAbstractCamera import IndiAbstractCamera

class IndiASICamera(IndiAbstractCamera):
    def __init__(self, serv_time, config=None,
                 connect_on_create=True):

        # Parent initialization
        super().__init__(
            serv_time=serv_time,
            config=config,
            connect_on_create=connect_on_create)

    def set_gain(self, value):
        self.set_number('CCD_CONTROLS', {'Gain': value}, sync=True, timeout=self.defaultTimeout)

    def get_gain(self):
        gain = self.get_number('CCD_CONTROLS')
        return gain["Gain"]
