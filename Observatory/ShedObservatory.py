# Basic stuff
import logging
import json

# Astropy stuff
import astropy.units as u
from astropy.coordinates import EarthLocation

# Astroplan stuff
from astroplan import Observer

class ShedObservatory(object):
    """Shed Observatory 
    """

    def __init__(self, configFileName=None, logger=None, servWeather=None):
        self.logger = logger or logging.getLogger(__name__)
        
        if configFileName is None:
            self.configFileName = 'ShedObservatory.json'
        else:
            self.configFileName = configFileName

        # Now configuring class
        self.logger.debug('Configuring ShedObservatory with file {}'.format(
                          self.configFileName))

        # Get key from json
        with open(self.configFileName) as jsonFile:
            data = json.load(jsonFile)
            self.gpsCoordinates = data['gpsCoordinates']
            self.logger.debug('ShedObservatory gps coordinates are: {}'.format(
                              self.gpsCoordinates))
            self.altitudeMeter = int(data['altitudeMeter'])
            self.horizon = data['horizon']
            self.ownerName = data['ownerName']
        
        # Finished configuring
        self.logger.debug('Configured ShedObservatory successfully')
    
    def getGpsCoordinates(self):
        return self.gpsCoordinates

    def getAltitudeMeter(self):
        return self.altitudeMeter

    def getHorizon(self):
        return self.horizon

    def getOwnerName(self):
        return self.ownerName

    def openEverything(self):
        self.logger.debug('ShedObservatory: open everything....')
        pass
        self.logger.debug('ShedObservatory: everything opened')
   
    def closeEverything(self):
        self.logger.debug('ShedObservatory: close everything....')
        pass
        self.logger.debug('ShedObservatory: everything closed')

    def onEmergency(self):
        self.logger.debug('ShedObservatory: on emergency routine started...')
        self.closeEverything()
        self.logger.debug('ShedObservatory: on emergency routine finished')

    def switchOnFlatPannel(self):
        self.logger.debug('ShedObservatory: Switching on flat pannel')
        pass
        self.logger.debug('ShedObservatory: Flat pannel switched on')

    def getAstropyEarthLocation(self):
        return EarthLocation(lat=self.gpsCoordinates['latitude']*u.deg,
                             lon=self.gpsCoordinates['longitude']*u.deg,
                             height=self.altitudeMeter*u.m)

    def getAstroplanObserver(self):
        location = self.getAstropyEarthLocation()
        pressure = 0.9 * u.bar,
        relative_humidity = 0.20,
        temperature = 15 * u.deg_C,
        if not (self.servWeather is None):
            pressure = self.servWeather.getPressure_mb() * u.bar,#TODO TN
            relative_humidity = self.servWeather.getRelative_humidity(),
            temperature = self.servWeather.getTemp_c() * u.deg_C,

        observer = Observer(name=self.ownerName,
            location=location,
            pressure=0.615 * u.bar,
            relative_humidity=0.11,
            temperature=0 * u.deg_C,
            timezone=timezone('US/Hawaii'),
            description="Description goes here")

