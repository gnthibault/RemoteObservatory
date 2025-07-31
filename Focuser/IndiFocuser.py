# Basic stuff
import io
import json
import logging

# Numerical stuff
import numpy as np

# Indi stuff
from helper.IndiDevice import IndiDevice
from Focuser.IndiFocuserMixin import IndiFocuserMixin

class IndiFocuser(IndiDevice, IndiFocuserMixin):
    """

    """
    def __init__(self, logger=None, config=None,
                 connect_on_create=True):
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                module="IndiFocuser",
                device_name="Focuser Simulator",
                port="/dev/ttyUSB0",
                focus_range=dict(
                    min=1,
                    max=10000),
                autofocus_step=dict(
                    coarse=100,
                    fine=10),
                autofocus_range=dict(
                    coarse=3000,
                    fine=7000),
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"
                ))

        self.port = config['port']
        self.focus_range = config['focus_range']
        self.autofocus_step = config['autofocus_step']
        self.autofocus_range = config['autofocus_range']

        logger.debug(f"Indi Focuser, focuser name is: {config['device_name']}")

        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config['device_name'],
                            indi_driver_name=config.get('indi_driver_name', None),
                            indi_client_config=config["indi_client"])
        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('Indi Focuser configured successfully')

    def park(self):
        self.logger.debug(f"Parking focuser {self.device_name}")
        self.deinitialize()
        self.disconnect()
        self.stop_indi_server()
        self.logger.debug(f"Successfully parked focuser {self.device_name}")

    def unpark(self):
        self.logger.debug(f"Unparking focuser {self.device_name} with a reset-like behaviour")
        self.park()
        self.start_indi_server()
        self.start_indi_driver()
        self.connect(connect_device=True)
        self.initialize()
        self.logger.debug(f"Successfully unparked focuser {self.device_name}")

    def deinitialize(self):
        self.logger.debug(f"Deinitializing {self.device_name}")
    def initialize(self):
        """
        This is not as simple a just connecting, because we must also set some
        specific values
        :return:
        """
        self.logger.debug(f"Initializing {self.device_name}")
        self.connect()
        self.set_port()

    def set_port(self):
        self.set_text("DEVICE_PORT", {"PORT": self.port}, sync=True, timeout=self.timeout)

    def on_emergency(self):
        self.logger.debug('Indi Focuser: on emergency routine started...')
        self.logger.debug('Indi Focuser: on emergency routine finished')

    def __str__(self):
        return f"Focuser: {self.device_name}"

    def __repr__(self):
        return self.__str__()
