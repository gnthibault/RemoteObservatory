#Basic stuff
import logging


class VirtualObservatory(object):
  """ Virtual Observatory """
  #name = 'observatory'    # class variable shared by all instances

  def __init__(self, configFileName, logger=None):
    self.logger = logger or logging.getLogger(__name__)
    self.configFileName = configFileName  # instance variable
