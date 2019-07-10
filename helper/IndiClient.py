# Basic stuff
import json
import logging
import threading

# Indi stuff
import PyIndi

# Local
from Base.Base import Base

# configure global variables
global indiClientGlobalBlobEvent
indiClientGlobalBlobEvent = threading.Event()

class IndiClient(PyIndi.BaseClient, Base):
  '''
    This Indi Client class can be used as a singleton, so that it can be used
    to interact with multiple devices, instead of declaring one client per
    device to manage.

    Every virtual function instanciated is called asynchronously by an external
    C++ thread, and not by the python main thread, so be careful.
  '''

  def __init__(self, config):
      # Init "our" Base class
      Base.__init__(self)

      # Call indi client base classe ctor
      PyIndi.BaseClient.__init__(self)

      if config is None:
            config = dict(indi_host = "localhost",
                          indi_port = 7624)
     
      self.remoteHost = config['indi_host']
      self.remotePort = int(config['indi_port'])

      self.setServer(self.remoteHost,self.remotePort)  
      self.logger.debug('Indi Client, remote host is: {} : {}'.format(
                        self.getHost(),self.getPort()))

      # Finished configuring
      self.logger.debug('Configured Indi Client successfully')

  def onEmergency(self):
      self.logger.debug('on emergency routine started...')
      pass
      self.logger.debug('on emergency routine finished')

  def connect(self):
      if self.isServerConnected():
          self.logger.warning('Already connected to server')
      else:
          self.logger.info('Connecting to server at {}:{}'.format(
                           self.getHost(),self.getPort()))

          if not self.connectServer():
              self.logger.error('No indiserver running on {}:{} '
                  ' - Try to run indiserver indi_simulator_telescope '
                  ' indi_simulator_ccd'.format(self.getHost(),self.getPort()))
          else:
              self.logger.info('Successfully connected to server at '
                               '{}:{}'.format(self.getHost(),self.getPort()))

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
      self.logger.debug("new BLOB received: "+bp.name)
      global indiClientGlobalBlobEvent
      indiClientGlobalBlobEvent.set()

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
      return 'INDI client connected to {}:{}'.format(self.remoteHost,
          self.remotePort)

  def __repr__(self):
      return self.__str__()

