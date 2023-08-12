# Basic stuff
import logging
import os

# Astropy stuff
import astropy.units as u
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
from utils.error import DomeControllerError

class Observatory(Base):
    """Shed Observatory 
    """

    def __init__(self, serv_weather=None, config=None):
        Base.__init__(self)
        
        # Now configuring class
        self.logger.debug('Configuring Observatory')

        if config is None:
            config = dict(
                investigator='gnthibault',
                latitude=45.01,  # Degrees
                longitude=3.01,  # Degrees
                elevation=600.0, # Meters
                horizon={        # Degrees
                    0: 30,
                    90: 30,
                    180: 30,
                    270: 30},
                scope_controller = dict(
                    module='DummyScopeController',
                    port='/dev/ttyACM0'),
                dome_controller=dict(
                    module='IndiDomeController',
                    port='/dev/ttyACM1')
            )

        # Get info from config
        self.gps_coordinates = dict(latitude=config['latitude'],
                                    longitude=config['longitude'])
        self.altitude_meter = config['elevation']
        self.horizon = config['horizon']
        self.max_altitude_degree = config.get("max_altitude_degree", 90)
        self.investigator = config['investigator']
        
        # Now find the timezone from the gps coordinate
        try:
            timezone_str = self.config['observatory']['timezone']
        except Exception as e:
            tzw = tzwhere.tzwhere()
            timezone_str = tzw.tzNameAt(self.gps_coordinates['latitude'],
                                        self.gps_coordinates['longitude'])
        self.timezone = pytz.timezone(timezone_str)
        self.logger.debug(f"Found timezone for observatory: {self.timezone.zone}")

        # If scope controller is specified in the config, load
        try:
            cfg = config['scope_controller']
            scope_controller_name = cfg['module']
            scope_controller = load_module('Observatory.'+scope_controller_name)
            self.scope_controller = getattr(scope_controller, scope_controller_name)(cfg)
        except Exception as e:
            self.scope_controller = None
            msg = f"Cannot instantiate scope controller properly: {e}"
            self.logger.error(msg)
            raise ScopeControllerError(msg)

        # If dome controller is specified in the config, load
        try:
            cfg = config['dome_controller']
            dome_controller_name = cfg['module']
            dome_controller = load_module('Observatory.'+dome_controller_name)
            self.dome_controller = getattr(dome_controller, dome_controller_name)(cfg)
        except Exception as e:
            self.dome_controller = None
            msg = f"Cannot load dome module: {e}"
            self.logger.error(msg)
            raise DomeControllerError(msg)

        # Other services
        self.serv_weather = serv_weather

        # Finished configuring
        self.logger.debug('Configured Observatory successfully')
    
    # def initialize(self):
    #     self.logger.debug("Initializing observatory")
    #     if self.has_dome:
    #         self.dome_controller.initialize()
    #     if self.has_scope:
    #         self.scope_controller.initialize()
    #     self.logger.debug("Successfully initialized observatory")

    # def deinitialize(self):
    #     self.logger.debug("Deinitializing observatory")
    #     if self.has_dome:
    #         self.dome_controller.deinitialize()
    #     if self.has_scope:
    #         self.scope_controller.deinitialize()
    #     self.logger.debug("Successfully deinitialized observatory")

    def get_gps_coordinates(self):
        return self.gps_coordinates

    def get_time_zone(self):
        return self.timezone

    def get_altitude_meter(self):
        return self.altitude_meter

    def get_horizon(self):
        return self.horizon

    def getOwnerName(self):
        return self.investigator

    @property
    def has_dome(self):
        return not (self.dome_controller is None)

    @property
    def has_scope(self):
        return not (self.scope_controller is None)

    @property
    def is_initialized(self):
        ret = True
        if self.has_dome and self.dome_controller.is_initialized:
            ret = ret and self.dome_controller.is_initialized
        if self.has_scope and self.scope_controller.is_initialized:
            ret = ret and self.scope_controller.is_initialized


    def park(self):
        self.logger.debug('Observatory: parking observatory')
        if self.has_dome:
            self.dome_controller.park()
        if self.has_scope:
            self.scope_controller.park()

    def unpark(self):
        self.logger.debug('Observatory: unparking')
        if self.has_dome:
            self.dome_controller.unpark()
        if self.has_scope:
            self.scope_controller.unpark()
        self.logger.debug('Successfully unparked Observatory')

    # def reset_config(self):
    #     if self.has_scope:
    #         self.scope_controller.reset_config()

    def open_everything(self):
        try:
            self.logger.debug('Observatory: open everything....')
            if self.has_dome:
                self.dome_controller.open()
            if self.has_scope:
                self.scope_controller.open()
            self.logger.debug('Observatory: everything opened')
        except Exception as e:
            self.logger.error('Failed opening everything, error: {}'.format(e))
            return False
        return True
   
    def close_everything(self):
        try:
            self.logger.debug('Observatory: close everything....')
            if self.has_scope:
                self.scope_controller.close()
            if self.has_dome:
                self.dome_controller.close()
            self.logger.debug('Observatory: everything closed')
        except Exception as e:
            self.logger.error(f"Failed closing everything, error: {e}")
            return False
        return True

    def on_emergency(self):
        self.logger.debug('Observatory: on emergency routine started...')
        self.close_everything()
        self.logger.debug('Observatory: on emergency routine finished')

    def switch_on_flat_panel(self):
        if self.has_scope_controller:
            self.logger.debug('Observatory: Switching on flat pannel')
            self.scope_controller.switch_on_flat_panel()
            self.logger.debug('Observatory: Flat pannel switched on')

    def switch_off_flat_panel(self):
        if self.has_scope_controller:
            self.logger.debug('Observatory: Switching off flat pannel')
            self.scope_controller.switch_off_flat_panel()
            self.logger.debug('Observatory: Flat pannel switched off')

    def getAstropyEarthLocation(self):
        return EarthLocation(lat=self.gps_coordinates['latitude']*u.deg,
                             lon=self.gps_coordinates['longitude']*u.deg,
                             height=self.altitude_meter*u.m)

    def getAstroplanObserver(self):
        location = self.getAstropyEarthLocation()
        pressure = 1 * u.bar
        relative_humidity = 0.20
        temperature = 15 * u.deg_C
        if self.serv_weather is not None:
            pressure = (self.serv_weather.getPressure_mb() / 1000) * u.bar
            relative_humidity = self.serv_weather.getRelative_humidity()
            temperature = self.serv_weather.getTemp_c() * u.deg_C

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
                  'location': self.gps_coordinates,
                  'altitude': self.altitude_meter,
                  'timezone': str(self.timezone) # not directly serializable
                 }
        if self.has_dome and self.dome_controller.is_initialized:
            status['dome'] = self.dome_controller.status()
        if self.has_scope and self.scope_controller.is_initialized:
            status['scope'] = self.scope_controller.status()

        return status
