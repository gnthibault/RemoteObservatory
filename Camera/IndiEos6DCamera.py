#Basic stuff
import logging
import json
import io

#Local stuff
from Camera.IndiAbstractCamera import IndiAbstractCamera
from Camera.IndiCamera import IndiCamera

class IndiEos6DCamera(IndiAbstractCamera):
    ''' Indi Camera class for eos 6D ( ×  full frame cmos) '''

    def __init__(self, serv_time, indi_client, config=None,
                 connect_on_create=True, primary=False):

        if config is None:
            config = dict(
                camera_name='GPhoto CCD',
                CCD_INFO=dict(
                    CCD_MAX_X=5472,
                    CCD_MAX_Y=3648,
                    CCD_PIXEL_SIZE=6.5,
                    CCD_PIXEL_SIZE_X=6.5,
                    CCD_PIXEL_SIZE_Y=6.5,
                    CCD_BITSPERPIXEL=14)
            )

        # device related intialization
        super().__init__(serv_time=serv_time, indi_client=indi_client,
                         config=config, connect_on_create=connect_on_create,
                         primary=primary)
        self.init_frame_features()

        # Finished configuring
        self.logger.debug('Configured Indi Eos 6D Camera successfully')

    '''
      Indi CCD related stuff
    '''
    def init_frame_features(self):
        self.logger.debug("COnfig for camera device is {}".format(self.indi_camera_config))
        # TODO TN: we decide that IndiCamera takes over AbstractCamera in the
        # case we have diamond like inheritance problem
        self.set_number("CCD_INFO", self.indi_camera_config["CCD_INFO"])