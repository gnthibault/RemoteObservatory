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
from Base.Base import Base
from helper.IndiDevice import IndiDevice
from Service.PanMessaging import PanMessaging


class IndiUranusMeteoSensor(threading.Thread, IndiDevice):
    """
        Here is the return of
        indi_getprop -h 192.168.8.202 -p 7624 "Uranus Meteo Sensor.*.*"
            Uranus Meteo Sensor.CONNECTION.CONNECT=On
            Uranus Meteo Sensor.CONNECTION.DISCONNECT=Off
            Uranus Meteo Sensor.DRIVER_INFO.DRIVER_NAME=Uranus Meteo Sensor
            Uranus Meteo Sensor.DRIVER_INFO.DRIVER_EXEC=indi_uranus_weather
            Uranus Meteo Sensor.DRIVER_INFO.DRIVER_VERSION=1.0
            Uranus Meteo Sensor.DRIVER_INFO.DRIVER_INTERFACE=192
            Uranus Meteo Sensor.DEBUG.ENABLE=Off
            Uranus Meteo Sensor.DEBUG.DISABLE=On
            Uranus Meteo Sensor.SIMULATION.ENABLE=Off
            Uranus Meteo Sensor.SIMULATION.DISABLE=On
            Uranus Meteo Sensor.CONFIG_PROCESS.CONFIG_LOAD=Off
            Uranus Meteo Sensor.CONFIG_PROCESS.CONFIG_SAVE=Off
            Uranus Meteo Sensor.CONFIG_PROCESS.CONFIG_DEFAULT=Off
            Uranus Meteo Sensor.CONFIG_PROCESS.CONFIG_PURGE=Off
            Uranus Meteo Sensor.POLLING_PERIOD.PERIOD_MS=5000
            Uranus Meteo Sensor.CONNECTION_MODE.CONNECTION_SERIAL=On
            Uranus Meteo Sensor.SYSTEM_PORTS.Pegasus_Astro_UPBv2_revD_UPB25S4VWV=Off
            Uranus Meteo Sensor.SYSTEM_PORTS.Pegasus_Astro_PPBADV_Gen2C_PPBA93RF0I=Off
            Uranus Meteo Sensor.SYSTEM_PORTS.Arduino_Uranus_MeteoSensor_95A5389D50555233342E3120FF12122B=Off
            Uranus Meteo Sensor.SYSTEM_PORTS.1a86_USB_Serial=Off
            Uranus Meteo Sensor.DEVICE_PORT.PORT=/dev/serial/by-id/usb-Arduino_Uranus_MeteoSensor_95A5389D50555233342E3120FF12122B-if00
            Uranus Meteo Sensor.DEVICE_BAUD_RATE.9600=Off
            Uranus Meteo Sensor.DEVICE_BAUD_RATE.19200=Off
            Uranus Meteo Sensor.DEVICE_BAUD_RATE.38400=Off
            Uranus Meteo Sensor.DEVICE_BAUD_RATE.57600=Off
            Uranus Meteo Sensor.DEVICE_BAUD_RATE.115200=On
            Uranus Meteo Sensor.DEVICE_BAUD_RATE.230400=Off
            Uranus Meteo Sensor.DEVICE_AUTO_SEARCH.INDI_ENABLED=Off
            Uranus Meteo Sensor.DEVICE_AUTO_SEARCH.INDI_DISABLED=On
            Uranus Meteo Sensor.DEVICE_PORT_SCAN.Scan Ports=Off
            Uranus Meteo Sensor.GEOGRAPHIC_COORD.LAT=43.932209999999997763
            Uranus Meteo Sensor.GEOGRAPHIC_COORD.LONG=5.7156500000000001194
            Uranus Meteo Sensor.GEOGRAPHIC_COORD.ELEV=0
            Uranus Meteo Sensor.TIME_UTC.UTC=2025-07-31T17:44:23
            Uranus Meteo Sensor.TIME_UTC.OFFSET=2.00
            Uranus Meteo Sensor.GPS_REFRESH.REFRESH=Off
            Uranus Meteo Sensor.GPS_REFRESH_PERIOD.PERIOD=0
            Uranus Meteo Sensor.SYSTEM_TIME_UPDATE.UPDATE_NEVER=Off
            Uranus Meteo Sensor.SYSTEM_TIME_UPDATE.UPDATE_ON_STARTUP=On
            Uranus Meteo Sensor.SYSTEM_TIME_UPDATE.UPDATE_ON_REFRESH=Off
            Uranus Meteo Sensor.SENSORS.AmbientTemperature=20.359999999999999432
            Uranus Meteo Sensor.SENSORS.RelativeHumidity=47
            Uranus Meteo Sensor.SENSORS.DewPoint=8.6699999999999999289
            Uranus Meteo Sensor.SENSORS.AbsolutePressure=944.26999999999998181
            Uranus Meteo Sensor.SENSORS.RelativePressure=0
            Uranus Meteo Sensor.SENSORS.BarometricAltitude=672
            Uranus Meteo Sensor.SENSORS.SkyTemperature=7.9100000000000001421
            Uranus Meteo Sensor.SENSORS.InfraredTemperature=20.550000000000000711
            Uranus Meteo Sensor.SENSORS.BatteryUsage=0
            Uranus Meteo Sensor.SENSORS.BatteryVoltage=5.0899999999999998579
            Uranus Meteo Sensor.CLOUDS.TemperatureDifference=19.730000000000000426
            Uranus Meteo Sensor.CLOUDS.CloudIndex=100
            Uranus Meteo Sensor.CLOUDS.CloudSkyTemperature=7.9100000000000001421
            Uranus Meteo Sensor.CLOUDS.CloudAmbientTemperature=20.550000000000000711
            Uranus Meteo Sensor.CLOUDS.InfraredEmissivity=1
            Uranus Meteo Sensor.SKYQUALITY.MPAS=19.820000000000000284
            Uranus Meteo Sensor.SKYQUALITY.NELM=5.3700000000000001066
            Uranus Meteo Sensor.SKYQUALITY.FullSpectrum=52
            Uranus Meteo Sensor.SKYQUALITY.VisualSpectrum=29
            Uranus Meteo Sensor.SKYQUALITY.InfraredSpectrum=23
            Uranus Meteo Sensor.SKYQUALITY_TIMER.VALUE=60
            Uranus Meteo Sensor.GPS.GPSFix=3
            Uranus Meteo Sensor.GPS.GPSTime=1753991063
            Uranus Meteo Sensor.GPS.UTCOffset=2
            Uranus Meteo Sensor.GPS.Latitude=43.932209999999997763
            Uranus Meteo Sensor.GPS.Longitude=5.7156500000000001194
            Uranus Meteo Sensor.GPS.SatelliteNumber=7
            Uranus Meteo Sensor.GPS.GPSSpeed=680
            Uranus Meteo Sensor.GPS.GPSBearing=0.54000000000000003553
            Uranus Meteo Sensor.WEATHER_UPDATE.PERIOD=60
            Uranus Meteo Sensor.WEATHER_REFRESH.REFRESH=Off
            Uranus Meteo Sensor.WEATHER_OVERRIDE.OVERRIDE=Off
            Uranus Meteo Sensor.WEATHER_STATUS.WEATHER_CLOUD=Alert
            Uranus Meteo Sensor.WEATHER_STATUS.WEATHER_TEMPERATURE=Ok
            Uranus Meteo Sensor.WEATHER_STATUS.WEATHER_HUMIDITY=Ok
            Uranus Meteo Sensor.WEATHER_PARAMETERS.WEATHER_CLOUD=100
            Uranus Meteo Sensor.WEATHER_PARAMETERS.WEATHER_MPAS=19.820000000000000284
            Uranus Meteo Sensor.WEATHER_PARAMETERS.WEATHER_TEMPERATURE=20.359999999999999432
            Uranus Meteo Sensor.WEATHER_PARAMETERS.WEATHER_HUMIDITY=47
            Uranus Meteo Sensor.WEATHER_CLOUD.MIN_OK=0
            Uranus Meteo Sensor.WEATHER_CLOUD.MAX_OK=85
            Uranus Meteo Sensor.WEATHER_CLOUD.PERC_WARN=15
            Uranus Meteo Sensor.WEATHER_CLOUD.ALERT_TYPE=0
            Uranus Meteo Sensor.WEATHER_MPAS.MIN_OK=1
            Uranus Meteo Sensor.WEATHER_MPAS.MAX_OK=30
            Uranus Meteo Sensor.WEATHER_MPAS.PERC_WARN=15
            Uranus Meteo Sensor.WEATHER_MPAS.ALERT_TYPE=0
            Uranus Meteo Sensor.WEATHER_TEMPERATURE.MIN_OK=-20
            Uranus Meteo Sensor.WEATHER_TEMPERATURE.MAX_OK=50
            Uranus Meteo Sensor.WEATHER_TEMPERATURE.PERC_WARN=15
            Uranus Meteo Sensor.WEATHER_TEMPERATURE.ALERT_TYPE=0
            Uranus Meteo Sensor.WEATHER_HUMIDITY.MIN_OK=0
            Uranus Meteo Sensor.WEATHER_HUMIDITY.MAX_OK=75
            Uranus Meteo Sensor.WEATHER_HUMIDITY.PERC_WARN=15
            Uranus Meteo Sensor.WEATHER_HUMIDITY.ALERT_TYPE=0
    """

    def __init__(self, logger=None, config=None, serv_time=None,
                 connect_on_create=True, loop_on_create=False):
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                service_name="AAG Cloud Watcher",
                delay_sec=60,
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"),
                limits=dict(
                    MAX_WEATHER_WIND_SPEED_KPH=25,
                    MAX_WEATHER_WIND_GUST_KPH=30,
                    MAX_WEATHER_CLOUD_COVER=5)
            )

        logger.debug(f"Indi Weather service, name is: {config['service_name']}")

        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config['service_name'],
                            indi_driver_name=config.get('indi_driver_name', None),
                            indi_client_config=config["indi_client"])

        # Init parent thread
        threading.Thread.__init__(self, target=self.serve)
        self._stop_event = threading.Event()

        # we broadcast data throught a message queue style mecanism
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

        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('Indi Weather service configured successfully')

        if loop_on_create:
            self.start()

    def initialize(self):
        """
        Connect, and setup coordinatea
        """
        self.connect()
        self.set_geographic_coord()
        self.set_update_period()

    def send_message(self, msg, channel='WEATHER'):
        if self.messaging is None:
            # TODO TN: if it breaks, checkout IndiWeather code instead
            self.messaging = PanMessaging(**self.config["messaging_publisher"])
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
                        {'LAT': self.config['observatory']['latitude'],
                         'LONG': self.config['observatory']['longitude'],
                         'ELEV': self.config['observatory']['elevation'] },
                        sync=True)

    def set_update_period(self):
        self.set_number('WEATHER_UPDATE',
                        {'PERIOD': self._delay_sec},
                        sync=True)

    def get_weather_features(self):
        """
            get the whole set of values
        """
        return self.get_number('WEATHER_PARAMETERS')

    def _fill_in_weather_data(self):
        """

        """
        features = self.get_weather_features()
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
        data["state"] = features["state"]
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
        data["safe"] = self._make_safety_decision(data)
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
        
