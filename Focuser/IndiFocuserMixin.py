# Basic stuff
import io
import json
import logging

# Numerical stuff
import numpy as np

# Indi stuff
from helper.IndiDevice import IndiDevice

class IndiFocuserMixin:
    """
    Mixin for devices that provide focuser functionality.
    Assumes the base class provides IndiDevice methods like set_number, get_number.
    """

    def park_focuser(self):
        self.logger.debug(f"{self} : parking focuser")
        if self.is_connected:
            self.move_to(self.focus_range['min'])

    def unpark_focuser(self):
        self.logger.debug(f"{self} : unparking focuser")
        if self.is_connected:
            self.move_to((self.focus_range['min']+self.focus_range['max'])/2)

    def get_position(self):
        """ Current encoder position of the focuser """
        #ret = self.get_number("REL_FOCUS_POSITION")["FOCUS_RELATIVE_POSITION"]
        ret = self.get_number("ABS_FOCUS_POSITION")["FOCUS_ABSOLUTE_POSITION"]
        self.logger.debug(f"{self} : current position is {ret}")
        return ret

    def move_to(self, position):
        """ Move focuser to new encoder position """
        self.logger.debug(f"{self}  moving to position {position}")
        self.set_number('ABS_FOCUS_POSITION', #REL_FOCUS_POSITION
                        {'FOCUS_ABSOLUTE_POSITION': np.float64(position)}, #FOCUS_RELATIVE_POSITION
                        sync=True, timeout=self.timeout)
        new_position = self.get_position()
        self.logger.debug(f"{self} Now position is {new_position}")
        return new_position