# Basic stuff
import json
import logging
import time

# Local
from Base.Base import Base
from helper.IndiDevice import IndiDevice
from utils.error import ScopeControllerError
from utils.error import IndiClientPredicateTimeoutError

class UPBV2(IndiDevice, Base):
    """
        'CONNECTION': <helper.device.indiswitchvector at 0x7effc16842e0>,
        'DRIVER_INFO': <helper.device.inditextvector at 0x7effc1638040>,
        'DEBUG': <helper.device.indiswitchvector at 0x7effc1638700>,
        'SIMULATION': <helper.device.indiswitchvector at 0x7effc16388b0>,
        'CONFIG_PROCESS': <helper.device.indiswitchvector at 0x7effc1638a60>,
        'POLLING_PERIOD': <helper.device.indinumbervector at 0x7effc1638cd0>,
        'CONNECTION_MODE': <helper.device.indiswitchvector at 0x7effc1638df0>,
        'SYSTEM_PORTS': <helper.device.indiswitchvector at 0x7effc1638f40>,
        'DEVICE_PORT': <helper.device.inditextvector at 0x7effc1684040>,
        'DEVICE_BAUD_RATE': <helper.device.indiswitchvector at 0x7effc16407f0>,
        'DEVICE_AUTO_SEARCH': <helper.device.indiswitchvector at 0x7effc1640b20>,
        'DEVICE_PORT_SCAN': <helper.device.indiswitchvector at 0x7effc1640cd0>,
        'FIRMWARE_INFO': <helper.device.inditextvector at 0x7effc1640190>,
        'POWER_CYCLE': <helper.device.indiswitchvector at 0x7effc16405e0>,
        'POWER_SENSORS': <helper.device.indinumbervector at 0x7effc1645ee0>,
        'POWER_CONSUMPTION': <helper.device.indinumbervector at 0x7effc164b700>,
        'REBOOT_DEVICE': <helper.device.indiswitchvector at 0x7effc164b880>,
        'POWER_CONTROL': <helper.device.indiswitchvector at 0x7effc1645e50>,
        'POWER_CONTROL_LABEL': <helper.device.inditextvector at 0x7effc164bdf0>,
        'POWER_CURRENT': <helper.device.indinumbervector at 0x7effc15840a0>,
        'POWER_ON_BOOT': <helper.device.indiswitchvector at 0x7effc1584250>,
        'POWER_OVER_CURRENT': <helper.device.indilightvector at 0x7effc15844f0>,
        'ADJUSTABLE_VOLTAGE': <helper.device.indinumbervector at 0x7effc15848e0>,
        'AUTO_DEW': <helper.device.indiswitchvector at 0x7effc1584a00>,
        'DEW_CONTROL_LABEL': <helper.device.inditextvector at 0x7effc1584c10>,
        'AUTO_DEW_AGG': <helper.device.indinumbervector at 0x7effc1584e20>,
        'DEW_PWM': <helper.device.indinumbervector at 0x7effc1584f40>,
        'DEW_CURRENT': <helper.device.indinumbervector at 0x7effc1586100>,
        'USB_HUB_CONTROL': <helper.device.indiswitchvector at 0x7effc1586280>,
        'USB_PORT_CONTROL': <helper.device.indiswitchvector at 0x7effc1586430>,
        'USB_CONTROL_LABEL': <helper.device.inditextvector at 0x7effc1586760>,
        'FOCUS_MOTION': <helper.device.indiswitchvector at 0x7effc1586a90>,
        'REL_FOCUS_POSITION': <helper.device.indinumbervector at 0x7effc1586c40>,
        'ABS_FOCUS_POSITION': <helper.device.indinumbervector at 0x7effc1586d60>,
        'FOCUS_MAX': <helper.device.indinumbervector at 0x7effc1586e80>,
        'FOCUS_ABORT_MOTION': <helper.device.indiswitchvector at 0x7effc1586fa0>,
        'FOCUS_SYNC': <helper.device.indinumbervector at 0x7effc1587130>,
        'FOCUS_REVERSE_MOTION': <helper.device.indiswitchvector at 0x7effc1587250>,
        'FOCUS_BACKLASH_TOGGLE': <helper.device.indiswitchvector at 0x7effc1587400>,
        'FOCUS_BACKLASH_STEPS': <helper.device.indinumbervector at 0x7effc15875b0>,
        'FOCUSER_SETTINGS': <helper.device.indinumbervector at 0x7effc15876d0>,
        'WEATHER_STATUS': <helper.device.indilightvector at 0x7effc15877f0>,
        'WEATHER_PARAMETERS': <helper.device.indinumbervector at 0x7effc1587940>,
        'WEATHER_TEMPERATURE': <helper.device.indinumbervector at 0x7effc1587ac0>,
        'WEATHER_HUMIDITY': <helper.device.indinumbervector at 0x7effc1587c40>,
        'WEATHER_DEWPOINT': <helper.device.indinumbervector at 0x7effc1587dc0>}
    """
    def __init__(self,
                 config=None,
                 connect_on_create=True):

        self.is_initialized = False

        if config is None:
            config = dict(
                device_name="Pegasus UPB",
                device_port="/dev/serial/by-id/usb-Pegasus_Astro_UPBv2_revD_UPB25S4VWV-if00-port0",
                connection_type="CONNECTION_SERIAL",
                baud_rate=9600,
                polling_ms=1000,
                dustcap_travel_delay_s=10,
                adjustable_voltage_value=5,
                power_labels=dict(
                    POWER_LABEL_1="MAIN_TELESCOPE_DUSTCAP_CONTROL",
                    POWER_LABEL_2="TELESCOPE_LEVEL_POWER", #SPOX_AND_DUSTCAP_POWER
                    POWER_LABEL_3="FOCUSER_LEVEL_POWER", #PRIMARY_FOCUSER_POWER
                    POWER_LABEL_4="MOUNT_POWER"),
                always_on_power_identifiers=dict(
                    MAIN_TELESCOPE_DUSTCAP_CONTROL=False,
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
                    ARDUINO_CONTROL_BOX=True,
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
                                 indi_port=7625))

        # Communication config
        self.device_port = config["device_port"]
        self.connection_type = config["connection_type"]
        self.baud_rate = str(config["baud_rate"])
        self.polling_ms = float(config["polling_ms"])
        self.dustcap_travel_delay_s = float(config["dustcap_travel_delay_s"])

        # labels
        self.power_labels = config["power_labels"]
        self.always_on_power_identifiers = config["always_on_power_identifiers"]
        self.usb_labels = config["usb_labels"]
        self.always_on_usb_identifiers = config["always_on_usb_identifiers"]
        self.dew_labels = config["dew_labels"]

        # power parameters
        self.adjustable_voltage_value = config["adjustable_voltage_value"]

        # dew parameters
        self.auto_dew_identifiers = config["auto_dew_identifiers"]
        self.auto_dew_aggressivity = str(config["auto_dew_aggressivity"])

        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config["device_name"],
                            indi_driver_name=config.get('indi_driver_name', None),
                            indi_client_config=config["indi_client"])

        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('configured successfully')

    def unpark(self):
        self.logger.debug("Unparking")
        self.start_indi_server()
        self.start_indi_driver()
        self.initialize()
        self.logger.debug("Successfully unparked")

    def initialize(self):
        """
        Connection is made in two phases:
          * connect client to server so that we can setup options, like port
          * connect server to actual physical device

        Then "initialize" all outputs such that the telescope is in a steady
        state, that can last a very long time (multiple days without operation)
        :return:
        """
        self.logger.debug("Initializing")
        self.connect(connect_device=False)
        self.set_device_communication_options()
        self.connect_device()
        self.set_all_labels()
        self.initialize_all_power_on_boot()
        self.initialize_all_power()
        self.initialize_adjustable_power_source()
        self.initialize_all_dew_outputs()
        self.set_auto_dew_aggressivity()
        time.sleep(1) # this is a very specific case, see https://github.com/indilib/indi-3rdparty/issues/822
        self.initialize_all_usb()
        self.initialize_usb_hub()

        self.is_initialized = True

        self.logger.debug("Successfully Initialized")

    def park(self):
        self.logger.debug("Parking")
        self.deinitialize()
        self.disconnect()
        self.stop_indi_server()
        self.logger.debug("Successfully parked")

    def deinitialize(self):
        if not self.is_initialized:
            self.logger.debug("No need for deinitializing")
            return
        self.logger.debug("Deinitializing")
        # Then switch off all electronic devices
        self.close_scope_dustcap()
        self.switch_off_scope_fan()
        self.switch_off_dew_heater()
        self.power_off_all_telescope_equipments()
        self.power_off_mount()

        self.is_initialized = False
        self.logger.debug("Successfully deinitialized")

    def set_device_communication_options(self):
        self.set_text("DEVICE_PORT", {"PORT": self.device_port})
        self.set_switch("CONNECTION_MODE", on_switches=[self.connection_type])
        self.set_switch("DEVICE_BAUD_RATE", on_switches=[self.baud_rate])
        self.set_polling_ms(polling_ms=self.polling_ms)

    def set_polling_ms(self, polling_ms=None):
        if polling_ms is not None:
            self.polling_ms = polling_ms
        self.set_number("POLLING_PERIOD", {'PERIOD_MS': self.polling_ms})

    def set_auto_dew_aggressivity(self, auto_dew_aggressivity=None):
        if auto_dew_aggressivity is not None:
            self.auto_dew_aggressivity = str(auto_dew_aggressivity)
        self.set_text("AUTO_DEW_AGG", {'AUTO_DEW_AGG_VALUE': self.auto_dew_aggressivity})

    def set_all_labels(self):
        self.set_text("POWER_CONTROL_LABEL", self.power_labels)
        self.set_text("USB_CONTROL_LABEL", self.usb_labels)
        self.set_text("DEW_CONTROL_LABEL", self.dew_labels)

    def initialize_all_power_on_boot(self):
        on_switches = [f"POWER_PORT_{i}" for i in range(1, 5) if self.always_on_power_identifiers[self.power_labels[f"POWER_LABEL_{i}"]]]
        off_switches = [f"POWER_PORT_{i}" for i in range(1, 5) if not self.always_on_power_identifiers[self.power_labels[f"POWER_LABEL_{i}"]]]
        self.set_switch("POWER_ON_BOOT", on_switches=on_switches, off_switches=off_switches)

    def initialize_all_power(self):
        on_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if self.always_on_power_identifiers[self.power_labels[f"POWER_LABEL_{i}"]]]
        off_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if not self.always_on_power_identifiers[self.power_labels[f"POWER_LABEL_{i}"]]]
        self.set_switch("POWER_CONTROL", on_switches=on_switches, off_switches=off_switches)

    def initialize_adjustable_power_source(self):
        self.set_number('ADJUSTABLE_VOLTAGE', {'ADJUSTABLE_VOLTAGE_VALUE': self.adjustable_voltage_value})

    def wait_dustcap_delay(self):
        time.sleep(self.dustcap_travel_delay_s)

    def initialize_all_usb(self):
        """
        On our setup, all but the PORT 5 need to be reset.
        PORT 5 is connected to our GL.inet router and needs to stay up always
        PORT ids goes from 1 to 6
        :return:
        """
        on_switches = [f"PORT_{i}" for i in range(1, 7) if self.always_on_usb_identifiers[self.usb_labels[f"USB_LABEL_{i}"]]]
        off_switches = [f"PORT_{i}" for i in range(1, 7) if not self.always_on_usb_identifiers[self.usb_labels[f"USB_LABEL_{i}"]]]
        self.set_switch("USB_PORT_CONTROL", on_switches=on_switches, off_switches=off_switches)

    def deinitialize_all_usb(self):
        self.initialize_all_usb()

    def initialize_usb_hub(self):
        self.logger.warning("initialize_usb_hub doesn't seems to be currently supported by indi driver")
        #self.set_switch("USB_HUB_CONTROL", on_switches=["INDI_ENABLED"])

    def power_on_spectro_controller(self):
        # 5V adjustable power source
        self.set_number('ADJUSTABLE_VOLTAGE', {'ADJUSTABLE_VOLTAGE_VALUE': self.adjustable_voltage_value})

    def power_on_acquisition_equipments(self):
        # Power telescope level equipments
        on_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if self.power_labels[f"POWER_LABEL_{i}"] in
                       ['MAIN_CAMERA_POWER']]
        self.set_switch("POWER_CONTROL", on_switches=on_switches)

    def switch_on_acquisition_equipments_usb(self):
        # USB
        on_switches = [f"PORT_{i}" for i in range(1, 7) if self.usb_labels[f"USB_LABEL_{i}"] in
                       ["FIELD_CAMERA", "PRIMARY_CAMERA", "GUIDE_CAMERA"]]
        self.set_switch("USB_PORT_CONTROL", on_switches=on_switches)

    def power_off_acquisition_equipments(self):
        # Power telescope level equipments
        off_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if self.power_labels[f"POWER_LABEL_{i}"] in
                       ['MAIN_CAMERA_POWER']]
        self.set_switch("POWER_CONTROL", off_switches=off_switches)

    def switch_off_acquisition_equipments_usb(self):
        # USB
        off_switches = [f"PORT_{i}" for i in range(1, 7) if self.usb_labels[f"USB_LABEL_{i}"] in
                       ["FIELD_CAMERA", "PRIMARY_CAMERA", "GUIDE_CAMERA"]]
        self.set_switch("USB_PORT_CONTROL", off_switches=off_switches)

    def power_on_calibration_equipments(self):
        # Power telescope level equipments
        on_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if self.power_labels[f"POWER_LABEL_{i}"] in
                       ['SPOX_AND_DUSTCAP_POWER']]
        self.set_switch("POWER_CONTROL", on_switches=on_switches)

    def switch_on_calibration_equipments_usb(self):
        # USB
        on_switches = [f"PORT_{i}" for i in range(1, 7) if self.usb_labels[f"USB_LABEL_{i}"] in
                       ["SPECTRO_CONTROL_BOX"]]
        self.set_switch("USB_PORT_CONTROL", on_switches=on_switches)

    def power_off_all_telescope_equipments(self):
        # Power off telescope level equipments
        off_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if self.power_labels[f"POWER_LABEL_{i}"] in
                        ['SPOX_AND_DUSTCAP_POWER', 'MAIN_CAMERA_POWER']]
        self.set_switch("POWER_CONTROL", off_switches=off_switches)

    def switch_off_all_telescope_equipments_usb(self):
        # USB
        off_switches = [f"PORT_{i}" for i in range(1, 7) if self.usb_labels[f"USB_LABEL_{i}"] in
                       ["FIELD_CAMERA", "PRIMARY_CAMERA", "SPECTRO_CONTROL_BOX", "ARDUINO_CONTROL_BOX", "GUIDE_CAMERA"]]
        self.set_switch("USB_PORT_CONTROL", off_switches=off_switches)

    def power_on_mount(self):
        # Power
        on_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if self.power_labels[f"POWER_LABEL_{i}"] == 'MOUNT_POWER']
        self.set_switch("POWER_CONTROL", on_switches=on_switches)

    def power_off_mount(self):
        # Power
        off_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if self.power_labels[f"POWER_LABEL_{i}"] == 'MOUNT_POWER']
        self.set_switch("POWER_CONTROL", off_switches=off_switches)

    def power_on_arduino_control_box(self):
        # 5V adjustable power source
        self.set_number('ADJUSTABLE_VOLTAGE', {'ADJUSTABLE_VOLTAGE_VALUE': self.adjustable_voltage_value})

    def switch_on_arduino_control_box_usb(self):
        # Now setup USB
        on_switches = [f"PORT_{i}" for i in range(1, 7) if self.usb_labels[f"USB_LABEL_{i}"] == "ARDUINO_CONTROL_BOX"]
        self.set_switch("USB_PORT_CONTROL", on_switches=on_switches)

    def initialize_all_dew_outputs(self):
        # Set power to 0 explicitly
        self.set_number("DEW_PWM", {'DEW_A': 0.0, 'DEW_B': 0.0, 'DEW_C': 0.0})

        # Set eligbility for automatic dew to False
        off_switches = [f"DEW_{l}" for i, l in enumerate("ABC")]
        self.set_switch("AUTO_DEW", off_switches=off_switches)

    def set_auto_dew_eligibility_on(self):
        """
        Set auto dew eligibility
        :return:
        """
        on_switches = [f"DEW_{l}" for i, l in enumerate("ABC") if self.auto_dew_identifiers[self.dew_labels[f"DEW_LABEL_{i+1}"]]]
        self.set_switch("AUTO_DEW", on_switches=on_switches)

    def set_auto_dew_eligibility_off(self):
        """
        Set auto dew eligibility
        :return:
        """
        off_switches = [f"DEW_{l}" for i, l in enumerate("ABC") if self.auto_dew_identifiers[self.dew_labels[f"DEW_LABEL_{i+1}"]]]
        self.set_switch("AUTO_DEW", off_switches=off_switches)

    def get_power_info(self):
        power_dict = self.get_number("POWER_SENSORS")
        #{'SENSOR_VOLTAGE': 13.7, 'SENSOR_CURRENT': 1.0, 'SENSOR_POWER': 13.0}
        power_dict.update(self.get_number("POWER_CONSUMPTION"))
        #{'CONSUMPTION_AVG_AMPS': 0.74, 'CONSUMPTION_AMP_HOURS': 249.28, 'CONSUMPTION_WATT_HOURS': 3402.6}
        power_dict.update(self.get_number("POWER_CURRENT"))
        #{'POWER_CURRENT_1': 0.0, 'POWER_CURRENT_2': 0.04, 'POWER_CURRENT_3': 0.0, 'POWER_CURRENT_4': 0.13}
        power_dict.update(self.get_number("DEW_CURRENT"))
        #{'DEW_CURRENT_A': 0.0, 'DEW_CURRENT_B': 0.0, 'DEW_CURRENT_C': 0.0}

        return power_dict

    def get_weather_info(self):
        """
        Relevant info vectors:
            'WEATHER_STATUS': <helper.device.indilightvector at 0x7effc15877f0>,
            'WEATHER_PARAMETERS': <helper.device.indinumbervector at 0x7effc1587940>,
            'WEATHER_TEMPERATURE': <helper.device.indinumbervector at 0x7effc1587ac0>,
            'WEATHER_HUMIDITY': <helper.device.indinumbervector at 0x7effc1587c40>,
            'WEATHER_DEWPOINT': <helper.device.indinumbervector at 0x7effc1587dc0>}
        :return:
        """
        weather_dict = self.get_light("WEATHER_STATUS")
        #{'WEATHER_TEMPERATURE': 'Ok'}
        weather_dict.update(self.get_number("WEATHER_PARAMETERS"))
        #{'WEATHER_TEMPERATURE': 17.8, 'WEATHER_HUMIDITY': 45.0, 'WEATHER_DEWPOINT': 5.7}
        #weather_dict.update(self.get_number("WEATHER_TEMPERATURE"))
        #{'MIN_OK': -15.0, 'MAX_OK': 35.0, 'PERC_WARN': 15.0}
        #weather_dict.update(self.get_number("WEATHER_HUMIDITY"))
        #{'MIN_OK': 0.0, 'MAX_OK': 100.0, 'PERC_WARN': 15.0}
        #weather_dict.update(self.get_number("WEATHER_DEWPOINT"))
        #{'MIN_OK': 0.0, 'MAX_OK': 100.0, 'PERC_WARN': 15.0}

        return weather_dict

    def switch_on_scope_fan(self):
        """ blocking call: switch on fan to cool down primary mirror
            set pwm value from 0 to 100
        """
        fan_dict = {k: 85 for i, k in enumerate(["DEW_A", "DEW_B", "DEW_C"]) if self.dew_labels[f"DEW_LABEL_{i+1}"] == "PRIMARY_FAN"}
        self.set_number("DEW_PWM", fan_dict)

    def switch_off_scope_fan(self):
        """ blocking call: switch off fan for primary mirror
        """
        fan_dict = {k: 0 for i, k in enumerate(["DEW_A", "DEW_B", "DEW_C"]) if self.dew_labels[f"DEW_LABEL_{i+1}"] == "PRIMARY_FAN"}
        self.set_number("DEW_PWM", fan_dict)

    def switch_on_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on secondary mirror
        """
        self.set_auto_dew_eligibility_on()
        self.logger.debug("Switching on automatic dew heater")

    def switch_off_dew_heater(self):
        """ blocking call: switch off dew heater on secondary mirror
        """
        self.set_auto_dew_eligibility_off()
        self.logger.debug("Switching off automatic dew heater")

    def power_on_mount(self):
        """ blocking call: switch on main mount
        """
        on_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if (self.power_labels[f"POWER_LABEL_{i}"] == "MOUNT_POWER")]
        self.set_switch("POWER_CONTROL", on_switches=on_switches)

    def power_off_mount(self):
        """ blocking call: switch off main mount
        """
        off_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if (self.power_labels[f"POWER_LABEL_{i}"] == "MOUNT_POWER")]
        self.set_switch("POWER_CONTROL", off_switches=off_switches)

    def open_scope_dustcap(self):
        """ blocking call: open up main scope dustcap
        """
        on_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if (self.power_labels[f"POWER_LABEL_{i}"] in
                                                                     ["SPOX_AND_DUSTCAP_POWER"])]
        off_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if (self.power_labels[f"POWER_LABEL_{i}"] in
                                                                     ["MAIN_TELESCOPE_DUSTCAP_CONTROL"])]
        self.set_switch("POWER_CONTROL", on_switches=on_switches, off_switches=off_switches)
        self.wait_dustcap_delay()

    def close_scope_dustcap(self):
        """ blocking call: close main scope dustcap
        """
        on_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if (self.power_labels[f"POWER_LABEL_{i}"] in
                                                                     ["SPOX_AND_DUSTCAP_POWER",
                                                                      "MAIN_TELESCOPE_DUSTCAP_CONTROL"])]
        self.set_switch("POWER_CONTROL", on_switches=on_switches)
        self.wait_dustcap_delay()

class ArduinoServoController(IndiDevice, Base):
    """
     'CONNECTION': <helper.device.indiswitchvector
     'FINDER_SERVO_DUSTCAP_POS': <helper.device.indinumbervector
     'FINDER_SERVO_DUSTCAP_SWITCH': <helper.device.indiswitchvector
     'DRIVER_INFO': <helper.device.inditextvector
     'DEBUG': <helper.device.indiswitchvector
     'POLLING_PERIOD': <helper.device.indinumbervector
     'CONFIG_PROCESS': <helper.device.indiswitchvector
     'CONNECTION_MODE': <helper.device.indiswitchvector
     'SYSTEM_PORTS': <helper.device.indiswitchvector
     'DEVICE_PORT': <helper.device.inditextvector
     'DEVICE_BAUD_RATE': <helper.device.indiswitchvector
     'DEVICE_AUTO_SEARCH': <helper.device.indiswitchvector
     'DEVICE_PORT_SCAN': <helper.device.indiswitchvector
    """
    def __init__(self,
                 config=None,
                 connect_on_create=True):

        self.is_initialized = False

        if config is None:
            config = dict(
                device_name="Arduino telescope controller",
                device_port="/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0",
                connection_type="CONNECTION_SERIAL",
                baud_rate=57600,
                polling_ms=1000,
                indi_client=dict(indi_host="localhost",
                                 indi_port=7624))

        # Communication config
        self.device_port = config["device_port"]
        self.connection_type = config["connection_type"]
        self.baud_rate = str(config["baud_rate"])
        self.polling_ms = float(config["polling_ms"])

        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config["device_name"],
                            indi_driver_name=config.get('indi_driver_name', None),
                            indi_client_config=config["indi_client"])

        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('configured successfully')

    def unpark(self):
        self.logger.debug("About to unpark")
        self.start_indi_server()
        self.start_indi_driver()
        self.initialize()
        self.logger.debug("Successfully Unparked")

    def initialize(self):
        """
        Connection is made in two phases:
          * connect client to server so that we can setup options, like port
          * connect server to actual physical device
        :return:
        """
        self.logger.debug("Initializing")
        self.connect(connect_device=False) #TODO TN Urgent check if this is ok
        self.set_device_communication_options()
        self.connect_device()
        # We set the polling period only after the connection
        #('setNumberVector', {'device': 'Arduino', 'name': 'POLLING_PERIOD', 'state': 'Alert', 'timeout': '0', 'timestamp': '2021-12-28T17:47:21',
        #'message': 'Cannot change property while device is disconnected.'})
        self.initialize_servo()
        self.is_initialized = True
        self.logger.debug("Initialization done")

    def park(self):
        self.logger.debug("About to park")
        self.deinitialize()
        self.disconnect()
        self.stop_indi_server()
        self.logger.debug("Successfully parked")

    def deinitialize(self):
        if not self.is_initialized:
            self.logger.debug("No need for deinitializing")
            return
        self.logger.debug("Denitialization")
        self.close_finder_dustcap()
        self.disconnect()
        self.is_initialized = False
        self.logger.debug("Deinitialization done")

    def set_device_communication_options(self):
        self.set_text("DEVICE_PORT", {"PORT": self.device_port})
        self.set_switch("CONNECTION_MODE", on_switches=[self.connection_type])
        self.set_switch("DEVICE_BAUD_RATE", on_switches=[self.baud_rate])

    def set_polling_ms(self, polling_ms=None):
        if polling_ms is not None:
            self.polling_ms = polling_ms
        self.set_number("POLLING_PERIOD", {'PERIOD_MS': self.polling_ms})

    def initialize_servo(self, auto_dew_aggressivity=None):
        self.close_finder_dustcap()

    def open_finder_dustcap(self):
        """ blocking call: open up finder dustcap
        """
        self.logger.debug("Opening up finder dustcap -- For some reason we had to remove the greenlight synchronization on indi_duino driver")
        self.set_switch("FINDER_SERVO_DUSTCAP_SWITCH",
                        on_switches=['SERVO_SWITCH'],
                        sync=False)

    def close_finder_dustcap(self):
        """ blocking call: close finder dustcap
        """
        self.logger.debug("close finder dustcap -- For some reason we had to remove the greenlight synchronization on indi_duino driver")
        self.set_switch("FINDER_SERVO_DUSTCAP_SWITCH",
                        off_switches=['SERVO_SWITCH'],
                        sync=False)



class AggregatedCustomScopeController(Base):
    """
    This is more or less a custom class for a custom setup, where config for ports
    is the following:
    /dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0 -> Custom arduino nano with firmata (ttyUSB0 at the time of the test)
    /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AD0JE0ID-if00-port0 ->  Shelyak arduino SPOX (ttyUSB1 at the time of the test)
    /dev/serial/by-id/usb-Pegasus_Astro_UPBv2_revD_UPB25S4VWV-if00-port0 -> PEGASUS (ttyUSB2 at the time of the test)
    """
    def __init__(self, config=None, connect_on_create=False):
        Base.__init__(self)

        self.is_initialized = False
        # pin on arduino need to be configured either as input or ouput
        # it means that we need to keep track of pin status internally
        self.statuses = {
            "scope_fan": False,
            "scope_dew": False,
            "finder_dew": False,
            "mount_relay": False,
        }

        if config is None:
            config = dict(
                config_upbv2=None,
                config_arduino=None,
                indi_driver_connect_delay_s=10,
                indi_resetable_instruments_driver_map={
                    "ZWO CCD": "ZWO CCD ASI290MM Mini",
                    "Altair": "Altair AA183MPRO",
                    "Shelyak SPOX": "Shelyak SPOX",
                    "PlayerOne CCD": "PlayerOne CCD Ares-M PRO",
                    "Arduino telescope controller": "Arduino"
                },
                indi_mount_driver_name="Losmandy Gemini",
                indi_webserver_host="localhost",
                indi_webserver_port="8624")

        # Actual device config
        self.config_upbv2 = config["config_upbv2"]
        self.config_arduino = config["config_arduino"]

        # Local features
        self._indi_resetable_instruments_driver_map = config["indi_resetable_instruments_driver_map"]
        self._indi_driver_connect_delay_s = config["indi_driver_connect_delay_s"]
        self._indi_mount_driver_name = config["indi_mount_driver_name"]
        self._indi_mount_device_name = config["indi_mount_device_name"]
        self._indi_webserver_host = config["indi_webserver_host"]
        self._indi_webserver_port = config["indi_webserver_port"]

        # device related intialization will happen at initialization
        self.upbv2 = UPBV2(
            config=self.config_upbv2,
            connect_on_create=False)

        self.arduino_servo_controller = ArduinoServoController(
            config=self.config_arduino,
            connect_on_create=False)

        if connect_on_create:
            self.power_on_all_equipments()

        # Finished configuring
        self.logger.debug('configured successfully')

    # def reset_config(self):
    #     # initialize upbv2
    #     self.start_upbv2_driver()
    #     self.upbv2.initialize() # This force to put to zero power and usb usually before an indiserver reset

    def unpark(self):

        self.logger.debug("About to unpark in a reset-like manner")
        self.park()

        # Now actually start unparking
        self.upbv2.unpark()
        # self.logger.debug(f'1#################################### {self.upbv2.get_switch("USB_PORT_CONTROL")["PORT_4"]}')

        # Power servo controller
        self.upbv2.power_on_arduino_control_box()
        # self.logger.debug(f'2#################################### {self.upbv2.get_switch("USB_PORT_CONTROL")["PORT_4"]}')

        # power-on USB for the arduino
        self.upbv2.switch_on_arduino_control_box_usb()
        # self.logger.debug(f'3#################################### {self.upbv2.get_switch("USB_PORT_CONTROL")["PORT_4"]}')
        # self.logger.debug(f'3.5#################################### {self.upbv2.get_switch("USB_PORT_CONTROL")["PORT_4"]}')

        # Power acquisition instruments: this is a very specific case, see https://github.com/indilib/indi-3rdparty/issues/822
        self.upbv2.switch_on_acquisition_equipments_usb()
        # self.logger.debug(f'4#################################### {self.upbv2.get_switch("USB_PORT_CONTROL")["PORT_4"]}')

        # Power mount
        self.switch_on_mount()
        # self.logger.debug(f'5#################################### {self.upbv2.get_switch("USB_PORT_CONTROL")["PORT_4"]}')

        # Wait for the os serial port to be created, and stuff like that
        time.sleep(self._indi_driver_connect_delay_s)

        # Power acquisition instruments: this is a very specific case, see https://github.com/indilib/indi-3rdparty/issues/822
        self.upbv2.power_on_acquisition_equipments()
        # self.logger.debug(f'6#################################### {self.upbv2.get_switch("USB_PORT_CONTROL")["PORT_4"]}')
        # time.sleep(self._indi_driver_connect_delay_s)

        # # start or restart drivers if needed
        # self.start_all_drivers()
        # Now we need to wait a bit before trying to connect driver
        # but _indi_driver_connect_delay_s was already waited for at previous step
        # for driver_name, device_name in self._indi_resetable_instruments_driver_map.items():
        #     if not self.probe_device_driver_connection(driver_name=driver_name, device_name=device_name):
        #         self.logger.debug(f"Device {device_name} doesn't seems to have its driver properly started - restarting")
        #         self.restart_driver(driver_name)
        # Now we need to wait a bit before trying to connect driver
        # if not self.probe_device_driver_connection(driver_name=self._indi_mount_driver_name,
        #                                            device_name=self._indi_mount_device_name):
        #     self.restart_driver(self._indi_mount_driver_name)

        # Initialize dependent device
        # self.logger.debug(f'7#################################### {self.upbv2.get_switch("USB_PORT_CONTROL")["PORT_4"]}')
        self.arduino_servo_controller.unpark()

        self.is_initialized = True
        self.logger.debug("Successfully unparked")

    def park(self):
        """
        :return:
        """
        self.logger.debug("Parking")

        # Power acquisition instruments: this is a very specific case, see https://github.com/indilib/indi-3rdparty/issues/822
        if self.is_initialized:
            self.upbv2.power_off_acquisition_equipments()
            time.sleep(1)
            self.upbv2.switch_off_acquisition_equipments_usb()

            # Deinitialize arduino servo first (as it relies on upb power)
            self.arduino_servo_controller.park()

        # Deinitialize upbv2
        self.upbv2.park()

        self.is_initialized = False
        self.logger.debug("Successfully parked")

    def open(self):
        """ blocking call: opens both main telescope and guiding scope dustcap
        """
        self.logger.debug("Opening AggregatedCustomScopeController")
        # if not self.is_initialized:
        #     self.power_on_all_equipments()
        self.open_finder_dustcap()
        self.open_scope_dustcap()

    def close(self):
        """ blocking call: closes both main telescope and guiding scope dustcap
        """
        self.logger.debug("Closing AggregatedCustomScopeController")
        self.close_finder_dustcap()
        self.close_scope_dustcap()

    def switch_on_acquisition_instruments(self):
        """ blocking call: switch on cameras, calibration tools, finderscopes, etc...
            We also need to load the corresponding indi driver
        """
        # assert self.is_initialized
        # if not self.is_initialized:
        #     self.power_on_all_equipments()
        self.logger.debug("Switching on all instruments")
        self.upbv2.power_on_acquisition_equipments()

    # def switch_off_instruments(self):
    #     """ blocking call: switch off camera
    #     """
    #     self.logger.debug("Switching off all equipments connected to upbv2")
    #
    #     self.upbv2.power_off_all_telescope_equipments()
    #     time.sleep(1)
    #     self.upbv2.deinitialize_all_usb()
    #     for driver_name, device_name in self._indi_resetable_instruments_driver_map.items():
    #         self.stop_driver(driver_name)

    # def start_upbv2_driver(self):
    #     self.start_driver(driver_name="Pegasus UPB", check_started=True)
    #
    # def stop_upbv2_driver(self):
    #     self.stop_driver(driver_name="Pegasus UPB", check_started=True)
    #
    # def start_servo_controller_driver(self):
    #     self.start_driver(driver_name="Arduino telescope controller", check_started=True)
    #
    # def start_all_drivers(self):
    #     for driver_name, device_name in self._indi_resetable_instruments_driver_map.items():
    #         self.start_driver(driver_name, check_started=True)
    #     self.start_driver(self._indi_mount_driver_name, check_started=True)

    # def stop_all_drivers(self):
    #     for driver_name, device_name in self._indi_resetable_instruments_driver_map.items():
    #         self.stop_driver(driver_name)
    #     self.stop_driver(self._indi_mount_driver_name)
    #     self.stop_upbv2_driver()

    def switch_on_scope_fan(self):
        """ blocking call: switch on fan to cool down primary mirror
        """
        self.logger.debug("Switching on fan to cool down primary mirror")
        self.upbv2.switch_on_scope_fan()
        self.statuses["scope_fan"] = True

    def switch_off_scope_fan(self):
        """ blocking call: switch off fan for primary mirror
        """
        self.logger.debug("Switching off telescope fan on primary mirror")
        self.upbv2.switch_off_scope_fan()
        self.statuses["scope_fan"] = False

    def switch_on_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on secondary mirror
        """
        self.logger.debug("Switching on dew heater for secondary mirror")
        self.upbv2.switch_on_dew_heater()
        self.statuses["scope_dew"] = True

    def switch_off_dew_heater(self):
        """ blocking call: switch off dew heater on secondary mirror
        """
        self.logger.debug("Switching off telescope dew heater on secondary "
                          "mirror")
        self.upbv2.switch_off_dew_heater()
        self.statuses["scope_dew"] = False

    def switch_on_mount(self):
        """ blocking call: switch on main mount
        """
        self.logger.debug("Switching on main mount")
        self.upbv2.power_on_mount()
        self.statuses["mount_relay"] = True

    def switch_off_mount(self):
        """ blocking call: switch off main mount
        """
        self.logger.debug("Switching off main mount")
        self.upbv2.power_off_mount()
        self.statuses["mount_relay"] = False

    def open_scope_dustcap(self):
        """ blocking call: open up main scope dustcap
        """
        self.logger.debug("Opening up main scope dustcap")
        self.upbv2.open_scope_dustcap()

    def close_scope_dustcap(self):
        """ blocking call: close main scope dustcap
        """
        self.logger.debug("close main scope dustcap")
        self.upbv2.close_scope_dustcap()

    def open_finder_dustcap(self):
        """ blocking call: open up finder dustcap
        """
        self.logger.debug("Opening up finder dustcap")
        self.arduino_servo_controller.open_finder_dustcap()

    def close_finder_dustcap(self):
        """ blocking call: close finder dustcap
        """
        self.logger.debug("close finder dustcap")
        self.arduino_servo_controller.close_finder_dustcap()
   
    def status(self):
        if self.is_initialized:
            status = self.statuses.copy()
            status["finder_dustcap_open"] = self.arduino_servo_controller.get_switch(
                'FINDER_SERVO_DUSTCAP_SWITCH')['SERVO_SWITCH']
            switch_name = [f"POWER_CONTROL_{i}" for i in range(1, 5) if
                self.upbv2.power_labels[f"POWER_LABEL_{i}"]=="MAIN_TELESCOPE_DUSTCAP_CONTROL"][0]
            status["scope_dustcap_closed"] = self.upbv2.get_switch(
                'POWER_CONTROL')[switch_name]
            return status
        else:
            return self.statuses
