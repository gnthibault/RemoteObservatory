# Basic stuff
from contextlib import contextmanager
import io
import json
import logging
import multiprocessing
import queue
import threading
#from transitions.extensions import LockedMachine
#import weakref

# Indi stuff
import PyIndi

# Imaging and Fits stuff
from astropy.io import fits

# Local
from Base.Base import Base
from helper.IndiWebManagerClient import IndiWebManagerClient, IndiWebManagerDummy
from utils.error import BLOBError, IndiClientPredicateTimeoutError

logger = logging.getLogger(__name__)

defaultTimeout = 30

class BLOB:
    def __init__(self, bp):
        self.name = bp.name
        self.label = bp.label
        self.format = bp.format
        self.blob_len = bp.bloblen
        self.size = bp.size
        self.data = bp.getblobdata()

    def get_fits(self):
        return fits.open(io.BytesIO(self.data))

    def save(self, filename):
        with open(filename, 'wb') as file:
            file.write(self.data)

class BLOBListener(Base):
    def __init__(self, device_name, queue_size=1):
        # Init "our" Base class
        Base.__init__(self)
        self.device_name = device_name
        self.queue = multiprocessing.Queue(maxsize=queue_size)

    def get(self, timeout=300):
        try:
            # logger.debug(f"BLOBListener[{self.device_name}]: waiting for blob, timeout={timeout}")
            blob = self.queue.get(True, timeout)
            # logger.debug(f"BLOBListener[{self.device_name}]: blob received name={blob.name}, label={blob.label}, "
            #     f"size={blob.size}, queue size: {self.queue.qsize()} (isEmpty: {self.queue.empty()}")
            return blob
        except queue.Empty:
            raise BLOBError(f"Timeout while waiting for BLOB on {self.device.name}")

    def __str__(self):
        return f"BLOBListener(device={self.device_name}"

    def __repr__(self):
        return self.__str__()

class SingletonIndiClientHolder:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if "config" in kwargs:
            config = kwargs["config"]
        else:
            config = args[0]

        if config.get("use_unique_client", False):
            return object.__new__(cls)

        key = f"{config['indi_host']}:{config['indi_port']}"
        if key not in cls._instances:
            cls._instances[key] = object.__new__(cls)
        return cls._instances[key]

# First inheritance is SingletonIndiClientHolder to ensure call of __new__
class IndiClient(SingletonIndiClientHolder, PyIndi.BaseClient, Base):
    '''
        This Indi Client class can be used as a singleton, so that it can be
        used to interact with multiple devices, instead of declaring one client
        per device to manage.

        Every virtual function instanciated is called asynchronously by an
        external C++ thread, and not by the python main thread, so be careful.
    '''

    # states = ['NotConnected', 'Connecting', 'Connected', 'Disconnecting']
    # transitions = [
    #     {'trigger': 'connect_to_server', 'source': 'NotConnected', 'dest': 'Connecting', 'before': 'make_hissing_noises', 'after':''},
    #     {'trigger': 'disconnection_trig', 'source': 'Connecting', 'dest': 'NotConnected'},
    #     {'trigger': 'GuideStep', 'source': 'SteadyGuiding', 'dest': 'SteadyGuiding'},
    # ]

    def __init__(self, config):
        # Init "our" Base class
        Base.__init__(self)

        # Call indi client base classe ctor
        PyIndi.BaseClient.__init__(self)

        if config is None:
            config = dict(indi_host="localhost",
                          indi_port=7624)
        self.remote_host = config['indi_host']
        self.remote_port = int(config['indi_port'])
        self.setServer(self.remote_host, self.remote_port)
        logger.debug(f"Indi Client, remote host is: {self.getHost()}:{self.getPort()}")

        self.indi_webmanager_client = IndiWebManagerDummy()
        if "indi_webmanager" in config:
            self.indi_webmanager_client = IndiWebManagerClient(config["indi_webmanager"], indi_config=config)

        # Blob related attributes
        self.blob_event = threading.Event() #TODO TN THIS IS NOT USED ANYMORE
        self.__blob_listeners = []
        self.queue_size = config.get('queue_size', 1)
        self.__pv_handlers = {}

        # Finished configuring
        logger.debug('Configured Indi Client successfully')

    ###############################################################################
    # <begin=Virtual methods>
    ###############################################################################
    def newDevice(self, d):
        '''Emmited when a new device is created from INDI server.'''
        logger.info(f"new device {d.getDeviceName()}")

    def removeDevice(self, d):
        '''Emmited when a device is deleted from INDI server.'''
        logger.info(f"remove device {d.getDeviceName()}")

    def newProperty(self, p):
        '''Emmited when a new property is created for an INDI driver.'''
        logger.info(f"new property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}")

    def updateProperty(self, p):
        '''Emmited when a new property value arrives from INDI server.'''
        # logger.info(f"update property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}")
        # if prop.getType() == PyIndi.INDI_NUMBER:
        #     self.newNumber(PyIndi.PropertyNumber(prop))
        # elif prop.getType() == PyIndi.INDI_SWITCH:
        #     self.newSwitch(PyIndi.PropertySwitch(prop))
        # elif prop.getType() == PyIndi.INDI_TEXT:
        #     self.newText(PyIndi.PropertyText(prop))
        # elif prop.getType() == PyIndi.INDI_LIGHT:
        #     self.newLight(PyIndi.PropertyLight(prop))
        # elif prop.getType() == PyIndi.INDI_BLOB:
        #     self.newBLOB(PyIndi.PropertyBlob(prop)[0])
        if p.getType() == PyIndi.INDI_BLOB:
            self.process_blob_handlers(PyIndi.PropertyBlob(p)[0])
        else:
            self.process_generic_handlers(p)

    def removeProperty(self, p):
        '''Emmited when a property is deleted for an INDI driver.'''
        logger.info(f"remove property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}")

    def newMessage(self, d, m):
        '''Emmited when a new message arrives from INDI server.'''
        logger.info(f"new Message {d.messageQueue(m)}")

    def serverConnected(self):
        '''Emmited when the server is connected.'''
        logger.info(f"Server connected ({self.getHost()}:{self.getPort()})")

    def serverDisconnected(self, code):
        '''Emmited when the server gets disconnected.'''
        logger.info(f"Server disconnected (exit code = {code},{self.getHost()}:{self.getPort()})")

    ###############################################################################
    # <end=Virtual methods>
    ###############################################################################

    def connect_device(self, device_name):
        self.connectDevice(deviceName=device_name)
    def disconnect_device(self, device_name):
        self.disconnectDevice(deviceName=device_name)
    def disconnect_from_server(self):
        self.disconnectServer()
    def connect_to_server(self, sync=True, timeout=defaultTimeout):
      if self.isServerConnected():
          logger.warning(f"Already connected fto server at {self.getHost()}: {self.getPort()}")
      else:
          logger.info(f"Connecting to server at {self.getHost()}: {self.getPort()}")
          if not self.connectServer():
              logger.error(f"No indiserver running on {self.getHost()}:{self.getPort()} - Try to run indiserver "
                  f"indi_simulator_telescope indi_simulator_ccd")
          else:
              logger.info(f"Successfully connected to server at {self.getHost()}:{self.getPort()}")

    # def exception(self, loop, context):
    #     raise context['exception']
    #
    # async def wait_running(self):
    #     while not self.running:
    #         await asyncio.sleep(0.01)
    #     return True
    #
    # async def wait_for_predicate(self, predicate_checker):
    #     is_ok = False
    #     while is_ok is False:
    #         is_ok = predicate_checker()
    #         await asyncio.sleep(0.01)
    #     return True
    #
    # def sync_with_predicate(self, predicate_checker, timeout=30):
    #     """
    #     Will launch the waiting mechanism
    #     light_checker is a callable that will return immediatly:
    #     * True is light is ok
    #     * False otherwise (busy or something else)
    #     """
    #     assert(timeout is not None)
    #     future = asyncio.run_coroutine_threadsafe(self.wait_for_predicate(predicate_checker), self.ioloop)
    #     try:
    #         assert (future.result(timeout) is True)
    #     except concurrent.futures.TimeoutError:
    #         msg = f"Waiting for predicate {predicate_checker} took too long..."
    #         future.cancel()
    #         raise IndiClientPredicateTimeoutError(msg)
    #     except Exception as exc:
    #         logger.error(f"Error while trying to wait for predicate: {exc!r}")
    #         raise RuntimeError
    #
    # def connect_to_server(self, sync=True, timeout=30):
    #     """
    #     Will launch the main listen-read/write async function in loop executed by self.thread
    #     """
    #     #self.running can be update from another thread, but read/right are atomic
    #     if (not self.client_connecting) and (not self.running):
    #         self.client_connecting = True
    #         asyncio.run_coroutine_threadsafe(self.connect(timeout=timeout), self.ioloop)
    #     if sync:
    #         future = asyncio.run_coroutine_threadsafe(self.wait_running(), self.ioloop)
    #         try:
    #             assert (future.result(timeout) is True)
    #         except concurrent.futures.TimeoutError:
    #             msg = "Setting up running state took too long..."
    #             logger.error(msg)
    #             future.cancel()
    #             raise RuntimeError(msg)
    #         except Exception as exc:
    #             msg = f"Error while trying to connect client: {exc!r}"
    #             logger.error(msg)
    #             raise RuntimeError(msg)

    '''
    Indi related stuff (implementing BaseClient methods)
    '''
    def device_names(self):
        return [d.getDeviceName() for d in self.getDevices()]

    def process_blob_handlers(self, bp):
        # this threading.Event is used for sync purpose in other part of the code
        logger.debug(f"new BLOB received: {bp.name}")
        #self.blob_event.set()
        for listener in self.__blob_listeners:
            if bp.bvp.device == listener.device_name:
                blob=BLOB(bp)
                # TODO TN, there doesn't seems to be a super reliable multiprocessing ringbuffer in python
                # Hence we implemented the ring bugger in the worse possible way...
                try:
                    listener.queue.put_nowait(blob)
                except queue.Full:
                    listener.queue.get_nowait()
                    listener.queue.put_nowait(blob)
        #del bp # This was pure madness

    def process_generic_handlers(self, pv):
        try:
            # if pv.getName() == "ABS_DOME_POSITION":
            #     print("test")
            list(
                map(
                    lambda f: f(pv),
                    self.__pv_handlers[pv.getDeviceName()][pv.getName()].values())
            )
        except KeyError:
            pass


    # @contextmanager
    # def listener(self, device_name):
    #     try:
    #         listener = BLOBListener(device_name, self.queue_size)
    #         self.__listeners.append(listener)
    #         yield(listener)
    #     finally:
    #         self.__listeners = [x for x in self.__listeners if x is not listener]

    def reset_blob_listener(self, device_name, queue_size=None):
        queue_size = self.queue_size if queue_size is None else queue_size
        # TODO TN you should use proper singleton pattern instead of this...
        # And any part manipulating __blob_listeners should be protected against concurrent access...
        #blob_listener = next((el for el in self.__blob_listeners if el.device_name == device_name), None)
        self.remove_blob_listener(device_name)
        #if blob_listener is None:
        blob_listener = BLOBListener(device_name, queue_size)
        self.__blob_listeners.append(blob_listener)
        return blob_listener

    def remove_blob_listener(self, device_name):
        self.__blob_listeners[:] = [el for el in self.__blob_listeners if el.device_name != device_name]

    def add_pv_handler(self, device_name, pv_name, handler_name, pv_handler):
        if device_name not in self.__pv_handlers:
            self.__pv_handlers[device_name] = {pv_name: {handler_name: pv_handler}}
        elif pv_name not in self.__pv_handlers[device_name]:
            self.__pv_handlers[device_name][pv_name] = {handler_name: pv_handler}
        else:
             self.__pv_handlers[device_name][pv_name][handler_name] = pv_handler

    def remove_pv_handler(self, device_name, pv_name=None, handler_name=None):
        # if no property vector is provided, remove all handler for this device
        if pv_name is None:
            self.__pv_handlers.pop(device_name, None)
        # if no handler name is provided, remove all handlers for this property vector
        elif handler_name is None:
            if device_name in self.__pv_handlers:
                self.__pv_handlers[device_name].pop(pv_name, None)
        else:
            if device_name in self.__pv_handlers:
                if handler_name in self.__pv_handlers[device_name]:
                    self.__pv_handlers[device_name][pv_name].pop(handler_name, None)

            self.__pv_handlers[device_name][pv_name].pop(handler_name, None)

    def __str__(self):
        return f"INDI client connected to {self.remote_host}:{self.remote_port}"

    def __repr__(self):
        return f"INDI client connected to {self.remote_host}:{self.remote_port}"
    #
    #
    # def trigger_get_properties(self):
    #     self.xml_to_indiserver("<getProperties version='1.7'/>")
    #
    def enable_blob(self, blob_mode=PyIndi.B_ALSO, device_name=None, property_name=None):
        """
        Sends a signal to the server that tells it, that this client wants to receive L{indiblob} objects.
        If this method is not called, the server will not send any L{indiblob}. The DCD clients calls it each time
        an L{indiblob} is defined.
        From https://github.com/indilib/indi/blob/master/libs/indiabstractclient/abstractbaseclient.h#L165C26-L165C38
         *  Set the BLOB handling mode for the client. The client may either receive:
         *  <ul>
         *    <li>Only BLOBS</li>
         *    <li>BLOBs mixed with normal messages</li>
         *    <li>Normal messages only, no BLOBs</li>
         *  </ul>
         *  If \e dev and \e prop are supplied, then the BLOB handling policy is set for this particular device and property.
         *  if \e prop is NULL, then the BLOB policy applies to the whole device.
         *
         *  @param blobH BLOB handling policy
         *  @param dev name of device, required.
         *  @param prop name of property, optional.

        B_ALSO = 1
        B_NEVER = 0
        B_ONLY = 2

        @return: B{None}
        @rtype: NoneType
        """
        self.setBLOBMode(blob_mode, device_name, property_name)

    #
    # def disable_blob(self):
    #     """
    #     Sends a signal to the server that tells it, that this client doesn't want to receive L{indiblob} objects.
    #     @return: B{None}
    #     @rtype: NoneType
    #     """
    #     self.xml_to_indiserver("<enableBLOB>Never</enableBLOB>")
    #
    # def xml_to_indiserver(self, xml):
    #     """
    #     put the xml argument in the
    #     to_indiQ.
    #     """
    #     asyncio.run_coroutine_threadsafe(self.to_indiQ.put(xml), self.ioloop)
    #     #self.ioloop.call_soon_threadsafe(self.to_indiQ.put_nowait, xml.encode())
    #
    # async def xml_from_indiserver(self, data):
    #     """
    #
    #     :param data:
    #     :return:
    #     """
    #     # This is way too verbose, even in debug mode
    #     # print(f"IndiClient just received data {data}")
    #     for sub in self.device_subscriptions.values():
    #         asyncio.run_coroutine_threadsafe(sub(data), self.ioloop)
    #     await asyncio.sleep(0.01)

    # def __str__(self):
    #     return f"INDI client connected to {self.host}:{self.port}"
    #
    # def __repr__(self):
    #     return f"INDI client connected to {self.host}:{self.port}"
