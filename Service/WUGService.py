#Basic stuff
import json
import logging
from pathlib import Path

# Service stuff
import urllib.request
import urllib.error

class WUGService(object):
  """ WUG Service """

  def __init__(self, configFileName=None, logger=None):
    self.logger = logger or logging.getLogger(__name__)

    if configFileName is None:
      # Default file is ~/.wug
      home = Path.home()
      config = home / '.wug'
      self.configFileName = str(config)
    else:
      self.configFileName = configFileName

    # Now configuring
    self.logger.info('Configuring WUG Service with file %s',\
    self.configFileName)

    # Get key from json
    with open(self.configFileName) as jsonFile:  
      data = json.load(jsonFile)
      self.key = data['key']
    
    # Finished configuring
    self.logger.info('Configured WUG service successfully')


  def sendRequest(self):
    try:
      pass
      #req = urllib.request.Request('http://api.wunderground.com/api/Your_Key/geolookup/conditions/q/IA/Cedar_Rapids.json')
      #res = urllib.request.urlopen(req)
      #jsonString = res.read()
      #parsed_json = json.loads(json_string)
      #location = parsed_json['location']['city']
      #temp_f = parsed_json['current_observation']['temp_f']
      #print( "Current temperature in %s is: %s" % (location, temp_f))
      #res.close()
    except urllib.error.URLError as e:
      logger.error("WUGService error is ",e.reason)

