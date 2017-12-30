#Basic stuff
import logging
import json

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
      # open a file and save buffer to disk
      #with open('frame.fits', 'wb') as f:
      #  f.write(blobfile.getvalue())
      # start new exposure for timelapse images!
      #self.takeExposure()

  def newSwitch(self, svp):
    if svp.getDeviceName() == self.cameraName:
      self.logger.info ('Indi Virtual Camera: new Switch '+svp.name)
      #svp.device

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

  def takeExposure(self):
    pass
    #self.logger.info('<<<<<<<< Exposure >>>>>>>>>')
    # get current exposure time
    #exp = self.device.getNumber('CCD_EXPOSURE')
    # set exposure time to 5 seconds
    #exp[0].value = 50
    # send new exposure time to server/device
    #self.sendNewNumber(exp)

