# Basic stuff

# Viz stuff
import matplotlib.pyplot as plt
from skimage import img_as_float
from skimage import exposure

# Local stuff : IndiClient
from helper.IndiClient import IndiClient

# Local stuff : Camera
from Camera.IndiAltairCamera import IndiAltairCamera
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
        camera_name='Altair AA183MPRO',
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
            indi_port=7625),
    )

    # test indi virtual camera class
    cam = IndiAltairCamera(config=config,
                        serv_time=HostTimeService(),
                        connect_on_create=False)
    cam.connect()

    # Play with camera configuration
    cam.set_roi({'X': 256, 'Y': 480, 'WIDTH': 512, 'HEIGHT': 640})
    # get_roi
    print(f"Current camera ROI is: {cam.get_roi()}")
    cam.set_roi({'X': 0, 'Y': 0, 'WIDTH': 5440, 'HEIGHT': 3648})
    # get_roi
    print(f"Current camera ROI is: {cam.get_roi()}")

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