# Basic stuff
import logging
import logging.config
import threading
import sys

sys.path.append('.')

# Miscellaneous
import io
from astropy.io import fits

# Local stuff : IndiClient
from helper.IndiClient import IndiClient

# Local stuff : Camera
from Camera.IndiVirtualCamera import IndiVirtualCamera


if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')
    logger = logging.getLogger('mainLogger')

    # test indi client
    indiCli = IndiClient(logger=logger)
    indiCli.connect()

    # test indi virtual camera class
    cam = IndiVirtualCamera(logger=logger, indiClient=indiCli,
                            configFileName=None, connectOnCreate=False)
    cam.connect()

    # Play with camera configuration
    cam.setRoi({'X':256, 'Y':480, 'WIDTH':512, 'HEIGHT':640})
    print('Current camera ROI is: {}'.format(cam.getRoi()))
    cam.setRoi({'X':0, 'Y':0, 'WIDTH':1280, 'HEIGHT':1024})
    print('Current camera ROI is: {}'.format(cam.getRoi()))

    cam.setTemperature(-22.22)
    print('Current camera temperature is: {}'.format(cam.getTemperature()))
    cam.setTemperature(-1)
    print('Current camera temperature is: {}'.format(cam.getTemperature()))

    #cam.setCoolingOn()
    #cam.setCoolingOff()
    cam.setFrameType('FRAME_LIGHT')
    cam.setFrameType('FRAME_DARK')
    cam.setFrameType('FRAME_FLAT')
    cam.setFrameType('FRAME_BIAS')

    # Acquire data
    cam.prepareShoot()
    cam.setExpTimeSec(10)
    cam.shootAsync()
    cam.synchronizeWithImageReception()
    fits = cam.getReceivedImage()