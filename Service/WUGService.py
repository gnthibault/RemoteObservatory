#Basic stuff
import json
import logging
from pathlib import Path

#Cached requests
import requests
import requests_cache

#Local stuff
from Base.Base import Base

class WUGService(Base):
    """ WUG Service """
    # API request engine
    defaultBaseAPIURL = 'http://api.wunderground.com/api'
    #update request only once every 3 min 
    defaultCacheTimeSec = 3*60

    def __init__(self, configFileName=None):
        Base.__init__(self)
        self.gpsCoordinates = {'latitude': '0.0', 'longitude': '0.0'}

        requests_cache.install_cache('wug_cache', backend='sqlite',\
        expire_after=self.defaultCacheTimeSec) 

        if configFileName is None:
            # Default file is ~/.wug.json
            home = Path.home()
            config = home / '.wug.json'
            self.configFileName = str(config)
        else:
            self.configFileName = configFileName

        # Now configuring
        self.logger.debug('Configuring WUG Service with file %s',\
            self.configFileName)

        # Get key from json
        with open(self.configFileName) as jsonFile:  
            data = json.load(jsonFile)
            self.key = data['key']
        
        # Finished configuring
        self.logger.debug('Configured WUG service successfully')

    def setGpsCoordinates(self,gpsCoordinates):
        self.gpsCoordinates = gpsCoordinates

    def sendRequest(self,APIFuncLink):
        try:
            # Forging the URL
            url = self.defaultBaseAPIURL+'/'+self.key+'/'+APIFuncLink+'/'+\
            self.gpsCoordinates['latitude']+','+self.gpsCoordinates['longitude']+\
            '.json'
            # Sending request
            self.logger.debug("WUGService about to send request: %s",url)
            data = requests.get(url).json()
            return data
        except requests.exceptions.RequestException as e:
            self.logger.error("WUGService error is %s",e)
            return None
