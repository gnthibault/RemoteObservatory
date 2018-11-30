# Basic stuff
import io
import json
import logging

# Numerical stuff
import numpy as np

# Indi stuff
import PyIndi
from helper.IndiDevice import IndiDevice
from helper.IndiClient import indiClientGlobalBlobEvent

# Imaging and Fits stuff
from astropy.io import fits

# Astropy
import astropy.units as u

# Local stuff: Focuser
from Focuser.IndiFocuser import IndiFocuser

class IndiCamera(IndiDevice):
    """ Indi Camera """

    UploadModeDict = {
        'local': 'UPLOAD_LOCAL',
        'client': 'UPLOAD_CLIENT',
        'both': 'UPLOAD_BOTH'}
    DEFAULT_EXP_TIME_SEC = 5
    MAXIMUM_EXP_TIME_SEC = 3601

    def __init__(self, indiClient, logger=None, configFileName=None,
                 connectOnCreate=True):
        logger = logger or logging.getLogger(__name__)
        
        if configFileName is None:
            self.configFileName = './conf_files/IndiCCDSimulatorCamera.json'
        else:
            self.configFileName = configFileName

        # Now configuring class
        logger.debug('Configuring Indi Camera with file {}'.format(
                      self.configFileName))

        self.focuser = None
        # Get key from json
        with open(self.configFileName) as jsonFile:
            data = json.load(jsonFile)
            deviceName = data['cameraName']
            if 'focuserCfg' in data:
                self.focuser = IndiFocuser(indiClient=indiClient,
                                           configFileName=data['focuserCfg'],
                                           connectOnCreate=connectOnCreate)

        logger.debug('Indi camera, camera name is: {}'.format(deviceName))
      
        # device related intialization
        IndiDevice.__init__(self, logger=logger, deviceName=deviceName,
                            indiClient=indiClient)
        if connectOnCreate:
            self.connect()

        # Frame Blob: reference that will be used to receive binary
        self.frameBlob = None

        # Default exposureTime, gain
        self.exp_time_sec=5
        self.gain=400

        # Now check if there is a focuser attached
        #try:
        #    self.focuser = IndiFocuser(indiClient=self.indi_client,
        #                               connectOnCreate=True)
        #except Exception:
        #    raise RuntimeError('Problem setting up focuser')

        # Finished configuring
        self.logger.debug('Configured Indi Camera successfully')

    @property
    def dynamic(self):
        return 2**self.get_dynamic()

    def onEmergency(self):
        self.logger.debug('on emergency routine started...')
        self.abortShoot(sync=False)
        self.logger.debug('on emergency routine finished')

    '''
      Indi CCD related stuff
    '''
    def prepareShoot(self):
        '''
          We should inform the indi server that we want to receive the
          "CCD1" blob from this device
        '''
        self.logger.debug('Indi client will register to server in order to '
                          'receive blob CCD1 when it is ready')
        self.indiClient.setBLOBMode(PyIndi.B_ALSO, self.deviceName, 'CCD1')
        self.frameBlob=self.get_prop(propName='CCD1', propType='blob')

    def synchronizeWithImageReception(self):
        try:
            global indiClientGlobalBlobEvent
            self.logger.debug('synchronizeWithImageReception: Start waiting')
            indiClientGlobalBlobEvent.wait()
            indiClientGlobalBlobEvent.clear()
            self.logger.debug('synchronizeWithImageReception: Done')
        except Exception as e:
            self.logger.error('Indi Camera Error in '
                'synchronizeWithImageReception: {}'.format(e))

    def getReceivedImage(self):
        try:
            ret = []
            self.logger.debug('getReceivedImage frameBlob: {}'.format(
                self.frameBlob))
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
            self.logger.info('launching acquisition with {} '
                             'sec exposure time'.format(self.exp_time_sec))
            self.setNumber('CCD_EXPOSURE',
                           {'CCD_EXPOSURE_VALUE': self.sanitize_exp_time(
                               self.exp_time_sec)}, sync=False)
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

    def get_dynamic(self):
        return self.get_number('CCD_INFO')['CCD_BITSPERPIXEL']['value']

    def get_temperature(self):
        return self.get_number(
            'CCD_TEMPERATURE')['CCD_TEMPERATURE_VALUE']['value']

    def set_temperature(self, temperature):
        """ It may take time to lower the temperature of a ccd """
        if isinstance(temperature, u.Quantity):
            temperature = temperature.to(u.deg_C).value
        if np.isfinite(temperature):
            self.setNumber('CCD_TEMPERATURE',
                           { 'CCD_TEMPERATURE_VALUE' : temperature },
                           sync=True, timeout=1200)

    def set_cooling_on(self):
        self.setSwitch('CCD_COOLER',['COOLER_ON'])

    def set_cooling_off(self):
        self.setSwitch('CCD_COOLER',['COOLER_OFF'])

    def set_gain(self, value):
        pass
        #TODO TN, Try to solve this
        #self.setNumber('DETECTOR_GAIN', [{'Gain': value}])

    def get_gain(self):
        gain = self.get_number('CCD_GAIN')
        print('returned Gain is {}'.format(gain))
        return gain

    def get_frame_type(self):
        return self.get_prop('CCD_FRAME_TYPE','switch')

    def set_frame_type(self, frame_type):
        """
        FRAME_LIGHT Take a light frame exposure
        FRAME_BIAS Take a bias frame exposure
        FRAME_DARK Take a dark frame exposure
        FRAME_FLAT Take a flat field frame exposure
        """
        self.setSwitch('CCD_FRAME_TYPE', [frame_type])

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

    def sanitize_exp_time(self, exp_time_sec):
        if isinstance(exp_time_sec, u.Quantity):
            exp_time_sec = exp_time_sec.to(u.s).value
        if not isinstance(exp_time_sec, float):
            try:
                float_exp_time_sec = float(exp_time_sec)
            except Exception as e:
                float_exp_time_sec = self.DEFAULT_EXP_TIME_SEC
        elif exp_time_sec < 0:
            float_exp_time_sec = abs(float_exp_time_sec)
        elif exp_time_sec == 0:
            float_exp_time_sec = self.DEFAULT_EXP_TIME_SEC
        elif exp_time_sec > self.MAXIMUM_EXP_TIME_SEC:
            float_exp_time_sec = self.MAXIMUM_EXP_TIME_SEC
        else:
            float_exp_time_sec = exp_time_sec
        # Show warning if needed
        if float_exp_time_sec != exp_time_sec:
            self.logger.warning('Sanitizing exposition time: cannot accept'
                                ' {}, using {} instead'.format(exp_time_sec
                                , float_exp_time_sec))

        return float_exp_time_sec

    def getExpTimeSec(self):
        return self.sanitize_exp_time(self.exp_time_sec)

    def setExpTimeSec(self, exp_time_sec):
        self.exp_time_sec = self.sanitize_exp_time(exp_time_sec)

    def __str__(self):
        return 'INDI Camera "{0}"'.format(self.name)

    def __repr__(self):
        return self.__str__()


