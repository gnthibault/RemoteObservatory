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
    def __init__(self, indi_client, logger=None, config_filename=None,
                 connect_on_create=True):
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
          device_name = data['FocuserName']

        logger.debug('Indi Focuser, focuser name is: {}'.format(
          device_name))
      
        # device related intialization
        IndiDevice.__init__(self, logger=logger, device_name=device_name,
          indi_client=indi_client)
        if connect_on_create:
          self.connect()

        # Finished configuring
        self.logger.debug('Indi Focuser configured successfully')

    def on_emergency(self):
        self.logger.debug('Indi Focuser: on emergency routine started...')
        self.logger.debug('Indi Focuser: on emergency routine finished')

    def __str__(self):
        return 'Focuser: {}'.format(self.name)

    def __repr__(self):
        return self.__str__()
