# Basic stuff

# Viz stuff
import matplotlib.pyplot as plt
from skimage import img_as_float
from skimage import exposure

# Local code
from Guider import GuiderPHD2
import time
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')

# Local stuff : Camera
from Camera.IndiAbstractCameraSimulator import IndiAbstractCameraSimulator
from Service.NTPTimeService import HostTimeService

if __name__ == '__main__':
    config = dict(
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
                                      config=config,
                                      connect_on_create=False)
    cam.connect()
    cam.prepare_shoot()


    config2 = dict(
        camera_name='Guide Simulator',
        SIMULATOR_SETTINGS=dict(
            SIM_XRES=1936,
            SIM_YRES=1096,
            SIM_XSIZE=2.9,
            SIM_YSIZE=2.9,
            SIM_MAXVAL=65000,
            SIM_SATURATION=1,
            SIM_LIMITINGMAG=17,
            SIM_NOISE=5,
            SIM_SKYGLOW=19.5,
            SIM_OAGOFFSET=0,
            SIM_POLAR=0,
            SIM_POLARDRIFT=0,
            SIM_ROTATION=0,
            SIM_KING_GAMMA=0,
            SIM_KING_THETA=0,
            SIM_TIME_FACTOR=1),
        SCOPE_INFO=dict(
            FOCAL_LENGTH=800,
            APERTURE=200),
        pointing_seconds=30,
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
    cam2 = IndiAbstractCameraSimulator(serv_time=HostTimeService(),
                                      config=config2,
                                      connect_on_create=False)
    cam2.connect()
    cam2.prepare_shoot()











    config = {
        "host": "localhost",
        "port": 4400,
        # profile_id : 1 # For IRL setup
        "profile_id": 2,
        "exposure_time_sec": 2,
        "settle": {
            "pixels": 1.5,
            "time": 10,
            "timeout": 60
        },
        "dither": {
            "pixels": 3.0,
            "ra_only": False
        }
    }

    g = GuiderPHD2.GuiderPHD2(config=config)
    g.launch_server()
    g.connect()
    g.get_connected()
    g.set_exposure(2.0)
    # g.loop() not needed
    g.guide()
    # guide for 5 min:
    for i in range(5 * 60):
        g.receive()
        time.sleep(0.1)
        # Acquire data
        cam.setExpTimeSec(4)
        cam.shoot_async()
        cam.synchronize_with_image_reception()
        fits = cam.get_received_image()

    g.disconnect()
    g.terminate_server()



















    # Show image
    fig, ax = plt.subplots(1, figsize=(16, 9))
    img = fits[0].data
    img_eq = exposure.equalize_hist(img)
    print_ready_img = img_as_float(img_eq)
    print(f"Print ready has shape {print_ready_img.shape}")
    ax.imshow(print_ready_img)
    plt.show()
