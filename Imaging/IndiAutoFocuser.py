
# Local stuff
from Imaging.AutoFocuser import AutoFocuser

class IndiAutoFocuser(AutoFocuser):
    """
    Autofocuser with specific commands for indi devices
    """
    def __init__(self, camera):
        super().__init__(camera)

    ##################################################################################################
    # Methods
    ##################################################################################################

    def move_to(self, position):
        """ Move focuser to new encoder position """
        raise NotImplementedError

