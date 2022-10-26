# Basic stuff
import logging

# Viz stuff
import matplotlib.pyplot as plt
from skimage import img_as_float
from skimage import exposure

# Local stuff : Camera
from Camera.IndiAbstractCameraSimulator import IndiAbstractCameraSimulator
from Service.NTPTimeService import HostTimeService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')

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
        autofocus_size=500,
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
                                      connect_on_create=False,
                                      primary=True)
    cam.connect()
    cam.prepare_shoot()
    # Acquire data
    cam.setExpTimeSec(4)
    cam.shoot_async()
    cam.synchronize_with_image_reception()
    fits = cam.get_received_image()

    # Show image
    fig, ax = plt.subplots(1, figsize=(16, 9))
    img = fits[0].data
    img_eq = exposure.equalize_hist(img)
    print_ready_img = img_as_float(img_eq)
    print(f"Print ready has shape {print_ready_img.shape}")
    ax.imshow(print_ready_img)
    plt.show()