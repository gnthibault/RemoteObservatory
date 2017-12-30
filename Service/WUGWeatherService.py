#Basic stuff
import logging
import json


# Local stuff
from Service.WUGService import WUGService

class WUGWeatherService(WUGService):
  """ WUGWeather Service:
    weather
    temp_c
    relative_humidity
    wind_kph
    wind_gust_kph
    pressure_mb
    dewpoint_c
    visibility_km
"""

  def __init__(self, configFileName=None, logger=None):
    WUGService.__init__(self,configFileName, logger)
    self.APIFuncLink = 'conditions/q'

  def printEverything(self):
    res = self.sendRequest(self.APIFuncLink)
    print(str(res))

  def getTemp_c(self):
    res = self.sendRequest(self.APIFuncLink)
    return float(res['current_observation']['temp_c'])

  def getRelative_humidity(self):
    res = self.sendRequest(self.APIFuncLink)
    return float(res['current_observation']['relative_humidity'].split('%')[0])

  def getWind_kph(self):
    res = self.sendRequest(self.APIFuncLink)
    return float(res['current_observation']['wind_kph'])
  
  def getWind_gust_kph(self):
    res = self.sendRequest(self.APIFuncLink)
    return float(res['current_observation']['wind_gust_kph'])
  
  def getPressure_mb(self):
    res = self.sendRequest(self.APIFuncLink)
    return float(res['current_observation']['pressure_mb'])
  
  def getDewpoint_c(self):
    res = self.sendRequest(self.APIFuncLink)
    return float(res['current_observation']['dewpoint_c'])
  
  def getVisibility_km(self):
    res = self.sendRequest(self.APIFuncLink)
    return float(res['current_observation']['visibility_km'])

  def getWeatherQuality(self):
    res = self.sendRequest(self.APIFuncLink)
    weather = res['current_observation']['weather']
    if weather == "Clear":
      return 0
    elif weather in ["Scattered Clouds","Partly Cloudy","Overcast",\
      "Patches of Fog","Partial Fog","Light Haze"]:
      return 1
    else:
      return 2
