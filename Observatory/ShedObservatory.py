#Basic stuff
import logging
import json

class ShedObservatory(object):
  """ Shed Observatory """

  def __init__(self, configFileName=None, logger=None):
    self.logger = logger or logging.getLogger(__name__)
    
    if configFileName is None:
      self.configFileName = 'ShedObservatory.json'
    else:
      self.configFileName = configFileName

    # Now configuring class
    self.logger.info('Configuring ShedObservatory with file %s',self.configFileName)

    # Get key from json
    with open(self.configFileName) as jsonFile:
      data = json.load(jsonFile)
      self.gpsCoordinates = data['gpsCoordinates']
      self.logger.info('ShedObservatory gps coordinates are: %s',\
      str(self.gpsCoordinates))
    
    # Finished configuring
    self.logger.info('Configured ShedObservatory successfully')
    
  def getGpsCoordinates(self):
    return self.gpsCoordinates

  def openEverything(self):
    self.logger.info('ShedObservatory: open everything....')
    pass
    self.logger.info('ShedObservatory: everything opened')
 
  def closeEverything(self):
    self.logger.info('ShedObservatory: close everything....')
    pass
    self.logger.info('ShedObservatory: everything closed')

  def onEmergency(self):
    self.logger.info('ShedObservatory: on emergency routine started...')
    self.closeEverything()
    self.logger.info('ShedObservatory: on emergency routine finished')

