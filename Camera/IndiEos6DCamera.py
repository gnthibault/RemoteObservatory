#Basic stuff
import logging
import json
import io

#Local stuff
from Camera.IndiAbstractCamera import IndiAbstractCamera
from Camera.IndiCamera import IndiCamera

class IndiEos6DCamera(IndiAbstractCamera):
    ''' Indi Camera class for eos 6D ( ×  full frame cmos) '''

    def __init__(self, indiClient, config=None,
                 connectOnCreate=True):
        self.logger.debug('Configuring Indi EOS6D Camera')

        if config is None:
            config = dict(
                camera_name='Canon DSLR Digital Rebel XT (normal mode)')


        # device related intialization
        super().__init__(self, indiClient, logger=self.logger,
                            config=config)

        # Finished configuring
        self.logger.debug('Configured Indi Eos 6D Camera successfully')

    '''
      Indi CCD related stuff
    '''
    def prepareShoot(self):
        self.setText("DEVICE_PORT",{"PORT":"/dev/ttyUSB0"})
        IndiCamera.prepareShoot(self)

