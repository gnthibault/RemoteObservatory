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
from Camera.IndiASICameraNonCool import IndiASICameraNonCool
from Observatory.AggregatedCustomScopeController import AggregatedCustomScopeController
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
        pointing_seconds=30,
        autofocus_seconds=5,
        autofocus_roi_size=650,
        autofocus_merit_function="half_flux_radius",
        focuser=dict(
            module="AggregatedCustomScopeController",
            focuser_name="Pegasus UPB",
            device_port="/dev/serial/by-id/usb-Pegasus_Astro_UPBv2_revD_UPB25S4VWV-if00-port0",
            connection_type="CONNECTION_SERIAL",
            baud_rate="9600",
            polling_ms="1000",
            dustcap_travel_delay_s="10",
            adjustable_voltage_value="5",
            power_labels=dict(
                POWER_LABEL_1="MAIN_TELESCOPE_DUSTCAP_CONTROL",
                POWER_LABEL_2="SPOX_AND_DUSTCAP_POWER",
                POWER_LABEL_3="MAIN_CAMERA_POWER",
                POWER_LABEL_4="MOUNT_POWER"),
            always_on_power_identifiers=dict(
                MAIN_TELESCOPE_DUSTCAP_CONTROL="True",
                SPOX_AND_DUSTCAP_POWER="False",
                MAIN_CAMERA_POWER="False",
                MOUNT_POWER="False"),
            usb_labels=dict(
                USB_LABEL_1="FIELD_CAMERA",
                USB_LABEL_2="PRIMARY_CAMERA",
                USB_LABEL_3="SPECTRO_CONTROL_BOX",
                USB_LABEL_4="ARDUINO_CONTROL_BOX",
                USB_LABEL_5="WIFI_ROUTER",
                USB_LABEL_6="GUIDE_CAMERA"),
            always_on_usb_identifiers=dict(
                FIELD_CAMERA="False",
                PRIMARY_CAMERA="False",
                SPECTRO_CONTROL_BOX="False",
                ARDUINO_CONTROL_BOX="False",
                WIFI_ROUTER="True,",
                GUIDE_CAMERA="False"),
            dew_labels=dict(
                DEW_LABEL_1="PRIMARY_FAN",
                DEW_LABEL_2="SECONDARY_DEW_HEATER",
                DEW_LABEL_3="FINDER_DEW_HEATER"),
            auto_dew_identifiers=dict(
                PRIMARY_FAN="False",
                SECONDARY_DEW_HEATER="True",
                FINDER_DEW_HEATER="True"),
            auto_dew_aggressivity="150 # Number between 50 and 250",
            focus_range=dict(
                min=25000,
                max=50000),
            autofocus_step=dict(
                coarse=2500,
                fine=1000),
            autofocus_range=dict(
                coarse=25000,
                fine=10000),
            indi_client=dict(
                indi_host="192.168.8.202",
                indi_port="7624")
        ),
        indi_client=dict(
            indi_host="192.168.8.202",
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
    assert autofocus_status[0], "Focusing failed"
    print("Done")
