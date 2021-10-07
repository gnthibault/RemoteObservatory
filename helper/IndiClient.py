# Basic stuff
import asyncio
import concurrent
from contextlib import contextmanager
import io
import json
import logging
import multiprocessing
import queue
import threading

# Indi stuff
from helper.client import INDIClient

# Imaging and Fits stuff
from astropy.io import fits

# Local
from Base.Base import Base
from utils.error import BLOBError

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
    def __init__(self, device_name, queue_size=0):
        # Init "our" Base class
        Base.__init__(self)
        self.device_name = device_name
        self.queue = multiprocessing.Queue(maxsize=queue_size)

    def get(self, timeout=300):
        try:
            self.logger.debug(f"BLOBListener[{self.device_name}]: waiting for "
                              f"blob, timeout={timeout}")
            blob = self.queue.get(True, timeout)
            self.logger.debug(f"BLOBListener[{self.device_name}]: blob received"
                f" name={blob.name}, label={blob.label}, size={blob.size}, "
                f" queue size: {self.queue.qsize()} "
                f"(isEmpty: {self.queue.empty()}")
            return blob
        except queue.Empty:
            raise BLOBError(f"Timeout while waiting for BLOB on "
                            f"{self.device.name}")

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

        Every virtual function instanciated is called asynchronously by an
        external C++ thread, and not by the python main thread, so be careful.
    '''

    def __init__(self, config):
        # Init "our" Base class
        Base.__init__(self)

        if config is None:
            config = dict(indi_host="localhost",
                          indi_port=7624)

        # Call indi client base classe ctor
        INDIClient.__init__(self,
            host=config["indi_host"],
            port=config["indi_port"])
        self.logger.debug(f"Indi Client, remote host is: {self.host}:{self.port}")

        # Start the main ioloop that will serve all async task in another (single) thread
        self.device_subscriptions = [] # list of coroutines
        self.ioloop = asyncio.new_event_loop()
        # Not sure why but the default exception handler halts the loops and never shows the traceback.
        self.ioloop.set_exception_handler(self.exception)
        self.thread = threading.Thread(target=self.ioloop.run_forever)
        self.thread.start()

        # Blob related attirubtes
        self.blob_event = threading.Event()
        self.__listeners = []
        self.queue_size = config.get('queue_size', 5)

        # Finished configuring
        self.logger.debug('Configured Indi Client successfully')

    def exception(self, loop, context):
        raise context['exception']

    async def wait_running(self):
        while not self.running:
            await asyncio.sleep(0)
        return True

    def connect_to_server(self, timeout=30, sync=True):
        """
        Will launch the main listen-read/write async function in loop executed by self.thread
        """
        asyncio.run_coroutine_threadsafe(self.connect(timeout=timeout), self.ioloop)
        if sync:
            future = asyncio.run_coroutine_threadsafe(self.wait_running(), self.ioloop)
            try:
                assert (future.result(timeout) == True)
            except concurrent.futures.TimeoutError:
                self.logger.error("Setting up running state took too long...")
                future.cancel()
                raise RuntimeError
            except Exception as exc:
                self.logger.error(f"Error while trying to connect client: {exc!r}")
                raise RuntimeError

    def trigger_get_properties(self):
        self.xml_to_indiserver("<getProperties version='1.7'/>")

    def xml_to_indiserver(self, xml):
        """
        put the xml argument in the
        to_indiQ.
        """
        asyncio.run_coroutine_threadsafe(self.to_indiQ.put(xml), self.ioloop)
        #self.ioloop.call_soon_threadsafe(self.to_indiQ.put_nowait, xml.encode())

    async def xml_from_indiserver(self, data):
        self.logger.error(f"IndiClient just received data {data}")
        for sub in self.device_subscriptions:
            asyncio.run_coroutine_threadsafe(sub(data), self.ioloop)

    #def set_switch
    #self.xml_to_indiserver(self, xml)

    '''
    Indi related stuff (implementing BaseClient methods)
    '''
    def newBLOB(self, bp):
        # this threading.Event is used for sync purpose in other part of the code
        self.logger.debug(f"new BLOB received: {bp.name}")
        #self.blob_event.set()
        for listener in self.__listeners:
            if bp.bvp.device == listener.device_name:
                self.logger.debug(f"Copying blob {bp.name} to listener "
                f"{listener}")
                listener.queue.put(BLOB(bp))
        del bp

    @contextmanager
    def listener(self, device_name):
        try:
            listener = BLOBListener(device_name, self.queue_size)
            self.__listeners.append(listener)
            yield(listener)
        finally:
            self.__listeners = [x for x in self.__listeners if x is not listener]

    def __str__(self):
        return f"INDI client connected to {self.host}:{self.port}"

    def __repr__(self):
        return f"INDI client connected to {self.host}:{self.port}"
