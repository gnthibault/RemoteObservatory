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


class IndiCamera(IndiDevice):
    """ Indi Camera """

    UploadModeDict = {
        'local': 'UPLOAD_LOCAL',
        'client': 'UPLOAD_CLIENT',
        'both': 'UPLOAD_BOTH'}

    def __init__(self, indiClient, logger=None, configFileName=None,
                 connectOnCreate=True):
        logger = logger or logging.getLogger(__name__)
        
        if configFileName is None:
            self.configFileName = 'IndiCCDSimulatorCamera.json'
        else:
            self.configFileName = configFileName

        # Now configuring class
        logger.debug('Configuring Indi Camera with file {}'.format(
                      self.configFileName))
        # Get key from json
        with open(self.configFileName) as jsonFile:
            data = json.load(jsonFile)
            deviceName = data['cameraName']

        logger.debug('Indi camera, camera name is: {}'.format(deviceName))
      
        # device related intialization
        IndiDevice.__init__(self, logger=logger, deviceName=deviceName,
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
        self.abortShoot(sync=False)
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
            self.logger.error('Indi Camera Error in '
                'synchronizeWithImageReception: {}'.format(e))

    def getReceivedImage(self):
        try:
            ret = []
            for blob in self.frameBlob:
                self.logger.debug('Indi camera, processing blob with name: {},'
                                   ', size: {}, format: {}'.format(
                                   blob.name,blob.size,blob.format))
                # pyindi-client adds a getblobdata() method to IBLOB item
                # for accessing the contents of the blob, which is a bytearray
                return fits.open(io.BytesIO(blob.getblobdata()))
        except Exception as e:
            self.logger.error('Indi Camera Error in getReceivedImage: '+str(e))

    def shootAsync(self):
        try:
            self.logger.info('Indi Camera: launching acquisition with {} '
                             'sec exposure time'.format(self.expTimeSec))
            self.setNumber('CCD_EXPOSURE',
                           {'CCD_EXPOSURE_VALUE': self.expTimeSec}, sync=False)
        except Exception as e:
            self.logger.error('Indi Camera Error in shoot: {}'.format(e))

    def abortShoot(self, sync=True):
        self.setNumber('CCD_ABORT_EXPOSURE', {'ABORT': 1}, sync=sync)

    def launchStreaming(self):
        self.setSwitch('VIDEO_STREAM',['ON'])

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
        """"
            X: Left-most pixel position
            Y: Top-most pixel position
            WIDTH: Frame width in pixels
            HEIGHT: Frame width in pixels
            ex: cam.setRoi({'X':256, 'Y':480, 'WIDTH':512, 'HEIGHT':640})
        """
        self.setNumber('CCD_FRAME', roi)
   
    def getTemperature(self):
        return self.getPropertyValueVector('CCD_TEMPERATURE',
                                           'number')['CCD_TEMPERATURE_VALUE']

    def setTemperature(self, temperature):
        """ It may take time to lower the temperature of a ccd """
        self.setNumber('CCD_TEMPERATURE',
                       { 'CCD_TEMPERATURE_VALUE' : temperature },
                       timeout=1200)

    #def setCoolingOn(self):
    #    self.setSwitch('CCD_COOLER',['COOLER_ON'])

    #def setCoolingOff(self):
    #    self.setSwitch('CCD_COOLER',['COOLER_OFF'])

    #def getFrameType(self):
    #    return self.getPropertyVector('CCD_FRAME_TYPE','switch')

    def setFrameType(self, frame_type):
        """
        FRAME_LIGHT Take a light frame exposure
        FRAME_BIAS Take a bias frame exposure
        FRAME_DARK Take a dark frame exposure
        FRAME_FLAT Take a flat field frame exposure
        """
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

    def getRelevantFlatDuration(self, filterName):
        #expRange = self.getExposureRange()
        #return int(expRange['minimum']+2*expRange['step'])
        return 1

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


