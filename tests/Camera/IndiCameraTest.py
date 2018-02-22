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
    print('Current camera ROI is: {}'.format(cam.getRoi()))
    cam.setRoi({'X':256, 'Y':480, 'WIDTH':512, 'HEIGHT':640})
    print('Current camera ROI is: {}'.format(cam.getRoi()))

    # Acquire data
    cam.prepareShoot()
    cam.setExpTimeSec(10)
    cam.shootAsync()
    cam.synchronizeWithImageReception()
    fits = cam.getReceivedImage()
