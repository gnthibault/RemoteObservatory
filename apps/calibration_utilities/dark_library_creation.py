# Asses the offset + thermal signal of the sensor, on a per pixels basis
# Most of the serious people asses the thermal signal in terms of 
# e- / s or ADU / s at a given temperature
# One can draw a graph with e- / s on y axis, and temperature on x axis

# Basic stuff
import argparse
import collections
import logging
import os
from time import sleep

# Numerical stuff
import numpy as np
import scipy.stats as scs

# Viz stuff
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.colors import LogNorm

# Miscellaneous ios
from skimage import io
from astropy.io import fits

# Astropy
import astropy.units as u

# Local stuff
from helper.IndiClient import IndiClient
from Service.NTPTimeService import NTPTimeService
from utils import load_module

class DarkLibraryBuilder():

    def __init__(self, camera, exp_time_list, gain_list, offset_list, temp_list=[np.NaN],
                 outdir=None, nb_image=100):
        #super(self).__init__()
        
        #attributes
        self.cam = camera
        self.exp_time_list = exp_time_list
        self.gain_list = gain_list
        self.offset_list = offset_list
        self.temp_list = temp_list
        self.outdir = outdir or './dark_calibration' #TODO TN replace
        self.nb_image = nb_image
        self.show_plot = False
        self.plot_sampling = 65536 #8192

    def set_temperature(self, temperature):
        if temperature is np.NaN :
            return
        else:
            print('Now settting camera to temperature {}'.format(temperature))
            self.cam.set_temperature(temperature)

    def cleanup_device(self):
        self.cam.set_cooling_off()

    def gen_report_temp_basedirname(self, temperature):
        return ("{}/calibration/{}/camera_{}/temperature_{}"
               "".format(self.outdir,
                         'dark',
                         self.cam.name,
                         temperature.to(u.Celsius).value
                  ))
    def gen_report_gain_basedirname(self, temperature, gain):
        return ("{}/calibration/{}/camera_{}/temperature_{}/gain_{}"
               "".format(self.outdir,
                         'dark',
                         self.cam.name,
                         temperature.to(u.Celsius).value,
                         gain
                  ))
    def gen_calib_basedirname(self, temperature, gain, offset, exp_time):
        return ("{}/calibration/{}/camera_{}/temperature_{}/gain_{}/exp_time_{}"
               "".format(self.outdir,
                         'dark',
                         self.cam.name,
                         temperature.to(u.Celsius).value,
                         gain,
                         offset,
                         exp_time.to(u.second).value
                  ))

    def gen_calib_filename(self, temperature, gain, offset, exp_time, index):
        image_dir = self.gen_calib_basedirname(temperature, gain, offset, exp_time)
        os.makedirs(image_dir, exist_ok=True)
        image_name = os.path.join(image_dir,str(index)+'.fits')
        return image_name

    def gen_calib_mastername(self, temperature, gain, offset, exp_time):
        image_dir = self.gen_calib_basedirname(temperature, gain, offset, exp_time)
        os.makedirs(image_dir, exist_ok=True)
        master_name = os.path.join(image_dir, 'master.tif')
        return master_name

    def gen_calib_masterstdname(self, temperature, gain, offset, exp_time):
        image_dir = self.gen_calib_basedirname(temperature, gain, offset, exp_time)
        os.makedirs(image_dir, exist_ok=True)
        master_std_name = os.path.join(image_dir, 'master_std.tif')
        return master_std_name

    def gen_calib_masterpsnrname(self, temperature, gain, offset, exp_time):
        image_dir = self.gen_calib_basedirname(temperature, gain, offset, exp_time)
        os.makedirs(image_dir, exist_ok=True)
        master_psnr_name = os.path.join(image_dir, 'master_psnr.tif')
        return master_psnr_name

    def gen_NLF_figname(self, temperature, gain, offset, exp_time):
        base_dir = self.gen_calib_basedirname(temperature, gain, offset, exp_time)
        os.makedirs(base_dir, exist_ok=True)
        conv_check = os.path.join(base_dir, 'NLF_conv_check.png')
        regression = os.path.join(base_dir, 'NLF_regression.png')
        return conv_check, regression

    def gen_defectmap_name(self, temperature, gain):
        tbase_dir = self.gen_report_temp_basedirname(temperature)
        base_dir = self.gen_report_gain_basedirname(temperature, gain)
        os.makedirs(base_dir, exist_ok=True)
        defectmap_filename = os.path.join(base_dir, 'defectmap.tif')
        mainregparpcfname = os.path.join(tbase_dir,
            'mainregression_pointcloud.png')
        regparpcfname = os.path.join(base_dir,
            'regression_pointcloud.png')
        regparam_a_name = os.path.join(base_dir, 'regparam_a.tif')
        regparam_b_name = os.path.join(base_dir, 'regparam_b.tif')
        return dict(defectmap_filename=defectmap_filename,
                    main_regression_param_pointcloud_figname=mainregparpcfname,
                    regression_param_pointcloud_figname=regparpcfname,
                    regparam_a_name=regparam_a_name,
                    regparam_b_name=regparam_b_name)

    def gen_therm_sig_figname(self, temperature):
        image_dir = self.gen_report_temp_basedirname(temperature)
        os.makedirs(image_dir, exist_ok=True)
        basename = os.path.join(image_dir, 'thermal_signal_map')
        return basename+'.png', basename+'.tif'

    def gen_therm_std_figname(self, temperature):
        image_dir = self.gen_report_temp_basedirname(temperature)
        os.makedirs(image_dir, exist_ok=True)
        basename = os.path.join(image_dir, 'thermal_std_map')
        return basename+'.png', basename+'.tif'

    def gen_therm_psnr_figname(self, temperature):
        image_dir = self.gen_report_temp_basedirname(temperature)
        os.makedirs(image_dir, exist_ok=True)
        basename = os.path.join(image_dir, 'thermal_psnr_map')
        return basename+'.png', basename+'.tif'

    def draw_NLF(self, mean, var, regfigname, nlffigname, order=1):
        """
        we would like to perform a polynomial regression
        in order to be able to link the thermal signal (dark current)
        with the variance, to see if wether behaviour is heteroskedastic
        or homoskedastic. This function is also called the noise level function
        """
        A = np.concatenate([mean.reshape(-1,1)**i for i in range(order+1)],
                           axis=1)
        b = var.reshape(-1)
        xk = np.linalg.lstsq(A, b)[0]
        self.plot_NLF(A, b, xk, nlffigname, order)

    def draw_NLF2(self, mean, var, regfigname, nlffigname, order=1):
        """
        we would like to perform a polynomial regression
        in order to be able to link the thermal signal (dark current)
        with the variance, to see if wether behaviour is heteroskedastic
        or homoskedastic. This function is also called the noise level function
        """
        A = np.concatenate([mean.reshape(-1,1)**i for i in range(order+1)],
                           axis=1)
        b = var.reshape(-1)
 
        # Optimization stuff, see https://github.com/gnthibault/Optimisation-Python
        xhat=np.ones(order+1) #np.random.rand(order+1)
        # define the proximity operator that we need:
        def prox_g_conj(u, gamma):
            tmp = u-gamma*b
            return np.sign(tmp)*np.minimum(np.abs(tmp),1)
        def prox_f(x):
            return np.maximum(x,0)
        #Run Chambolle-Pock algorithm
        Anorm = 0.8*np.linalg.norm(A)#**2 #take 1% margin
        tau = 1./Anorm
        sigma = 1./Anorm
        rho = 1.05 #rho > 1 allows to speed up through momentum effect
        nbIter = 10000
        xk = np.zeros_like(xhat)  #primal var at current iteration
        xk_m1 = np.zeros_like(xhat)
        xk_tilde = np.zeros_like(xk)  #primal var estimator
        uk = np.zeros_like(A.shape[0]) #dual var
        primObj = np.zeros(nbIter)
        #dualObj = np.zeros(nbIter)
        for iter in range(nbIter):
            uk = prox_g_conj(uk + sigma * np.dot(A,xk_tilde), sigma)
            xk = prox_f( xk_m1 - tau * np.dot(A.T,uk) )
            xk_tilde = xk + rho*( xk - xk_m1 )
            primObj[iter] = np.sum(np.abs(np.dot(A,xk)-b))
            #dualObj[iter] = np.abs(np.dot(A,xk)-b).sum()
            xk_m1 = xk

        # Plot convergence
        fig = plt.figure(figsize=(15,10))
        ax = fig.add_subplot(211)
        ax.set_title("NLF LAD estimation: value of the composite objective "
                     "along the iterations")
        ax.set_xlabel("Iteration index")
        ax.set_ylabel("Primal objective value")
        ax.plot(range(nbIter),(primObj),label="Primal objective")
        #ax.plot(range(nbIter),np.log10(dualObj,out=np.zeros_like(dualObj),
        #         where=(dualObj<=0)),label="Dual objective")
        ax.legend()
        if self.show_plot:
            plt.show()
        fig.tight_layout()
        fig.savefig(regfigname, dpi=fig.dpi)
        self.plot_NLF(A, b, xk, nlffigname, order)

    def plot_NLF(self, A, b, xk, nlffigname, order):
        # Now plot regression
        fig = plt.figure(figsize=(15,15))
        ax = fig.add_subplot(111)
        ax.set_title('Order-{} polynomial regression: {}(increasing order)'
                     ''.format(order, xk))
        ax.set_xlabel("Signal estimation")
        ax.set_ylabel("Variance estimation")
        #sampling maximum k points
        sampling = np.random.choice(b.size, min(self.plot_sampling, b.size),
                                    replace=False)
        x = A[:,1][sampling]
        y = b[sampling]
        idxsorted = np.argsort(x)
        x = x[idxsorted]
        y = y[idxsorted]
        y_reg = np.sum([xk[i]*x**i for i in range(order+1)], axis=0)
        ax.scatter(x,y,label="Actual values", alpha=0.2, marker='x')
        ax.plot(x, y_reg, label="LAD regression")
        ax.legend()
        #if self.show_plot:
        #    plt.show()
        fig.tight_layout()
        fig.savefig(nlffigname, dpi=fig.dpi)

        # Now plot actual data points with estimated variance margin
        #ax = fig.add_subplot(212)
        #ax.set_title('Order-{} polynomial regression: {}(increasing order)'
        #             ''.format(order, xk))
        #ax.set_xlabel("Signal estimation")
        #ax.set_ylabel("Actual signal")
        #ax.plot(range(nbIter),(primObj),label="Primal objective")
        #ax.plot(range(nbIter),np.log10(dualObj,out=np.zeros_like(dualObj),
        #         where=(dualObj<=0)),label="Dual objective")
        #ax.legend()
        #if self.show_plot:
        #    plt.show()
        #fig.tight_layout()
        #fig.savefig(regfigname, dpi=fig.dpi)

    def compute_master_dark_stat(self, stack):
        """ Implemented a more robust mean (denoised) estimator by removing
            samples that are farther than 3 sigma from the initial mean estimate
            Heuristic for maximum probability of possibly leptokurtic distr.
        """
        mean = np.apply_along_axis(lambda x:
            np.mean(scs.sigmaclip(x, low=5.0, high=5.0)[0],
                    dtype=np.float32),
            2, stack)
        var = stack-mean.reshape((*mean.shape, 1))
        var = np.mean(var**2, axis=2, dtype=np.float32)

        # better safe than sorry
        psnr = np.divide(self.cam.dynamic**2, var,
                         out=np.zeros_like(var), where=var!=0)
        psnr = 10*np.log10(psnr, out=np.zeros_like(psnr), where=(psnr!=0))
        return mean, np.sqrt(var), psnr

    def draw_gain_exp_heatmap(self, temperature, info_map, map_title, figname):
        """ x-axis is time, y-axis is gain
        """
        fig, ax = plt.subplots()
        heatmap = ax.pcolor(info_map,
                            norm=LogNorm(vmin=info_map.min(), vmax=info_map.max()),
                            cmap='jet')
        plt.colorbar(heatmap, format=FormatStrFormatter('%.2e'))

        # We want to show all ticks...
        ax.set_xticks(np.arange(len(self.exp_time_list)))
        ax.set_yticks(np.arange(len(self.gain_list)))
        # ... and label them with the respective list entries
        formatter = lambda x: "{:.2E}".format(x)
        ax.set_xticklabels(map(formatter, self.exp_time_list))
        #ax.xaxis.set_major_formatter(FormatStrFormatter('%.2e'))
        ax.set_yticklabels(map(formatter, self.gain_list))
        #ax.yaxis.set_major_formatter(FormatStrFormatter('%.2e'))

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

    def compute_NLF_regression(self):
        """ We would like to perform a polynomial regression
            in order to be able to link the thermal signal (dark current)
            with the variance, to see if wether behaviour is heteroskedastic
            or homoskedastic
        """
        for temperature in self.temp_list:
            for gi, gain in enumerate(self.gain_list):
                for ei, exp_time in enumerate(self.exp_time_list):
                    regfigname, nlffigname = self.gen_NLF_figname(temperature,
                                                                  gain,
                                                                  exp_time)
                    if not (os.path.exists(regfigname) and os.path.exists(
                            nlffigname)):
                        # TODO might be worth excluding defect map
                        master_name = self.gen_calib_mastername(
                            temperature, gain, exp_time)
                        mean = io.imread(master_name)
                        master_std_name = self.gen_calib_masterstdname(
                            temperature, gain, exp_time)
                        std = io.imread(master_std_name)
                        self.draw_NLF(mean, std**2, regfigname, nlffigname,
                                      order=2)

    def compute_thermal_signal_map(self):
        """ 2D map of thermal signal: x-axis is time, y-axis is gain
            and z axis is mean value expressed in % of full dynamic
        """
        for temperature in self.temp_list:
            sigfigname, sigfilename = self.gen_therm_sig_figname(temperature)
            stdfigname, stdfilename = self.gen_therm_std_figname(temperature)
            psnrfigname, psnrfilename = self.gen_therm_psnr_figname(temperature)
            if not (os.path.exists(sigfigname) and os.path.exists(stdfigname)
                and os.path.exists(psnrfigname)):
                map_shape = (len(self.gain_list), len(self.exp_time_list))
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
                    'Mean thermal signal \n in % of dynamic', sigfigname)
                io.imsave(sigfilename, thermal_signal_map)
                self.draw_gain_exp_heatmap(temperature,
                    thermal_std_map/self.cam.dynamic,
                    'Mean thermal noise std \n in % of dynamic', stdfigname)
                io.imsave(stdfilename, thermal_std_map)
                self.draw_gain_exp_heatmap(temperature, thermal_psnr_map,
                    'Mean thermal signal \n PSNR in dB', psnrfigname)
                io.imsave(psnrfilename, thermal_psnr_map)

    def compute_defect_map(self):
        """ First try to do a (feature=time) affine regression, pixel wise
            then on resulting a and b regression parameter map, perform a 
            statistical test to find outliers
            outliers on a are hot/warm and cold/cool pixels
            b is supposed to be the bias
        """
        for temperature in self.temp_list:
            # for each temperature, show a point cloud (with different 
            # temperature for each gain) of the ofset/gain
            figmain = plt.figure(figsize=(15,15))
            axmain = figmain.add_subplot(111)
            axmain.set_title('Affine regression parameters: offset and '
                          'gain at temperature'.format(temperature))
            axmain.set_xlabel("Offset")
            axmain.set_ylabel("Gain")
            mainxmin, mainxmax, mainymin, mainymax = 4*[None]
            cm = plt.get_cmap('gist_rainbow')
            colors = [cm(1.*i/len(self.gain_list)) for i in
                      range(len(self.gain_list))]
            for gi, gain in enumerate(self.gain_list):
                dark_signal = None
                names = self.gen_defectmap_name(temperature, gain)
                if not all(map(lambda x:os.path.exists(x), names.values())):
                    for ei, exp_time in enumerate(self.exp_time_list):
                        master_name = self.gen_calib_mastername(
                            temperature, gain, exp_time)
                        im = io.imread(master_name)
                        if dark_signal is None:
                            dark_signal = im
                        else:
                            dark_signal = np.dstack((dark_signal, im))
                    # Now perform the regression a*exp_time+b for each pixel
                    amap = np.zeros(dark_signal.shape[:2])
                    bmap = np.zeros(dark_signal.shape[:2])
                    for i in range(dark_signal.shape[0]):
                        for j in range(dark_signal.shape[1]):
                            x = self.exp_time_list
                            y = dark_signal[i,j]
                            M = np.concatenate((y.reshape(-1,1),
                                np.ones_like(y).reshape(-1,1)), axis=1)
                            # use Moore-penrose pseudo inverse to solve ls
                            amap[i,j],bmap[i,j] = np.linalg.lstsq(M,x)[0]
                    # Now write output
                    io.imsave(names['regparam_a_name'],amap)
                    io.imsave(names['regparam_b_name'],bmap)
                    # Now plot regression param scattering
                    fig = plt.figure(figsize=(15,15))
                    ax = fig.add_subplot(111)
                    ax.set_title('Affine regression parameters: offset and '
                                 'gain at hardware gain {} and temperature'
                                 ' '.format(gain, temperature))
                    ax.set_xlabel("Offset")
                    ax.set_ylabel("Gain")
                    #sampling maximum k points
                    sampling = np.random.choice(amap.size,
                        min(self.plot_sampling, amap.size), replace=False)
                    x = bmap.reshape(-1)[sampling]
                    y = amap.reshape(-1)[sampling]
                    ax.scatter(x,y,label="Regression parameters", alpha=0.2,
                               marker='x')
                    sampling = np.random.choice(x.size, min(1024, x.size), replace=False)
                    axmain.scatter(x[sampling], y[sampling],
                                   label="Gain = {}".format(gain), alpha=0.2,
                                   marker='x', color=colors[gi])
                    # Set limits for the plot not to be disturbed by outliers
                    minmarger = lambda s : (1-np.sign(s)*0.25)*s
                    maxmarger = lambda s : 1.25*s
                    xmin, xmax = np.percentile(x,[1, 99])
                    ymin, ymax = np.percentile(y,[1, 99])
                    xmin, ymin = map(minmarger, (xmin, ymin))
                    xmax, ymax = map(maxmarger, (xmax, ymax))
                    ax.set_xlim(left=xmin, right=xmax)
                    ax.set_ylim(bottom=ymin, top=ymax)
                    if any(np.array([mainxmin, mainxmax, mainymin, mainymax])==None):
                        mainxmin, mainxmax = xmin, xmax
                        mainymin, mainymax = ymin, ymax
                    else:
                        mainxmin, mainxmax = min(xmin,mainxmin), max(xmax,mainxmax)
                        mainymin, mainymax = min(ymin,mainymin), max(ymax,mainymax)
                    ax.legend()
                    #if self.show_plot:
                    #    plt.show()
                    fig.tight_layout()
                    fig.savefig(names['regression_param_pointcloud_figname'],
                                dpi=fig.dpi)

                    # perform statistical test
                    #io.imsave(names['defectmap_filename'],)
            #Now draw all the points on the same graph
            axmain.legend()
            axmain.set_xlim(left=mainxmin, right=mainxmax)
            axmain.set_ylim(bottom=mainymin, top=mainymax)
            if self.show_plot:
                plt.show()
            figmain.tight_layout()
            figmain.savefig(names['main_regression_param_pointcloud_figname'],
                        dpi=fig.dpi)

    def acquire_images(self):
        self.cam.set_frame_type('FRAME_DARK')
        self.cam.prepare_shoot()
        for temperature in self.temp_list:
            self.set_temperature(temperature)
            for offset in self.offset_list:
                self.set_offset(offset)
                for gain in self.gain_list:
                    self.cam.set_gain(gain)
                    for exp_time in self.exp_time_list:
                        for i in range(self.nb_image):
                            print('Temperature {}, gain {}, offset {}, exp time {}, Acquiring'
                                  ' image {}'.format(temperature, gain, offset, exp_time, i))
                            fname = self.gen_calib_filename(temperature, gain, offset, exp_time, i)
                            if not os.path.exists(fname):
                                print('before set exp time')
                                self.cam.setExpTimeSec(exp_time)
                                print('before shoot')
                                self.cam.shoot_async()
                                print('After shoot_async, going to sync')
                                self.cam.synchronize_with_image_reception()
                                print('After sync')
                                fits = self.cam.get_received_image()
                                print('Image received')
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

        # Try to understand if noise in homoskedastic or heteroskedastic
        self.compute_NLF_regression()

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
                        io.imsave(master_name, mean)
                        io.imsave(master_std_name, std)
                        io.imsave(master_psnr_name, psnr)


    def build(self):
        print('Starting dark calibration image acquisition')
        self.acquire_images()
        print('Starting dark calibration image analysis')
        self.compute_statistics()

def main(config_file='./jsonModel/IndiCCDSimulatorCamera.json',
         cam_class='IndiCamera', show_plot=False):
    # Instanciate indiclient, in order to connect to camera
    indiCli = IndiClient()
    indiCli.connect()

    # Instanciate a time server as well
    serv_time = NTPTimeService()    

    #cam = IndiASI120MCCamera(indi_client=indiCli,
    try:
        cam_module = load_module('Camera.{}'.format(cam_class))
        cam_ctor = getattr(cam_module, cam_class)
        print('cam_ctor is {}'.format(cam_ctor))
        cam = cam_ctor(indi_client=indiCli,
            config_filename=config_file,
            connect_on_create=False)
    except RuntimeError as e:
        raise RuntimeError('Please provide a valid cam_class. current one is '
                           '{} and error is {}'.format(cam_class, e))

    cam.connect()

    # just some tests
    #print('Dynamic is {}'.format(cam.dynamic))
    #g=10
    #print('Now setting gain to {}'.format(g))
    #cam.set_gain(g)
    #print('Done')
    #print('Gain is now {}'.format(cam.get_gain()))

    # launch stuff
#    exp_time_list = np.linspace(1, 30, 8)*u.second
    exp_time_list = np.array([1,5,10,30,60,120])*u.second
#    gain_list = np.linspace(0,100,10, dtype=np.int32).tolist()
    gain_list = [120, 150]
    offset_list = [20, 30]
    temp_list = [np.NaN*u.Celsius]
    b = DarkLibraryBuilder(cam, exp_time_list, temp_list=temp_list,
                           gain_list=gain_list,
                           offset_list=offset_list,
                           outdir='./dark_calibration',
                           nb_image=19)
    b.show_plot = show_plot
    b.build()

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', help='Path to the config file of the '
                      'camera', default='./conf_files/IndiDatysonT7MC.json')
    parser.add_argument('--cam_class', help='Name of the class of the camera '
                      'can be IndiCamera or IndiASI120MCCamera',
                      default='IndiASI120MCCamera')
    parser.add_argument('--show_plot', default='False')
    args = parser.parse_args()
    main(args.config_file, args.cam_class, str2bool(args.show_plot))

#PYTHONPATH=. python ./apps/calibration_utilities/dark_library_creation.py --config_file ./conf_files/IndiDatysonT7MC.json --cam_class IndiASI120MCCamera
