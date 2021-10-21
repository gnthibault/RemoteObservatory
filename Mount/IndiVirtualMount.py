#Basic stuff
import logging
import json
import io

#Indi stuff
from Mount.IndiMount import IndiMount

class IndiVirtualMount(IndiMount):
    ''' Indi Virtual Mount '''

    def __init__(self, indi_client, logger=None, configFileName=None,\
          connect_on_create=True):
        logger = logger or logging.getLogger(__name__)
        
        logger.debug('Configuring Indi Virtual Mount')

        # device related intialization
        IndiMount.__init__(self, indi_client,\
          configFileName=configFileName)

        # Finished configuring
        self.logger.debug('Configured Indi Virtual Mount successfully')
