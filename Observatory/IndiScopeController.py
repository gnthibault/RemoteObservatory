# Basic stuff
import logging

# Local
from Base.Base import Base
from helper.IndiDevice import IndiDevice
from utils.error import ScopeControllerError

class IndiScopeController(IndiDevice, Base):
    def __init__(self, indi_client, config=None, connect_on_create=True,
                 logger=None):
        Base.__init__(self)

        self._is_initialized = False
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                board_name = "Arduino",
                port = "/dev/ttyACM0"
            )

        self.board = config['board_name']
        self.port = config['port']

        # Indi stuff
        logger.debug('Indi ScopeController, controller board name is: {}'
                     ''.format(self.board))
      
        # device related intialization
        IndiDevice.__init__(self, logger=logger, device_name=self.board,
                            indi_client=indi_client)
        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('configured successfully')

    @property
    def is_initialized(self):
        return self._is_initialized

    def initialize(self):
        self.connect()
        self.setText("DEVICE_PORT",{"PORT":self.port})
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
        self.set_switch('SCOPE_SERVO_DUSTCAP_SWITCH',
            onSwitches=['SERVO_SWITCH'])
        self.set_switch("FINDER_SERVO_DUSTCAP_SWITCH",
            onSwitches=['SERVO_SWITCH'])

    def close(self):
        """ blocking call: closes both main telescope and guiding scope dustcap
        """
        self.logger.debug("Closing ArduiScopeController")
        self.set_switch('SCOPE_SERVO_DUSTCAP_SWITCH',
            offSwitches=['SERVO_SWITCH'])
        self.set_switch("FINDER_SERVO_DUSTCAP_SWITCH",
            offSwitches=['SERVO_SWITCH'])

    def switch_on_camera(self):
        """ blocking call: switch on camera
        """
        self.logger.debug("Switching on camera")
        self.set_switch("CAMERA_RELAY", onSwitches=['RELAY_CMD'])

    def switch_off_camera(self):
        """ blocking call: switch off camera
        """
        self.logger.debug("Switching off camera")
        self.set_switch("CAMERA_RELAY", offSwitches=['RELAY_CMD'])

    def switch_on_flat_panel(self):
        """ blocking call: switch on flip flat
        """
        self.logger.debug("Switching on flip flat")
        self.set_switch("FLAT_PANEL_RELAY", onSwitches=['RELAY_CMD'])

    def switch_off_flat_panel(self):
        """ blocking call: switch off flip flat
        """
        self.logger.debug("Switching off flip flat")
        self.set_switch("FLAT_PANEL_RELAY", offSwitches=['RELAY_CMD'])

    def switch_on_scope_fan(self):
        """ blocking call: switch on fan to cool down primary mirror
        """
        self.logger.debug("Switching on fan to cool down primary mirror")
        self.set_switch("PRIMARY_FAN_RELAY", onSwitches=['RELAY_CMD'])

    def switch_off_scope_fan(self):
        """ blocking call: switch off fan for primary mirror
        """
        self.logger.debug("Switching off telescope fan on primary mirror")
        self.set_switch("PRIMARY_FAN_RELAY", offSwitches=['RELAY_CMD'])

    def switch_on_scope_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on secondary mirror
        """
        self.logger.debug("Switching on dew heater for secondary mirror")
        self.set_switch("SCOPE_DEW_HEAT_RELAY", onSwitches=['RELAY_CMD'])

    def switch_off_scope_dew_heater(self):
        """ blocking call: switch off dew heater on secondary mirror
        """
        self.logger.debug("Switching off telescope dew heater on secondary "
                          "mirror")
        self.set_switch("SCOPE_DEW_HEAT_RELAY", offSwitches=['RELAY_CMD'])

    def switch_on_corrector_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on corrector
        """
        self.logger.debug("Switching on dew heater for corrector")
        self.set_switch("CORRECTOR_DEW_HEAT_RELAY", onSwitches=['RELAY_CMD'])

    def switch_off_corrector_dew_heater(self):
        """ blocking call: switch off dew heater on corrector
        """
        self.logger.debug("Switching off dew heater for corrector")
        self.set_switch("CORRECTOR_DEW_HEAT_RELAY", offSwitches=['RELAY_CMD'])

    def switch_on_finder_dew_heater(self):
        """ blocking call: switch on dew heater to avoid dew on finder lens
        """
        self.logger.debug("Switching on dew heater for finder lens")
        self.set_switch("FINDER_DEW_HEAT_RELAY", onSwitches=['RELAY_CMD'])

    def switch_off_finder_dew_heater(self):
        """ blocking call: switch off dew heater on finder lens
        """
        self.logger.debug("Switching off dew heater on finder lens ")
        self.set_switch("FINDER_DEW_HEAT_RELAY", offSwitches=['RELAY_CMD'])

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
