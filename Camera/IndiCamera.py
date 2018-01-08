# Basic stuff
import io
import json
import logging

# Indi stuff
import PyIndi
from helper.IndiDevice import IndiDevice
from helper.IndiClient import indiClientGlobalBlobEvent

# Imaging and Fits stuff
from astropy.io import fits
import matplotlib.pyplot as plt

class CameraSettingsRunner:
  def __init__(self, camera, roi=None, binning=None,\
      compressionFormat=None, frameType=None, properties=None, numbers=None,
      switches=None):
    self.camera = camera
    self.roi = roi
    self.binning = binning
    self.compressionFormat = compressionFormat
    self.frameType = frameType
    self.properties = properties
    self.numbers = numbers
    self.switches = switches

  def run(self):
    if self.roi:
      self.camera.setRoi(self.roi)
    if self.binning:
      self.camera.setBinning(self.binning)
    if self.compressionFormat:
      self.camera.setCompressionFormat(self.compressionFormat)
    if self.frameType:
      self.camera.setFrameType(self.frameType)
    if self.properties:
      self.camera.setProperties(self.properties)
    if self.numbers:
      for propName, valueVector in self.numbers.items():
        self.camera.setNumber(propName, valueVector)
    if self.switches:
      for propName, valueVector in self.switches.items():
        self.camera.setSwitch(propName, valuesVector['on']\
          if 'on' in valueVector else [], valueVector['off']\
          if 'off' in valueVector else [])

  def __str__(self):
    values = [['roi', self.roi],\
      ['bin', self.binning],\
      ['compressionFormat', self.compressionFormat],\
      ['frameType', self.frameType],\
      ['properties', self.properties],\
      ['numbers', self.numbers],\
      ['switches', self.switches]]
    values = [': '.join([x[0], str(x[1])]) for x in values if x[1]]
    return 'Change camera settings: {0}'.format(', '.join(values))

  def __repr__(self):
      return self.__str__()

class IndiCamera(IndiDevice):
  ''' Indi Camera '''

  UploadModeDict = {'local': 'UPLOAD_LOCAL',
    'client': 'UPLOAD_CLIENT',\
    'both': 'UPLOAD_BOTH'}

  def __init__(self, indiClient, logger=None, configFileName=None,\
      connectOnCreate=True):
    logger = logger or logging.getLogger(__name__)
    
    if configFileName is None:
      self.configFileName = 'IndiCCDSimulatorCamera.json'
    else:
      self.configFileName = configFileName

    # Now configuring class
    logger.debug('Configuring Indi Camera with file %s',\
      self.configFileName)
    # Get key from json
    with open(self.configFileName) as jsonFile:
      data = json.load(jsonFile)
      deviceName = data['cameraName']

    logger.debug('Indi camera, camera name is: '+\
      deviceName)
  
    # device related intialization
    IndiDevice.__init__(self, logger=logger, deviceName=deviceName,\
      indiClient=indiClient)
    if connectOnCreate:
      self.connect()

    # Frame Blob: reference that will be used to receive binary
    self.frameBlob = None

    # Default exposureTime, gain
    self.expTimeSec=5
    self.gain=400

    # Finished configuring
    self.logger.debug('Configured Indi Camera successfully')

  def onEmergency(self):
    self.logger.debug('Indi Camera: on emergency routine started...')
    pass
    self.logger.debug('Indi Camera: on emergency routine finished')

  '''
    Indi CCD related stuff
  '''
  def prepareShoot(self):
    '''
      We should inform the indi server that we want to receive the
      "CCD1" blob from this device
    '''
    self.indiClient.setBLOBMode(PyIndi.B_ALSO, self.deviceName, 'CCD1')
    self.frameBlob=self.getPropertyVector(propName='CCD1', propType='blob')

  def synchronizeWithImageReception(self):
    try:
      global indiClientGlobalBlobEvent
      indiClientGlobalBlobEvent.wait()
      indiClientGlobalBlobEvent.clear()
    except Exception as e:
      self.logger.error('Indi Camera Error in synchronizeWithImageReception: '\
        +str(e))

  def getReceivedImage(self):
    try:
      ret = []
      for blob in self.frameBlob:
        self.logger.debug("Indi camera, processing blob with name: "+\
          blob.name+" size: "+str(blob.size)+" format: "+str(blob.format))
        # pyindi-client adds a getblobdata() method to IBLOB item
        # for accessing the contents of the blob, which is a bytearray in Python
        blobObj=blob.getblobdata()
        # write image data to BytesIO buffer
        byteStream = io.BytesIO(blobObj)
        return fits.open(byteStream)
        #plt.imshow(hdulist[0].data)
        #plt.show()
        #del hdul[0].data
        #hdulist.close
        # open a file and save buffer to disk
        #with open("frame"+str(self.imgIdx)+".fit", "wb") as f:
        #  f.write(blobfile.getvalue())
        #  print("fits data type: ", type(fits))
    except Exception as e:
      self.logger.error('Indi Camera Error in getReceivedImage: '+str(e))

  def shootAsync(self):
    try:
      self.logger.info('Indi Camera: launching acquisition with '+\
        str(self.expTimeSec)+' sec exposure time')
      self.setNumber('CCD_EXPOSURE', {'CCD_EXPOSURE_VALUE': self.expTimeSec},\
        sync=False)
    except Exception as e:
      self.logger.error('Indi Camera Error in shoot: '+str(e))

  def setUploadPath(self, path, prefix = 'IMAGE_XXX'):
    self.setText('UPLOAD_SETTINGS', {'UPLOAD_DIR': path,\
      'UPLOAD_PREFIX': prefix})

  def getBinning(self):
    return self.getPropertyValueVector('CCD_BINNING', 'number')

  def setBinning(self, hbin, vbin = None):
    if vbin == None:
      vbin = hbin
    self.setNumber('CCD_BINNING', {'HOR_BIN': hbin, 'VER_BIN': vbin })

  def getRoi(self):
    return self.getPropertyValueVector('CCD_FRAME', 'number')

  def setRoi(self, roi):
    self.setNumber('CCD_FRAME', roi)

  def getCompressionFormat(self):
    return self.switchValues('CCD_COMPRESSION')

  def setCompressionFormat(self, ccdCompression):
    self.setSwitch('CCD_COMPRESSION', [ccdCompression])

  def getFrameType(self):
    return self.switchValues('CCD_FRAME_TYPE')

  def setFrameType(self, frame_type):
    self.setSwitch('CCD_FRAME_TYPE', [frame_type])

  def getCCDControls(self):
    return self.getPropertyValueVector('CCD_CONTROLS', 'number')

  def setCCDControls(self, controls):
    self.setNumber('CCD_CONTROLS', controls)

  def setUploadTo(self, uploadTo = 'local'):
    uploadTo = IndiCamera.UploadModeDict[upload_to]
    self.setSwitch('UPLOAD_MODE', [uploadTo] )

  def getExposureRange(self):
    pv = self.getCCDControls('CCD_EXPOSURE', 'number')[0]
    return { 'minimum': pv.min,
      'maximum': pv.max,
      'step': pv.step }

  def getExpTimeSec(self):
    return self.expTimeSec

  def setExpTimeSec(self, expTimeSec):
    self.expTimeSec = expTimeSec

  def getGain(self):
    return self.gain

  def setGain(self):
    return self.gain

  def __str__(self):
    return 'INDI Camera "{0}"'.format(self.name)

  def __repr__(self):
    return self.__str__()


