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
from Camera.IndiCamera import IndiCamera


if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    config = dict(
        camera_name='CCD Simulator',
        focuser=dict(
            module="IndiFocuser",
            focuser_name="Focuser Simulator",
            port="/dev/ttyUSB0",
            backlash=10,
            focus_range=dict(
                min=0,
                max=100),
            autofocus_step=dict(
                coarse=1,
                fine=10),
            autofocus_range=dict(
                coarse=40,
                fine=60),
            indi_client=dict(
                indi_host="localhost",
                indi_port="7624")
            ),
        indi_client=dict(
            indi_host="localhost",
            indi_port="7624")
        )

    # test indi virtual camera class
    cam = IndiCamera(config=config, connect_on_create=True)

    # Now focus
    assert(cam.focuser.is_connected)
    autofocus_event = threading.Event()
    #cam.autofocus_async(autofocus_event)

    thumbnail_size = 500
    cam.prepare_shoot()
    fits = cam.get_thumbnail(exp_time_sec=5, thumbnail_size=thumbnail_size)
    try:
        image = fits.data
    except:
        image = fits[0].data
    plt.imshow(image)
    plt.show()
