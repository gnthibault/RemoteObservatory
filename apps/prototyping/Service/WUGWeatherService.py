# Basic stuff
import logging
import logging.config
import sys

# Local stuff : Service
from Service.WUGWeatherService import WUGWeatherService

if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    # weather service
    s = WUGWeatherService()
    s.setgps_coordinates({"latitude": "50.0", "longitude": "0.1"})
 
    # Print everything (I am a lazy person)
    s.printEverything()
