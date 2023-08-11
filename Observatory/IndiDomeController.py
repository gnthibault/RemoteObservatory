# Basic stuff
import logging
import time

# Indi stuff
from helper.IndiDevice import IndiDevice

# Local
from utils.error import DomeControllerError


class IndiDomeController(IndiDevice):
    """Controller roll off roof and other stuff
    """

    def __init__(self, config=None, connect_on_create=True):
        device_name = config['dome_name']
        self.dome_movement_timeout_s = config["dome_movement_timeout_s"]
        self._is_initialized = False

        # device related intialization
        IndiDevice.__init__(self, device_name=device_name,
                            indi_client_config=config["indi_client"])

        if connect_on_create:
            self.connect()

        # Finished configuring
        self.logger.debug('Indi dome configured successfully')

    def initialize(self):
        self._is_initialized = True
        self.logger.debug("Initializing dome, not doing much actually")

    def deinitialize(self):
        self._is_initialized = False
        self.logger.debug("Deinitializing dome, not doing much actually")

    @property
    def is_initialized(self):
        return self._is_initialized

    def unpark(self):
        self.logger.debug("Unparking")
        self.start_indi_server()
        self.start_indi_driver()
        self.connect(connect_device=True)
        self.set_switch("DOME_PARK", on_switches=["UNPARK"], sync=True, timeout=self.dome_movement_timeout_s)

    def park(self):
        self.logger.debug("Parking")
        self.set_switch("DOME_PARK", on_switches=["PARK"], sync=True, timeout=self.dome_movement_timeout_s)
        self.disconnect()
        self.shutdown_indi_server()

    def open(self):
        self.logger.debug("Opening")
        self.set_switch("DOME_SHUTTER", on_switches=["SHUTTER_OPEN"], off_switches=["SHUTTER_CLOSE"], sync=True, timeout=self.dome_movement_timeout_s)

    def close(self):
        self.logger.debug("Closing")
        self.set_switch("DOME_SHUTTER", on_switches=["SHUTTER_CLOSE"], off_switches=["SHUTTER_OPEN"], sync=True, timeout=self.dome_movement_timeout_s)

    def get_dome_position(self):
        self.get_number("ABS_DOME_POSITION")["DOME_ABSOLUTE_POSITION"]

    @property
    def is_parked(self):
        return self.get_switch("DOME_PARK")["PARK"] == "On"

    @property
    def is_open(self):
        return self.get_switch("DOME_SHUTTER")["SHUTTER_OPEN"] == "On"

    def status(self):
        return {"is_open": self.is_open, "position": self.get_dome_position()}
