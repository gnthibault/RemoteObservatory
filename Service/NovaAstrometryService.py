#Basic stuff
import json
import logging
from pathlib import Path


class NovaAstrometryService(object):
  """ Nova Astrometry Service """
  # API request engine
  defaultAPIURL = 'http://nova.astrometry.net/api/'

  def __init__(self, configFileName=None, logger=None):
    self.logger = logger or logging.getLogger(__name__)

    if configFileName is None:
      # Default file is ~/.nova.json
      home = Path.home()
      config = home / '.nova.json'
      self.configFileName = str(config)
    else:
      self.configFileName = configFileName

    # Now configuring
    self.logger.debug('Configuring Nova Astrometry Service with file %s',\
      self.configFileName)

    # Get key from json
    with open(self.configFileName) as jsonFile:  
      data = json.load(jsonFile)
      self.key = data['key']
    
    # Finished configuring
    self.logger.debug('Configured Nova Astrometry service successfully')

