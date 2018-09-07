#Basic stuff
import logging
import json
import io

#Indi stuff
import PyIndi
from Camera.IndiCamera import IndiCamera

class IndiEos350DCamera(IndiCamera):
    ''' Indi Camera class for eos 350D (3456 × 2304 apsc cmos) '''

    def __init__(self, indiClient, logger=None, configFileName=None,
                 connectOnCreate=True):
        logger = logger or logging.getLogger(__name__)
        logger.debug('Configuring Indi EOS350D Camera')

        if config_filename is None:
            config_filename = './conf_files/IndiEos350DCamera.json'

        # device related intialization
        IndiCamera.__init__(self, indiClient, logger=logger,
                            configFileName=config_filename)

        # Finished configuring
        self.logger.debug('Configured Indi Eos 350D Camera successfully')

    '''
      Indi CCD related stuff
    '''
    def prepareShoot(self):
        self.setText("DEVICE_PORT",{"PORT":"/dev/ttyUSB0"})
        IndiCamera.prepareShoot(self)


