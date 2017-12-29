#Basic stuff
import logging
import json
import datetime

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
   res = self.sendRequest(self.APIFuncLink)
   print(str(res))

  def getPercentIlluminated(self):
   res = self.sendRequest(self.APIFuncLink)
   return int(res['moon_phase']['percentIlluminated'])

  def getAgeOfMoon(self):
   res = self.sendRequest(self.APIFuncLink)
   return int(res['moon_phase']['ageOfMoon'])

  def hasMoonRose(self):
   res = self.sendRequest(self.APIFuncLink)
   curTime = datetime.time(hour=int(res['moon_phase']['current_time']['hour']),\
     minute=int(res['moon_phase']['current_time']['minute']))
   moonRise = datetime.time(hour=int(res['moon_phase']['moonrise']['hour']),\
     minute=int(res['moon_phase']['moonrise']['minute']))
   moonSet = datetime.time(hour=int(res['moon_phase']['moonset']['hour']),\
     minute=int(res['moon_phase']['moonset']['minute']))
 
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

