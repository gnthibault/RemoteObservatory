#Basic stuff
import logging
import json
import io

#Local stuff
from Camera.IndiAbstractCamera import IndiAbstractCamera
from Camera.IndiCamera import IndiCamera

class IndiEos350DCamera(IndiAbstractCamera):
    ''' Indi Camera class for eos 350D (3456 × 2304 apsc cmos) '''

    def __init__(self, indi_client, config=None,
                 connect_on_create=True):
        self.logger.debug('Configuring Indi EOS6D Camera')

        if config is None:
            config = dict(
                camera_name='Canon DSLR Digital Rebel XT (normal mode)')


        # device related intialization
        super().__init__(indi_client, logger=self.logger,
                            config=config)

        # Finished configuring
        self.logger.debug('Configured Indi Eos 350D Camera successfully')

    '''
      Indi CCD related stuff
    '''
    def prepare_shoot(self):
        self.set_text("DEVICE_PORT",{"PORT":"/dev/ttyUSB0"})
        IndiCamera.prepare_shoot(self)


