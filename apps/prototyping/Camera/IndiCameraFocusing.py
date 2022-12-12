# Basic stuff
import logging
import logging.config
import threading

# Miscellaneous
from astropy.io import fits
import io
import matplotlib.pyplot as plt
import numpy as np

# Local stuff : Camera
from Camera.IndiAbstractCameraSimulator import IndiAbstractCameraSimulator
from Service.NTPTimeService import HostTimeService

# For this t
if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    config = dict(
        camera_name='CCD Simulator',
        SIMULATOR_SETTINGS=dict(
            SIM_XRES=1000,
            SIM_YRES=1000,
            SIM_XSIZE=5.2,
            SIM_YSIZE=5.2,
            SIM_MAXVAL=65000,
            SIM_SATURATION=1,
            SIM_LIMITINGMAG=17,
            SIM_NOISE=0.5,
            SIM_SKYGLOW=19.5,
            SIM_OAGOFFSET=0,
            SIM_POLAR=0,
            SIM_POLARDRIFT=0,
            SIM_ROTATION=0,
            SIM_PEPERIOD=0,
            SIM_PEMAX=0,
            SIM_TIME_FACTOR=1),
        SCOPE_INFO=dict(
            FOCAL_LENGTH=800,
            APERTURE=200),
        pointing_seconds=30,
        autofocus_seconds=5,
        autofocus_roi_size=650,
        autofocus_merit_function="half_flux_radius",
        focuser=dict(
            module="IndiFocuser",
            focuser_name="Focuser Simulator",
            port="/dev/ttyUSB0",
            focus_range=dict(
                min=25000,
                max=50000),
            autofocus_step=dict(
                coarse=2500,
                fine=1000),
            autofocus_range=dict(
                coarse=25000,
                fine=10000),
            indi_client=dict(
                indi_host="localhost",
                indi_port="7624")
            ),
        indi_client=dict(
            indi_host="localhost",
            indi_port="7624")
        )

    # test indi virtual camera class
    cam = IndiAbstractCameraSimulator(serv_time=HostTimeService(), config=config, connect_on_create=True)
    cam.prepare_shoot()

    def get_thumb(cam):
        thumbnail_size = 500
        cam.prepare_shoot()
        fits = cam.get_thumbnail(exp_time_sec=5, thumbnail_size=thumbnail_size)
        try:
            image = fits.data
        except:
            image = fits[0].data
        plt.imshow(image)
        plt.show()

    # Now focus
    assert(cam.focuser.is_connected)
    autofocus_status = [False]
    #autofocus_event = cam.autofocus_async(coarse=True, autofocus_status=autofocus_status)
    autofocus_event = cam.autofocus_async(coarse=False, autofocus_status=autofocus_status)
    autofocus_event.wait()
    assert autofocus_status[0], "Focusing failed"
    print("Done")
