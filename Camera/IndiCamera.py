# Basic stuff
import io
import json
import logging

# Numerical stuff
import numpy as np

# Indi stuff
import PyIndi
from helper.IndiDevice import IndiDevice
#from helper.IndiClient import IndiClientGlobalBlobEvent

# Imaging and Fits stuff
from astropy.io import fits

# Astropy
import astropy.units as u

# Local stuff: Focuser
from Imaging.IndiAutoFocuser import IndiAutoFocuser
from utils import load_module

class IndiCamera(IndiDevice):
    """ Indi Camera """

    UploadModeDict = {
        'local': 'UPLOAD_LOCAL',
        'client': 'UPLOAD_CLIENT',
        'both': 'UPLOAD_BOTH'}
    DEFAULT_EXP_TIME_SEC = 5
    MAXIMUM_EXP_TIME_SEC = 3601
    READOUT_TIME_MARGIN = 10

    def __init__(self, logger=None, config=None, connect_on_create=True):
        logger = logger or logging.getLogger(__name__)
        
        if config is None:
            config = dict(
                camera_name='CCD Simulator',
                autofocus_seconds=5,
                pointing_seconds=30,
                autofocus_size=500,
                focuser=dict(
                    module="IndiFocuser",
                    focuser_name=""),
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"
                ))
        device_name = config['camera_name']
        self.autofocus_seconds = float(config['autofocus_seconds'])
        self.pointing_seconds = float(config['pointing_seconds'])
        self.autofocus_size = int(config['autofocus_size'])
        # If scope focuser is specified in the config, load
        try:
            cfg = config['focuser']
            focuser_name = cfg['module']
            focuser = load_module('Focuser.'+focuser_name)
            self.focuser = getattr(focuser, focuser_name)(
                logger=None, config=cfg, connect_on_create=connect_on_create)
        except Exception as e:
            logger.warning(f"Cannot load focuser module: {e}")
            self.focuser = None

        logger.debug('Indi camera, camera name is: {}'.format(device_name))
      
        # device related intialization
        IndiDevice.__init__(self,
                            device_name=device_name,
                            indi_client_config=config["indi_client"])
        if connect_on_create:
            self.connect()

        # Frame Blob: reference that will be used to receive binary
        #self.frame_blob = None
        self.last_blob = None

        # Default exposureTime, gain
        self.exp_time_sec = 5
        self.gain = 400

        # Now check if there is a focuser attached
        #try:
        #    self.focuser = IndiFocuser(indi_client=self.indi_client,
        #                               connect_on_create=True)
        #except Exception:
        #    raise RuntimeError('Problem setting up focuser')

        # Finished configuring
        self.logger.debug('Configured Indi Camera successfully')

    @property
    def dynamic(self):
        return 2**self.get_dynamic()

    def on_emergency(self):
        self.logger.debug('on emergency routine started...')
        self.abort_shoot(sync=False)
        self.logger.debug('on emergency routine finished')

    '''
      Indi CCD related stuff
    '''
    def prepare_shoot(self):
        '''
          We should inform the indi server that we want to receive the
          "CCD1" blob from this device
        '''
        self.logger.debug('Indi client will register to server in order to '
                          'receive blob CCD1 when it is ready')
        self.indi_client.setBLOBMode(PyIndi.B_ALSO, self.device_name, 'CCD1')
        #self.frame_blob = self.get_prop(propName='CCD1', propType='blob')

    def synchronize_with_image_reception(self):
        try:
            #global IndiClientGlobalBlobEvent
            self.logger.debug('synchronize_with_image_reception: Start waiting')
            received = False
            #while not received:
            #    self.indi_client.blob_event.wait()
            #    for blob in self.frame_blob:
            #        device = blob.bvp.device
            #        self.logger.debug(f"Received blob for device {device}")
            #        if device == self.device_name:
            #            received = True
            #    self.indi_client.blob_event.clear()
            ##with self.indi_client.listener(self.device_name) as blob_listener:
            ##    self.last_blob = blob_listener.get()
            self.logger.debug('synchronize_with_image_reception: Done')

        except Exception as e:
            self.logger.error(f"Indi Camera Error in "
                f"synchronize_with_image_reception: {e}")

    def get_received_image(self):
        try:
            #ret = []
            #self.logger.debug(f"get_received_image frame_blob: "
            #                  f"{self.frame_blob}")
            #blobs = [b for b in self.frame_blob]
            #for blob in blobs: #self.frame_blob:
            #    self.logger.debug(f"Indi camera, processing blob with name: "
            #                      f"{blob.name}, size: {blob.size}, format: "
            #                      f"blob.format")#format generates an error
            #    # pyindi-client adds a getblobdata() method to IBLOB item
            #    # for accessing the contents of the blob, which is a bytearray
            #    #return fits.open(io.BytesIO(blob.getblobdata()))
            #return fits.open(io.BytesIO(blobs[0].getblobdata()))
            if self.last_blob is None:
                with self.indi_client.listener(self.device_name) as blob_listener:
                    image = blob_listener.get(timeout=self.exp_time_sec+
                        self.READOUT_TIME_MARGIN).get_fits()
            else:
                image = self.last_blob.get_fits()
                self.last_blob = None
            return image
        except Exception as e:
            self.logger.error('Indi Camera Error in get_received_image: '+str(e))

    def shoot_async(self):
        try:
            with self.indi_client.listener(self.device_name) as blob_listener:
                self.logger.info(f"launching acquisition with {self.exp_time_sec} "
                                 "sec exposure time")
                self.set_number('CCD_EXPOSURE',
                               {'CCD_EXPOSURE_VALUE': self.sanitize_exp_time(
                               self.exp_time_sec)}, sync=False)
                self.last_blob = blob_listener.get(timeout=self.exp_time_sec+
                                                   self.READOUT_TIME_MARGIN)
        except Exception as e:
            self.logger.error(f"Indi Camera Error in shoot: {e}")

    def get_thumbnail(self, exp_time_sec, thumbnail_size):
        """
            There are 4 cases:
            -ccd size is even, thumb size is even
            2-2 = 0 ok
            2-1 = 1 ok
            -ccd size is even, thumb size is odd
            2-1.5 = 0.5 floor
            2-0.5 = 1.5 floor
            -ccd size is odd, thumb size is even
            2.5-2 = 0.5 floor
            2.5-1 = 1.5 floor
            -ccd size is odd, thumb size is odd
            2.5-2.5 = 0 ok
            2.5-1.5 = 1 ok
        """
        sensor_size = self.get_sensor_size()
        assert (thumbnail_size < sensor_size["CCD_MAX_X"])
        assert (thumbnail_size < sensor_size["CCD_MAX_Y"])
        center_x = sensor_size["CCD_MAX_X"] / 2
        center_y = sensor_size["CCD_MAX_Y"] / 2
        left_most = np.floor(center_x - thumbnail_size / 2)
        top_most = np.floor(center_y - thumbnail_size / 2)
        roi = {'X': left_most, 'Y': top_most, 'WIDTH': thumbnail_size,
                     'HEIGHT': thumbnail_size}
        self.logger.debug(f"Setting camera {self.name} roi to {roi}")
        self.set_roi(roi)
        old_exp_time_sec = self.exp_time_sec
        self.exp_time_sec = exp_time_sec
        self.shoot_async()
        self.synchronize_with_image_reception()
        fits = self.get_received_image()
        roi = {'X': 0, 'Y': 0, 'WIDTH': sensor_size["CCD_MAX_X"],
                     'HEIGHT': sensor_size["CCD_MAX_Y"]}
        self.logger.debug(f"Resetting camera {self.name} roi to {roi}")
        self.set_roi(roi)
        self.exp_time_sec = old_exp_time_sec
        return fits


    def abort_shoot(self, sync=True):
        self.set_number('CCD_ABORT_EXPOSURE', {'ABORT': 1}, sync=sync, timeout=5)

    def launch_streaming(self):
        self.set_switch('VIDEO_STREAM', ['ON'])

    def set_upload_path(self, path, prefix = 'IMAGE_XXX'):
        self.set_text('UPLOAD_SETTINGS', {'UPLOAD_DIR': path, 'UPLOAD_PREFIX': prefix})

    def get_binning(self):
        return self.get_number('CCD_BINNING')

    def set_binning(self, hbin, vbin = None):
        if vbin == None:
            vbin = hbin
        self.set_number('CCD_BINNING', {'HOR_BIN': hbin, 'VER_BIN': vbin})

    def get_roi(self):
        """"
            X: Left-most pixel position
            Y: Top-most pixel position
            WIDTH: Frame width in pixels
            HEIGHT: Frame width in pixels
            ex: {'X':256, 'Y':480, 'WIDTH':512, 'HEIGHT':640}
        """
        number_vector = self.get_number('CCD_FRAME')
        return {k: number_vector[k] for k in ["X", "Y", "WIDTH", "HEIGHT"]}

    def set_roi(self, roi):
        """"
            X: Left-most pixel position
            Y: Top-most pixel position
            WIDTH: Frame width in pixels
            HEIGHT: Frame width in pixels
            ex: cam.set_roi({'X':256, 'Y':480, 'WIDTH':512, 'HEIGHT':640})
        """
        self.set_number('CCD_FRAME', roi, sync=True, timeout=5)

    def get_dynamic(self):
        return self.get_number('CCD_INFO')['CCD_BITSPERPIXEL']

    def get_maximum_dynamic(self):
        return self.get_dynamic()

    def get_sensor_size(self):
        number_vector = self.get_number('CCD_INFO')
        return {k: number_vector[k] for k in ["CCD_MAX_X", "CCD_MAX_Y"]}

    def get_pixel_size(self):
        number_vector = self.get_number('CCD_INFO')
        return {k: number_vector[k] for k in ["CCD_PIXEL_SIZE_X", "CCD_PIXEL_SIZE_Y"]}

    def get_temperature(self):
        return self.get_number('CCD_TEMPERATURE')['CCD_TEMPERATURE_VALUE']

    def set_temperature(self, temperature):
        """ It may take time to lower the temperature of a ccd """
        if isinstance(temperature, u.Quantity):
            temperature = temperature.to(u.deg_C).value
        if np.isfinite(temperature):
            self.set_number('CCD_TEMPERATURE',
                           {'CCD_TEMPERATURE_VALUE': temperature},
                           sync=True, timeout=1200)

    def set_cooling_on(self):
        self.set_switch('CCD_COOLER', ['COOLER_ON'], sync=True, timeout=5)

    def set_cooling_off(self):
        self.set_switch('CCD_COOLER', ['COOLER_OFF'], sync=True, timeout=5)

    def set_gain(self, value):
        self.set_number('CCD_GAIN', {'GAIN': value}, sync=True, timeout=5)

    def get_gain(self):
        gain = self.get_number('CCD_GAIN')
        return gain["GAIN"]

    def get_frame_type(self):
        return self.get_prop('CCD_FRAME_TYPE', 'switch')

    def set_frame_type(self, frame_type):
        """
        FRAME_LIGHT Take a light frame exposure
        FRAME_BIAS Take a bias frame exposure
        FRAME_DARK Take a dark frame exposure
        FRAME_FLAT Take a flat field frame exposure
        """
        self.set_switch('CCD_FRAME_TYPE', [frame_type], sync=True, timeout=5)

    def setUploadTo(self, upload_to='local'):
        uploadTo = IndiCamera.UploadModeDict[upload_to]
        self.set_switch('UPLOAD_MODE', [uploadTo], sync=True, timeout=5)

    # def getExposureRange(self):
    #     pv = self.getCCDControls('CCD_EXPOSURE', 'number')[0]
    #     return {'minimum': pv.min,
    #             'maximum': pv.max,
    #             'step': pv.step }

    def sanitize_exp_time(self, exp_time_sec):
        if isinstance(exp_time_sec, u.Quantity):
            exp_time_sec = exp_time_sec.to(u.s).value
        if not isinstance(exp_time_sec, float):
            try:
                float_exp_time_sec = float(exp_time_sec)
            except Exception as e:
                float_exp_time_sec = self.DEFAULT_EXP_TIME_SEC
        elif exp_time_sec < 0:
            float_exp_time_sec = abs(exp_time_sec)
        elif exp_time_sec == 0:
            float_exp_time_sec = self.DEFAULT_EXP_TIME_SEC
        elif exp_time_sec > self.MAXIMUM_EXP_TIME_SEC:
            float_exp_time_sec = self.MAXIMUM_EXP_TIME_SEC
        else:
            float_exp_time_sec = exp_time_sec
        # Show warning if needed
        if float_exp_time_sec != exp_time_sec:
            self.logger.warning(f"Sanitizing exposition time: cannot accept "
                                f" {exp_time_sec}, using {float_exp_time_sec} "
                                f"instead")
        return float_exp_time_sec

    def getExpTimeSec(self):
        return self.sanitize_exp_time(self.exp_time_sec)

    def setExpTimeSec(self, exp_time_sec):
        self.exp_time_sec = self.sanitize_exp_time(exp_time_sec)

    def autofocus_async(self, coarse=True):
        """

        """
        self.logger.info(f"Camera {self.device_name} is going to start "
                         f"autofocus with device {self.focuser.device_name}...")
        af = IndiAutoFocuser(camera=self)
        autofocus_event = af.autofocus(coarse=coarse, blocking=False,
                                       make_plots=True)
        self.logger.info(f"Camera {self.device_name} just launched async "
                         f"autofocus with focuser {self.focuser.device_name}")
        return autofocus_event

    def __str__(self):
        return f"INDI Camera {self.device_name}"

    def __repr__(self):
        return self.__str__()
