
# Local stuff
from Imaging.AutoFocuser import AutoFocuser

class IndiAutoFocuser(AutoFocuser):
    """
    Autofocuser with specific commands for indi devices
    """
    def __init__(self, camera, *args, **kwargs,):
        super().__init__(*args, **kwargs, camera=camera)

    ###########################################################################
    # Properties
    ###########################################################################
    @property
    def uid(self):
        """ Serial number of the focuser """
        return self.camera.focuser.name

    @property
    def model(self):
        """ Model of the focuser """
        return self.camera.focuser.name

    @property
    def name(self):
        """ Name of the focuser """
        return self.camera.focuser.name

    @property
    def position(self):
        """ Current encoder position of the focuser """
        return self.camera.focuser.get_position()

    @property
    def min_position(self):
        """ Get position of close limit of focus travel, in encoder units """
        return self.camera.focuser.focus_range["min"]

    @property
    def max_position(self):
        """ Get position of far limit of focus travel, in encoder units """
        return self.camera.focuser.focus_range["max"]

    ##################################################################################################
    # Methods
    ##################################################################################################

    def move_to(self, position):
        """ Move focuser to new encoder position """
        return self.camera.focuser.move_to(position)
