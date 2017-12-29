# Basic stuff
import logging
import logging.config


# Local stuff
from Observatory.VirtualObservatory import VirtualObservatory
from Observatory.ShedObservatory import ShedObservatory
from Service.VirtualService import VirtualService
from Service.WUGMoonService import WUGMoonService
from Service.WUGWeatherService import WUGWeatherService


if __name__ == '__main__':

  # load the logging configuration
  logging.config.fileConfig('logging.ini')
  logger = logging.getLogger('mainLogger')

  # Instanciate object of interest
  #obs = VirtualObservatory(logger=logger)
  obs = ShedObservatory(logger=logger)

  # test moon service
  servMoon = WUGMoonService(logger=logger)
  servMoon.setGpsCoordinates(obs.getGpsCoordinates())
  servMoon.printEverything()
  print('illuminated moon is '+str(servMoon.getPercentIlluminated()))
  print('Age of moon is '+str(servMoon.getAgeOfMoon()))
  print('Is moon risen '+str(servMoon.isMoonRisen()))

  # test Weather service
  servWeather = WUGWeatherService(logger=logger)
  servWeather.setGpsCoordinates(obs.getGpsCoordinates())
  servWeather.printEverything()
  
