#Basic stuff
import logging


class VirtualService(object):
  """ Virtual Service """
  #name = 'service'    # class variable shared by all instances

  def __init__(self, configFileName=None, logger=None):
    self.logger = logger or logging.getLogger(__name__)
    self.configFileName = configFileName  # instance variable
    self.logger.info('Configuring object with file %s',self.configFileName)

  def isConnected(self):
    return False

  def connect(self):
    self.logger.info('Connecting service...')
    pass
    self.logger.info('Service connected')

  def disconnect(self):
    self.logger.info('Disconnecting service...')
    pass
    self.logger.info('Service disconnected')

  def onEmergency(self):
    self.logger.info('Service: on emergency routine started...')
    self.disconnect()
    self.logger.info('Service: on emergency routine finished')

