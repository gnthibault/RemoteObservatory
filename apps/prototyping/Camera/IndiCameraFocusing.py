# Basic stuff
import logging
import logging.config
import threading

# Miscellaneous
import io
from astropy.io import fits

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
            port = "/dev/ttyUSB0",
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