#Basic stuff
import logging
import json
import io

#Indi stuff
import PyIndi
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
        IndiCamera.__init__(self, indi_client, logger=logger,
                            config_filename=config_filename)

        # Finished configuring
        self.logger.debug('Configured Indi ASI120MC camera successfully')
        
        # Always use maximum dynamic
        dyn = self.get_dynamic()
        max_dyn = self.get_maximum_dynamic()
        if dyn != max_dyn:
            self.logger.warn('Camera {} using format {} with dynamic {} although it is capable '
                             'of {}. Trying to set maximum bit depth'.format(self.name,
                                 self.get_current_format(), dyn, max_dyn))
            self.set_switch('CCD_VIDEO_FORMAT', ['ASI_IMG_RAW16'])
            self.logger.info('Now camera {} has format {} allowing for dynamic {}'.format(
                self.name, self.get_current_format(), self.get_dynamic()))

    '''
      Indi CCD related stuff
    '''
    def set_cooling_on(self):
        pass

    def set_cooling_off(self):
        pass

    def get_current_format(self):
        return [key for key, val in self.get_switch('CCD_VIDEO_FORMAT').items() if val['value']]

    def get_maximum_dynamic(self):
        return self.get_number('ADC_DEPTH')['BITS']['value']

    def set_gain(self, value):
        self.setNumber('CCD_CONTROLS', {'Gain':value})
        pass

    def get_gain(self):
        return self.get_number('CCD_CONTROLS')['Gain']['value']

    def get_temperature(self):
        return np.nan

    def set_temperature(self, temperature):
        pass
