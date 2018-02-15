# Basic stuff
import json
import logging

# Astropy stuff
from astropy import units as u
from astropy.time import Time as aspyTime
from astropy.coordinates import EarthLocation

class TargetList:

    def __init__(self, ntpServ, obs, configFileName=None, logger=None):
        self.ntpServ = ntpServ
        self.obs = obs
        self.logger = logger or logging.getLogger(__name__)
        
        if configFileName is None:
            self.configFileName = 'TargetList.json'
        else:
            self.configFileName = configFileName

        # Now configuring class
        self.logger.debug('Configuring TargetList with file {}'.format(
                          self.configFileName))

        # Get key from json
        with open(self.configFileName) as jsonFile:
            self.targetList = json.load(jsonFile)
            self.logger.debug('TargetList is: {}'.format(self.targetList))
        
        # Finished configuring
        self.logger.debug('TargetList configured successfully')


    def getAstropyTimeFromUTC(self):
      return aspyTime(self.ntpServ.getUTCFromNTP())
      
      
    def getAstropyEarthLocation(self):
        gpsCoord = self.obs.getGpsCoordinates()
        altitude = self.obs.getAltitudeMeter()

        return EarthLocation(lat=gpsCoord['latitude']*u.deg,
                             lon=gpsCoord['longitude']*u.deg,
                             height=altitude*u.m)

    def getTargetList(self):
        return self.targetList
