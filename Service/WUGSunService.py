#Basic stuff
import logging
import json
import datetime

# Local stuff
from Service.WUGService import WUGService

class WUGSunService(WUGService):
  """ WUGSun Service:
    https://www.wunderground.com/weather/api/d/docs?d=data/astronomy&MR=1
  """

  def __init__(self, configFileName=None, logger=None):
    WUGService.__init__(self,configFileName, logger)
    self.APIFuncLink = 'astronomy/q'

  def printEverything(self):
   res = self.sendRequest(self.APIFuncLink)
   print(str(res))

  def getCurrentTime(self):
    res = self.sendRequest(self.APIFuncLink)
    return datetime.time(hour=int(res['moon_phase']['current_time']['hour']),\
      minute=int(res['moon_phase']['current_time']['minute']))

  def getSunRiseTime(self):
    res = self.sendRequest(self.APIFuncLink)
    return datetime.time(hour=int(res['sun_phase']['sunrise']['hour']),\
      minute=int(res['sun_phase']['sunrise']['minute']))

  def getSunSetTime(self):
    res = self.sendRequest(self.APIFuncLink)
    return datetime.time(hour=int(res['sun_phase']['sunset']['hour']),\
      minute=int(res['sun_phase']['sunset']['minute']))


  def hasSunRose(self):
   res = self.sendRequest(self.APIFuncLink)
   curTime = datetime.time(hour=int(res['moon_phase']['current_time']['hour']),\
     minute=int(res['moon_phase']['current_time']['minute']))
   sunRise = datetime.time(hour=int(res['sun_phase']['sunrise']['hour']),\
     minute=int(res['sun_phase']['sunrise']['minute']))
   sunSet = datetime.time(hour=int(res['sun_phase']['sunset']['hour']),\
     minute=int(res['sun_phase']['sunset']['minute']))

   if curTime>sunRise and curTime<sunSet:
     return True
   else:
     return False

