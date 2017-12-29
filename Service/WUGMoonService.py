#Basic stuff
import logging
import json


# Local stuff
from Service.WUGService import WUGService

class WUGMoonService(WUGService):
  """ WUGMoon Service:
  moon_phase:
    precentIlluminated
    ageOfMoon
    current_time.hour
    current_time.minute
    sunrise.hour
    sunrise.minute
    sunset.hour
    sunset.minute"""

  def __init__(self, configFileName=None, logger=None):
    WUGService.__init__(self,configFileName, logger)
    self.APIFuncLink = 'astronomy/q'

  def printEverything(self):
   res = self.sendRequest(self.APIFuncLink)
   print(str(res))   
