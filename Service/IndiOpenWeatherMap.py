# Generic stuff
import json
import logging

#Local stuff
from Service.IndiWeather import IndiWeather

class IndiOpenWeatherMap(IndiWeather):
    """

    """

    def __init__(self, logger=None, config=None, serv_time=None,
                 connect_on_create=True, loop_on_create=False):
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                service_name="OpenWeatherMap",
                key_path="/var/RemoteObservatory/keys.json",
                publish_port=6510,
                delay_sec=60,
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"
                ))

        logger.debug(f"Indi OpenWeatherMap service, name is: "
                     f"{config['service_name']}")

        # device related intialization
        super().__init__(logger=logger, config=config, serv_time=serv_time,
                         connect_on_create=False, loop_on_create=False)

        # actual specific attributes of that class
        self.api_key = None

        if connect_on_create:
            self.initialize(config)

        if loop_on_create:
            self.start()

        # Finished configuring
        self.logger.debug('Indi Weather service configured successfully')

    def initialize(self, config):
        super().initialize()
        with open(config["key_path"]) as json_file:  
            data = json.load(json_file)
            self.api_key = data['OpenWeatherMap']
        self.set_api_key()

    def set_api_key(self):
        self.set_text('OWM_API_KEY',{'API_KEY': self.api_key})

    def _fill_in_weather_data(self):
        """

        """
        features = self.get_weather_features()
        data = {}
        # name: WEATHER_FORECAST, label: Weather, format: '%4.2f'
        data["WEATHER_FORECAST"] = features["WEATHER_FORECAST"]['value']
        # name: WEATHER_TEMPERATURE, label: Temperature (C), format: '%4.2f'
        data["WEATHER_TEMPERATURE"] = features["WEATHER_TEMPERATURE"]['value']
        # name: WEATHER_PRESSURE, label: Pressure (hPa), format: '%4.2f'
        data["WEATHER_PRESSURE"] = features["WEATHER_TEMPERATURE"]['value']
        # name: WEATHER_HUMIDITY, label: Humidity (%), format= '%4.2f'
        data["WEATHER_HUMIDITY"] = features["WEATHER_HUMIDITY"]['value']
        # name: WEATHER_WIND_SPEED, label: Wind (kph), format: '%4.2f'
        data["WEATHER_WIND_SPEED"] = features["WEATHER_WIND_SPEED"]['value']
        # name: WEATHER_RAIN_HOUR, label: Precip (mm), format: '%4.2f'
        data["WEATHER_RAIN_HOUR"] = features["WEATHER_RAIN_HOUR"]['value']
        # name: WEATHER_SNOW_HOUR, label: Precip (mm), format: '%4.2f'
        data["WEATHER_RAIN_HOUR"] = features["WEATHER_RAIN_HOUR"]['value']
        # name: WEATHER_CLOUD_COVER, label: Clouds (%), format: '%4.2f'
        data["WEATHER_RAIN_HOUR"] = features["WEATHER_RAIN_HOUR"]['value']
        data["safe"] = self._make_safety_decision(data)
        return data

    def _make_safety_decision(self, features):
        """
        based on:
        # name: WEATHER_FORECAST, label: Weather, format: '%4.2f'
        # name: WEATHER_TEMPERATURE, label: Temperature (C), format: '%4.2f'
        # name: WEATHER_PRESSURE, label: Pressure (hPa), format: '%4.2f'
        # name: WEATHER_HUMIDITY, label: Humidity (%), format= '%4.2f'
        # name: WEATHER_WIND_SPEED, label: Wind (kph), format: '%4.2f'
        # name: WEATHER_RAIN_HOUR, label: Precip (mm), format: '%4.2f'
        # name: WEATHER_SNOW_HOUR, label: Precip (mm), format: '%4.2f'
        # name: WEATHER_CLOUD_COVER, label: Clouds (%), format: '%4.2f'
        """
        status = False
        status = status and (np.float32(features["WEATHER_WIND_SPEED"]) <
                             self.limits["MAX_WEATHER_WIND_SPEED_KPH"])
        status = status and (np.float32(features["WEATHER_CLOUD_COVER"]) <
                             self.limits["MAX_WEATHER_CLOUD_COVER"])
        status = status and (np.float32(features["WEATHER_RAIN_HOUR"]) == 0)
        status = status and (np.float32(features["WEATHER_SNOW_HOUR"]) == 0)

        # name: WEATHER_CLOUD_COVER, label: Clouds (%), format: '%4.2f'

        return status


    def __str__(self):
        return f"Weather service: {self.device_name}"

    def __repr__(self):
        return self.__str__()        # Get key from json
        
