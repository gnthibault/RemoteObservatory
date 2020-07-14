# Basic stuff
from contextlib import contextmanager
import io
import json
import logging
import multiprocessing
import queue
import threading

# Indi stuff
import PyIndi

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
class IndiClient(SingletonIndiClientHolder, PyIndi.BaseClient, Base):
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

      # Call indi client base classe ctor
      PyIndi.BaseClient.__init__(self)

      if config is None:
            config = dict(indi_host="localhost",
                          indi_port=7624)
      self.remoteHost = config['indi_host']
      self.remotePort = int(config['indi_port'])
      self.setServer(self.remoteHost, self.remotePort)
      self.logger.debug(f"Indi Client, remote host is: {self.getHost()}:"
                        f"{self.getPort()}")

      # Blov related attirubtes
      self.blob_event = threading.Event()
      self.__listeners = []
      self.queue_size = config.get('queue_size', 5)

      # Finished configuring
      self.logger.debug('Configured Indi Client successfully')

    def connect(self):
      if self.isServerConnected():
          self.logger.warning('Already connected to server')
      else:
          self.logger.info(f"Connecting to server at {self.getHost()}:"
                           f"{self.getPort()}")

          if not self.connectServer():
              self.logger.error(f"No indiserver running on {self.getHost()}:"
                  f"{self.getPort()} - Try to run indiserver "
                  f"indi_simulator_telescope indi_simulator_ccd")
          else:
              self.logger.info(f"Successfully connected to server at "
                               f"{self.getHost()}:{self.getPort()}")

    '''
    Indi related stuff (implementing BaseClient methods)
    '''
    def device_names(self):
        return [d.getDeviceName() for d in self.getDevices()]

    def newDevice(self, d):
        pass

    def newProperty(self, p):
        pass

    def removeProperty(self, p):
        pass

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

    def newSwitch(self, svp):
        pass

    def newNumber(self, nvp):
        pass

    def newText(self, tvp):
        pass

    def newLight(self, lvp):
        pass

    def newMessage(self, d, m):
        pass

    def serverConnected(self):
        self.logger.debug('Server connected')

    def serverDisconnected(self, code):
        self.logger.debug('Server disconnected')

    def __str__(self):
        return f"INDI client connected to {self.remoteHost}:{self.remotePort}"

    def __repr__(self):
        return f"INDI client connected to {self.remoteHost}:{self.remotePort}"
