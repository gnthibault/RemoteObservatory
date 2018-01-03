#Basic stuff
import logging
import json

class VirtualObservatory(object):
  """ Virtual Observatory """
  #name = 'observatory'    # class variable shared by all instances

  def __init__(self, configFileName=None, logger=None):
    self.logger = logger or logging.getLogger(__name__)
    self.configFileName = configFileName  # instance variable
    self.logger.debug('Configuring object with file %s',self.configFileName)

  def openEverything(self):
    self.logger.debug('Observatory: open everything....')
    pass
    self.logger.debug('Observatory: everything opened')
 
  def closeEverything(self):
    self.logger.debug('Observatory: close everything....')
    pass
    self.logger.debug('Observatory: everything closed')

  def onEmergency(self):
    self.logger.debug('Observatory: on emergency routine started...')
    self.closeEverything()
    self.logger.debug('Observatory: on emergency routine finished')

