# Generic stuff
import json
import logging

# Numeric stuff
import numpy as np

# Local stuff
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
                key_path="/opt/RemoteObservatory/keys.json",
                publish_port=6510,
                delay_sec=60,
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"),
                limits=dict(
                    MAX_WEATHER_WIND_SPEED_KPH=25,
                    MAX_WEATHER_WIND_GUST_KPH=30,
                    MAX_WEATHER_CLOUD_COVER=5)
                )

        logger.debug(f"Indi OpenWeatherMap service, name is: "
                     f"{config['service_name']}")

        # device related intialization
        super().__init__( config=config, serv_time=serv_time,
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
        self.set_text('OWM_API_KEY',{'API_KEY': self.api_key}, sync=True)

    def _fill_in_weather_data(self):
        """

        """
        features = self.get_weather_features()
        data = {}
        # Generic indi state for this property, can be OK, IDLE, BUSY, ALERT
        data["state"] = features["state"]
        # name: WEATHER_FORECAST, label: Weather, format: '%4.2f'
        data["WEATHER_FORECAST"] = features["WEATHER_FORECAST"]
        # name: WEATHER_TEMPERATURE, label: Temperature (C), format: '%4.2f'
        data["WEATHER_TEMPERATURE"] = features["WEATHER_TEMPERATURE"]
        # name: WEATHER_PRESSURE, label: Pressure (hPa), format: '%4.2f'
        data["WEATHER_PRESSURE"] = features["WEATHER_TEMPERATURE"]
        # name: WEATHER_HUMIDITY, label: Humidity (%), format= '%4.2f'
        data["WEATHER_HUMIDITY"] = features["WEATHER_HUMIDITY"]
        # name: WEATHER_WIND_SPEED, label: Wind (kph), format: '%4.2f'
        data["WEATHER_WIND_SPEED"] = features["WEATHER_WIND_SPEED"]
        # name: WEATHER_RAIN_HOUR, label: Precip (mm), format: '%4.2f'
        data["WEATHER_RAIN_HOUR"] = features["WEATHER_RAIN_HOUR"]
        # name: WEATHER_SNOW_HOUR, label: Precip (mm), format: '%4.2f'
        data["WEATHER_SNOW_HOUR"] = features["WEATHER_SNOW_HOUR"]
        # name: WEATHER_CLOUD_COVER, label: Clouds (%), format: '%4.2f'
        data["WEATHER_CLOUD_COVER"] = features["WEATHER_CLOUD_COVER"]
        # name: WEATHER_CODE, label: Status code, format = '%4.2f'
        # min: 200, max: 810
        data["WEATHER_CODE"] = features["WEATHER_CODE"]
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
        # name: WEATHER_CODE, label: Status code, format = '%4.2f'
                    Group 2xx: Thunderstorm
            ID	Main	Description	Icon
            200	Thunderstorm	thunderstorm with light rain	 11d
            201	Thunderstorm	thunderstorm with rain	 11d
            202	Thunderstorm	thunderstorm with heavy rain	 11d
            210	Thunderstorm	light thunderstorm	 11d
            211	Thunderstorm	thunderstorm	 11d
            212	Thunderstorm	heavy thunderstorm	 11d
            221	Thunderstorm	ragged thunderstorm	 11d
            230	Thunderstorm	thunderstorm with light drizzle	 11d
            231	Thunderstorm	thunderstorm with drizzle	 11d
            232	Thunderstorm	thunderstorm with heavy drizzle	 11d
                    Group 3xx: Drizzle
            ID	Main	Description	Icon
            300	Drizzle	light intensity drizzle	 09d
            301	Drizzle	drizzle	 09d
            302	Drizzle	heavy intensity drizzle	 09d
            310	Drizzle	light intensity drizzle rain	 09d
            311	Drizzle	drizzle rain	 09d
            312	Drizzle	heavy intensity drizzle rain	 09d
            313	Drizzle	shower rain and drizzle	 09d
            314	Drizzle	heavy shower rain and drizzle	 09d
            321	Drizzle	shower drizzle	 09d
                    Group 5xx: Rain
            ID	Main	Description	Icon
            500	Rain	light rain	 10d
            501	Rain	moderate rain	 10d
            502	Rain	heavy intensity rain	 10d
            503	Rain	very heavy rain	 10d
            504	Rain	extreme rain	 10d
            511	Rain	freezing rain	 13d
            520	Rain	light intensity shower rain	 09d
            521	Rain	shower rain	 09d
            522	Rain	heavy intensity shower rain	 09d
            531	Rain	ragged shower rain	 09d
                    Group 6xx: Snow
            ID	Main	Description	Icon
            600	Snow	light snow	 13d
            601	Snow	Snow	 13d
            602	Snow	Heavy snow	 13d
            611	Snow	Sleet	 13d
            612	Snow	Light shower sleet	 13d
            613	Snow	Shower sleet	 13d
            615	Snow	Light rain and snow	 13d
            616	Snow	Rain and snow	 13d
            620	Snow	Light shower snow	 13d
            621	Snow	Shower snow	 13d
            622	Snow	Heavy shower snow	 13d
                    Group 7xx: Atmosphere
            ID	Main	Description	Icon
            701	Mist	mist	 50d
            711	Smoke	Smoke	 50d
            721	Haze	Haze	 50d
            731	Dust	sand/ dust whirls	 50d
            741	Fog	fog	 50d
            751	Sand	sand	 50d
            761	Dust	dust	 50d
            762	Ash	volcanic ash	 50d
            771	Squall	squalls	 50d
            781	Tornado	tornado	 50d
                    Group 800: Clear
            ID	Main	Description	Icon
            800	Clear	clear sky	 01d  01n
                    Group 80x: Clouds
            ID	Main	Description	Icon
            801	Clouds	few clouds: 11-25%	 02d  02n
            802	Clouds	scattered clouds: 25-50%	 03d  03n
            803	Clouds	broken clouds: 51-84%	 04d  04n
            804	Clouds	overcast clouds: 85-100%	 04d  04n
        """
        status = features["state"] == 'OK'
        status = status and (np.float32(features["WEATHER_WIND_SPEED"]) <
                             self.limits["MAX_WEATHER_WIND_SPEED_KPH"])
        status = status and (np.float32(features["WEATHER_CLOUD_COVER"]) <
                             self.limits["MAX_WEATHER_CLOUD_COVER"])
        status = status and (np.float32(features["WEATHER_RAIN_HOUR"]) == 0)
        status = status and (np.float32(features["WEATHER_SNOW_HOUR"]) == 0)
        status = status and ((np.float32(features["WEATHER_CODE"]) == 800) or
                             (np.float32(features["WEATHER_CODE"]) == 801))
        return bool(status)


    def __str__(self):
        return f"Weather service: {self.device_name}"

    def __repr__(self):
        return self.__str__()        # Get key from json
        
