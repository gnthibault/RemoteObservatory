# Basic stuff
import logging.config

# Miscellaneous
import matplotlib.pyplot as plt

# Local stuff : Camera
from Camera.IndiASICameraNonCool import IndiASICameraNonCool
from Service.NTPTimeService import HostTimeService

# For this t
if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    config = dict(
        camera_name='ZWO CCD ASI290MM Mini',
        # SCOPE_INFO=dict(
        #     FOCAL_LENGTH=800,
        #     APERTURE=200),
        default_exp_time_sec=5,
        default_gain=300,
        default_offset=10,
        autofocus_seconds=4,
        autofocus_roi_size=None,
        autofocus_merit_function="half_flux_radius", #"vollath_F4"
        focuser=dict(
            module="IndiBaaderSteelDrive2Focuser",
            device_name="Baader SteelDriveII",
            device_port="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AB0KCL5O-if00-port0",
            connection_type="CONNECTION_SERIAL",
            baud_rate="19200",
            polling_ms="1000",
            home_position="2000",
            default_focus="1300",
            focus_range=dict(
                min=1250,
                max=2750),
            autofocus_step=dict(
                coarse=100,
                fine=50),
            autofocus_range=dict(
                coarse=1500,
                fine=500),
            indi_client=dict(
                indi_host="192.168.0.194",
                indi_port="7624")
        ),
        indi_client=dict(
            indi_host="192.168.0.194",
            indi_port="7624")
        )

    # test indi virtual camera class
    cam = IndiASICameraNonCool(serv_time=HostTimeService(), config=config, connect_on_create=True)
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
    cam.focuser.park_focuser()
    assert autofocus_status[0], "Focusing failed"
    print("Done")
