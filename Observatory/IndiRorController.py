# Basic stuff
import logging

# Local
from Base.Base import Base

class IndiRorController(Base):
    """Controller roll off roof and other stuff
    """

    def __init__(self, config):
        Base.__init__(self)
        
        # TODO TN: this statement should be deleted and value should be
        # received fron a sensor """
        self.is_open = False

    def initialize(self):
        self.logger.debug("Initializing IndiRorController")
        
    def deinitialize(self):
        self.logger.debug("Deinitializing IndiRorController")

    def open(self):
        self.logger.debug("Opening IndiRorController")
        # TODO TN: this statement should be deleted and value should be
        # received fron a sensor """
        self.is_open = True

    def close(self):
        self.logger.debug("Closing IndiRorController")
        self._is_open = False

    @property
    def is_open(self):
        """ TODO TN: this getter should be changed and value should be received
            fron a sensor """
        return self._is_open

    @is_open.setter
    def is_open(self, do_open):
        """ TODO TN: this setter should be deleted and value should be received
            fron a sensor """
        self._is_open = do_open

    def status(self):
        return {"is_open": self.is_open}
