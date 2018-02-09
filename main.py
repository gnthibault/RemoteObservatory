# Basic stuff
import logging
import logging.config
import threading
import time

# Miscellaneous
import io
from astropy.io import fits

# Local stuff : Observatory
from Observatory.VirtualObservatory import VirtualObservatory
from Observatory.ShedObservatory import ShedObservatory

# Local stuff : Service
from Service.VirtualService import VirtualService
from Service.WUGSunService import WUGSunService
from Service.WUGMoonService import WUGMoonService
from Service.WUGWeatherService import WUGWeatherService
from Service.NTPTimeService import NTPTimeService
from Service.NovaAstrometryService import NovaAstrometryService

# Local stuff : IndiClient
from helper.IndiClient import IndiClient
from helper.IndiDevice import IndiDevice

# Local stuff : Camera
from Camera.IndiVirtualCamera import IndiVirtualCamera
from Camera.IndiEos350DCamera import IndiEos350DCamera

# Local stuff : Imaging tools
from Imaging.FitsWriter import FitsWriter

# Local stuff: Sequencer
from Sequencer.ShootingSequence import ShootingSequence
from Sequencer.SequenceBuilder import SequenceBuilder
from Sequencer.SequenceRunner import SequenceRunner


if __name__ == '__main__':

  # load the logging configuration
  logging.config.fileConfig('logging.ini')
  logger = logging.getLogger('mainLogger')

  # Instanciate object of interest
  vObs = VirtualObservatory(logger=logger)
  obs = ShedObservatory(logger=logger)

  # test moon service
  servMoon = WUGMoonService(logger=logger)
  servMoon.setGpsCoordinates(obs.getGpsCoordinates())
  #servMoon.printEverything()
  #print('illuminated moon is '+str(servMoon.getPercentIlluminated()))
  #print('Age of moon is '+str(servMoon.getAgeOfMoon()))
  #print('has moon rose '+str(servMoon.hasMoonRose()))

  # test sun service
  servSun = WUGSunService(logger=logger)
  servSun.setGpsCoordinates(obs.getGpsCoordinates())
  #servSun.printEverything()
  #print('Current time is '+str(servSun.getCurrentTime()))
  #print('Sun rise time is '+str(servSun.getSunRiseTime()))
  #print('Sun set time is '+str(servSun.getSunSetTime()))
  #print('has sun rose '+str(servSun.hasSunRose()))

  #test ntp time server
  servTime = NTPTimeService(logger=logger)
  ntpTime = servTime.getUTCFromNTP()
  #print('Current Time from NTP is : ',str(ntpTime))

  # test Weather service
  servWeather = WUGWeatherService(logger=logger)
  servWeather.setGpsCoordinates(obs.getGpsCoordinates())
  #servWeather.printEverything()
  #print('Temperature is ',str(servWeather.getTemp_c()))
  #print('relative humidity is ',str(servWeather.getRelative_humidity()))
  #print('Wind is ',str(servWeather.getWind_kph()))
  #print('Wind gust is',str(servWeather.getWind_gust_kph()))
  #print('Pressure is ',str(servWeather.getPressure_mb()))
  #print('dewpoint is ',str(servWeather.getDewpoint_c()))
  #print('visibility is ',str(servWeather.getVisibility_km()))
  #print('Weather quality is ',str(servWeather.getWeatherQuality()))

  # test indi client
  indiCli = IndiClient(logger=logger)
  indiCli.connect()

  # test indi Device
  indiDevice = IndiDevice(logger=logger,deviceName='CCD Simulator',\
    indiClient=indiCli)

  # test indi virtual camera class
  cam = IndiVirtualCamera(logger=logger, indiClient=indiCli,\
    configFileName=None, connectOnCreate=False)
  cam.connect()
  cam.prepareShoot()
  cam.setExpTimeSec(10)
  cam.shootAsync(coord={'ra':12.0, 'dec':45.0})
  cam.synchronizeWithImageReception()
  fits = cam.getReceivedImage()

  # test indi camera class on a old EOS350D
  #cam = IndiEos350DCamera(logger=logger, indiClient=indiCli,\
  #  configFileName='IndiEos350DCamera.json', connectOnCreate=False)
  #cam.connect()
  #cam.prepareShoot()
  #cam.setExpTimeSec(5)
  #cam.shootAsync()
  #cam.synchronizeWithImageReception()
  #fits = cam.getReceivedImage()

  # test nova Astrometry service
  nova = NovaAstrometryService(logger=logger,configFileName='local')
  nova.login()
  t=io.BytesIO()
  fits.writeto(t)
  astrometry = nova.solveImage(t.getvalue())
  corrected = nova.getNewFits()
  print('fits content is '+str(corrected))
  wcs=nova.getWcs()
  print('wcs content is '+str(wcs))
  kml=nova.getKml()
  print('kml content is '+str(kml))
  nova.printRaDecWCSwithSIPCorrectedImage('radec.png')

  # Write fits file with all interesting metadata:
  writer = FitsWriter(logger=logger, observatory=obs, servWeather=servWeather,
    servSun=servSun, servMoon=servMoon, servTime=servTime,
    servAstrometry=nova)
  hwriter = lambda f : writer.writeWithTag(f)
  w = threading.Thread(target=hwriter, args=(fits))
  w.start()

  # Test a Shooting Sequence
  seq = ShootingSequence(cam, target='M51', exposure=10, count=3, )

  seqBuilder = SequenceBuilder(camera=cam)
