#Basic stuff
import logging
import json
import io

#Indi stuff
import PyIndi
from Mount.IndiMount import IndiMount

class IndiVirtualMount(IndiMount):
    ''' Indi Virtual Mount '''

    def __init__(self, indiClient, logger=None, configFileName=None,\
          connectOnCreate=True):
        logger = logger or logging.getLogger(__name__)
        
        logger.debug('Configuring Indi Virtual Mount')

        # device related intialization
        IndiMount.__init__(self, indiClient, logger=logger,\
          configFileName=configFileName)

        # Finished configuring
        self.logger.debug('Configured Indi Virtual Mount successfully')
