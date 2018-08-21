# Generic stuff
import sys

# Astropy
from astropy.utils.exceptions import AstropyWarning

# Local
from Base import Base


class Error(AstropyWarning, Base):

    """ Base class for Panoptes errors """

    def __init__(self, msg=None, exit=False):
        Base.__init__(self)
        if msg:
            if exit:
                self.exit_program(msg)
            else:
                self.logger.error('{}: {}'.format(self.__class__.__name__, msg))
                self.msg = msg

    def exit_program(self, msg='No reason specified'):
        """ Kills running program """
        print("TERMINATING: {}".format(msg))
        sys.exit(1)


class InvalidSystemCommand(Error):

    """ Error for a system level command malfunction """

    def __init__(self, msg='Problem running system command'):
        super().__init__(msg)


class Timeout(Error):

    """ Error called when an event times out """

    def __init__(self, msg='Timeout waiting for event'):
        super().__init__(msg)


class NoObservation(Error):

    """ Generic no Observation """

    def __init__(self, msg='No valid observations found.'):
        super().__init__(msg)


class NotFound(Error):

    """ Generic not found class """
    pass


class InvalidCollection(NotFound):
    """Error raised if a collection name is invalid."""
    pass


class InvalidConfig(Error):

    """ Error raised if config file is invalid """
    pass


class InvalidCommand(Error):

    """ Error raised if a system command does not run """
    pass


class InvalidMountCommand(Error):

    """ Error raised if attempting to send command that doesn't exist """
    pass


class BadConnection(Error):

    """ Error raised when a connection is bad """
    pass


class BadSerialConnection(Error):

    """ Error raised when serial command is bad """
    pass


class ArduinoDataError(Error):
    """Error raised when there is something very wrong with Arduino information."""
    pass


class MountNotFound(NotFound):

    """ Mount cannot be import """

    def __init__(self, msg='Mount Not Found'):
        self.exit_program(msg=msg)


class CameraNotFound(NotFound):

    """ Camera cannot be imported """
    pass


class DomeNotFound(NotFound):
    """Dome device not found."""
    pass


class SolveError(NotFound):

    """ Camera cannot be imported """
    pass


class TheSkyXError(Error):
    """ Errors from TheSkyX """
    pass


class TheSkyXKeyError(TheSkyXError):
    """ Errors from TheSkyX because bad key passed """
    pass


class TheSkyXTimeout(TheSkyXError):
    """ Errors from TheSkyX because bad key passed """
    pass


class GoogleCloudError(Error):
    """ Errors related to google cloud """
    pass
