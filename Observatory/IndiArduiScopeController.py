# Basic stuff
import logging
import requests
import time

# Local
from Base.Base import Base
from helper.IndiDevice import IndiDevice
from utils.error import ScopeControllerError


class IndiScopeController(IndiDevice, Base):
    def __init__(self, config=None, connect_on_create=True):
        Base.__init__(self)

        self._is_initialized = False

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
        logging.debug(f"Indi ScopeController, controller board port is: "
                     f"{self.port}")
      
        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config["controller_name"],
                            indi_driver_name=config.get('indi_driver_name', None),
                            indi_client_config=config["indi_client"])
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
