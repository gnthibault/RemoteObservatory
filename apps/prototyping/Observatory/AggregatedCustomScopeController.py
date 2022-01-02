# Basic stuff
import logging
import time

# Local stuff : IndiClient
#from helper.IndiClient import IndiClient

# Local stuff : Mount
from Observatory.AggregatedCustomScopeController import UPBV2
from Observatory.AggregatedCustomScopeController import ArduinoServoController
#from Observatory.AggregatedCustomScopeController import AggregatedCustomScopeController


#Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

if __name__ == '__main__':

    # TEST UPBV2 first
    config_upbv2 = dict(
                device_name="Pegasus UPB",
                device_port="/dev/serial/by-id/usb-Pegasus_Astro_UPBv2_revD_UPB25S4VWV-if00-port0",
                connection_type="CONNECTION_SERIAL",
                baud_rate=9600,
                polling_ms=1000,
                adjustable_voltage_value=5,
                power_labels=dict(
                    POWER_LABEL_1="MAIN_TELESCOPE_DUSTCAP_CONTROL",
                    POWER_LABEL_2="TELESCOPE_LEVEL_POWER", #SPOX_AND_DUSTCAP_POWER
                    POWER_LABEL_3="FOCUSER_LEVEL_POWER", #PRIMARY_FOCUSER_POWER
                    POWER_LABEL_4="MOUNT_POWER"),
                always_on_power_identifiers=dict(
                    MAIN_TELESCOPE_DUSTCAP_CONTROL=True,
                    TELESCOPE_LEVEL_POWER=False, #SPOX_AND_DUSTCAP_POWER
                    FOCUSER_LEVEL_POWER=False, #PRIMARY_FOCUSER_POWER
                    MOUNT_POWER=False),
                usb_labels=dict(
                    USB_LABEL_1="PRIMARY_CAMERA",
                    USB_LABEL_2="ARDUINO_CONTROL_BOX",
                    USB_LABEL_3="GUIDE_CAMERA",
                    USB_LABEL_4="FIELD_CAMERA",
                    USB_LABEL_5="WIFI_ROUTER",
                    USB_LABEL_6="SPECTRO_CONTROL_BOX"),
                always_on_usb_identifiers=dict(
                    PRIMARY_CAMERA=False,
                    ARDUINO_CONTROL_BOX=False,
                    GUIDE_CAMERA=False,
                    FIELD_CAMERA=False,
                    WIFI_ROUTER=True,
                    SPECTRO_CONTROL_BOX=False),
                dew_labels=dict(
                    DEW_LABEL_1="PRIMARY_FAN",
                    DEW_LABEL_2="SECONDARY_DEW_HEATER",
                    DEW_LABEL_3="FINDER_DEW_HEATER"),
                auto_dew_identifiers=dict(
                    PRIMARY_FAN=False,
                    SECONDARY_DEW_HEATER=True,
                    FINDER_DEW_HEATER=True),
                auto_dew_aggressivity=200, # Number between 50 and 250
                indi_client=dict(indi_host="localhost",
                                 indi_port=7624))

    # Now test UPBV2
    upbv2 = UPBV2(
        config=config_upbv2,
        connect_on_create=True)
    print(upbv2.get_power_info())
    print(upbv2.get_weather_info())

    # Now test Arduino controller
    upbv2.setup_telescope_power_on()

    # config for simple arduino
    config_arduino = dict(
                device_name="Arduino",
                device_port="/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0",
                connection_type="CONNECTION_SERIAL",
                baud_rate=57600,
                polling_ms=1000,
                indi_client=dict(indi_host="localhost",
                                 indi_port=7624))
    arduino = ArduinoServoController(
        config=config_arduino,
        connect_on_create=True)
    print("test")
    arduino.open_finder_dustcap()
    arduino.close_finder_dustcap()

    config_aggregated = dict(
        config_upbv2=config_upbv2,
        config_arduino=config_arduino,
    )

    aggregated = AggregatedCustomScopeController(
        config=config_aggregated,
        connect_on_create=True)

    # delay_sec = 5
    # print(f"Switching on flat panel {controller.status()}")
    # controller.switch_on_flat_panel()
    # print(f"{controller.status()}")
    # time.sleep(delay_sec)
    # controller.switch_off_flat_panel()
    # print(f"Switching on scope fan {controller.status()}")
    # controller.switch_on_scope_fan()
    # print(f"{controller.status()}")
    # time.sleep(delay_sec)
    # controller.switch_off_scope_fan()
    # print(f"Switching on scope dew heater {controller.status()}")
    # controller.switch_on_scope_dew_heater()
    # print(f"{controller.status()}")
    # time.sleep(delay_sec)
    # controller.switch_off_scope_dew_heater()
    # print(f"Switching on corrector dew heater {controller.status()}")
    # controller.switch_on_corrector_dew_heater()
    # print(f"{controller.status()}")
    # time.sleep(delay_sec)
    # controller.switch_off_corrector_dew_heater()
    # print(f"Switching on finder dew heater {controller.status()}")
    # controller.switch_on_finder_dew_heater()
    # print(f"{controller.status()}")
    # time.sleep(delay_sec)
    # controller.switch_off_finder_dew_heater()
    # print(f"Switching on camera {controller.status()}")
    # controller.switch_on_camera()
    # print(f"{controller.status()}")
    # time.sleep(delay_sec)
    # controller.switch_off_camera()
    # print(f"Switching on main mount {controller.status()}")
    # controller.switch_on_mount()
    # print(f"{controller.status()}")
    # time.sleep(delay_sec)
    # controller.switch_off_mount()
    # print(f"Opening up main scope dustcap {controller.status()}")
    # print(f"Before opening scope dustcap status: "
    #       f"{controller.get_switch('FINDER_SERVO_DUSTCAP_SWITCH')}")
    # controller.open_finder_dustcap()
    # print(f"{controller.status()}")
    # time.sleep(delay_sec)
    # print(f"After opening scope dustcap status: "
    #       f"{controller.get_switch('FINDER_SERVO_DUSTCAP_SWITCH')}")
    # controller.close_finder_dustcap()
    # print(f"After closing scope dustcap: "
    #       f"{controller.get_switch('FINDER_SERVO_DUSTCAP_SWITCH')}")
    # print(f"{controller.status()}")
    # print("Opening up finder dustcap")
    # print(f"Before opening finder dustcap status: "
    #       f"{controller.get_switch('SCOPE_SERVO_DUSTCAP_SWITCH')}")
    # controller.open_scope_dustcap()
    # print(f"{controller.status()}")
    # time.sleep(delay_sec)
    # print(f"After opening finder dustcap status: "
    #       f"{controller.get_switch('SCOPE_SERVO_DUSTCAP_SWITCH')}")
    # controller.close_scope_dustcap()
    # print(f"After closing finder dustcap status: "
    #       f"{controller.get_switch('SCOPE_SERVO_DUSTCAP_SWITCH')}")
    # print(f"{controller.status()}")
    # time.sleep(delay_sec)

    #res = controller.get_switch("CAMERA_RELAY")
    #res = controller.device.getSwitch("CAMERA_RELAY")
    #print(res)
    #for i in res:
    #    print("======")
    #    print(i.name)
    #    print(i.s)

