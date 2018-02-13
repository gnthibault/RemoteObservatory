# Basic stuff
import json
import logging

# Astropy stuff
from astropy import units as u
from astropy.time import Time as aspyTime
from astropy.coordinates import EarthLocation

class TargetList:

    def __init__(self, ntpServ, obs):
        self.netServ = ntpServ
        self.obs = obs


    def getAstropyTimeFromUTC(self):
      return aspyTime(self.ntpServ.getUTCFromNTP())
      
      
    def getAstropyEarthLocation(self):
        gpsCoord = self.obs.getGpsCoordinates()
        altitude = self.obs.getAltitudeMeter()

        return EarthLocation(lat=gpsCoord['latitude']*u.deg,
                             lon=gpsCoord['longitude']*u.deg,
                             height=altitude*u.m)

