# Basic stuff
import logging
import time

# Local stuff : IndiClient
#from helper.IndiClient import IndiClient

# Local stuff : Mount
from Observatory.AggregatedCustomScopeController import UPBV2
from Observatory.AggregatedCustomScopeController import ArduinoServoController
from Observatory.AggregatedCustomScopeController import AggregatedCustomScopeController


#Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord
logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':

    # TEST UPBV2 first
    config_upbv2= dict(
        device_name="Pegasus UPB",
        device_port="/dev/serial/by-id/usb-Pegasus_Astro_UPBv2_revD_UPB25S4VWV-if00-port0",
        connection_type="CONNECTION_SERIAL",
        baud_rate="9600",
        polling_ms="1000",
        dustcap_travel_delay_s="10",
        adjustable_voltage_value="5",
        power_labels= dict(
            POWER_LABEL_1="MAIN_TELESCOPE_DUSTCAP_CONTROL",
            POWER_LABEL_2="SPOX_AND_DUSTCAP_POWER",
            POWER_LABEL_3="MAIN_CAMERA_POWER",
            POWER_LABEL_4="MOUNT_POWER"),
        always_on_power_identifiers= dict(
            MAIN_TELESCOPE_DUSTCAP_CONTROL="True",
            SPOX_AND_DUSTCAP_POWER="False",
            MAIN_CAMERA_POWER="False",
            MOUNT_POWER="False"),
        usb_labels= dict(
            USB_LABEL_1="FIELD_CAMERA",
            USB_LABEL_2="PRIMARY_CAMERA",
            USB_LABEL_3="SPECTRO_CONTROL_BOX",
            USB_LABEL_4="ARDUINO_CONTROL_BOX",
            USB_LABEL_5="WIFI_ROUTER",
            USB_LABEL_6="GUIDE_CAMERA"),
        always_on_usb_identifiers= dict(
            FIELD_CAMERA="False",
            PRIMARY_CAMERA="False",
            SPECTRO_CONTROL_BOX="False",
            ARDUINO_CONTROL_BOX="False",
            WIFI_ROUTER="True,",
            GUIDE_CAMERA="False"),
        dew_labels= dict(
            DEW_LABEL_1="PRIMARY_FAN",
            DEW_LABEL_2="SECONDARY_DEW_HEATER",
            DEW_LABEL_3="FINDER_DEW_HEATER"),
        auto_dew_identifiers= dict(
            PRIMARY_FAN="False",
            SECONDARY_DEW_HEATER="True",
            FINDER_DEW_HEATER="True"),
        auto_dew_aggressivity="150 # Number between 50 and 250",
        indi_client= dict(
            indi_host="localhost",
            indi_port="7625")
    )

    # Now test UPBV2
    upbv2 = UPBV2(
        config=config_upbv2,
        connect_on_create=True)
    print(upbv2.get_power_info())
    print(upbv2.get_weather_info())

    getval = lambda: getval()
    upbv2.power_on_arduino_control_box()
    print(f'2#################################### {getval()}')
    upbv2.switch_on_arduino_control_box_usb()
    print(f'3#################################### {getval()}')
    print(f'3.5#################################### {getval()}')
    # Power acquisition instruments: this is a very specific case, see https://github.com/indilib/indi-3rdparty/issues/822
    print(f'4#################################### {getval()}')
    # Power mount
    print(f'5#################################### {getval()}')

    # # Now test Arduino controller
    # upbv2.open_scope_dustcap()
    #
    # # config for simple arduino
    # config_arduino = dict(
    #             device_name="Arduino",
    #             device_port="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AB0L9VL1-if00-port0",
    #             connection_type="CONNECTION_SERIAL",
    #             baud_rate=57600,
    #             polling_ms=1000,
    #             indi_client=dict(indi_host="localhost",
    #                              indi_port=7625))
    # # One need to enable usb power for arduino controller beforehand
    # upbv2.power_on_arduino_control_box()
    # indi_driver_connect_delay_s = 10
    # time.sleep(indi_driver_connect_delay_s)
    # arduino = ArduinoServoController(
    #     config=config_arduino,
    #     connect_on_create=True)
    #
    # arduino.open_finder_dustcap()
    # arduino.close_finder_dustcap()
    #
    # config_aggregated = dict(
    #     config_upbv2=config_upbv2,
    #     config_arduino=config_arduino,
    #     indi_driver_connect_delay_s=10,
    #     indi_resetable_instruments_driver_name_list=dict(
    #         driver_1="ZWO CCD",
    #         driver_2="Altair",
    #         driver_3="Shelyak SPOX",
    #         driver_4="PlayerOne CCD",
    #         driver_5="Arduino telescope controller"
    #     ),
    #     indi_mount_driver_name="Losmandy Gemini",
    #     indi_webserver_host="localhost",
    #     indi_webserver_port="8624", )
    #
    # aggregated = AggregatedCustomScopeController(
    #     config=config_aggregated,
    #     connect_on_create=True)
    # aggregated.switch_on_instruments()
    # aggregated.open()
    # aggregated.close()
    # aggregated.switch_off_instruments()
    # aggregated.deinitialize()
    # aggregated.initialize()
    # aggregated.open()
    # aggregated.close()