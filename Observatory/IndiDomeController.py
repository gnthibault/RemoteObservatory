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
                            indi_driver_name=config.get('indi_driver_name', None),
                            indi_client_config=config["indi_client"])

        if connect_on_create:
            self.connect()

        # Finished configuring
        self.logger.debug('Indi dome configured successfully')

    def initialize(self):
        self.logger.debug(f"Initializing dome {self.device_name}")
        self.set_switch("DOME_PARK", on_switches=["UNPARK"], sync=True, timeout=self.dome_movement_timeout_s)
        self.set_switch("DOME_AUTOSYNC", on_switches=["DOME_AUTOSYNC_ENABLE"], sync=True)
        self.set_number("DOME_PARAMS", {"AUTOSYNC_THRESHOLD": 0.5})
        self.logger.debug(f"Successfully initialized dome {self.device_name}")

    def deinitialize(self):
        self.logger.debug(f"Deinitializing dome {self.device_name}")
        if self._is_initialized:
            self.set_switch("DOME_PARK", on_switches=["PARK"], sync=True, timeout=self.dome_movement_timeout_s)
        self.logger.debug(f"Successfully deinitialized dome {self.device_name}")

    @property
    def is_initialized(self):
        return self._is_initialized

    def unpark(self):
        self.logger.debug("Unparking with a reset-like behaviour")
        self.park()
        self.start_indi_server()
        self.start_indi_driver()
        self.connect(connect_device=True)
        self.initialize()
        self._is_initialized = True
        self.logger.debug("Successfully unparked")

    def park(self):
        self.logger.debug("Parking")
        self.deinitialize()
        self.disconnect()
        self.stop_indi_server()
        self._is_initialized = False
        self.logger.debug("Successfully parked")

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
