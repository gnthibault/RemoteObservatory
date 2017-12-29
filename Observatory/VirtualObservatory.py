#Basic stuff
import logging


class VirtualObservatory(object):
  """ Virtual Observatory """
  #name = 'observatory'    # class variable shared by all instances

  def __init__(self, configFileName=None, logger=None):
    self.logger = logger or logging.getLogger(__name__)
    self.configFileName = configFileName  # instance variable
    self.logger.info('Configuring object with file %s',self.configFileName)

  def openEverything(self):
    self.logger.info('Observatory: open everything....')
    pass
    self.logger.info('Observatory: everything opened')
 
  def closeEverything(self):
    self.logger.info('Observatory: close everything....')
    pass
    self.logger.info('Observatory: everything closed')

  def onEmergency(self):
    self.logger.info('Observatory: on emergency routine started...')
    self.closeEverything()
    self.logger.info('Observatory: on emergency routine finished')

