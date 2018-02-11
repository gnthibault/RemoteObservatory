#Basic stuff
import logging
import json
import io

#Indi stuff
import PyIndi
from FilterWheel.IndiFilterWheel import IndiFilterWheel

class IndiVirtualFilterWheel(IndiFilterWheel):
    ''' Indi Virtual FilterWheel '''

    def __init__(self, indiClient, logger=None, configFileName=None,\
          connectOnCreate=True):
        logger = logger or logging.getLogger(__name__)
        
        logger.debug('Configuring Indi Virtual FilterWheel')

        # device related intialization
        IndiFilterWheel.__init__(self, indiClient, logger=logger,\
          configFileName=configFileName)

        # Finished configuring
        self.logger.debug('Configured Indi Virtual FilterWheel successfully')
