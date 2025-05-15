# Generic stuff
import logging
import sys

# The class to play with
import time

from Observatory.IndiDomeController import IndiDomeController

import logging

# Viz stuff
import matplotlib.pyplot as plt
from skimage import img_as_float
from skimage import exposure

# Local stuff : Camera
from Camera.IndiAbstractCameraSimulator import IndiAbstractCameraSimulator
from Service.NTPTimeService import HostTimeService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')

def test_IndiDomeController():
    config = dict(
        dome_name="Dome Simulator",
        dome_movement_timeout_s=600,
        indi_client=dict(
            indi_host="localhost",
            indi_port=7624)
    )
    # Instanciate Dome
    dome = IndiDomeController(config=config, connect_on_create=True)
    dome.park()
    assert dome.is_parked
    dome.unpark()
    assert not dome.is_parked
    dome.close()
    assert not dome.is_open
    dome.open()
    assert dome.is_open
    # Check position
    assert isinstance(dome.get_dome_position(), float)
    print(f" Checking current dome position before open {dome.get_dome_position()}")
    h_name = "MY_VECTOR_HANDLER"
    dome.register_vector_handler_to_client(
        vector_name="ABS_DOME_POSITION",
        handler_name=h_name,
        callback=lambda pv: print(f" RECEIVED VALUE: {pv.getNumber()[0].getValue()}")
    )
    time.sleep(2)
    # Play with Kstars client for instance
    dome.unregister_vector_handler_to_client(
        vector_name="ABS_DOME_POSITION",
        handler_name=h_name,
    )
    # Then play with dynamic position
    # Be careful dome park may not be in sync for some reason ....
    dome.park()
