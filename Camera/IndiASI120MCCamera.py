#Basic stuff
import logging
import json
import io

# Numerical stuff
import numpy as np

#Indi stuff
from Camera.IndiCamera import IndiCamera

class IndiASI120MCCamera(IndiCamera):
    ''' Indi Camera class for eos 350D (3456 × 2304 apsc cmos) '''

    def __init__(self, indi_client, logger=None, config_filename=None,
                 connect_on_create=True):
        logger = logger or logging.getLogger(__name__)
        logger.debug('Configuring Indi EOS350D Camera')

        if config_filename is None:
            config_filename = './conf_files/IndiASI120MCCamera.json'

        # device related intialization
        IndiCamera.__init__(self, indi_client,
                            config_filename=config_filename)

        # Finished configuring
        self.logger.debug('Configured Indi ASI120MC camera successfully')
        
        # Always use maximum dynamic
        dyn = self.get_dynamic()
        max_dyn = self.get_maximum_dynamic()
        if dyn != max_dyn:
            self.logger.warning(f"Camera {self.name} using format "
                f"{self.get_current_format()} with dynamic {dyn} although it "
                f"is capable of {max_dyn}. Trying to set maximum bit depth")
            self.set_switch("CCD_VIDEO_FORMAT", ["ASI_IMG_RAW16"])
            self.logger.info(f"Now camera {self.name} has format "
                f"{self.get_current_format()} allowing for dynamic "
                f"{self.get_dynamic()}")

    '''
      Indi CCD related stuff
    '''
    def set_cooling_on(self):
        pass

    def set_cooling_off(self):
        pass

    def get_current_format(self):
        return [key for key, val in self.get_switch('CCD_VIDEO_FORMAT').items() if val == "On"]

    def get_maximum_dynamic(self):
        return self.get_number('ADC_DEPTH')['BITS']

    def set_gain(self, value):
        self.set_number('CCD_CONTROLS', {'Gain':value})
        pass

    def get_gain(self):
        return self.get_number('CCD_CONTROLS')['Gain']

    def get_temperature(self):
        return np.nan

    def set_temperature(self, temperature):
        pass
