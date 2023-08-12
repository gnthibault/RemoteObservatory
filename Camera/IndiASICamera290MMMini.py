# Basic stuff
import numpy as np

# Local stuff
from Camera.IndiASICamera import IndiASICamera
from Camera.IndiASICameraNonCool import IndiASICameraNonCool

class IndiASICamera290MMMini(IndiASICameraNonCool):
    def __init__(self, serv_time, config=None,
                 connect_on_create=True):

        # Parent initialization
        super().__init__(
            serv_time=serv_time,
            config=config,
            connect_on_create=connect_on_create)

    def set_offset(self, value):
        pass
