# Basic stuff
import json
import logging
import threading

# Indi stuff
import PyIndi

# Local
from Base.Base import Base

# configure global variables
#global IndiClientGlobalBlobEvent
#IndiClientGlobalBlobEvent = threading.Event()

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
      self.blob_event = threading.Event()
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
        #global IndiClientGlobalBlobEvent
        #IndiClientGlobalBlobEvent.set()
        self.blob_event.set()

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