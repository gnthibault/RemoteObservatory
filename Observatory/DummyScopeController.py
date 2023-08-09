# Basic stuff
import logging
import time

# Local
from Base.Base import Base
from utils.error import ScopeControllerError


class DummyScopeController(Base):
    def __init__(self, config=None, connect_on_create=True,
                 logger=None):
        Base.__init__(self)

        self._is_initialized = False
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                controller_name="Dummy")

        self.statuses = {
            "finder_dew": False,
            "finder_dustcap_open": False,
            "flat_panel": False,
            "scope_fan": False,
            "scope_dustcap_open": False,
            "scope_dew": False,
            "corrector_dew": False,
            "camera_relay": False,
            "mount_relay": False,
        }

        # Indi stuff
        logger.debug(f"Indi Dummy ScopeController constructor")
      
        # Finished configuring
        self.logger.debug('configured successfully')

    @property
    def is_initialized(self):
        return self._is_initialized

    def initialize(self):
        self._is_initialized = True

    def power_on_all_equipments(self):
        self.logger.debug("Powering on all equipements")

    def power_off_all_equipments(self):
        self.logger.debug("Shutting down all equipements")

    def deinitialize(self):
        self.logger.debug("Deinitializing DummyScopeController")

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
        self.logger.debug("Setting port")

    def open(self):
        """ blocking call: opens both main telescope and guiding scope dustcap
        """
        self.logger.debug("Opening DummyScopeController")
        self.open_finder_dustcap()
        self.open_scope_dustcap()

    def close(self):
        """ blocking call: closes both main telescope and guiding scope dustcap
        """
        self.logger.debug("Closing DummyScopeController")
        self.close_finder_dustcap()
        self.close_scope_dustcap()

    def switch_on_camera(self):
        """ blocking call: switch on camera. We also need to load the
                           corresponding indi driver
        """
        self.logger.debug("Switching on camera")
        self.statuses["camera_relay"] = True


    def switch_off_camera(self):
        """ blocking call: switch off camera
        """
        self.logger.debug("Switching off camera")
        self.statuses["camera_relay"] = False

    def switch_on_flat_panel(self):
        """ blocking call: switch on flip flat
        """
        self.logger.debug("Switching on flip flat")
        self.statuses["flat_panel"] = True

    def switch_off_flat_panel(self):
        """ blocking call: switch off flip flat
        """
        self.logger.debug("Switching off flip flat")
        self.statuses["flat_panel"] = False

    def switch_on_scope_fan(self):
        """ blocking call: switch on fan to cool down primary mirror
        """
        self.logger.debug("Switching on fan to cool down primary mirror")
        self.statuses["scope_fan"] = True

    def switch_off_scope_fan(self):
        """ blocking call: switch off fan for primary mirror
        """
        self.logger.debug("Switching off telescope fan on primary mirror")
        self.statuses["scope_fan"] = False

    def switch_on_scope_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on secondary mirror
        """
        self.logger.debug("Switching on dew heater for secondary mirror")
        self.statuses["scope_dew"] = True

    def switch_off_scope_dew_heater(self):
        """ blocking call: switch off dew heater on secondary mirror
        """
        self.logger.debug("Switching off telescope dew heater on secondary "
                          "mirror")
        self.statuses["scope_dew"] = False

    def switch_on_corrector_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on corrector
        """
        self.logger.debug("Switching on dew heater for corrector")
        self.statuses["corrector_dew"] = True

    def switch_off_corrector_dew_heater(self):
        """ blocking call: switch off dew heater on corrector
        """
        self.logger.debug("Switching off dew heater for corrector")
        self.statuses["corrector_dew"] = False

    def switch_on_finder_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on finder lens
        """
        self.logger.debug("Switching on dew heater for finder lens")
        self.statuses["finder_dew"] = True

    def switch_off_finder_dew_heater(self):
        """ blocking call: switch off dew heater on finder lens
        """
        self.logger.debug("Switching off dew heater on finder lens ")
        self.statuses["finder_dew"] = False

    def switch_on_mount(self):
        """ blocking call: switch on main mount
        """
        self.logger.debug("Switching on main mount")
        self.statuses["mount_relay"] = True

    def switch_off_mount(self):
        """ blocking call: switch off main mount
        """
        self.logger.debug("Switching off main mount")
        self.statuses["mount_relay"] = False

    def open_scope_dustcap(self):
        """ blocking call: open up main scope dustcap
        """
        self.statuses["scope_dustcap_open"] = True
        self.logger.debug("Opening up main scope dustcap")

    def close_scope_dustcap(self):
        """ blocking call: close main scope dustcap
        """
        self.statuses["scope_dustcap_open"] = False
        self.logger.debug("close main scope dustcap")

    def open_finder_dustcap(self):
        """ blocking call: open up finder dustcap
        """
        self.statuses["finder_dustcap_open"] = True
        self.logger.debug("Opening up finder dustcap")

    def close_finder_dustcap(self):
        """ blocking call: close finder dustcap
        """
        self.statuses["finder_dustcap_open"] = False
        self.logger.debug("close finder dustcap")
   
    def status(self):
        return self.statuses
