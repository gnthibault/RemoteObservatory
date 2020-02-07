# Basic stuff
import logging
import logging.config
import sys

# Local stuff : IndiClient
from helper.IndiClient import IndiClient

# Local stuff : Mount
from Service.IndiWeather import IndiWeather
from Service.IndiOpenWeatherMap import IndiOpenWeatherMap
from Service.HostTimeService import HostTimeService

#Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    # define config
    config1 = dict(
        service_name="Weather Simulator",
        publish_port=65106,
        delay_sec=30,
        indi_client=dict(
            indi_host="localhost",
            indi_port="7624"),
        limits = dict(
            MAX_WEATHER_WIND_SPEED_KPH=25,
            MAX_WEATHER_WIND_GUST_KPH=30,
            MAX_WEATHER_CLOUD_COVER=5)
        )
    config2 = dict(
        service_name = "OpenWeatherMap",
        key_path = "/var/RemoteObservatory/keys.json",
        publish_port = 6510,
        delay_sec = 60,
        indi_client = dict(
            indi_host="localhost",
            indi_port="7624"),
        limits=dict(
            MAX_WEATHER_WIND_SPEED_KPH=25,
            MAX_WEATHER_WIND_GUST_KPH=30,
            MAX_WEATHER_CLOUD_COVER=5)
        )

    # Now test IndiWeather
    #serv = IndiWeather(logger=None, config=config1,
    #                          serv_time=HostTimeService(),
    #                          connect_on_create=True, loop_on_create=False)
    serv = IndiOpenWeatherMap(logger=None, config=config2,
                       serv_time=HostTimeService(),
                       connect_on_create=True, loop_on_create=False)
    # Set slew ret to be used afterwards
    print(serv.capture())
    serv.set_geographic_coord()
    print(serv.get_weather_features())