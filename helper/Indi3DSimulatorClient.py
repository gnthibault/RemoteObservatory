# Basic stuff
import json
import logging
import threading

# Indi stuff
import PyIndi

# Local stuff
from Base.Base import Base
from helper.IndiClient import IndiClient

class Indi3DSimulatorClient(IndiClient):
  '''
    We designed this class, derived from Indiclient, in order to catch all
    the numbers/text that can help us to update the simulation status
  '''

  def __init__(self, simulator, configFileName=None):
      # Call indi client base classe ctor
      IndiClient.__init__(self)

      #Dictionary of callbacks, key=device, value=conditions + callback
      self.number_callbacks = []

  def register_number_callback(self, device_name, vec_name, callback):
      self.number_callbacks.append((device_name, vec_name, callback))

  def newNumber(self, nvp):
      self.logger.debug('Received newNumber !')
      for (device_name, vec_name, callback) in self.number_callbacks:
          if nvp.device == device_name and nvp.name==vec_name:
              number_vec = dict(map(lambda c: (c.name, c.value),nvp))
              callback(number_vec)
              #for nb in nvp:
              #    print('Received nvp: {} - {} - {} - {} - {}'.format(
              #        nvp.name, nvp.label, nb.name, nb.label,nb.value))
      pass

