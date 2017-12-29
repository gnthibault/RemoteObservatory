#Basic stuff
import json
import logging
from pathlib import Path

# Service stuff
import urllib.request
import urllib.error

class WUGService(object):
  """ WUG Service """

  def __init__(self, configFileName=None, logger=None):
    self.logger = logger or logging.getLogger(__name__)
    self.gpsCoordinates = {'latitude': '0.0', 'longitude': '0.0'}
    self.baseAPIURL = 'http://api.wunderground.com/api'

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

      self.logger.debug("WUGService about to send request: %s",url)

      req = urllib.request.Request(url)
      with urllib.request.urlopen(req) as res:
        jsonString = res.read()
        data = json.loads(jsonString)
    except urllib.error.URLError as e:
      logger.error("WUGService error is ",e.reason)

    return data
