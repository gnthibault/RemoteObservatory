# Generic imports
import logging
import time

# Astorpy helpers
import astropy.units as u

# Local code
from Camera.IndiAbstractCameraSimulator import IndiAbstractCameraSimulator
from Guider import GuiderPHD2
from Service.NTPTimeService import HostTimeService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')

def test_annoying_camera_bug():
    cam_config = dict(
        camera_name='CCD Simulator',
        SIMULATOR_SETTINGS=dict(
            SIM_XRES=5496,
            SIM_YRES=3672,
            SIM_XSIZE=2.4,
            SIM_YSIZE=2.4,
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
        pointing_seconds=30,
        adjust_center_x=400,
        adjust_center_y=400,
        adjust_roi_search_size=50,
        adjust_pointing_seconds=5,
        autofocus_seconds=5,
        autofocus_roi_size=500,
        autofocus_merit_function="half_flux_radius",
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
    cam = IndiAbstractCameraSimulator(serv_time=HostTimeService(),
                                      onfig=cam_config,
                                      connect_on_create=False)
    # cam.connect()
    # cam.park()
    # cam.unpark()
    # cam.prepare_shoot()
    # # Acquire data
    # cam.setExpTimeSec(2)
    # cam.shoot_async()
    # cam.synchronize_with_image_reception()
    # fits = cam.get_received_image()
    #
    # # Show image
    # #fig, ax = plt.subplots(1, figsize=(16, 9))
    # img = fits[0].data
    # img_eq = exposure.equalize_hist(img)
    # print_ready_img = img_as_float(img_eq)
    # print(f"Print ready has shape {print_ready_img.shape}")
    # #ax.imshow(print_ready_img)
    # #plt.show()

config = {
    "host": "localhost",
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

g = GuiderPHD2.GuiderPHD2(config=config)
# g.launch_server()
# g.connect_server()
# print(f"Is server connected: {g.is_server_connected()}")
# g.connect_profile()
# print(f"Is profile connected: {g.is_profile_connected()} = {g.is_profile_connected(g.profile_name)}")
# print(f"Currently connected equipment is {g.get_current_equipment()}")
# g.set_exposure(4.0)
# print("About to start looping to get images")
# g.loop()
# print("About to start star selection")
# ret = g.find_star(x=250, y=250, width=500, height=500)
# print(f"Return from find_star is {ret}")
# # If successful, there should be a lock position set
# ret = g.get_lock_position()
# print(f"Get lock position now returns {ret}")
#
# ret = g.get_calibrated()
# print(f"Get Calibrated returns {ret}")
# g.guide(recalibrate=False)
# print(f"Guiding is now steady, about to check lock position")
# ret = g.get_lock_position()
# print(f"Get lock position now returns {ret}")
# print("About to set lock position")
# g.set_lock_position(ret[0]+100, ret[1]+100, exact=True, wait_reached=True, angle_sep_reached=2*u.arcsec)
# print("Lock position set")
# # If successful, there should be a lock position set
# ret = g.get_lock_position()
# print(f"Get lock position now returns {ret}")
#
# # guide for some time (receive takes some time)
# for i in range(1*60):
#     g.receive()
#     time.sleep(1)
#
# # you can use set_paused in full mode (pause both looping and guiding) to test if profile disconnection works
# g.set_paused(paused=True, full="full")
# # you can use set_paused without full mode (looping continues, but not guiding output)
# #g.set_paused(paused=True, full="")
#
# print("Before disconnecting profile")
# g.disconnect_profile()
# print(f"Is profile connected: {g.is_profile_connected()} = {g.is_profile_connected(g.profile_name)}")
# g.disconnect_server()
# print(f"Is server connected: {g.is_server_connected()}")
# g.terminate_server()