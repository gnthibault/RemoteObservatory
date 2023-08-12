# Basic stuff
import numpy as np

# Local stuff
from Camera.IndiAltairCamera import IndiAltairCamera

class IndiAltairCameraNonCool(IndiAltairCamera):
    def __init__(self, serv_time, config=None,
                 connect_on_create=True):

        # Parent initialization
        super().__init__(
            serv_time=serv_time,
            config=config,
            connect_on_create=connect_on_create)

    def set_cooling_on(self):
        """
            Altair AA183MPRO.TC_FAN_SPEED.INDI_DISABLED=Off
            Altair AA183MPRO.TC_FAN_SPEED.FAN_SPEED1=Off
            Altair AA183MPRO.TC_FAN_SPEED.FAN_SPEED2=On
        :return:
        """
        self.set_switch('TC_FAN_SPEED', ['FAN_SPEED2'], sync=True)


    def set_cooling_off(self):
        """
            Altair AA183MPRO.TC_FAN_SPEED.INDI_DISABLED=Off
            Altair AA183MPRO.TC_FAN_SPEED.FAN_SPEED1=Off
            Altair AA183MPRO.TC_FAN_SPEED.FAN_SPEED2=On
        :return:
        """
        self.set_switch('TC_FAN_SPEED', ['INDI_DISABLED'], sync=True)

    def get_temperature(self):
        return np.nan

    def set_temperature(self, temperature):
        pass