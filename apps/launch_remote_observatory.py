# Generic import
import logging
import logging.config
import multiprocessing
import os
import queue
import sys
import time
import warnings

# Astropy
from astropy import units as u

# Local
from Base.Base import Base
from Manager.Manager import Manager
from StateMachine.StateMachine import StateMachine
from utils import get_free_space
#from Service.PanMessaging import PanMessaging
from Service.PanMessagingZMQ import PanMessagingZMQ
#from Service.PanMessagingMQTT import PanMessagingMQTT

class RemoteObservatoryFSM(StateMachine, Base):

    """The main class representing the Remote Observatory Control Software

    Interaction with the observatory is done through instances of this class.
    An instance consists primarily of a 'Manager' object, which contains the
    mount, cameras, scheduler, etc.
    See `Manager.Manager`. The manager should create all attached hardware
    but leave the initialization up to this FSM class (this FSM class will call
    the manager `initialize` method).

    The instance itself is designed to be run as a state machine via
    the `run` method.

    Args:
        manager(Manager): An instance of a `Manager.Manager`
            class. FSM will call the `initialize` method of the manager.
        state_machine_file(str): Filename of the state machine to use, defaults
            is 'simple_state_table'.
        messaging(bool): If messaging should be included, defaults to False.
        simulator(list): A list of the different modules that can run in
            simulator mode. Possible  modules include: all, mount, camera,
            weather, night. Defaults to an empty list.

    Attributes:
        name (str): Name of the observatory
        manager (`Manager.Manager`): The Manager object

    """

    def __init__(
            self,
            manager,
            state_machine_file='conf_files/simple_state_table.yaml',
            messaging=True,
            **kwargs):

        assert isinstance(manager, Manager)

        # Explicitly call the base classes in the order we want
        Base.__init__(self, **kwargs)

        # local init
        self.name = 'Remote Observatory'
        self.logger.info('Initializing Remote Observatory - {}'.format(
                         self.name))
        self._has_messaging = None
        self.has_messaging = messaging

        # default loop delay. safety delay take precedence for safety sleep
        self._sleep_delay = kwargs.get('sleep_delay', 2.5)  
        # Safety check delay
        self._safe_delay = kwargs.get('safe_delay', 60 * 1)
        self._is_safe = False

        StateMachine.__init__(self, state_machine_file, **kwargs)

        # Add manager object, which does the bulk of the work
        self.manager = manager

        self._connected = True
        self._initialized = False
        self._interrupted = False
        self.force_reschedule = False

        self._retry_attempts = kwargs.get('retry_attempts', 3)
        self._obs_run_retries = self._retry_attempts

        self.status()

    @property
    def is_initialized(self):
        """ Indicates if remote observatory has been initalized or not """
        return self._initialized

    @property
    def interrupted(self):
        """If remote observatory has been interrupted

        Returns:
            bool: If an interrupt signal has been received
        """
        return self._interrupted

    @property
    def connected(self):
        """ Indicates if remote observatory is connected """
        return self._connected

    @property
    def has_messaging(self):
        return self._has_messaging

    @has_messaging.setter
    def has_messaging(self, value):
        self._has_messaging = value
        if self._has_messaging:
            self._setup_messaging()

    @property
    def should_retry(self):
        return self._obs_run_retries >= 0


###############################################################################
# Methods
###############################################################################

    def initialize(self):
        """Initialize POCS.

        Calls the Manager `initialize` method.

        Returns:
            bool: True if all initialization succeeded, False otherwise.
        """

        if not self._initialized:
            try:
                self.logger.debug("Initializing manager")
                self.manager.initialize()
            except Exception as e:
                self.logger.info(f"Oh wait. There was a problem initializing: {e}")
                self.logger.info(f"Since we didn not initialize, I am going to exit.")
                self.power_down()
            else:
                self._initialized = True
        self.status()
        return self._initialized

    def status(self):
        status = dict()

        try:
            status['state'] = self.state
            status['system'] = {
                'free_space': get_free_space().value,
            }
            status['observatory'] = self.manager.status()
        except Exception as e:  # pragma: no cover
            self.logger.warning("Can't get status: {}".format(e))
        else:
            self.send_message(status, channel='STATUS')

        return status

    def say(self, msg):
        """ Remote observatory Units like to talk!
        Send a message. Message sent out through mqtt has unit name as channel.
        Args:
            msg(str): Message to be sent
        """
        if not self.has_messaging:
            self.logger.info(f"Unit says: {msg}")
        else:
            self.send_message(f"{msg}", channel='chat')

    def send_message(self, msg, channel='chat'):
        """ Send a message

        This will use the `self._msg_publisher` to send a message

        Note:
            The `channel` and `msg` params are switched for convenience

        Arguments:
            msg {str} -- Message to be sent

        Keyword Arguments:
            channel {str} -- Channel to send message on (default: {'POCS'})
        """
        if self.has_messaging:
            self._msg_publisher.send_message(channel, msg)
        else:
            self.logger.info(f"MESSAGE {channel}: {msg}")


    def check_messages(self):
        """ Check messages for the system

        If `self.has_messaging` is True then there is a separate process
        running responsible for checking incoming zeromq messages. That process
        will fill various `queue.Queue`s with messages depending on their type.
        This method is a thin-wrapper around private methods that are
        responsible for message dispatching based on which queue received a
        message.
        """
        if self.has_messaging:
            self._check_messages('command', self._cmd_queue)
            self._check_messages('schedule', self._sched_queue)

    def power_down(self):
        """Actions to be performed upon shutdown

        Note:
            This method is automatically called from the interrupt handler.
            The definition should include what you want to happen upon shutdown
            but you don't need to worry about calling it manually.
        """
        if self.connected:
            self.logger.info('Shutting down {}, please be patient and allow '
                             'for exit.', self.name)

            if not self.manager.close_dome():
                self.logger.critical('Unable to close dome!')

            # Park if needed
            if self.state not in ['parking', 'parked', 'sleeping',
                                  'housekeeping']:
                # TODO(jamessynge): Figure out how to handle the situation
                # where we have both mount and dome, but this code is only
                # checking for a mount.
                if self.manager.mount.is_connected:
                    if not self.manager.mount.is_parked:
                        self.logger.info("Parking mount")
                        self.park() #FSM trigger

            if self.state == 'parking':
                if self.manager.mount.is_connected:
                    if self.manager.mount.is_parked:
                        self.logger.info('Mount is parked, setting Parked '
                                         'state')
                        self.set_park() #FSM trigger

            if not self.manager.mount.is_parked:
                self.logger.info('Mount not parked, parking')
                self.manager.mount.park()

            # Manager shut down
            self.manager.power_down()

            # Shut down messaging
            self.logger.debug('Shutting down messaging system')
            self._msg_client.close_connection()
            #for name, proc in self._processes.items():
            #    if proc.is_alive():
            #        self.logger.debug('Terminating {} - PID {}'.format(
            #            name, proc.pid))
            #        proc.terminate()

            self._keep_running = False
            self._do_states = False
            self._connected = False
            self.logger.info("Power down complete")

    def reset_observing_run(self):
        """Reset an observing run loop. """
        self.logger.debug("Resetting observing run attempts")
        self._obs_run_retries = self._retry_attempts

###############################################################################
# Safety Methods
###############################################################################

    def is_safe(self, no_warning=False):
        """Checks the safety flag of the system to determine if safe.

        This will check the weather station as well as various other environmental
        aspects of the system in order to determine if conditions are safe for
        operation.

        Note:
            This condition is called by the state machine during each transition

        Args:
            no_warning (bool, optional): If a warning message should show in logs,
                defaults to False.

        Returns:
            bool: Latest safety flag

        """
        if not self.connected:
            return False

        is_safe_values = dict()

        # Check if night time: synchronous
        is_safe_values['is_dark'] = self.is_dark()

        # Check weather: not really synchronous, checks db
        is_safe_values['good_weather'] = self.is_weather_safe()

        # Check if computer has free disk space
        is_safe_values['free_space'] = self.has_free_space()

        safe = all(is_safe_values.values())

        if not safe:
            if no_warning is False:
                self.logger.warning(f"Unsafe conditions: {is_safe_values}")

            if self.state not in ['sleeping', 'parked', 'parking',
                                  'housekeeping', 'ready']:
                #self.logger.warning('Safety failed so sending to park')
                #self.park() #FSM trigger
                # TODO TN urgent: corriger
                pass

        #return safe
        # TODO TN urgent: corriger
        return True

    def is_dark(self):
        """Is it dark

        Checks whether it is dark at the location provided. This checks for the
        config entry `location.horizon` or 18 degrees (astronomical twilight).

        Returns:
            bool: Is night at location

        """
        # See if dark
        is_dark = self.manager.is_dark

        self.logger.debug("Dark Check: {}".format(is_dark))
        return is_dark

    def is_weather_safe(self, stale=180):
        """Determines whether current weather conditions are safe or not

        Args:
            stale (int, optional): Number of seconds before record is stale,
            defaults to 180

        Returns:
            bool: Conditions are safe (True) or unsafe (False)

        """

        # Always assume False
        self.logger.debug("Checking weather safety")
        is_safe = False
        record = {'safe': False}

        try:
            record = self.db.get_current('weather')
            is_safe = record['data'].get('safe', False)
            timestamp = record['date']
            age = (self.manager.serv_time.get_utc() -
                   timestamp).total_seconds()
            self.logger.debug(f"Weather Safety: {is_safe} [{age:.0f} sec old "
                              f"- {timestamp}]")
        except (TypeError, KeyError) as e:
            self.logger.warning("No record found in DB: {}", e)
        except BaseException as e:
            self.logger.error("Error checking weather: {}", e)
        else:
            if age > stale:
                self.logger.warning("Weather record looks stale, marking unsafe.")
                is_safe = False

        self._is_safe = is_safe

        return self._is_safe

    def has_free_space(self, required_space=0.25 * u.gigabyte):
        """Does hard drive have disk space (>= 0.5 GB)

        Args:
            required_space (u.gigabyte, optional): Amount of free space required
            for operation

        Returns:
            bool: True if enough space
        """
        free_space = get_free_space()
        return free_space.value >= required_space.to(u.gigabyte).value


################################################################################
# Convenience Methods
################################################################################

    def sleep(self, delay=2.5, with_status=True):
        """ Send system to sleep

        Loops for `delay` number of seconds. If `delay` is more than 10.0 seconds,
        `check_messages` will be called every 10.0 seconds in order to allow for
        interrupt.

        Keyword Arguments:
            delay {float} -- Number of seconds to sleep (default: 2.5)
            with_status {bool} -- Show system status while sleeping
                (default: {True if delay > 2.0})
        """
        if delay is None:
            delay = self._sleep_delay

        if with_status and delay > 2.0:
            self.status()

        # If delay is greater than 10 seconds check for messages during wait
        if delay >= 10.0:
            while delay >= 10.0:
                self.check_messages()
                # If we shutdown leave loop
                if self.connected is False:
                    return

                time.sleep(10.0)
                delay -= 10.0

        if delay > 0.0:
            time.sleep(delay)

    def wait_until_safe(self):
        """ Waits until weather is safe.

        This will wait until a True value is returned from the safety check,
        blocking until then.
        """
        while not self.is_safe(no_warning=True):
            self.sleep(delay=self._safe_delay)


###############################################################################
# Class Methods
###############################################################################

    @classmethod
    def check_environment(cls):
        """ Checks to see if environment is set up correctly
        """
        if sys.version_info[:2] < (3, 0):  # pragma: no cover
            warnings.warn("Remote Observatory requires Python 3.x to run")

        #if not os.path.exists("{}/logs".format(mydir)):
        #    print("Creating log dir at {}/logs".format(mydir))
        #    os.makedirs("{}/logs".format(mydir))

###############################################################################
# Private Methods
###############################################################################

    def _check_messages(self, queue_type, q):
        cmd_dispatch = {
            'command': {
                'park': self._interrupt_and_park,
                'shutdown': self._interrupt_and_shutdown,
            },
            'schedule': {}
        }

        while True:
            try:
                msg_obj = q.get_nowait()
                call_method = msg_obj.get('message', '')
                # Lookup and call the method
                self.logger.info(f"Message received: {queue_type} "
                                 f"{call_method}")
                cmd_dispatch[queue_type][call_method]()
            except queue.Empty:
                break
            except KeyError:
                pass
            except Exception as e:
                self.logger.warning(f"Problem calling method from messaging: "
                                    f"{e}")
            else:
                break

    def _interrupt_and_park(self):
        self.logger.info('Park interrupt received')
        self._interrupted = True
        self.park() #FSM trigger

    def _interrupt_and_shutdown(self):
        self.logger.warning('Shutdown command received')
        self._interrupted = True
        self.power_down()

    # def _setup_messaging(self):
    #     #mqtt_host = self.config['messaging']['mqtt_host']
    #     #mqtt_port = self.config['messaging']['mqtt_port']
    #     #self._msg_client = PanMessaging(mqtt_host, mqtt_port, connect=True)
    # 
    #     self._cmd_queue = multiprocessing.Queue()
    #     self._sched_queue = multiprocessing.Queue()
    #     self._msg_client = PanMessaging(**self.config['messaging'])
    # 
    #     def new_cmd_callback(msg_type, msg_obj):
    #         self._sched_queue.put(msg_obj)
    #     def new_sched_callback(msg_type, msg_obj):
    #         self._cmd_queue.put(msg_obj)
    # 
    #     self._msg_client.register_callback(callback=new_cmd_callback, cmd_type="POCS-CMD/#")
    #     self._msg_client.register_callback(callback=new_sched_callback, cmd_type="POCS-SCHED/#")
    
    def _setup_messaging(self):
        cmd_port = self.config['messaging']['cmd_port']
        msg_port = self.config['messaging']['msg_port']

        def create_forwarder(port):
            try:
                PanMessagingZMQ.create_forwarder(port, port + 1)
            except Exception:
                pass

        cmd_forwarder_process = multiprocessing.Process(
            target=create_forwarder, args=(
                cmd_port,), name='CmdForwarder')
        cmd_forwarder_process.start()

        msg_forwarder_process = multiprocessing.Process(
            target=create_forwarder, args=(
                msg_port,), name='MsgForwarder')
        msg_forwarder_process.start()

        self._do_cmd_check = True
        self._cmd_queue = multiprocessing.Queue()
        self._sched_queue = multiprocessing.Queue()

        self._msg_publisher = PanMessagingZMQ.create_publisher(msg_port)

        def check_message_loop(cmd_queue):
            cmd_subscriber = PanMessagingZMQ.create_subscriber(cmd_port + 1)

            poller = zmq.Poller()
            poller.register(cmd_subscriber.socket, zmq.POLLIN)

            try:
                while self._do_cmd_check:
                    # Poll for messages
                    sockets = dict(poller.poll(500))  # 500 ms timeout

                    if cmd_subscriber.socket in sockets and \
                            sockets[cmd_subscriber.socket] == zmq.POLLIN:

                        msg_type, msg_obj = cmd_subscriber.receive_message(
                            flags=zmq.NOBLOCK)

                        # Put the message in a queue to be processed
                        if msg_type == 'POCS-CMD':
                            cmd_queue.put(msg_obj)

                    time.sleep(1)
            except KeyboardInterrupt:
                pass

        self.logger.debug('Starting command message loop')
        check_messages_process = multiprocessing.Process(
            target=check_message_loop, args=(self._cmd_queue,))
        check_messages_process.name = 'MessageCheckLoop'
        check_messages_process.start()
        self.logger.debug('Command message subscriber set up on port {}'.format(
                          cmd_port))

        self._processes = {
            'check_messages': check_messages_process,
            'cmd_forwarder': cmd_forwarder_process,
            'msg_forwarder': msg_forwarder_process,
        }

if __name__ == '__main__':
    # load the logging configuration
    logging.config.fileConfig('logging.ini')
    m = Manager()
    r = RemoteObservatoryFSM(manager=m)
    r.initialize()
    r.run()
