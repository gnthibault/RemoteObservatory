#Basic stuff
import logging
import json
import traceback


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
    try:
      res = self.sendRequest(self.APIFuncLink)
      print(str(res))
    except Exception as e:
      self.logger.error('WUGWeatherService error while retrieving data: '\
        +str(e))#+', error stack is '+traceback.format_exc())

  def getTemp_c(self):
    try:
      res = self.sendRequest(self.APIFuncLink)
      return float(res['current_observation']['temp_c'])
    except Exception as e:
      self.logger.error('WUGWeatherService error while retrieving data: '\
        +str(e))#+', error stack is '+traceback.format_exc())
      return self.defaultFloat

  def getRelative_humidity(self):
    try:
      res = self.sendRequest(self.APIFuncLink)
      return float(res['current_observation']['relative_humidity'].split('%')[0])
    except Exception as e:
      self.logger.error('WUGWeatherService error while retrieving data: '\
        +str(e))#+', error stack is '+traceback.format_exc())
      return self.defaultFloat

  def getWind_kph(self):
    try:
      res = self.sendRequest(self.APIFuncLink)
      return float(res['current_observation']['wind_kph'])
    except Exception as e:
      self.logger.error('WUGWeatherService error while retrieving data: '\
        +str(e))#+', error stack is '+traceback.format_exc())
    return self.defaultFloat

  def getWind_gust_kph(self):
    try:
      res = self.sendRequest(self.APIFuncLink)
      return float(res['current_observation']['wind_gust_kph'])
    except Exception as e:
      self.logger.error('WUGWeatherService error while retrieving data: '\
        +str(e))#+', error stack is '+traceback.format_exc())
      return self.defaultFloat

  def getPressure_mb(self):
    try:
      res = self.sendRequest(self.APIFuncLink)
      return float(res['current_observation']['pressure_mb'])
    except Exception as e:
      self.logger.error('WUGWeatherService error while retrieving data: '\
        +str(e))#+', error stack is '+traceback.format_exc())
      return self.defaultFloat

  def getDewpoint_c(self):
    try:
      res = self.sendRequest(self.APIFuncLink)
      return float(res['current_observation']['dewpoint_c'])
    except Exception as e:
      self.logger.error('WUGWeatherService error while retrieving data: '\
        +str(e))#+', error stack is '+traceback.format_exc())
      return self.defaultFloat

  def getVisibility_km(self):
    try:
      res = self.sendRequest(self.APIFuncLink)
      return float(res['current_observation']['visibility_km'])
    except Exception as e:
      self.logger.error('WUGWeatherService error while retrieving data: '\
        +str(e))#+', error stack is '+traceback.format_exc())
      return self.defaultFloat

  def getWeatherQuality(self):
    try:
      res = self.sendRequest(self.APIFuncLink)
      return res['current_observation']['weather']
    except Exception as e:
      self.logger.error('WUGWeatherService error while retrieving data: '\
        +str(e))#+', error stack is '+traceback.format_exc())
      return self.defaultString

  def getWeatherQualityIndex(self):
    weather = self.getWeatherQuality()
    if weather == "Clear":
      return 0
    elif weather in ["Scattered Clouds","Partly Cloudy","Overcast",\
      "Patches of Fog","Partial Fog","Light Haze"]:
      return 1
    else:
      return 2
