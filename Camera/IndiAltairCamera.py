# Basic stuff

# Local stuff
from Camera.IndiAbstractCamera import IndiAbstractCamera
from Camera.IndiCamera import IndiCamera

class IndiAltairCamera(IndiAbstractCamera):
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
            #self.set_switch("CCD_CAPTURE_FORMAT", ["INDI_MONO_16"])
            #self.logger.info(f"Now camera {self.name} has format {self.get_current_format()} allowing for dynamic "
            #                 f"{self.get_dynamic()}")

    def get_current_format(self):
        return [key for key, val in self.get_switch('CCD_CAPTURE_FORMAT').items() if val == "On"]

    def get_maximum_dynamic(self):
        return 16

    def set_gain(self, value):
        self.set_number('CCD_CONTROLS', {'Gain': value}, sync=True, timeout=self.timeout)

    def get_gain(self):
        gain = self.get_number('CCD_CONTROLS')
        return gain["Gain"]
