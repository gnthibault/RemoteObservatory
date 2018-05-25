# Basic stuff
import json
import logging
import threading

# Indi stuff
import PyIndi

# Local stuff
import IndiClient

class Indi3DSimulatorClient(IndiClient):
  '''
    We designed this class, derived from Indiclient, in order to catch all
    the numbers/text that can help us to update the simulation status
  '''

  def __init__(self, simulator, configFileName=None, logger=None):
      self.logger = logger or logging.getLogger(__name__)
      
      # Call indi client base classe ctor
      self.logger.debug('starting constructing base class')
      super(IndiClient, self).__init__()
      self.logger.debug('finished constructing base class')

  def newNumber(self, nvp):
      pass

