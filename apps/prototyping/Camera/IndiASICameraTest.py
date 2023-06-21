# Basic stuff

# Viz stuff
import matplotlib.pyplot as plt
from skimage import img_as_float
from skimage import exposure

# Local stuff : IndiClient
from helper.IndiClient import IndiClient

# Local stuff : Camera
from Camera.IndiASICamera import IndiASICamera
from Service.NTPTimeService import HostTimeService

if __name__ == '__main__':
    # test indi client
    # config = dict(
    # camera_name='Altair AA183MPRO',
    # autofocus_seconds=5,
    # pointing_seconds=30,
    # autofocus_roi_size=500,
    # indi_client=dict(
    #     indi_host="192.168.0.33",
    #     indi_port="7624"
    # ))
    config = dict(
        camera_name='ZWO CCD ASI183MM Pro',
        pointing_seconds=30,
        adjust_center_x=400,
        adjust_center_y=400,
        adjust_roi_search_size=50,
        adjust_pointing_seconds=5,
        autofocus_seconds=5,
        autofocus_roi_size=500,
        autofocus_merit_function="half_flux_radius",
        indi_client=dict(
            indi_host="192.168.144.32",
            indi_port=7624),
        # focuser=dict(
        #     module="IndiFocuser",
        #     focuser_name="Focuser Simulator",
        #     port="/dev/ttyUSB0",
        #     focus_range=dict(
        #         min=30000,
        #         max=50000),
        #     autofocus_step=dict(
        #         fine=750,
        #         coarse=2500),
        #     autofocus_range=dict(
        #         fine=15000,
        #         coarse=30000),
        #     indi_client=dict(
        #         indi_host="192.168.144.32",
        #         indi_port="7624"),
        # )
    )

    # test indi virtual camera class
    cam = IndiASICamera(config=config,
                        serv_time=HostTimeService(),
                        connect_on_create=False)
    cam.connect()

    # Play with camera configuration
    cam.set_roi({'X': 256, 'Y': 480, 'WIDTH': 512, 'HEIGHT': 640})
    # get_roi
    print(f"Current camera ROI is: {cam.get_roi()}")
    cam.set_roi({'X': 0, 'Y': 0, 'WIDTH': 1280, 'HEIGHT': 1024})
    # get_roi
    print(f"Current camera ROI is: {cam.get_roi()}")

    #print('Setting cooling on')
    #cam.set_cooling_on() THIS VECTOR IS EXPECTED TO BE IN BUSY STATE, NOT IDLE NOR OK, THAT's WHY THERE IS TIMEOUT
    print(f"Current camera temperature is: {cam.get_temperature()}")
    target_temp = -5.5
    print(f"Now, setting temperature to: {target_temp}")
    cam.set_temperature(target_temp)
    print(f"Current camera temperature is: {cam.get_temperature()}")
    target_temp = -8
    print(f"Now, setting temperature to: {target_temp}")
    cam.set_temperature(target_temp)
    print(f"Current camera temperature is: {cam.get_temperature()}")
    #cam.set_cooling_off()

    # set frame type (mostly for simulation purpose
    cam.set_frame_type('FRAME_DARK')
    cam.set_frame_type('FRAME_FLAT')
    cam.set_frame_type('FRAME_BIAS')
    cam.set_frame_type('FRAME_LIGHT')

    # set gain
    print(f"gain is {cam.get_gain()}")
    cam.set_gain(100)
    print(f"gain is {cam.get_gain()}")

    # Acquire data
    cam.prepare_shoot()
    cam.setExpTimeSec(10)
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