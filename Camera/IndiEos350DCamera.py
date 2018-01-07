#Basic stuff
import logging
import json
import io

#Indi stuff
import PyIndi
from Camera.IndiCamera import IndiCamera

class IndiEos350DCamera(IndiCamera):
  ''' Indi Virtual Camera '''

  def __init__(self, indiClient, logger=None, configFileName=None,\
      connectOnCreate=True):
    logger = logger or logging.getLogger(__name__)
    
    logger.debug('Configuring Indi EOS350D Camera')
    # device related intialization
    IndiCamera.__init__(self, indiClient, logger=logger,\
      configFileName=configFileName)

    # Finished configuring
    self.logger.debug('Configured Indi Eos 350D Camera successfully')

  '''
    Indi CCD related stuff
  '''
  def prepareShoot(self):
    self.setText("DEVICE_PORT",{"PORT":"/dev/ttyUSB0"})
    IndiCamera.prepareShoot(self)

