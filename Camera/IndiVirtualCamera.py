#Basic stuff
import logging
import json
import io

#Indi stuff
import PyIndi

class IndiVirtualCamera(PyIndi.BaseClient):
  ''' Indi Virtual Camera '''

  def __init__(self, configFileName=None, logger=None):
    self.logger = logger or logging.getLogger(__name__)
    
    # Call indi client base classe ctor
    self.logger.debug('IndiVirtualCamera: starting constructing base class')
    super(IndiVirtualCamera, self).__init__()
    self.logger.debug('IndiVirtualCamera: finished constructing base class')

    if configFileName is None:
      self.cameraName = 'CCD Simulator'
      self.remoteHost = 'localhost'
      self.remotePort = 7624
    else:
      self.configFileName = configFileName
      # Now configuring class
      self.logger.info('Configuring Indi Virtual Camera with file %s',\
        self.configFileName)
      # Get key from json
      with open(self.configFileName) as jsonFile:
        data = json.load(jsonFile)
        self.cameraName = data['cameraName']
        self.remoteHost = data['remoteHost']
        self.remotePort = int(data['remotePort'])

    self.setServer(self.remoteHost,self.remotePort)  
    self.logger.info('Indi Virtual camera, camera name is: '+\
      self.cameraName)
    self.logger.info('Indi Virtual camera, remote host is: '+\
      self.getHost()+':'+str(self.getPort()))
  
    # Frame acquisition related stuff
    self.acquisitionReady = False

    # Finished configuring
    self.logger.info('Configured Indi Virtual Camera successfully')
    

  def onEmergency(self):
    self.logger.info('Indi Virtual Camera: on emergency routine started...')
    pass
    self.logger.info('Indi Virtual Camera: on emergency routine finished')

  '''
    Indi related stuff (implementing BaseClient methods)
  '''
  def newDevice(self, d):
    if d.getDeviceName() == self.cameraName:
      self.logger.info('Indi Virtual Camera: new device '+d.getDeviceName())
      self.cameraDevice = d

  def newProperty(self, p):
    if (self.cameraDevice is not None 
        and p.getName() == "CONNECTION" 
        and p.getDeviceName() == self.cameraDevice.getDeviceName()):
      self.logger.info('Indi Virtual Camera: Got property CONNECTION for '+\
        'device '+p.getDeviceName())
      # connect to device
      self.connectDevice(self.cameraDevice.getDeviceName())
      # set BLOB mode to BLOB_ALSO
      self.setBLOBMode(1, self.cameraDevice.getDeviceName(), None)
      self.acquisitionReady = True

  def removeProperty(self, p):
    if p.getDeviceName() == self.cameraName:
      self.logger.info('Indi Virtual Camera: remove property '+ p.getName())

  def newBLOB(self, bp):
    if bp.getDeviceName() == self.cameraName:
      self.logger.info('Indi Virtual Camera: new BLOB received '+ bp.name)
      # get image data
      img = bp.getblobdata()
      # write image data to BytesIO buffer
      blobfile = io.BytesIO(img)
      self.acquisitionReady = False

  def newSwitch(self, svp):
    if svp.device == self.cameraName:
      self.logger.info ('Indi Virtual Camera: new Switch '+svp.name)

  def newNumber(self, nvp):
    if nvp.getDeviceName() == self.cameraName:
      self.logger.info('Indi Virtual Camera: new Number '+ nvp.name)
      #nvp.device)

  def newText(self, tvp):
    if tvp.getDeviceName() == self.cameraName:
      self.logger.info('Indi Virtual Camera: new Text '+ tvp.name +\
        ' label is '+tvp.label+', group is '+tvp.group+\
        ' and timestamp is'+tvp.timestamp)
        #tvp.device)

  def newLight(self, lvp):
    if lvp.getDeviceName() == self.cameraName:
      self.logger.info('Indi Virtual Camera: new Light '+ lvp.name)
      #lvp.device)

  def newMessage(self, d, m):
    if d.getDeviceName() == self.cameraName:
      self.logger.info('Indi Virtual Camera: new Message '+ d.messageQueue(m))

  def serverConnected(self):
    self.logger.info('Indi Virtual Camera: Server connected ('\
      +self.getHost()+':'+str(self.getPort())+')')

  def serverDisconnected(self, code):
    self.logger.info('Indi Virtual Camera: Server disconnected (\
      exit code = '+str(code)+', '+\
      str(self.getHost())+':'+str(self.getPort())+')')

  ''' 
    Now application related methods
  '''
  def connect(self):
    self.logger.info('Indi Virtual Camera: Connecting to server')
    if not self.connectServer():
      self.logger.error('Indi Virtual Camera: No indiserver running on '+\
        self.getHost()+':'+str(self.getPort())+' - Try to run '+\
        'indiserver indi_simulator_telescope indi_simulator_ccd')

  def launchAcquisition(self, expTimeSec=1):
    if self.acquisitionReady:
      # get current exposure feature ?
      exposure = self.cameraDevice.getNumber('CCD_EXPOSURE')
      # set exposure time in seconds
      exposure[0].value = expTimeSec
      self.logger.info('Indi Virtual Camera: launching acquisition with '+\
        str(expTimeSec)+' sec exposure time')
      self.acquisitionReady = False
      self.sendNewNumber(exposure)
    else:
      self.logger.error('Indi Virtual Camera: cannot launch acquisition '+\
        'because device is not ready')

# open a file and save buffer to disk
#with open('frame.fits', 'wb') as f:
#  f.write(blobfile.getvalue())

