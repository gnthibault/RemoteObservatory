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
    self.logger.debug('Configuring ShedObservatory with file %s',self.configFileName)

    # Get key from json
    with open(self.configFileName) as jsonFile:
      data = json.load(jsonFile)
      self.gpsCoordinates = data['gpsCoordinates']
      self.logger.debug('ShedObservatory gps coordinates are: %s',\
        str(self.gpsCoordinates))
      self.altitudeMeter=int(data['altitudeMeter'])
      self.ownerName=data['ownerName']
    
    # Finished configuring
    self.logger.debug('Configured ShedObservatory successfully')
    
  def getGpsCoordinates(self):
    return self.gpsCoordinates

  def getAltitudeMeter(self):
    return self.altitudeMeter

  def getOwnerName(self):
    return self.ownerName

  def openEverything(self):
    self.logger.debug('ShedObservatory: open everything....')
    pass
    self.logger.debug('ShedObservatory: everything opened')
 
  def closeEverything(self):
    self.logger.debug('ShedObservatory: close everything....')
    pass
    self.logger.debug('ShedObservatory: everything closed')

  def onEmergency(self):
    self.logger.debug('ShedObservatory: on emergency routine started...')
    self.closeEverything()
    self.logger.debug('ShedObservatory: on emergency routine finished')

