# Basic stuff
import logging
import json

# Astropy stuff
import astropy.units as AU
from astropy.coordinates import EarthLocation

# Astroplan stuff
from astroplan import Observer

#Time stuff
import pytz
from tzwhere import tzwhere

# Local
from Base.Base import Base

class ShedObservatory(Base):
    """Shed Observatory 
    """

    def __init__(self, configFileName=None, logger=None, servWeather=None):
        Base.__init__(self)
        
        if configFileName is None:
            self.configFileName = './conf_files/ShedObservatory.json'
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
        
        # Now find the timezone from the gps coordinate
        tzw = tzwhere.tzwhere()
        timezone_str = tzw.tzNameAt(self.gpsCoordinates['latitude'],
                                    self.gpsCoordinates['longitude'])
        self.timezone = pytz.timezone(timezone_str)
        self.logger.debug('Found timezone for observatory: {}'.format(
                          self.timezone.zone))

        # Other services
        self.servWeather = servWeather

        # Finished configuring
        self.logger.debug('Configured ShedObservatory successfully')
    
    def initialize(self):
        self.logger.debug("Initializing observatory")

    def deinitialize(self):
        self.logger.debug("Deinitializing observatory")

    def getGpsCoordinates(self):
        return self.gpsCoordinates

    def get_time_zone(self):
        return self.timezone

    def getAltitudeMeter(self):
        return self.altitudeMeter

    def get_horizon(self):
        return self.horizon

    def getOwnerName(self):
        return self.ownerName

    def open_everything(self):
        self.logger.debug('ShedObservatory: open everything....')
        pass
        self.logger.debug('ShedObservatory: everything opened')
   
    def close_everything(self):
        self.logger.debug('ShedObservatory: close everything....')
        pass
        self.logger.debug('ShedObservatory: everything closed')

    def onEmergency(self):
        self.logger.debug('ShedObservatory: on emergency routine started...')
        self.close_everything()
        self.logger.debug('ShedObservatory: on emergency routine finished')

    def switchOnFlatPannel(self):
        self.logger.debug('ShedObservatory: Switching on flat pannel')
        pass
        self.logger.debug('ShedObservatory: Flat pannel switched on')

    def getAstropyEarthLocation(self):
        return EarthLocation(lat=self.gpsCoordinates['latitude']*AU.deg,
                             lon=self.gpsCoordinates['longitude']*AU.deg,
                             height=self.altitudeMeter*AU.m)

    def getAstroplanObserver(self):
        location = self.getAstropyEarthLocation()
        pressure = 0.85 * AU.bar
        relative_humidity = 0.20
        temperature = 15 * AU.deg_C
        if self.servWeather is not None:
            pressure = (self.servWeather.getPressure_mb() / 1000) * AU.bar
            relative_humidity = self.servWeather.getRelative_humidity()
            temperature = self.servWeather.getTemp_c() * AU.deg_C

        observer = Observer(name=self.ownerName,
            location=location,
            pressure=pressure,
            relative_humidity=relative_humidity,
            temperature=temperature,
            timezone=self.timezone,
            description="Description goes here")

        return observer 
