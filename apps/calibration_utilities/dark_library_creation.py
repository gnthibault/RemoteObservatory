# Asses the offset + thermal signal of the sensor, on a per pixels basis
# Most of the serious people asses the thermal signal in terms of 
# e- / s or ADU / s at a given temperature
# One can draw a graph with e- / s on y axis, and temperature on x axis

# Basic stuff
import collections
import os
from time import sleep

# Numerical stuff
import numpy as np

# Miscellaneous
import io
from astropy.io import fits

# Local stuff
from Camera.IndiCamera import IndiCamera
from helper.IndiClient import IndiClient
from Service.NTPTimeService import NTPTimeService
from utils import error
from utils import Timeout

class DarkLibraryBuilder():
    TEMPERATURE_WAITING_DELAY_S = 5
    MAX_TEMP_WAIT_S = 500 #8m20s

    __init__(camera, exp_time_list, temp_list=[np.NaN], outdir, nb_image=100):
        super(self).__init__()
        
        #attributes
        self.cam = camera
        self.exp_time_list = exp_time_list
        self.temp_list = temp_list
        self.outdir = outdir
        self.nb_image = nb_image

    def set_temperature(temperature)
        if temperature == np.NaN
            return
        else:
            try:
                self.cam.set_coolingOn()
                self.cam.set_temperature(temperature)
                timeout = Timeout(MAX_TEMP_WAIT_S)
                temp = cam.get_temperature()
                while temp != temperature:
                    self.logger.info('Waiting for temperature to reach target: '
                        '{} / {}'.format(temp, temperature))
                    if timeout.expired():
                        raise error.Timeout
                        temp = cam.get_temperature()
                    sleep(self.TEMPERATURE_WAITING_DELAY)
            except error.Timeout as e:
                self.logger.error('Timeout while waiting for camera {} to reach'
                                  'target temperature {}'.format(self.cam.name,
                                                                 temperature))
            except Exception as e:
                self.logger.warning('Problem while waiting for camera cooling '
                                    '{}: {}'.format(e, traceback.format_exc()))

    def cleanup_device():
        self.cam.set_cooling_off()

    def gen_calib_filename(temperature, exp_time, index):
        image_dir = "{}/calibration/{}/{}/{}/{}".format(
            self.outdir,
            'dark',
            self.cam.name,
            temperature.to(u.Celsius).value,
            exp_time.to(u.second).value
        )
        os.makedirs(image_dir, exist_ok=True)
        image_name = os.path.join(image_dir,str(index)+'.fits')
        if os.path.exists(image_name):
            return None
        else:
            return image_name

    def acquire_images()
        self.cam.setFrameType('FRAME_DARK')
        self.cam.prepareShoot()
        for temperature in self.temp_list:
            self.set_temperature(temperature)
            for exp_time in self.exp_time_list:
                for i in range(self.nb_image):
                    fname = self.gen_calib_filename(temperature, exp_time, i)
                    if fname:
                        self.cam.setExpTimeSec(exp_time)
                        self.cam.shootAsync()
                        self.cam.synchronizeWithImageReception()
                        fits = self.cam.getReceivedImage()
                        with open(fname, "wb") as f:
                            fits.writeto(f)
        self.cleanup_device()

    def compute_statistics():
        for temperature in self.temp_list:
            for exp_time in self.exp_time_list:
                for i in range(self.nb_image):
                    pass

    def build():
        self.acquire_images()

def main(cam_name='IndiCamera'):
    # Instanciate indiclient, in order to connect to camera
    indiCli = IndiClient()
    indiCli.connect()

    # Instanciate a time server as well
    serv_time = NTPTimeService()    

    # test indi virtual camera class
    cam = IndiCamera(indiClient=indiCli,
        configFileName='./jsonModel/IndiCCDSimulatorCamera.json', connectOnCreate=False)
#        configFileName='./jsonModel/DatysonT7MC.json', connectOnCreate=True)
    cam.connect()

    # launch stuff


if __name__ == '__main__':


