# Generic stuff
import logging
import re
import sys
import time

# time/date
from datetime import datetime as dt
from dateutil.parser import parse as date_parser

# Numerical stuff
import numpy as np

# Astropy
import astropy.units as u

# Local stuff
from Service.NTPTimeService import NTPTimeService

from utils.config import load_config
#from utils.messaging import PanMessaging


def get_mongodb():
    from utils.database import DB
    return DB()


class DummyCloudSensor:

    def __init__(self, store_result=True):
        print('Initializing cloud sensor')
        self.name = 'Random weather generator'
        self.safe_dict = None
        self.serv_time = NTPTimeService()
        self.weather_entries = []
        self.safety_delay = 60

        self.db = None
        if store_result:
            self.db = get_mongodb()

    def capture(self, store_result=False, send_message=False, **kwargs):
        """ Query the CloudWatcher """
        
        self.logger = kwargs.get('logger', logging.getLogger(__name__))
        self.logger.debug("Updating weather")

        data = {}
        data['weather_sensor_name'] = self.name

        data['sky_temp_C'] = np.random.randint(-10,30)
        data['ambient_temp_C'] = np.random.randint(-10,30)
        data['rain_sensor_temp_C'] = str(np.random.randint(-10,30))
        data['rain_frequency'] = np.random.randint(-10,30)
        data['errors'] = 'no error'
        data['wind_speed_KPH'] = str(np.random.randint(-10,100))

        # Make Safety Decision
        #self.safe_dict = self.make_safety_decision(data)
        data['safe'] = True
        data['sky_condition'] = 'Sky_condition'
        data['wind_condition'] = 'Wind_condition'
        data['gust_condition'] = 'Gust_condition'
        data['rain_condition'] = 'Rain_condition'

        # Store current weather
        data['date'] = self.serv_time.getUTCFromNTP()
        self.weather_entries.append(data)

        # If we get over a certain amount of entries, trim the earliest
        if len(self.weather_entries) > int(self.safety_delay):
            del self.weather_entries[:1]

        if send_message:
            self.send_message({'data': data}, channel='weather')

        if store_result:
            if self.db is None:
                self.db = get_mongodb()
            self.db.insert_current('weather', data)

        return data

