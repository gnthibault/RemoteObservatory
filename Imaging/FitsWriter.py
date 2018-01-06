#Basic stuff
import logging
import datetime

# Astropy for handling FITS
from astropy.io import fits

# Local stuff

class FitsWriter():
  """
    Check FITS manipulation with astropy:
    http://docs.astropy.org/en/stable/io/fits/
  """

  def __init__(self, logger=None, observatory=None, servWeather=None,
      servSun=None, servMoon=None, servTime=None):
    self.logger = logger or logging.getLogger(__name__)
    self.logger.debug('Configuring FitsWriter')
    self.imgIdx=0
    self.logger.debug('FitsWriter configured successfully')

  def writeWithTag(self, fits):
    filename="frame"+str(self.imgIdx)+".fits"
    try:
      with open(filename, "wb") as f:
        fits.writeto(f, overwrite=True)
    except Exception as e:
      self.logger.error('FitsWriter error while writing file '+filename+\
        ' : '+str(e))
    self.imgIdx=self.imgIdx+1
