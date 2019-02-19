# Basic stuff
import logging

# Local
from Base.Base import Base
from utils.messaging import PanMessaging

class ArduiScopeController(Base):
    def __init__(self, config=None):
        Base.__init__(self)

        if config is None:
            config = dict(
                board = "scope_controller",
                port = "/dev/ttyACM0",
                cmd_port = 6501,
                msg_port = 6510,
                pin_scope_dustcap = 10,
                pin_finder_dustcap = 11,
                pin_flat_panel=13,
                pin_fan_primary=14,
            )

        self.config = config
        self.board = config['board']
        self.latest_status = dict(default_status="! inactive")

        # for communication
        self._cmd_channel = "{}:commands".format(self.board)
        self._sub = None
        self._pub = None 

    def initialize(self):
        self.latest_status = dict(default_status="! active")
        self.logger.debug("Initializing ArduiScopeController with ports: "
                          "subscribe({}), publish({})".format(
                              self.config['msg_port'],
                              self.config['cmd_port']))
        self._sub = PanMessaging.create_subscriber(port=self.config['msg_port'],
                                                   channel=self.board)
        self._pub = PanMessaging.create_publisher(self.config['cmd_port'],
                                                  bind=True)

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
        self._pub.send_message(self._cmd_channel, msg)

    def send_order(self, pin, value):
        msg = dict()
        msg['command'] = 'write_line'
        msg['line'] = '{} {}'.format(pin, value)
        self._pub.send_message(self._cmd_channel, msg)

    def send_blocking_order(self, pin, value):
        self.send_order(pin, value)
        self.wait_feedback(pin, value)

    def wait_feedback(self, pin, value):
        is_confirmed = False

        while not is_confirned:
            mtype, mmsg = self._sub.receive_message(blocking=True)
            for entry in mmsg:
                try:
                    cpin, cval = [entry[x] for x in ['pin_number', 'pin_value']]
                except KeyError as ke:
                    pass
            is_confirmed = True if (cpin==pin) and (cval==value) else False
        

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
            timeout_obj = serialutil.Timeout(1.0)
            while not timeout_obj.expired():
                msg_type, msg_obj = self._sub.receive_message(blocking=False)
        except Exception as e:
            self.logger.warning("Cannot receive status from arduino board "
                                "{}".format(self.board))
            return self.latest_status

    def status(self):
        return self.receive_status
