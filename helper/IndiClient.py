# Basic stuff
import json
import logging
import threading

# Indi stuff
import PyIndi

# configure global variables
global indiClientGlobalBlobEvent
indiClientGlobalBlobEvent = threading.Event()

class IndiClient(PyIndi.BaseClient):
  '''
    This Indi Client class can be used as a singleton, so that it can be used
    to interact with multiple devices, instead of declaring one client per
    device to manage.

    Every virtual function instanciated is called asynchronously by an external
    C++ thread, and not by the python main thread, so be careful.
  '''

  def __init__(self, configFileName=None, logger=None):
      self.logger = logger or logging.getLogger(__name__)
      
      # Call indi client base classe ctor
      self.logger.debug('starting constructing base class')
      super(IndiClient, self).__init__()
      self.logger.debug('finished constructing base class')

      if configFileName is None:
          self.configFileName = './conf_files/IndiClient.json'
      else:
          self.configFileName = configFileName

      # Now configuring class
      self.logger.debug('Configuring Indiclient with file {}'.format(
          self.configFileName))
      # Get key from json
      with open(self.configFileName) as jsonFile:
          data = json.load(jsonFile)
          self.remoteHost = data['remoteHost']
          self.remotePort = int(data['remotePort'])

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
      return 'INDI client connected to {}:{}'.format(self.host, self.port)

  def __repr__(self):
      return self.__str__()

