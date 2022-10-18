# Generic stuff
from collections import deque
import json
import logging
import threading
import time

# Numerical tools
import numpy as np

# Astropy
import astropy.units as u

#Local stuff
from Base.Base import _config
from helper.IndiDevice import IndiDevice
from Service.PanMessaging import PanMessaging

class IndiWeather(threading.Thread, IndiDevice):
    """
        Based on indi-driver compatible stations, and simulator
    """

    def __init__(self, logger=None, config=None, serv_time=None,
                 connect_on_create=True, loop_on_create=False):
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                service_name="Weather Simulator",
                delay_sec=60,
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"),
                observatory=dict(
                    latitude=43.56,   # Degrees
                    longitude=5.43,   # Degrees
                    elevation=150.0,  # Meters
                ),
                limits=dict(
                    MAX_WEATHER_WIND_SPEED_KPH=25,
                    MAX_WEATHER_WIND_GUST_KPH=30,
                    MAX_WEATHER_CLOUD_COVER=5)
            )

        logger.debug(f"Indi Weather service, name is: {config['service_name']}")

        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config['service_name'],
                            indi_client_config=config["indi_client"])

        # Init parent thread
        threading.Thread.__init__(self, target=self.serve)
        self._stop_event = threading.Event()

        # we broadcast data through a message queue style mechanism
        self.messaging = None

        # store result in a database
        self.serv_time = serv_time
        self.store_result = True
        self._do_run = True
        self._delay_sec = config["delay_sec"]
        # we store the last 10 entries
        self.weather_entries = deque([], 3)

        # Actual threshold for safety alerts
        self.limits = config["limits"]

        # Observatory location
        self.observatory = config["observatory"]

        if connect_on_create:
            self.initialize(config=config)

        # Finished configuring
        self.logger.debug('Indi Weather service configured successfully')

        if loop_on_create:
            self.start()

    def initialize(self, config=None):
        """
        Connect, and setup coordinatea
        """
        self.connect()
        self.set_geographic_coord()
        self.set_update_period()
        self.initialize_messaging(config=config)

    def initialize_messaging(self, config):
        if self.messaging is None:
            self.messaging = PanMessaging(**config["messaging"])

    def send_message(self, msg, channel='WEATHER'):
        self.messaging.send_message(channel, msg)

    def capture(self, send_message=True, store_result=True):
        """ Query the weather station and eventually publish results"""
        self.logger.debug("Updating weather")
        data = self._fill_in_weather_data()
        data['weather_sensor_name'] = self.device_name
        data['date'] = self.serv_time.get_utc()
        self.weather_entries.append(data)

        if send_message:
            self.send_message({'data': data}, channel='WEATHER')

        if store_result and self.store_result:
            self.db.insert_current('weather', data)

        return data

    def serve(self):
        """
        Continuously generates weather reports
        """
        while not self.stopped():
            self.capture()
            time.sleep(self._delay_sec)

    def stop(self):
        """
        Stops the web server.
        """
        self._stop_event.set()

    def stopped(self):
        """
        Checks if server is stopped.

        :return: True if server is stopped, False otherwise
        """
        return self._stop_event.is_set()

    def set_geographic_coord(self):
        self.set_number('GEOGRAPHIC_COORD',
                        {'LAT': self.observatory['latitude'],
                         'LONG': self.observatory['longitude'],
                         'ELEV': self.observatory['elevation']},
                        sync=True,
                        timeout=self.defaultTimeout)

    def set_update_period(self):
        self.set_number('WEATHER_UPDATE',
                        {'PERIOD': self._delay_sec},
                        sync=True,
                        timeout=self.defaultTimeout)

    def get_weather_features(self):
        """
            get the whole set of values for both:
            WATHER_STATUS:
            {'WEATHER_FORECAST': 'Ok',
             'WEATHER_TEMPERATURE': 'Ok',
             'WEATHER_WIND_SPEED': 'Ok',
             'WEATHER_RAIN_HOUR': 'Ok'}
            WEATHER_PARAMETERS:
            {'WEATHER_FORECAST': 0.0,
             'WEATHER_TEMPERATURE': 15.0,
             'WEATHER_WIND_SPEED': 0.0,
             'WEATHER_WIND_GUST': 0.0,
             'WEATHER_RAIN_HOUR': 0.0}
        """
        status = self.get_light("WEATHER_STATUS")
        numbers = self.get_number("WEATHER_PARAMETERS")
        return status, numbers

    def _fill_in_weather_data(self):
        """

        """
        status, features = self.get_weather_features()
        data = {}
        #data['sky_temp_C'] = np.random.randint(-10, 30)
        #data['ambient_temp_C'] = np.random.randint(-10, 30)
        #data['rain_sensor_temp_C'] = np.random.randint(-10, 30)
        #data['rain_frequency'] = np.random.randint(-10, 30)
        #data['errors'] = 'no error'
        #data['wind_speed_KPH'] = np.random.randint(0, 100)

        # some electronic stuff
        #data['pwm_value'] = np.random.randint(0, 50)
        #data['ldr_resistance_Ohm'] = np.random.randint(2500, 5000)

        # Make Safety Decision
        # self.safe_dict = self.make_safety_decision(data)
        #data['safe'] = True
        #data['sky_condition'] = 'Sky_condition'
        #data['wind_condition'] = 'Wind_condition'
        #data['gust_condition'] = 'Gust_condition'
        #data['rain_condition'] = 'Rain_condition'

        # Generic indi state for this property, can be OK, IDLE, BUSY, ALERT
        if all([status[f] == "Ok" for f in ["WEATHER_FORECAST", "WEATHER_TEMPERATURE", "WEATHER_WIND_SPEED", "WEATHER_RAIN_HOUR"]]):
            data["state"] = "OK"
        else:
            data["state"] = "NOK"
        # name: WEATHER_FORECAST, label: Weather, format: '%4.2f'
        data["WEATHER_FORECAST"] = features["WEATHER_FORECAST"]
        # name: WEATHER_TEMPERATURE, label: Temperature (C), format: '%4.2f'
        data["WEATHER_TEMPERATURE"] = features["WEATHER_TEMPERATURE"]
        # name: WEATHER_WIND_SPEED, label: Wind (kph), format: '%4.2f'
        data["WEATHER_WIND_SPEED"] = features["WEATHER_WIND_SPEED"]
        # name: WEATHER_WIND_GUST, label: Gust (kph), format: '%4.2f'
        data["WEATHER_WIND_GUST"] = features["WEATHER_WIND_GUST"]
        # name: WEATHER_RAIN_HOUR, label: Precip (mm), format: '%4.2f'
        data["WEATHER_RAIN_HOUR"] = features["WEATHER_RAIN_HOUR"]
        data["safe"] = self._make_safety_decision(data) #True or False
        return data

    def _make_safety_decision(self, features):
        """
        based on:
            name: WEATHER_FORECAST, label: Weather, format: '%4.2f'
            name: WEATHER_TEMPERATURE, label: Temperature (C), format: '%4.2f'
            name: WEATHER_WIND_SPEED, label: Wind (kph), format: '%4.2f'
            name: WEATHER_WIND_GUST, label: Gust (kph), format: '%4.2f'
            name: WEATHER_RAIN_HOUR, label: Precip (mm), format: '%4.2f'
        """
        status = features["state"] == 'OK'
        status = status and (np.float32(features["WEATHER_WIND_SPEED"]) <
                             self.limits["MAX_WEATHER_WIND_SPEED_KPH"])
        status = status and (np.float32(features["WEATHER_WIND_GUST"]) <
                             self.limits["MAX_WEATHER_WIND_GUST_KPH"])
        status = status and (np.float32(features["WEATHER_RAIN_HOUR"]) == 0)
        return bool(status)

    def __str__(self):
        return f"Weather service: {self.device_name}"

    def __repr__(self):
        return self.__str__()        # Get key from json
        
