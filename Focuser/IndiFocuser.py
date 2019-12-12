# Basic stuff
import io
import json
import logging

# Indi stuff
import PyIndi
from helper.IndiDevice import IndiDevice


class IndiFocuser(IndiDevice):
    """

    """
    def __init__(self, logger=None, config=None,
                 connect_on_create=True):
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                focuser_name="Focuser Simulator",
                port="/dev/ttyUSB0",
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"
                ))

        self.port = config['port']

        logger.debug(f"Indi Focuser, focuser name is: {config['focuser_name']}")

        # device related intialization
        IndiDevice.__init__(self, logger=logger,
                            device_name=config['focuser_name'],
                            indi_client_config=config["indi_client"])
        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('Indi Focuser configured successfully')

    def initialize(self):
        self._setup_indi_client()
        self.connect_client()
        self.connect_driver()
        self.set_port()
        self.connect_device()

    def set_port(self):
        self.set_text("DEVICE_PORT", {"PORT": self.port})

    def on_emergency(self):
        self.logger.debug('Indi Focuser: on emergency routine started...')
        self.logger.debug('Indi Focuser: on emergency routine finished')

    def __str__(self):
        return f"Focuser: {self.device_name}"

    def __repr__(self):
        return self.__str__()
