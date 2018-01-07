#Basic stuff
import logging
import json
import io

#Indi stuff
import PyIndi
from Camera.IndiCamera import IndiCamera

class IndiVirtualCamera(IndiCamera):
  ''' Indi Virtual Camera '''

  def __init__(self, indiClient, logger=None, configFileName=None,\
      connectOnCreate=True):
    logger = logger or logging.getLogger(__name__)
    
    logger.debug('Configuring Indi Virtual Camera')

    # device related intialization
    IndiCamera.__init__(self, indiClient, logger=logger,\
      configFileName=configFileName)

    # Finished configuring
    self.logger.debug('Configured Indi Virtual Camera successfully')

  '''
    Indi CCD related stuff
  '''
  def shoot(self, coord=None):
    '''
      Just in case one uses a virtual camera, you should provide 'ra' and 'dec'
      coordinates in the following format:
      RA:  hh:mm:ss as 0.12345 or 23.999
      DEC: dd:mm:ss as -89.999 or +89.999
    '''
    if coord is not None:
      self.setNumber(\
        'EQUATORIAL_PE', {'RA_PE': coord['ra'], 'DEC_PE': coord['dec']},\
        timeout=5)
    
    IndiCamera.shoot(self)

