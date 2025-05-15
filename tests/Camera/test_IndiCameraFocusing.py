# Basic stuff
import logging

# Viz stuff
import matplotlib.pyplot as plt
from skimage import img_as_float
from skimage import exposure

# Local stuff : Camera
from Camera.IndiAbstractCameraSimulatorNonCoolNonOffset import IndiAbstractCameraSimulatorNonCoolNonOffset
from Service.NTPTimeService import HostTimeService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')


def test_indiSimulatorCamera():
    config = dict(
        camera_name='CCD Simulator',
        do_acquisition=False,
        SIMULATOR_SETTINGS=dict(
            SIM_XRES=1000,
            SIM_YRES=1000,
            SIM_XSIZE=9,
            SIM_YSIZE=9,
            SIM_MAXVAL=65000,
            SIM_SATURATION=1,
            SIM_LIMITINGMAG=17,
            SIM_NOISE=5,
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
        subsample_astrometry=1,
        do_guiding=True,
        do_pointing=True,
        pointing_seconds=5,
        default_exp_time_sec=5,
        default_gain=50,
        default_offset=30,
        do_adjust_pointing=True,
        adjust_center_x=580,
        adjust_center_y=400,
        adjust_roi_search_size=50,
        adjust_pointing_seconds=5,
        do_autofocus=True,  # true,
        autofocus_seconds=4,
        autofocus_roi_size=750,
        autofocus_merit_function="half_flux_radius",  # vollath_F4
        indi_client=dict(
            indi_host="localhost",
            indi_port="7624"),
        focuser=dict(
            module="IndiFocuser",
            focuser_name="Focuser Simulator",
            port="/dev/ttyUSB0",
            focus_range=dict(
                min=30000,
                max=50000),
            autofocus_step=dict(
                fine=750,
                coarse=2500),
            autofocus_range=dict(
                fine=15000,
                coarse=30000),
            indi_client=dict(
                indi_host="localhost",
                indi_port="7624"),
        )
    )

    # test indi virtual camera class
    cam = IndiAbstractCameraSimulatorNonCoolNonOffset(serv_time=HostTimeService(),
                                                      config=config,
                                                      connect_on_create=False)
    cam.prepare_shoot()
    # test indi focusing
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
