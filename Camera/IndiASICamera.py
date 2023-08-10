# Basic stuff

# Local stuff
from Camera.IndiAbstractCamera import IndiAbstractCamera
from Camera.IndiCamera import IndiCamera

class IndiASICamera(IndiAbstractCamera):
    def __init__(self, serv_time, config=None,
                 connect_on_create=True):

        # Parent initialization
        super().__init__(
            serv_time=serv_time,
            config=config,
            connect_on_create=connect_on_create)

    def prepare_shoot(self):
        # Call parent method
        IndiCamera.prepare_shoot(self)
        # Always use maximum dynamic
        dyn = self.get_dynamic()
        max_dyn = self.get_maximum_dynamic()
        if dyn < max_dyn:
            self.logger.warning(f"Camera {self.name} using format {self.get_current_format()} with dynamic {dyn} although it "
                                f"is capable of {max_dyn}.") #Trying to set maximum bit depth")
            #self.set_switch("CCD_VIDEO_FORMAT", ["ASI_IMG_RAW16"])
            #self.logger.info(f"Now camera {self.name} has format {self.get_current_format()} allowing for dynamic "
            #                 f"{self.get_dynamic()}")

    def get_current_format(self):
        return [key for key, val in self.get_switch('CCD_VIDEO_FORMAT').items() if val == "On"]

    def get_maximum_dynamic(self):
        return self.get_number('ADC_DEPTH')['BITS']

    def set_gain(self, value):
        self.set_number('CCD_CONTROLS', {'Gain': value}, sync=True, timeout=self.defaultTimeout)

    def get_gain(self):
        gain = self.get_number('CCD_CONTROLS')
        return gain["Gain"]

    def set_offset(self, value):
        self.set_number('CCD_CONTROLS', {'Offset': value}, sync=True, timeout=self.defaultTimeout)

    def get_offset(self):
        offset = self.get_number('CCD_CONTROLS')
        return offset["Offset"]

