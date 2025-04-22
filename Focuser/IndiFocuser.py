# Basic stuff
import io
import json
import logging

# Numerical stuff
import numpy as np

# Indi stuff
from helper.IndiDevice import IndiDevice

class IndiFocuser(IndiDevice):
    """

    """
    def __init__(self, logger=None, config=None,
                 connect_on_create=True):
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                module="IndiFocuser",
                focuser_name="Focuser Simulator",
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

        logger.debug(f"Indi Focuser, focuser name is: {config['focuser_name']}")

        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config['focuser_name'],
                            indi_driver_name=config.get('indi_driver_name', None),
                            indi_client_config=config["indi_client"])
        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('Indi Focuser configured successfully')

    def initialize(self):
        """
        This is not as simple a just connecting, because we must also set some
        specific values
        :return:
        """
        self.connect()
        self.set_port()

    def set_port(self):
        self.set_text("DEVICE_PORT", {"PORT": self.port}, sync=True, timeout=self.timeout)

    def on_emergency(self):
        self.logger.debug('Indi Focuser: on emergency routine started...')
        self.logger.debug('Indi Focuser: on emergency routine finished')

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

    def __str__(self):
        return f"Focuser: {self.device_name}"

    def __repr__(self):
        return self.__str__()
