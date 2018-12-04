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
    def __init__(self, indiClient, logger=None, config_filename=None,
                 connectOnCreate=True):
        logger = logger or logging.getLogger(__name__)
        
        if config_filename is None:
          self.config_filename = './conf_files/IndiSimulatorFocuser.json'
        else:
          self.config_filename = config_filename

        # Now configuring class
        logger.debug('Indi Focuser, configuring with file {}'.format(
          self.config_filename))
        # Get config from json
        with open(self.config_filename) as jsonFile:
          data = json.load(jsonFile)
          deviceName = data['FocuserName']

        logger.debug('Indi Focuser, focuser name is: {}'.format(
          deviceName))
      
        # device related intialization
        IndiDevice.__init__(self, logger=logger, deviceName=deviceName,
          indiClient=indiClient)
        if connectOnCreate:
          self.connect()

        # Finished configuring
        self.logger.debug('Indi Focuser configured successfully')

    def onEmergency(self):
        self.logger.debug('Indi Focuser: on emergency routine started...')
        self.logger.debug('Indi Focuser: on emergency routine finished')

    def __str__(self):
        return 'Focuser: {}'.format(self.name)

    def __repr__(self):
        return self.__str__()
