#Basic stuff
import json
import logging
from pathlib import Path

#Cached requests
import requests
import requests_cache

class WUGService(object):
  """ WUG Service """

  def __init__(self, configFileName=None, logger=None):
    self.logger = logger or logging.getLogger(__name__)
    self.gpsCoordinates = {'latitude': '0.0', 'longitude': '0.0'}

    # API request engine
    self.baseAPIURL = 'http://api.wunderground.com/api'
    #update request only once every 3 min 
    self.cacheTimeSec = 3*60
    requests_cache.install_cache('wug_cache', backend='sqlite',\
    expire_after=self.cacheTimeSec) 

    if configFileName is None:
      # Default file is ~/.wug.json
      home = Path.home()
      config = home / '.wug.json'
      self.configFileName = str(config)
    else:
      self.configFileName = configFileName

    # Now configuring
    self.logger.info('Configuring WUG Service with file %s',\
    self.configFileName)

    # Get key from json
    with open(self.configFileName) as jsonFile:  
      data = json.load(jsonFile)
      self.key = data['key']
    
    # Finished configuring
    self.logger.info('Configured WUG service successfully')

  def setGpsCoordinates(self,gpsCoordinates):
    self.gpsCoordinates = gpsCoordinates
  
  def sendRequest(self,APIFuncLink):
    try:
      # Forging the URL
      url = self.baseAPIURL+'/'+self.key+'/'+APIFuncLink+'/'+\
      self.gpsCoordinates['latitude']+','+self.gpsCoordinates['longitude']+\
      '.json'
      # Sending request
      self.logger.debug("WUGService about to send request: %s",url)
      data = requests.get(url).json()
      return data
    except requests.exceptions.RequestException as e:
      self.logger.error("WUGService error is %s",e)
      return None
