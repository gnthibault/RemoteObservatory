# Basic stuff

# Numerical stuff
import numpy as np

# Local stuff
from Mount.IndiAbstractMount import IndiAbstractMount

class IndiAbstractMountSimulator(IndiAbstractMount):
    def __init__(self, location, serv_time, config=None,
                 connect_on_create=True):

        # Parent initialization
        super().__init__(
            location=location,
            serv_time=serv_time,
            config=config,
            connect_on_create=connect_on_create)
    def get_pier_side(self):
        ''' GEM Pier Side
            PIER_EAST Mount on the East side of pier (Pointing West).
            PIER_WEST Mount on the West side of pier (Pointing East).
        '''
        pier_side = {
            'PIER_WEST': 'Off',
            'PIER_EAST': 'On'
        }
        return pier_side
