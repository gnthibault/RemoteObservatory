# Basic stuff
import asyncio
import concurrent
import logging
import threading
#from transitions.extensions import LockedMachine
#import weakref

# Indi stuff
from helper.client import INDIClient
from helper.IndiWebManagerClient import IndiWebManagerClient, IndiWebManagerDummy
from utils.error import IndiClientPredicateTimeoutError

# Imaging and Fits stuff
from astropy.io import fits

# Local
from Base.Base import Base
from utils.error import BLOBError

logger = logging.getLogger(__name__)

class SingletonIndiClientHolder:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if "config" in kwargs:
            config = kwargs["config"]
        else:
            config = args[0]
        if "use_unique_client" in config:
            if config["use_unique_client"] is True:
                return object.__new__(cls)

        key = f"{config['indi_host']}:{config['indi_port']}"
        if key not in cls._instances:
            cls._instances[key] = object.__new__(cls)
        return cls._instances[key]

# First inheritance is SingletonIndiClientHolder to ensure call of __new__
class IndiClient(SingletonIndiClientHolder, INDIClient, Base):
    '''
        This Indi Client class can be used as a singleton, so that it can be
        used to interact with multiple devices, instead of declaring one client
        per device to manage.
    '''

    # states = ['NotConnected', 'Connecting', 'Connected', 'Disconnecting']
    # transitions = [
    #     {'trigger': 'connect_to_server', 'source': 'NotConnected', 'dest': 'Connecting', 'before': 'make_hissing_noises', 'after':''},
    #     {'trigger': 'disconnection_trig', 'source': 'Connecting', 'dest': 'NotConnected'},
    #     {'trigger': 'GuideStep', 'source': 'SteadyGuiding', 'dest': 'SteadyGuiding'},
    # ]

    def __init__(self, config):

        # If the class has already been initialized, skip
        if hasattr(self, 'ioloop'):
            return

        # Init "our" Base class
        Base.__init__(self)

        # Initialize the state machine
        # self.machine = LockedMachine(model=self,
        #                              states=IndiClient.states,
        #                              transitions=IndiClient.transitions,
        #                              initial=IndiClient.states[0])

        if config is None:
            config = dict(indi_host="localhost",
                          indi_port=7624)

        # Call MMTO indi client base classe ctor
        INDIClient.__init__(self,
                            host=config["indi_host"],
                            port=config["indi_port"])
        logger.debug(f"Indi Client, remote host is: {self.host}:{self.port}")

        self.indi_webmanager_client = IndiWebManagerDummy()
        if "indi_webmanager" in config:
            self.indi_webmanager_client = IndiWebManagerClient(config["indi_webmanager"], indi_config=config)

        # Start the main ioloop that will serve all async task in another (single) thread
        self.device_subscriptions = {} # dict of device_name: coroutines
        self.ioloop = asyncio.new_event_loop()
        # Not sure why but the default exception handler halts the loops and never shows the traceback.
        self.ioloop.set_exception_handler(self.exception)
        self.thread = threading.Thread(target=self.ioloop.run_forever)
        self.thread.start()

        # Finished configuring
        logger.debug('Configured Indi Client successfully')

    def stop(self):
        # Inform the task running in the ioloop (itself ran by self.thread) that they can stop looping
        self.running = False
        # Now wait until the main connection loop (also running in ioloop) is over
        #self.communication_over_event.wait()

        # TODO TN THIS IS QUITE EXPERIMENTAL (runinng stop in its own loop...)
        remaining_tasks = asyncio.all_tasks(loop=self.ioloop)
        while remaining_tasks:
            future = asyncio.run_coroutine_threadsafe(asyncio.wait(remaining_tasks, return_when=asyncio.ALL_COMPLETED), self.ioloop)
            _ = future.result()
            remaining_tasks = asyncio.all_tasks(loop=self.ioloop)
        # We need to force stop the ioloop that has been started with run_forever
        self.ioloop.call_soon_threadsafe(self.ioloop.stop)

        #self.ioloop.run_until_complete(self.ioloop.shutdown_asyncgens())
        # self.ioloop.close()
        # The thread whose only work was to run the ioloop forever should properly terminate
        self.thread.join()

    def exception(self, loop, context):
        raise context['exception']

    async def wait_running(self):
        while not self.running:
            await asyncio.sleep(0.01)
        return True

    async def wait_for_predicate(self, predicate_checker):
        is_ok = False
        while is_ok is False:
            is_ok = predicate_checker()
            await asyncio.sleep(0.01)
        return True

    def sync_with_predicate(self, predicate_checker, timeout=30):
        """
        Will launch the waiting mechanism
        light_checker is a callable that will return immediatly:
        * True is light is ok
        * False otherwise (busy or something else)
        """
        assert(timeout is not None)
        future = asyncio.run_coroutine_threadsafe(self.wait_for_predicate(predicate_checker), self.ioloop)
        try:
            assert (future.result(timeout) is True)
        except concurrent.futures.TimeoutError:
            msg = f"Waiting for predicate {predicate_checker} took too long..."
            future.cancel()
            raise IndiClientPredicateTimeoutError(msg)
        except Exception as exc:
            logger.error(f"Error while trying to wait for predicate: {exc!r}")
            raise RuntimeError

    def connect_to_server(self, sync=True, timeout=30):
        """
        Will launch the main listen-read/write async function in loop executed by self.thread
        """
        #self.running can be update from another thread, but read/right are atomic
        if (not self.client_connecting) and (not self.running):
            self.client_connecting = True
            asyncio.run_coroutine_threadsafe(self.connect(timeout=timeout), self.ioloop)
        if sync:
            future = asyncio.run_coroutine_threadsafe(self.wait_running(), self.ioloop)
            try:
                assert (future.result(timeout) is True)
            except concurrent.futures.TimeoutError:
                msg = "Setting up running state took too long..."
                logger.error(msg)
                future.cancel()
                raise RuntimeError(msg)
            except Exception as exc:
                msg = f"Error while trying to connect client: {exc!r}"
                logger.error(msg)
                raise RuntimeError(msg)

    def trigger_get_properties(self):
        self.xml_to_indiserver("<getProperties version='1.7'/>")

    def enable_blob(self):
        """
        Sends a signal to the server that tells it, that this client wants to receive L{indiblob} objects.
        If this method is not called, the server will not send any L{indiblob}. The DCD clients calls it each time
        an L{indiblob} is defined.
        @return: B{None}
        @rtype: NoneType
        """
        self.xml_to_indiserver("<enableBLOB>Also</enableBLOB>")

    def disable_blob(self):
        """
        Sends a signal to the server that tells it, that this client doesn't want to receive L{indiblob} objects.
        @return: B{None}
        @rtype: NoneType
        """
        self.xml_to_indiserver("<enableBLOB>Never</enableBLOB>")

    def xml_to_indiserver(self, xml):
        """
        put the xml argument in the
        to_indiQ.
        """
        asyncio.run_coroutine_threadsafe(self.to_indiQ.put(xml), self.ioloop)
        #self.ioloop.call_soon_threadsafe(self.to_indiQ.put_nowait, xml.encode())

    async def xml_from_indiserver(self, data):
        """

        :param data:
        :return:
        """
        # This is way too verbose, even in debug mode
        # print(f"IndiClient just received data {data}")
        for sub in self.device_subscriptions.values():
            asyncio.run_coroutine_threadsafe(sub(data), self.ioloop)
        await asyncio.sleep(0.01)

    def __str__(self):
        return f"INDI client connected to {self.host}:{self.port}"

    def __repr__(self):
        return f"INDI client connected to {self.host}:{self.port}"
