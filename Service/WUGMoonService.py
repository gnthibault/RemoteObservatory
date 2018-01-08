#Basic stuff
import logging
import json
import datetime
import traceback

# Local stuff
from Service.WUGService import WUGService

class WUGMoonService(WUGService):
  """ WUGMoon Service:
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
     self.logger.error('WUGMoonService error while retrieving data: '\
       +str(e)+', error stack is '+traceback.format_exc())

  def getPercentIlluminated(self):
   try:
     res = self.sendRequest(self.APIFuncLink)
     return int(res['moon_phase']['percentIlluminated'])
   except Exception as e:
     self.logger.error('WUGMoonService error while retrieving data: '\
       +str(e)+', error stack is '+traceback.format_exc())
     return 0

  def getAgeOfMoon(self):
   try:
     res = self.sendRequest(self.APIFuncLink)
     return int(res['moon_phase']['ageOfMoon'])
   except Exception as e:
     self.logger.error('WUGMoonService error while retrieving data: '\
       +str(e)+', error stack is '+traceback.format_exc())
     return 0

  def getMoonRiseTime(self):
   try:
    res = self.sendRequest(self.APIFuncLink)
    return datetime.time(hour=int(res['moon_phase']['moonrise']['hour']),\
      minute=int(res['moon_phase']['moonrise']['minute']))
   except Exception as e:
     self.logger.error('WUGMoonService error while retrieving data: '\
       +str(e)+', error stack is '+traceback.format_exc())
     return datetime.datetime.now().time()

  def getMoonSetTime(self):
   try:
    res = self.sendRequest(self.APIFuncLink)
    return datetime.time(hour=int(res['moon_phase']['moonset']['hour']),\
      minute=int(res['moon_phase']['moonset']['minute']))
   except Exception as e:
     self.logger.error('WUGMoonService error while retrieving data: '\
       +str(e)+', error stack is '+traceback.format_exc())
     return datetime.datetime.now().time()

  def getCurrentTime(self):
   try:
    res = self.sendRequest(self.APIFuncLink)
    return datetime.time(hour=int(res['moon_phase']['current_time']['hour']),\
     minute=int(res['moon_phase']['current_time']['minute']))
   except Exception as e:
     self.logger.error('WUGMoonService error while retrieving data: '\
       +str(e)+', error stack is '+traceback.format_exc())
     return datetime.datetime.now().time()

  def hasMoonRose(self):
   res = self.sendRequest(self.APIFuncLink)
   curTime = self.getCurrentTime() 
   moonRise = self.getMoonRiseTime()
   moonSet = self.getMoonSetTime()
 
   # First check wether the rise/set is within the current day
   isWithin = moonRise<moonSet

   if isWithin:
     if curTime>moonRise and curTime<moonSet:
       return True
     else:
       return False
   else:
     if curTime>moonRise:
       return True
     else:
       return False

