#Basic stuff
import logging
import json
import io

#Indi stuff
import PyIndi
from Camera.IndiCamera import IndiCamera

class IndiASI120MCCamera(IndiCamera):
    ''' Indi Camera class for eos 350D (3456 × 2304 apsc cmos) '''

    def __init__(self, indiClient, logger=None, config_filename=None,
                 connectOnCreate=True):
        logger = logger or logging.getLogger(__name__)
        logger.debug('Configuring Indi EOS350D Camera')

        if config_filename is None:
            config_filename = './conf_files/IndiASI120MCCamera.json'

        # device related intialization
        IndiCamera.__init__(self, indiClient, logger=logger,
                            configFileName=config_filename)

        # Finished configuring
        self.logger.debug('Configured Indi ASI120MC camera successfully')

    '''
      Indi CCD related stuff
    '''
    def get_dynamic(self):
        return self.get_number('ADC_DEPTH')['BITS']['value']

    def set_gain(self, value):
        self.setNumber('CCD_CONTROLS', {'Gain':value})
        pass

    def get_gain(self):
        return self.get_number('CCD_CONTROLS')['Gain']['value']

