# Basic stuff
import logging
import json

# Local
from Base.Base import Base


class IsOpenSensor():
    """ default sensor """
    def __init__(self):
        pass

class RorDome(Base):
    """Shed Observatory 
    """

    def __init__(self, configFileName=None):
        Base.__init__(self)
        
        if configFileName is None:
            self.configFileName = './conf_files/RorDome.json'
        else:
            self.configFileName = configFileName

        # Now configuring class
        self.logger.debug('Configuring RorDome with file {}'.format(
                          self.configFileName))

        # Get key from json
        with open(self.configFileName) as jsonFile:
            data = json.load(jsonFile)
            self.name = data['DomeName']

        # TODO TN: this statement should be deleted and value should be
        # received fron a sensor """
        self.is_open = False

        # Finished configuring
        self.logger.debug('Configured RorDome successfully')

    def initialize(self):
        self.logger.debug("Initializing RorDome")
        
    def deinitialize(self):
        self.logger.debug("Deinitializing RorDome")

    def open(self):
        self.logger.debug("Opening RorDome")
        # TODO TN: this statement should be deleted and value should be
        # received fron a sensor """
        self.is_open = True

    def close(self):
        self.logger.debug("Closing RorDome")
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
