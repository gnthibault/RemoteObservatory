# Basic stuff
import json
import logging
import os

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
from utils import load_module

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
            self.owner_name = data['ownerName']
            dome_module_name = data['domeModuleName']
            #flat_panel_module_name = data['flatPanelName']
        
        # Now find the timezone from the gps coordinate
        tzw = tzwhere.tzwhere()
        timezone_str = tzw.tzNameAt(self.gpsCoordinates['latitude'],
                                    self.gpsCoordinates['longitude'])
        self.timezone = pytz.timezone(timezone_str)
        self.logger.debug('Found timezone for observatory: {}'.format(
                          self.timezone.zone))

        # If dome is specified in the config, load dome
        if dome_module_name is not 'None':
            dome_module = load_module('Observatory.'+dome_module_name)
            self.dome = getattr(dome_module, dome_module_name)()
        else:
            self.dome = None

        # If flat panel is specified in the config, load flat_panel
        #if flat_panel_module_name is not 'None':
        #    flat_panel_module = load_module('Observatory.'+
        #                                    flat_panel_module_name)
        #    self.flat_panel = getattr(flat_panel_module,
        #                              flat_panel_module_name)()
        #else
        self.flat_panel = None

        # Other services
        self.servWeather = servWeather

        # Finished configuring
        self.logger.debug('Configured ShedObservatory successfully')
    
    def initialize(self):
        self.logger.debug("Initializing observatory")
        if self.has_dome:
            self.dome.initialize()
        if self.has_flat_panel:
            self.flat_panel.initialize()
        self.logger.debug("Successfully initialized observatory")

    def deinitialize(self):
        self.logger.debug("Deinitializing observatory")
        if self.has_dome:
            self.dome.deinitialize()
        if self.has_flat_panel:
            self.flat_panel.deinitialize()
        self.logger.debug("Successfully deinitialized observatory")

    def getGpsCoordinates(self):
        return self.gpsCoordinates

    def get_time_zone(self):
        return self.timezone

    def getAltitudeMeter(self):
        return self.altitudeMeter

    def get_horizon(self):
        return self.horizon

    def getOwnerName(self):
        return self.owner_name

    @property
    def has_dome(self):
        return self.dome is not None

    @property
    def has_flat_panel(self):
        return self.flat_panel is not None

    def open_everything(self):
        try:
            self.logger.debug('ShedObservatory: open everything....')
            if self.has_dome:
                self.dome.open()
            self.logger.debug('ShedObservatory: everything opened')
        except Exception as e:
            self.logger.error('Failed opening everything, error: {}'.format(e))
            return False
        return True
   
    def close_everything(self):
        try:
            self.logger.debug('ShedObservatory: close everything....')
            if self.has_dome:
                self.dome.close()
            self.logger.debug('ShedObservatory: everything closed')
        except Exception as e:
            self.logger.error('Failed closing everything, error: {}'.format(e))
            return False
        return True

    def onEmergency(self):
        self.logger.debug('ShedObservatory: on emergency routine started...')
        self.close_everything()
        self.logger.debug('ShedObservatory: on emergency routine finished')

    def switchOnFlatPannel(self):
        if self.has_flat_panel:
            self.logger.debug('ShedObservatory: Switching on flat pannel')
            self.flat_panel.switch_on()
            self.logger.debug('ShedObservatory: Flat pannel switched on')

    def switchOffFlatPannel(self):
        if self.has_flat_panel:
            self.logger.debug('ShedObservatory: Switching off flat pannel')
            self.flat_panel.switch_off()
            self.logger.debug('ShedObservatory: Flat pannel switched off')

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

        observer = Observer(name=self.owner_name,
            location=location,
            pressure=pressure,
            relative_humidity=relative_humidity,
            temperature=temperature,
            timezone=self.timezone,
            description="Description goes here")

        return observer

    def status(self):
        status = {'owner': self.owner_name,
                  'location': self.gpsCoordinates,
                  'altitude': self.altitudeMeter,
                  'timezone': self.timezone
                 }

        if self.has_dome:
            status['dome'] = self.dome.status()
        if self.has_flat_panel:
            status['flat_panel'] = self.flat_panel.status()

        return status
