# Basic stuff
import logging
import requests
import time

# Local
from Base.Base import Base
from helper.IndiDevice import IndiDevice
from utils.error import ScopeControllerError


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
                 connect_on_create=True,
                 logger=None):

        self._is_initialized = False
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                device_name="Pegasus UPB",
                device_port="/dev/serial/by-id/usb-Pegasus_Astro_UPBv2_revD_UPB25S4VWV-if00-port0",
                connection_type="CONNECTION_SERIAL",
                baud_rate=9600,
                polling_ms=1000,
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
                    USB_LABEL_4="PRIMARY_FOCUSER_CONTROL_BOX",
                    USB_LABEL_5="WIFI_ROUTER",
                    USB_LABEL_6="SPECTRO_CONTROL_BOX"),
                always_on_usb_identifiers=dict(
                    PRIMARY_CAMERA=False,
                    ARDUINO_CONTROL_BOX=False,
                    GUIDE_CAMERA=False,
                    PRIMARY_FOCUSER_CONTROL_BOX=False,
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

        # Communication config
        self.device_port = config["device_port"]
        self.connection_type = config["connection_type"]
        self.baud_rate = str(config["baud_rate"])
        self.polling_ms = float(config["polling_ms"])

        # labels
        self.power_labels = config["power_labels"]
        self.always_on_power_identifiers = config["always_on_power_identifiers"]
        self.usb_labels = config["usb_labels"]
        self.always_on_usb_identifiers = config["always_on_usb_identifiers"]
        self.dew_labels = config["dew_labels"]

        # dew parameters
        self.auto_dew_identifiers = config["auto_dew_identifiers"]
        self.auto_dew_aggressivity = str(config["auto_dew_aggressivity"])

        # Indi stuff
        logger.debug(f"UPBV2, controller board port is on port: {self.device_port}")

        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config["device_name"],
                            indi_client_config=config["indi_client"])

        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('configured successfully')

    def initialize(self):
        """
        Connection is made in two phases:
          * connect client to server so that we can setup options, like port
          * connect server to actual physical device
        :return:
        """
        self.connect(connect_device=False)
        self.set_device_communication_options()
        self.connect_device()
        self.set_all_labels()
        self.initialize_all_power_on_boot()
        self.initialize_all_power()
        self.initialize_all_dew()
        self.initialize_all_usb()
        self.initialize_usb_hub()
        self.set_auto_dew_aggressivity()

        self._is_initialized = True

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

    def initialize_usb_hub(self):
        logging.warning("initialize_usb_hub doesn't seems to be currently supported by indi driver")
        #self.set_switch("USB_HUB_CONTROL", on_switches=["INDI_ENABLED"])

    def setup_telescope_power_on(self):
        # Power
        on_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if self.power_labels[f"POWER_LABEL_{i}"] == 'TELESCOPE_LEVEL_POWER']
        self.set_switch("POWER_CONTROL", on_switches=on_switches)

        # USB
        on_switches = [f"PORT_{i}" for i in range(1, 7) if self.usb_labels[f"USB_LABEL_{i}"]=="ARDUINO_CONTROL_BOX"]
        self.set_switch("USB_PORT_CONTROL", on_switches=on_switches)

    def setup_mount_power_on(self):
        # Power
        on_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if self.power_labels[f"POWER_LABEL_{i}"] == 'MOUNT_POWER']
        self.set_switch("POWER_CONTROL", on_switches=on_switches)

    def setup_instruments_power_on(self):
        # Power
        on_switches = [f"POWER_CONTROL_{i}" for i in range(1, 5) if self.power_labels[f"POWER_LABEL_{i}"] == 'FOCUSER_LEVEL_POWER']
        self.set_switch("POWER_CONTROL", on_switches=on_switches)

        # USB
        on_switches = [f"PORT_{i}" for i in range(1, 7) if self.usb_labels[f"USB_LABEL_{i}"] in
                       ["PRIMARY_CAMERA", "GUIDE_CAMERA", "PRIMARY_FOCUSER_CONTROL_BOX", "SPECTRO_CONTROL_BOX"]]
        self.set_switch("USB_PORT_CONTROL", on_switches=on_switches)

        # Dew
        self.set_auto_dew_eligibility()

    def initialize_all_dew(self):
        # Set power to 0
        self.set_number("DEW_PWM", {'DEW_A': 0.0, 'DEW_B': 0.0, 'DEW_C': 0.0})

        # Set eligibility to None for all by default
        off_switches = [f"DEW_{l}" for i, l in enumerate("ABC")]
        self.set_switch("AUTO_DEW", off_switches=off_switches)

    def set_auto_dew_eligibility(self):
        """
        Set auto dew eligibility
        :return:
        """
        on_switches = [f"DEW_{l}" for i,l in enumerate("ABC") if self.auto_dew_identifiers[self.dew_labels[f"DEW_LABEL_{i+1}"]]]
        self.set_switch("AUTO_DEW", on_switches=on_switches)

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
                 connect_on_create=True,
                 logger=None):

        self._is_initialized = False
        logger = logger or logging.getLogger(__name__)

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

        # Indi stuff
        logger.debug(f"Arduino, controller board port is on port: {self.device_port}")

        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config["device_name"],
                            indi_client_config=config["indi_client"])

        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('configured successfully')

    def initialize(self):
        """
        Connection is made in two phases:
          * connect client to server so that we can setup options, like port
          * connect server to actual physical device
        :return:
        """
        self.connect(connect_device=False)
        self.set_device_communication_options()
        self.connect_device()
        self.initialize_servo()
        self._is_initialized = True

    def set_device_communication_options(self):
        self.set_text("DEVICE_PORT", {"PORT": self.device_port})
        self.set_switch("CONNECTION_MODE", on_switches=[self.connection_type])
        self.set_switch("DEVICE_BAUD_RATE", on_switches=[self.baud_rate])
        self.set_polling_ms(polling_ms=self.polling_ms)

    def set_polling_ms(self, polling_ms=None):
        if polling_ms is not None:
            self.polling_ms = polling_ms
        self.set_number("POLLING_PERIOD", {'PERIOD_MS': self.polling_ms})

    def initialize_servo(self, auto_dew_aggressivity=None):
        print("Not much for now")


class AggregatedCustomScopeController(IndiDevice, Base):
    """
    This is more or less a custom class for a custom setup, where config for ports
    is the following:
    /dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0 -> Custom arduino nano with firmata (ttyUSB0 at the time of the test)
    /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AD0JE0ID-if00-port0 ->  Shelyak arduino SPOX (ttyUSB1 at the time of the test)
    /dev/serial/by-id/usb-Pegasus_Astro_UPBv2_revD_UPB25S4VWV-if00-port0 -> PEGASUS (ttyUSB2 at the time of the test)
    """
    def __init__(self, config=None, connect_on_create=True,
                 logger=None):
        Base.__init__(self)

        self._is_initialized = False
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                port="/dev/ttyUSB0",
                controller_name="Arduino",
                indi_driver_connect_delay_s = 5,
                indi_camera_driver_name="Canon DSLR",
                indi_mount_driver_name="Losmandy Gemini",
                indi_webserver_host="192.168.0.33",
                indi_webserver_port="8624",
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"
                ))

        self.port = config["port"]
        self._indi_camera_driver_name = config["indi_camera_driver_name"]
        self._indi_driver_connect_delay_s = \
            config["indi_driver_connect_delay_s"]
        self._indi_mount_driver_name = config["indi_mount_driver_name"]
        self._indi_webserver_host = config["indi_webserver_host"]
        self._indi_webserver_port = config["indi_webserver_port"]
        # Indi stuff
        logger.debug(f"Indi ScopeController, controller board port is: "
                     f"{self.port}")
      
        # device related intialization
        #IndiDevice.__init__(self, ,
        #                    device_name=config["controller_name"],
        #                    indi_client_config=config["indi_client"])
        if connect_on_create:
            self.initialize()

        # pin on arduino need to be configured either as input or ouput
        # it means that we need to keep track of pin status internally
        self.statuses = {
            "flat_panel": False,
            "scope_fan": False,
            "scope_dew": False,
            "corrector_dew": False,
            "finder_dew": False,
            "camera_relay": False,
            "mount_relay": False,
        }

        # Finished configuring
        self.logger.debug('configured successfully')

    @property
    def is_initialized(self):
        return self._is_initialized

    def initialize(self):
        self.connect()
        self.set_port()
        self._is_initialized = True

    def deinitialize(self):
        self.logger.debug("Deinitializing IndiScopeController")

        # First close dustcap
        self.close()

        # Then switch off all electronic devices
        self.switch_off_flat_panel()
        self.switch_off_scope_fan()
        self.switch_off_scope_dew_heater()
        self.switch_off_corrector_dew_heater()
        self.switch_off_finder_dew_heater()
        self.switch_off_camera()
        self.switch_off_mount()
        self.close()

    def set_port(self):
        self.set_text("DEVICE_PORT", {"PORT":self.port})

    def open(self):
        """ blocking call: opens both main telescope and guiding scope dustcap
        """
        self.logger.debug("Opening IndiScopeController")
        self.open_finder_dustcap()
        self.open_scope_dustcap()

    def close(self):
        """ blocking call: closes both main telescope and guiding scope dustcap
        """
        self.logger.debug("Closing IndiScopeController")
        self.close_finder_dustcap()
        self.close_scope_dustcap()

    def start_driver(self, driver_name):
        try:
            base_url = f"http://{self._indi_webserver_host}:"\
                       f"{self._indi_webserver_port}"
            req = f"{base_url}/api/drivers/start/"\
                  f"{driver_name.replace(' ', '%20')}"
            response = requests.post(req)
        except Exception as e:
            self.logger.warning(f"Cannot load indi driver : {e}")

    def stop_driver(self, driver_name):
        try:
            base_url = f"http://{self._indi_webserver_host}:"\
                       f"{self._indi_webserver_port}"
            req = f"{base_url}/api/drivers/stop/"\
                  f"{driver_name.replace(' ', '%20')}"
            response = requests.post(req)
        except Exception as e:
            self.logger.warning(f"Cannot load indi driver : {e}")

    def switch_on_camera(self):
        """ blocking call: switch on camera. We also need to load the
                           corresponding indi driver
        """
        self.logger.debug("Switching on camera")
        self.set_switch("CAMERA_RELAY", on_switches=['RELAY_CMD'])
        # Now we need to wait a bit before trying to connect driver
        time.sleep(self._indi_driver_connect_delay_s)
        self.start_driver(self._indi_camera_driver_name)
        self.statuses["camera_relay"] = True


    def switch_off_camera(self):
        """ blocking call: switch off camera
        """
        self.logger.debug("Switching off camera")
        self.set_switch("CAMERA_RELAY", off_switches=['RELAY_CMD'])
        self.stop_driver(self._indi_camera_driver_name)
        self.statuses["camera_relay"] = False

    def switch_on_flat_panel(self):
        """ blocking call: switch on flip flat
        """
        self.logger.debug("Switching on flip flat")
        self.set_switch("FLAT_PANEL_RELAY", on_switches=['RELAY_CMD'])
        self.statuses["flat_panel"] = True

    def switch_off_flat_panel(self):
        """ blocking call: switch off flip flat
        """
        self.logger.debug("Switching off flip flat")
        self.set_switch("FLAT_PANEL_RELAY", off_switches=['RELAY_CMD'])
        self.statuses["flat_panel"] = False

    def switch_on_scope_fan(self):
        """ blocking call: switch on fan to cool down primary mirror
        """
        self.logger.debug("Switching on fan to cool down primary mirror")
        self.set_switch("PRIMARY_FAN_RELAY", on_switches=['RELAY_CMD'])
        self.statuses["scope_fan"] = True

    def switch_off_scope_fan(self):
        """ blocking call: switch off fan for primary mirror
        """
        self.logger.debug("Switching off telescope fan on primary mirror")
        self.set_switch("PRIMARY_FAN_RELAY", off_switches=['RELAY_CMD'])
        self.statuses["scope_fan"] = False

    def switch_on_scope_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on secondary mirror
        """
        self.logger.debug("Switching on dew heater for secondary mirror")
        self.set_switch("SCOPE_DEW_HEAT_RELAY", on_switches=['RELAY_CMD'])
        self.statuses["scope_dew"] = True

    def switch_off_scope_dew_heater(self):
        """ blocking call: switch off dew heater on secondary mirror
        """
        self.logger.debug("Switching off telescope dew heater on secondary "
                          "mirror")
        self.set_switch("SCOPE_DEW_HEAT_RELAY", off_switches=['RELAY_CMD'])
        self.statuses["scope_dew"] = False

    def switch_on_corrector_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on corrector
        """
        self.logger.debug("Switching on dew heater for corrector")
        self.set_switch("CORRECTOR_DEW_HEAT_RELAY", on_switches=['RELAY_CMD'])
        self.statuses["corrector_dew"] = True

    def switch_off_corrector_dew_heater(self):
        """ blocking call: switch off dew heater on corrector
        """
        self.logger.debug("Switching off dew heater for corrector")
        self.set_switch("CORRECTOR_DEW_HEAT_RELAY", off_switches=['RELAY_CMD'])
        self.statuses["corrector_dew"] = False

    def switch_on_finder_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on finder lens
        """
        self.logger.debug("Switching on dew heater for finder lens")
        self.set_switch("FINDER_DEW_HEAT_RELAY", on_switches=['RELAY_CMD'])
        self.statuses["finder_dew"] = True

    def switch_off_finder_dew_heater(self):
        """ blocking call: switch off dew heater on finder lens
        """
        self.logger.debug("Switching off dew heater on finder lens ")
        self.set_switch("FINDER_DEW_HEAT_RELAY", off_switches=['RELAY_CMD'])
        self.statuses["finder_dew"] = False

    def switch_on_mount(self):
        """ blocking call: switch on main mount
        """
        self.logger.debug("Switching on main mount")
        self.set_switch("MOUNT_RELAY", on_switches=['RELAY_CMD'])
        # Now we need to wait a bit before trying to connect driver
        time.sleep(self._indi_driver_connect_delay_s)
        self.start_driver(self._indi_mount_driver_name)
        self.statuses["mount_relay"] = True

    def switch_off_mount(self):
        """ blocking call: switch off main mount
        """
        self.logger.debug("Switching off main mount")
        self.set_switch("MOUNT_RELAY", off_switches=['RELAY_CMD'])
        self.stop_driver(self._indi_mount_driver_name)
        self.statuses["mount_relay"] = False

    def open_scope_dustcap(self):
        """ blocking call: open up main scope dustcap
        """
        self.logger.debug("Opening up main scope dustcap")
        self.set_switch("SCOPE_SERVO_DUSTCAP_SWITCH",
                        on_switches=['SERVO_SWITCH'])

    def close_scope_dustcap(self):
        """ blocking call: close main scope dustcap
        """
        self.logger.debug("close main scope dustcap")
        self.set_switch("SCOPE_SERVO_DUSTCAP_SWITCH",
                        off_switches=['SERVO_SWITCH'])

    def open_finder_dustcap(self):
        """ blocking call: open up finder dustcap
        """
        self.logger.debug("Opening up finder dustcap")
        self.set_switch("FINDER_SERVO_DUSTCAP_SWITCH",
                        on_switches=['SERVO_SWITCH'])

    def close_finder_dustcap(self):
        """ blocking call: close finder dustcap
        """
        self.logger.debug("close finder dustcap")
        self.set_switch("FINDER_SERVO_DUSTCAP_SWITCH",
                        off_switches=['SERVO_SWITCH'])
   
    def status(self):
        if self.is_connected:
            status = self.statuses.copy()
            status["finder_dustcap_open"] = self.get_switch(
                'FINDER_SERVO_DUSTCAP_SWITCH')['SERVO_SWITCH']
            status["scope_dustcap_open"] = self.get_switch(
                'SCOPE_SERVO_DUSTCAP_SWITCH')['SERVO_SWITCH']
            return status
        else:
            return self.statuses
