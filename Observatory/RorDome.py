# Basic stuff
import logging
import json

# Local
from Base.Base import Base




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

        # Finished configuring
        self.logger.debug('Configured RorDome successfully')

    def initialize(self):
        self.logger.debug("Initializing RorDome")
        
    def deinitialize(self):
        self.logger.debug("Deinitializing RorDome")

    def open(self):
        self.logger.debug("Opening RorDome")
        self._is_open = True

    def close(self):
        self.logger.debug("Closing RorDome")
        self._is_open = False

    @property
    def is_open(self):
        return self._is_open

    def status(self):
        return {"is_open": self.is_open}
