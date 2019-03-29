# Basic stuff
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
from utils.error import ScopeControllerError

class ShedObservatory(Base):
    """Shed Observatory 
    """

    def __init__(self, servWeather=None, config=None):
        Base.__init__(self)
        
        # Now configuring class
        self.logger.debug('Configuring ShedObservatory')

        if config is None:
            config = dict(
                investigator = 'gnthibault',
                latitude = 45.01,  # Degrees
                longitude = 3.01,  # Degrees
                elevation = 600.0, # Meters
                horizon = {    # Degrees
                    0 : 30,
                    90 : 30,
                    180 : 30,
                    270 : 30},
                scope_controller = dict(
                    module = 'ArduiScopeController',
                    port = '/dev/ttyACM0'),
                dome_controller = dict(
                    module = None,
                    port = '/dev/ttyACM1')
            )

        # Get info from config
        self.gpsCoordinates = dict(latitude = config['latitude'],
                                   longitude = config['longitude'])
        self.altitudeMeter = config['elevation']
        self.horizon = config['horizon']
        self.investigator = config['investigator']
        
        # Now find the timezone from the gps coordinate
        tzw = tzwhere.tzwhere()
        timezone_str = tzw.tzNameAt(self.gpsCoordinates['latitude'],
                                    self.gpsCoordinates['longitude'])
        self.timezone = pytz.timezone(timezone_str)
        self.logger.debug('Found timezone for observatory: {}'.format(
                          self.timezone.zone))

        # If scope controller is specified in the config, load
        try:
            cfg = config['scope_controller']
            scope_controller_name = cfg['module']
            scope_controller = load_module('Observatory.'+scope_controller_name)
            self.scope_controller = getattr(scope_controller,
                                            scope_controller_name)(cfg)
        except Exception as e:
            self.scope_controller = None
            msg = 'Cannot instantiate scope controller properly: '.format(e)
            self.logger.error(msg)
            raise ScopeControllerError(msg)

        # If dome controller is specified in the config, load
        try:
            cfg = config['dome_controller']
            dome_controller_name = cfg['module']
            dome_controller = load_module('Observatory.'+dome_controller_name)
            self.dome_controller = getattr(dome_controller,
                                           dome_controller_name)(cfg)
        except Exception as e:
            self.logger.warning("Cannot load dome module: {}".format(e))
            self.dome_controller = None

        # Other services
        self.servWeather = servWeather

        # Finished configuring
        self.logger.debug('Configured ShedObservatory successfully')
    
    def initialize(self):
        self.logger.debug("Initializing observatory")
        if self.has_dome:
            self.dome_controller.initialize()
        if self.has_scope:
            self.scope_controller.initialize()
        self.logger.debug("Successfully initialized observatory")

    def deinitialize(self):
        self.logger.debug("Deinitializing observatory")
        if self.has_dome:
            self.dome_controller.deinitialize()
        if self.has_scope:
            self.scope_controller.deinitialize()
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
        return self.investigator

    @property
    def has_dome(self):
        return self.dome_controller is not None

    @property
    def has_scope(self):
        return self.scope_controller is not None

    def park(self):
        self.logger.debug('ShedObservatory: parking scope')
        if self.has_scope:
            self.scope_controller.close()

    def unpark(self):
        self.logger.debug('ShedObservatory: unparking scope')
        if self.has_scope:
            self.scope_controller.open()

    def open_everything(self):
        try:
            self.logger.debug('ShedObservatory: open everything....')
            if self.has_dome:
                self.dome_controller.open()
            if self.has_scope:
                self.scope_controller.open()
            self.logger.debug('ShedObservatory: everything opened')
        except Exception as e:
            self.logger.error('Failed opening everything, error: {}'.format(e))
            return False
        return True
   
    def close_everything(self):
        try:
            self.logger.debug('ShedObservatory: close everything....')
            if self.has_scope:
                self.scope_controller.close()
            if self.has_dome:
                self.dome_controller.close()
            self.logger.debug('ShedObservatory: everything closed')
        except Exception as e:
            self.logger.error('Failed closing everything, error: {}'.format(e))
            return False
        return True

    def onEmergency(self):
        self.logger.debug('ShedObservatory: on emergency routine started...')
        self.close_everything()
        self.logger.debug('ShedObservatory: on emergency routine finished')

    def switch_on_flat_panel(self):
        if self.has_scope_controller:
            self.logger.debug('ShedObservatory: Switching on flat pannel')
            self.scope_controller.switch_on_flat_panel()
            self.logger.debug('ShedObservatory: Flat pannel switched on')

    def switch_off_flat_panel(self):
        if self.has_scope_controller:
            self.logger.debug('ShedObservatory: Switching off flat pannel')
            self.scope_controller.switch_off_flat_panel()
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

        observer = Observer(name=self.investigator,
            location=location,
            pressure=pressure,
            relative_humidity=relative_humidity,
            temperature=temperature,
            timezone=self.timezone,
            description="Description goes here")

        return observer

    def status(self):
        status = {'owner': self.investigator,
                  'location': self.gpsCoordinates,
                  'altitude': self.altitudeMeter,
                  'timezone': str(self.timezone) # not directly serializable
                 }
        if self.has_dome and self.dome_controller.is_initialized:
            status['dome'] = self.dome_controller.status()
        if self.has_scope and self.scope_controller.is_initialized:
            status['scope'] = self.scope_controller.status()

        return status
