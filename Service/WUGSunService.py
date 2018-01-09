#Basic stuff
import logging
import json
import datetime
import traceback

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
   try:
     res = self.sendRequest(self.APIFuncLink)
     print(str(res))
   except Exception as e:
     self.logger.error('WUGSunService error while retrieving data: '\
       +str(e))#+', error stack is '+traceback.format_exc())

  def getCurrentTime(self):
   try:
    res = self.sendRequest(self.APIFuncLink)
    return datetime.time(hour=int(res['moon_phase']['current_time']['hour']),\
      minute=int(res['moon_phase']['current_time']['minute']))
   except Exception as e:
     self.logger.error('WUGSunService error while retrieving data: '\
       +str(e))#+', error stack is '+traceback.format_exc())
     return datetime.datetime.now().time()

  def getSunRiseTime(self):
   try:
    res = self.sendRequest(self.APIFuncLink)
    return datetime.time(hour=int(res['sun_phase']['sunrise']['hour']),\
      minute=int(res['sun_phase']['sunrise']['minute']))
   except Exception as e:
     self.logger.error('WUGSunService error while retrieving data: '\
       +str(e))#+', error stack is '+traceback.format_exc())
     return datetime.datetime.now().time()

  def getSunSetTime(self):
   try:
    res = self.sendRequest(self.APIFuncLink)
    return datetime.time(hour=int(res['sun_phase']['sunset']['hour']),\
      minute=int(res['sun_phase']['sunset']['minute']))
   except Exception as e:
     self.logger.error('WUGSunService error while retrieving data: '\
       +str(e))#+', error stack is '+traceback.format_exc())
     return datetime.datetime.now().time()


  def hasSunRose(self):
   res = self.sendRequest(self.APIFuncLink)
   curTime = self.getCurrentTime()
   sunRise = self.getSunRiseTime()
   sunSet = self.getSunSetTime()

   if curTime>sunRise and curTime<sunSet:
     return True
   else:
     return False

