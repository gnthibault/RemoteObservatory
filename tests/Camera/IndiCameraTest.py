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

    # test indi client
    indiCli = IndiClient()
    indiCli.connect()

    # test indi virtual camera class
    cam = IndiVirtualCamera(indiClient=indiCli, configFileName=None,
                     connectOnCreate=False)
    cam.connect()

    # Play with camera configuration
    #cam.setRoi({'X':256, 'Y':480, 'WIDTH':512, 'HEIGHT':640})
    # getRoi Not implemented, TODO TN
    #print('Current camera ROI is: {}'.format(cam.getRoi()))
    #cam.setRoi({'X':0, 'Y':0, 'WIDTH':1280, 'HEIGHT':1024})
    # getRoi Not implemented, TODO TN
    #print('Current camera ROI is: {}'.format(cam.getRoi()))

    #print('Setting cooling on')
    #cam.set_cooling_on() that just never work
    print('Current camera temperature is: {}'.format(cam.get_temperature()))
    target_temp = 15
    print('Now, setting temperature to: {}'.format(target_temp))
    cam.set_temperature(target_temp)
    print('Current camera temperature is: {}'.format(cam.get_temperature()))
    target_temp = 17.5
    print('Now, setting temperature to: {}'.format(target_temp))
    cam.set_temperature(target_temp)
    print('Current camera temperature is: {}'.format(cam.get_temperature()))
    #cam.set_cooling_off() that just never work

    # set frame type (mostly for simulation purpose
    cam.set_frame_type('FRAME_LIGHT')
    cam.set_frame_type('FRAME_DARK')
    cam.set_frame_type('FRAME_FLAT')
    cam.set_frame_type('FRAME_BIAS')

    # set gain
    print('gain is {}'.format(cam.get_gain()))
    cam.set_gain(10)

    # Acquire data
    cam.prepareShoot()
    cam.setExpTimeSec(10)
    cam.shootAsync()
    cam.synchronizeWithImageReception()
    fits = cam.getReceivedImage()
