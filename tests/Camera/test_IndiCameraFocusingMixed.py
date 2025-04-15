# Basic stuff
import logging
import time

# Viz stuff
import matplotlib.pyplot as plt
from skimage import exposure

# Astropy
from astropy import units as u
from astroplan import ObservingBlock
from astroplan import FixedTarget

# Local stuff : Camera
from Camera.IndiAbstractCameraSimulatorNonCoolNonOffset import IndiAbstractCameraSimulatorNonCoolNonOffset
from Guider.GuiderPHD2 import GuiderPHD2
from ObservationPlanner.Observation import Observation
from Service.NTPTimeService import HostTimeService

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

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

    #############################################
    # Connect camera and simulate pointing
    ##############################################
    cam = IndiAbstractCameraSimulatorNonCoolNonOffset(
        serv_time=HostTimeService(),config=config,connect_on_create=False)
    cam.connect()
    #cam.park()
    cam.unpark()
    cam.prepare_shoot()
    # Acquire data
    cam.setExpTimeSec(2)
    cam.shoot_async()
    cam.synchronize_with_image_reception()
    fits = cam.get_received_image()

    #############################################
    # Start guiding setup
    ##############################################
    config = {
        "host": "127.0.0.1",
        "port": 4400,
        "do_calibration": False,
        "profile_name": "Simulator",
        "exposure_time_sec": 2,
        "settle": {
            "pixels": 1.5,
            "time": 10,
            "timeout": 60},
        "dither": {
            "pixels": 3.0,
            "ra_only": False}
    }
    g = GuiderPHD2(config=config)
    g.launch_server()
    g.connect_server()
    g.connect_profile()
    g.guide()
    # guide for some time (receive takes some time)
    for i in range(1*20):
        g.receive()
        time.sleep(1)

    # # test indi focusing
    # def get_thumb(cam):
    #     thumbnail_size = 500
    #     cam.prepare_shoot()
    #     fits = cam.get_thumbnail(exp_time_sec=5, thumbnail_size=thumbnail_size)
    #     try:
    #         image = fits.data
    #     except:
    #         image = fits[0].data
    #     plt.imshow(image)
    #     plt.show()

    #############################################
    # Start focusing
    ##############################################
    g.set_paused(paused=True)
    exp_time_sec = cam.get_remaining_exposure_time()
    try:
        time.sleep(exp_time_sec + 5)
        #cam.synchronize_with_image_reception(exp_time_sec=exp_time_sec)
    except Exception as e:
        print(f"Exception is {e}")
    assert(cam.focuser.is_connected)
    autofocus_status = [False]
    #autofocus_event = cam.autofocus_async(coarse=True, autofocus_status=autofocus_status)
    autofocus_event = cam.autofocus_async(coarse=False, autofocus_status=autofocus_status)
    autofocus_event.wait()
    assert autofocus_status[0], "Focusing failed"
    g.set_paused(paused=False)
    g.wait_for_state(one_of_states=["Guiding", "SteadyGuiding"])
    # model.manager.guiding_camera.set_frame_type("FRAME_LIGHT")
    # 2025-04-26 20:35:07,686 - IndiWeather - DEBUG - Updating weather
    # 2025-04-26 20:35:09,301 - helper.IndiClient - DEBUG - new BLOB received: CCD1
    # 2025-04-26 20:35:09,301 - helper.IndiClient - DEBUG - Copying blob CCD1 to listener BLOBListener(device=Guide Simulator
    # model.manager.guiding_camera.set_frame_type("FRAME_LIGHT")
    for i in range(1*20):
        g.receive()
        time.sleep(1)

    #############################################
    # Simulate offset pointing
    ##############################################
    g.stop_capture()
    exp_time_sec = cam.get_remaining_exposure_time()
    try:
        cam.synchronize_with_image_reception(exp_time_sec=exp_time_sec)
    except Exception as e:
        print(f"Exception is {e}")
    cam.set_frame_type("FRAME_LIGHT")
    observation = Observation(ObservingBlock.from_exposures(
        FixedTarget.from_name('Deneb'),0, 5*u.s,1,
        configuration={"gain":0, "offset":1, "temperature":-10})
    )
    observation.seq_time = "test"
    camera_event = cam.take_observation(
        observation=observation,
        headers={},
        filename="/tmp/todelete.fit",
        exp_time=cam.adjust_pointing_seconds * u.second,
        # external_trigger=external_trigger
    )
    status = camera_event.wait(timeout=30)
    print("Done")
