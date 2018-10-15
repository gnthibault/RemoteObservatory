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
import scipy.stats as scs

# Viz stuff
import matplotlib.pyplot as plt

# Miscellaneous ios
from skimage import io
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

    __init__(camera, exp_time_list, gain_list, temp_list=[np.NaN], outdir=None,
             nb_image=100):
        #super(self).__init__()
        
        #attributes
        self.cam = camera
        self.exp_time_list = exp_time_list
        self.gain_list = gain_list
        self.temp_list = temp_list
        self.outdir = outdir or './dark_calibration' #TODO TN replace
        self.nb_image = nb_image
        self.show_plot = False

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

    def gen_report_temp_basedirname(self, temperature):
        return "{}/calibration/{}/camera_{}/temperature_{}}"
               "".format(self.outdir,
                         'dark',
                         self.cam.name,
                         temperature.to(u.Celsius).value
                  )
    def gen_calib_basedirname(self, temperature, gain, exp_time, index):
        return "{}/calibration/{}/camera_{}/temperature_{}/gain_{}/exp_time_{}"
               "".format(self.outdir,
                         'dark',
                         self.cam.name,
                         temperature.to(u.Celsius).value,
                         gain,
                         exp_time.to(u.second).value
                  )

    def gen_calib_filename(self, temperature, gain, exp_time, index):
        image_dir = self.gen_calib_basedirname(temperature, gain, exp_time,
                                               index)
        os.makedirs(image_dir, exist_ok=True)
        image_name = os.path.join(image_dir,str(index)+'.fits')
        return image_name

    def gen_calib_mastername(temperature, gain, exp_time):
        image_dir = self.gen_calib_basedirname(temperature, gain, exp_time)
        os.makedirs(image_dir, exist_ok=True)
        master_name = os.path.join(image_dir, 'master.tif')
        return master_name

    def gen_calib_masterstdname(temperature, gain, exp_time):
        image_dir = self.gen_calib_basedirname(temperature, gain, exp_time)
        os.makedirs(image_dir, exist_ok=True)
        master_std_name = os.path.join(image_dir, 'master_std.tif')
        return master_std_name

    def gen_therm_sig_figname(temperature):
        image_dir = self.gen_report_temp_basedirname(temperature)
        os.makedirs(image_dir, exist_ok=True)
        basename = os.path.join(image_dir, 'thermal_signal_map')
        return basename+'.png', basename+'.tif'

    def gen_therm_std_figname(temperature):
        image_dir = self.gen_report_temp_basedirname(temperature)
        os.makedirs(image_dir, exist_ok=True)
        basename = os.path.join(image_dir, 'thermal_std_map')
        return basename+'.png', basename+'.tif'

    def gen_therm_psnr_figname(temperature):
        image_dir = self.gen_report_temp_basedirname(temperature)
        os.makedirs(image_dir, exist_ok=True)
        basename = os.path.join(image_dir, 'thermal_psnr_map')
        return basename+'.png', basename+'.tif'

    def compute_master_dark_stat(self, stack):
        """ Implemented a more robust mean (denoised) estimator by removing
            samples that are farther than 3 sigma from the initial mean estimate
            Heuristic for maximum probability of possibly leptokurtic distr.
        """
        mean = np.apply_along_axis(lambda x:
            np.mean(scs.sigmaclip(x, low=5.0, high=5.0)[0],
                    dtype=np.float32),
            2, stack)
        std = stack-mean.reshape((*mean.shape, 1))
        std = np.sqrt(np.mean(std**2, axis=2, dtype=np.float32))

        # better safe than sorry
        psnr = np.divide(self.camera.dynamic, std, out=np.zeros_like(std),
                         where=std!=0)**2
        psnr = 10*np.log10(psnr, out=np.zeros_like(psnr), where=(psnr!=0))
        return mean, std, psnr


    def draw_gain_exp_heatmap(self, temperature, info_map, map_title, figname):
        """ x-axis is time, y-axis is gain
        """
        fig, ax = plt.subplots()
        im = ax.imshow(info_map)

        # We want to show all ticks...
        ax.set_xticks(np.arange(len(self.exp_time_list)))
        ax.set_yticks(np.arange(len(self.gain_list)))
        # ... and label them with the respective list entries
        ax.set_xticklabels(self.exp_time_list)
        ax.set_yticklabels(self.gain_list)

        # Rotate the tick labels and set their alignment.
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
                 rotation_mode="anchor")

        # set infos about the plot
        ax.set_title(map_title+' - (camera: '+self.cam.name+')')
        ax.set_xlabel('Exposure time in s')
        ax.set_ylabel('Camera gain')

        fig.tight_layout()
        if self.show_plot:
            plt.show()
        fig.savefig(figname, dpi=fig.dpi)

    def compute_thermal_signal_map(self):
        """ 2D map of thermal signal: x-axis is time, y-axis is gain
            and z axis is mean value expressed in % of full dynamic
        """
        for temperature in self.temp_list:
            sigfigname, sigfilename = self.gen_therm_sig_figname(temperature)
            stdfigname, stdfilename = self.gen_therm_std_figname(temperature)
            psnrfigname, psnrfilename = self.gen_therm_psnr_figname(temperature)
            if not os.path.exists(figname):
                map_shape = (len(self.exp_time_list), len(self.gain_list))
                thermal_signal_map = np.zeros(map_shape)
                thermal_std_map = np.zeros(map_shape)
                thermal_psnr_map = np.zeros(map_shape)
                for gi, gain in enumerate(self.gain_list):
                    for ei, exp_time in enumerate(self.exp_time_list):

                        # TODO might be worth excluding defect map
                        master_name = self.gen_calib_mastername(
                            temperature, gain, exp_time)
                        image = io.imread(master_name)
                        thermal_signal_map[gi, ei] = image.mean()

                        master_std_name = self.gen_calib_masterstdname(
                            temperature, gain, exp_time)
                        image = io.imread(master_std_name)
                        thermal_std_map[gi, ei] = image.mean()

                        master_psnr_name = self.gen_calib_masterpsnrname(
                            temperature, gain, exp_time)
                        image = io.imread(master_psnr_name)
                        thermal_psnr_map[gi, ei] = image.mean()

                # Now draw and print thermal signal map with a nice heatmap
                # notice that we save ADU values but show in % of dynamic
                self.draw_gain_exp_heatmap(temperature,
                    thermal_signal_map/self.cam.dynamic,
                    'Mean thermal signal in % of dynamic', sigfigname)
                io.imsave(sigfilename, thermal_signal_map)
                self.draw_gain_exp_heatmap(temperature,
                    thermal_std_map/self.cam.dynamic,
                    'Mean thermal noise std in % of dynamic', stdfigname)
                io.imsave(stdfilename, thermal_std_map)
                self.draw_gain_exp_heatmap(temperature, thermal_psnr_map,
                    'Mean thermal signal PSNR in dB', psnrfigname)
                io.imsave(psnrfilename, thermal_psnr_map)

    def self.compute_defect_map(self):
        """ First try to do a (feature=time) affine regression, pixel wise
            then on resulting a and b regression parameter map, perform a 
            statistical test to find outliers
            outliers on a are hot/warm and cold/cool pixels
            b is supposed to be the bias
        """
        for temperature in self.temp_list:
            sigfigname, sigfilename = self.gen_ther_sig_figname(temperature)
            stdfigname, stdfilename = self.gen_therm_std_figname(temperature)
            psnrfigname, psnrfilename = self.gen_therm_psnr_figname(temperature)
            if not os.path.exists(figname):
                map_shape = (len(self.exp_time_list), len(self.gain_list))
                thermal_signal_map = np.zeros(map_shape)
                thermal_std_map = np.zeros(map_shape)
                thermal_psnr_map = np.zeros(map_shape)
                for gi, gain in enumerate(self.gain_list):
                    for ei, exp_time in enumerate(self.exp_time_list):



    def acquire_images(self):
        self.cam.setFrameType('FRAME_DARK')
        self.cam.prepareShoot()
        for temperature in self.temp_list:
            self.set_temperature(temperature)
            for gain in self.gain_list:
                self.set_gain(gain)
                for exp_time in self.exp_time_list:
                    for i in range(self.nb_image):
                        fname = self.gen_calib_filename(temperature, gain,
                                                        exp_time,i)
                        if not os.path.exists(fname):
                            self.cam.setExpTimeSec(exp_time)
                            self.cam.shootAsync()
                            self.cam.synchronizeWithImageReception()
                            fits = self.cam.getReceivedImage()
                            with open(fname, "wb") as f:
                                fits.writeto(f)
        self.cleanup_device()

    def compute_statistics(self):
        # first compute master for each directory
        self.compute_master_dark()

        # heatmap of thermal signal: x-axis is time, y-axis is gain
        # and heat is mean value expressed in % of full dynamic

        # heatmap of thermal noise: x-axis is time, y-axis is gain
        # and heat is std value expressed in % of full dynamic

        # heatmap of thermal signal/thermal noise ratio x-axis is time y-axis
        # is gain and heat is psnr of thermal signal in db, with the formula
        # that takes into account the dynamic of the signal
        self.compute_thermal_signal_map()

        # exp-time series:
        # by doing a linear regression for each gain over the exp-time series,
        # we can find the theoretical offset map (b in ax+b)
        # we can find the gain map (a in ax+b)
        # chi2 test on spatial offset data at 5% gives the 2D map of hot pixels
        # chi2 test on spatial linearity data 5%, and excluding the hot pixels,
        # gives the 2D map of warm
        # please notice that doing the regression directly on the master dark
        # (denoised) value instead of the full point cloud should make the
        # method slightly less robust to noise in case we have very few points
        # but more robust to heteroskedasticity in case it arise 
        # Indeed, when working with master dark, each datapoint has equal weight
        # if working with the full point cloud, then high variance point might
        # dictate the regression.
        # Another approach would be to use weighted least square. That would
        # definitely be the best solution, but computational burden would be
        # quite high
        self.compute_defect_map()

        # From there, we can compute the graph of hot pixels where x-axis is
        # gain, and y-axis is number of hot pixels, and numerous temperature
        # are numerous lines
        
    def print_statistics(self):
        """ For printing statistics, we decided to print most of the
            values, especially RMS and mean, etc.. in terms of % of the
            maximum ADU, aka % of the dynamic
        """
        pass

    def compute_master_dark(self):
        # first: compute master
        for temperature in self.temp_list:
            for gain in self.gain_list:
                for exp_time in self.exp_time_list:
                    master_name = self.gen_calib_mastername(temperature,
                                                            gain, exp_time)
                    master_std_name = self.gen_calib_masterstdname(temperature,
                                                            gain, exp_time)
                    master_psnr_name = self.gen_calib_masterpsnrname(temperature,
                                                            gain, exp_time)
                    if not (os.path.exists(master_name) and
                            os.path.exists(master_std_name)):
                        master = None
                        for i in range(self.nb_image):
                            #open file and stack content
                            fname = self.gen_calib_filename(temperature, gain,
                                                            exp_time, i)
                            f = fits.open(fname)
                            header, im = f[0].header, f[0].data
                            if master is None:
                                master = im
                            else:
                                master = np.dstack((master, im))
                        #Now perform statistics (ie denoise, using
                        # mean+sigma clipping)
                        mean, std, psnr = self.compute_master_dark_stat(master)
                        io.imsave(master_name, master)
                        io.imsave(master_std_name, std)
                        io.imsave(master_psnr_name, psnr)


    def build():
        self.acquire_images()
        self.compute_statistics()

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
    exp_time_list = np.linspace(1, 30, 8)*u.second
    b = DarkLibraryBuilder(cam, exp_time_list, temp_list=[np.NaN],
                           outdir='./dark_calibration',
                           nb_image=16)
    b.build()


if __name__ == '__main__':


