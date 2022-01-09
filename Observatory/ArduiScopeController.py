# Basic stuff
import logging
from serial import serialutil
import threading

# Local
from apps.launch_arduino_capture import main as arduinolauncher
from Base.Base import Base
from utils.error import ScopeControllerError
from utils.messaging import PanMessaging

class ArduiScopeController(Base):
    def __init__(self, config=None):
        Base.__init__(self)

        self._is_initialized = False

        if config is None:
            config = dict(
                board="scope_controller",
                port="/dev/ttyACM0",
                pin_scope_dustcap=10,
                pin_finder_dustcap=11,
                pin_flat_panel=13,
                pin_fan_primary=14,
            )

        self.config = config
        self.board = config['board']
        self.latest_status = dict(default_status="! inactive")
        self.acquisition_thread = None

        # for communication
        self._cmd_channel = "{}:commands".format(self.board)
        self.messaging = None
        
    @property
    def is_initialized(self):
        return self._is_initialized

    def initialize(self):
        self.latest_status = dict(default_status="! active")
        self.logger.debug("Initializing ArduiScopeController with ports: "
                          "subscribe({}), publish({})".format(
                              self.config['msg_port'],
                              self.config['cmd_port']))
        self.messaging = PanMessaging.create_client(**self.config["messaging"])
        # we also need to launch the arduino service !
        self.acquisition_thread = threading.Thread(
            target=arduinolauncher,
            kwargs=dict(board=self.board,
                        cmd_port=self.config['cmd_port'],
                        msg_port=self.config['msg_port']))
        self.acquisition_thread.start()
        self._is_initialized = True

    def deinitialize(self):
        self.latest_status["main_status"]="inactive"
        self.logger.debug("Deinitializing ArduiScopeController")

        # First close dustcap
        self.close()
        # Then switch off flat panel
        self.switch_off_flat_panel()

        # Now shutdown
        msg = dict()
        msg['command'] = 'shutdown'
        self.messaging.send_message(self._cmd_channel, msg)

        # acquisition thread should terminate after shutdown
        self.acquisition_thread.join()

    def send_order(self, pin, value):
        msg = dict()
        msg['command'] = 'write_line'
        msg['line'] = '{},{}'.format(pin, value)
        self.messaging.send_message(self._cmd_channel, msg)

    def send_blocking_order(self, pin, value):
        """
            We should receive all parameters as string, not integers
        """
        try:
            self.send_order(pin, value)
            assert(self.wait_feedback(pin, value))
        except Exception as e:
            msg = 'Order pin:{}, value:{} failed: {}'.format(pin, value, e)
            self.logger.error(msg)
            raise ScopeControllerError(msg)

    def wait_feedback(self, pin, value):
        is_confirmed = False
        timeout_obj = serialutil.Timeout(100)
        while not timeout_obj.expired():
            mtype, mmsg = self.messaging.receive_message(blocking=True)
            for device in mmsg['data']['devices']:
                try:
                    cpin, cval = [device[x] for x in ['pin_number', 'pin_value']]
                except KeyError as ke:
                    pass
            is_confirmed = True if (cpin==pin) and (cval==value) else False
            if is_confirmed:
                return is_confirmed
        return is_confirmed

    def open(self):
        """ blocking call: opens both main telescope and guiding scope dustcap
        """
        self.logger.debug("Opening ArduiScopeController")
        self.send_blocking_order(self.config['pin_scope_dustcap'], 1)
        self.send_blocking_order(self.config['pin_finder_dustcap'], 1)

    def close(self):
        """ blocking call: closes both main telescope and guiding scope dustcap
        """
        self.logger.debug("Closing ArduiScopeController")
        self.send_blocking_order(self.config['pin_scope_dustcap'], 0)
        self.send_blocking_order(self.config['pin_finder_dustcap'], 0)

    def switch_on_flat_panel(self):
        """ blocking call: switch on flip flat
        """
        self.logger.debug("Switching on flip flat")
        self.send_blocking_order(self.config['pin_flat_panel'], 1)

    def switch_off_flat_panel(self):
        """ blocking call: switch off flip flat
        """
        self.logger.debug("Switching off flip flat")
        self.send_blocking_order(self.config['pin_flat_panel'], 0)

    def switch_on_scope_fan(self):
        """ blocking call: switch on fan to cool down primary mirror
        """
        self.logger.debug("Switching on fan to cool down primary mirror")
        self.send_blocking_order(self.config['pin_fan_primary'], 1)

    def switch_off_scope_fan(self):
        """ blocking call: switch off fan for primary mirror
        """
        self.logger.debug("Switching off telescope fan on primary mirror")
        self.send_blocking_order(self.config['pin_fan_primary'], 0)

    def receive_status(self):
        try:
            timeout_obj = serialutil.Timeout(4.0)
            while not timeout_obj.expired():
                msg_type, msg_obj = self.messaging.receive_message(blocking=False)
                if msg_obj is not None:
                    if self.board in msg_obj:
                        self.latest_status = msg_obj
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
