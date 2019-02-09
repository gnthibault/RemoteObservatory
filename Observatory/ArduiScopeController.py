# Basic stuff
import logging

# Local
from Base.Base import Base

class ArduiScopeController(Base):
    def __init__(self):
        Base.__init__(self)
        self.latest_status = dict(main_status="inactive")

    def initialize(self):
        self.latest_status["main_status"]="active"
        self.logger.debug("Initializing ArduiScopeController")

    def deinitialize(self):
        self.latest_status["main_status"]="inactive"
        self.logger.debug("Deinitializing ArduiScopeController")

    def open(self):
        """ blocking call: opens both main telescope and guiding scope dustcap
        """
        self.logger.debug("Opening ArduiScopeController")

    def close(self):
        """ blocking call: closes both main telescope and guiding scope dustcap
        """
        self.logger.debug("Closing ArduiScopeController")

    def switch_on_flat_panel(self):
        """ blocking call: switch on flip flat
        """
        self.logger.debug("Switching on flip flat")

    def switch_off_flat_panel(self):
        """ blocking call: switch off flip flat
        """
        self.logger.debug("Switching off flip flat")

    def status(self):
        return self.latest_status
