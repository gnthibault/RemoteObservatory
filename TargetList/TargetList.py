# Basic stuff
import json
import logging

# Astropy stuff
from astropy import units as u
from astropy.time import Time as aspyTime
from astropy.coordinates import EarthLocation

class TargetList:

    def __init__(self, ntpServ, obs, configFileName=None, logger=None):
        self.netServ = ntpServ
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
            data = json.load(jsonFile)
            self.gpsCoordinates = data['TargetList']
            self.logger.debug('TargetList gps coordinates are: {}'.format(
                              self.gpsCoordinates))
        
        # Finished configuring
        self.logger.debug('Configured TargetList successfully')


    def getAstropyTimeFromUTC(self):
      return aspyTime(self.ntpServ.getUTCFromNTP())
      
      
    def getAstropyEarthLocation(self):
        gpsCoord = self.obs.getGpsCoordinates()
        altitude = self.obs.getAltitudeMeter()

        return EarthLocation(lat=gpsCoord['latitude']*u.deg,
                             lon=gpsCoord['longitude']*u.deg,
                             height=altitude*u.m)

