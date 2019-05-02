# Basic stuff
import logging

# Local
from Base.Base import Base
from helper.IndiDevice import IndiDevice
from utils.error import ScopeControllerError

class IndiScopeController(IndiDevice, Base):
    def __init__(self, indi_client, config=None, connectOneCreate=True):
        Base.__init__(self)

        self._is_initialized = False

        if config is None:
            config = dict(
                board_name = "scope_controller",
            )

        self.config = config
        self.board = config['board_name']

        # Indi stuff
        logger.debug('Indi ScopeController, controller board name is: {}'
                     ''.format(self.board))
      
        # device related intialization
        IndiDevice.__init__(self, deviceName=self.board,
                            indiClient=indi_client)
        if connect_on_create:
            self.connect()
            self._is_initialized = True

        # Finished configuring
        self.logger.debug('configured successfully')

    @property
    def is_initialized(self):
        return self._is_initialized

    def initialize(self):
        self.connect()
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


    def open(self):
        """ blocking call: opens both main telescope and guiding scope dustcap
        """
        self.logger.debug("Opening IndiScopeController")
        self.setSwitch('SCOPE_SERVO_DUSTCAP_SWITCH', ['ON'])
        self.setSwitch("FINDER_SERVO_DUSTCAP_SWITCH", ['ON'])

    def close(self):
        """ blocking call: closes both main telescope and guiding scope dustcap
        """
        self.logger.debug("Closing ArduiScopeController")
        self.setSwitch('SCOPE_SERVO_DUSTCAP_SWITCH',['OFF'])
        self.setSwitch("FINDER_SERVO_DUSTCAP_SWITCH",['OFF'])

    def switch_on_camera(self):
        """ blocking call: switch on camera
        """
        self.logger.debug("Switching on camera")
        self.setSwitch("CAMERA_RELAY",['ON'])

    def switch_off_camera(self):
        """ blocking call: switch off camera
        """
        self.logger.debug("Switching off camera")
        self.setSwitch("CAMERA_RELAY",['OFF'])

    def switch_on_flat_panel(self):
        """ blocking call: switch on flip flat
        """
        self.logger.debug("Switching on flip flat")
        self.setSwitch("FLAT_PANEL_RELAY",['ON'])

    def switch_off_flat_panel(self):
        """ blocking call: switch off flip flat
        """
        self.logger.debug("Switching off flip flat")
        self.setSwitch("FLAT_PANEL_RELAY",['OFF'])

    def switch_on_scope_fan(self):
        """ blocking call: switch on fan to cool down primary mirror
        """
        self.logger.debug("Switching on fan to cool down primary mirror")
        self.setSwitch("PRIMARY_FAN_RELAY", ['ON'])

    def switch_off_scope_fan(self):
        """ blocking call: switch off fan for primary mirror
        """
        self.logger.debug("Switching off telescope fan on primary mirror")
        self.setSwitch("PRIMARY_FAN_RELAY", ['OFF'])

    def switch_on_scope_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on secondary mirror
        """
        self.logger.debug("Switching on dew heater for secondary mirror")
        self.setSwitch("SCOPE_DEW_HEAT_RELAY", ['ON'])

    def switch_off_scope_dew_heater(self):
        """ blocking call: switch off dew heater on secondary mirror
        """
        self.logger.debug("Switching off telescope dew heater on secondary "
                          "mirror")
        self.setSwitch("SCOPE_DEW_HEAT_RELAY", ['OFF'])

    def switch_on_corrector_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on corrector
        """
        self.logger.debug("Switching on dew heater for corrector")
        self.setSwitch("CORRECTOR_DEW_HEAT_RELAY", ['ON'])

    def switch_off_corrector_dew_heater(self):
        """ blocking call: switch off dew heater on corrector
        """
        self.logger.debug("Switching off dew heater for corrector")
        self.setSwitch("CORRECTOR_DEW_HEAT_RELAY", ['OFF'])

    def switch_on_finder_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on finder lens
        """
        self.logger.debug("Switching on dew heater for finder lens")
        self.setSwitch("FINDER_DEW_HEAT_RELAY", ['ON'])

    def switch_off_finder_dew_heater(self):
        """ blocking call: switch off dew heater on finder lens
        """
        self.logger.debug("Switching off dew heater on finder lens ")
        self.setSwitch("FINDER_DEW_HEAT_RELAY", ['OFF'])

    def receive_status(self):
        try:
            return {} #TODO TN URGENT
        except Exception as e:
            msg=("Cannot receive status from arduino board "
                 "{}".format(self.board))
            self.logger.error(msg)
            raise ScopeControllerError(msg)

    def status(self):
        if self.is_initialized:
            return self.receive_status()
        else:
            return {}
