# Basic stuff
import io
import json
import logging

# Indi stuff
import PyIndi

# Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord
#c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')

# Local stuff
from Mount.AbstractMount import AbstractMount
from Mount.IndiMount import IndiMount

class IndiAbstractMount(IndiMount, AbstractMount):
    """
        We recall that, with indi, telescopes should be adressed using JNow
        coordinates, see:
        http://indilib.org/develop/developer-manual/101-standard-properties.html#h3-telescopes

        EQUATORIAL_EOD_COORD:
        Equatorial astrometric epoch of date coordinate
        RA JNow RA, hours
        DEC JNow Dec, degrees +N
        
        EQUATORIAL_COORD:
        Equatorial astrometric J2000 coordinate:
        RA  J2000 RA, hours
        DEC J2000 Dec, degrees +N
        
        HORIZONTAL_COORD:
        topocentric coordinate
        ALT Altitude, degrees above horizon
        AZ Azimuth, degrees E of N
    """
    def __init__(self, indiClient, location, serv_time, logger=None,
                 configFileName=None):
        logger = logger or logging.getLogger(__name__)
        

        # device related intialization
        IndiMount.__init__(self, indiClient=indiClient, logger=logger,
                           configFileName=configFileName, connectOnCreate=False)
        # setup AbstractMount config
        self._setup_abstract_config()
        #Setup AbstractMount
        AbstractMount.__init__(self, location=location, serv_time=serv_time,
                               logger=logger)



###############################################################################
# Overriding Properties
###############################################################################

    @property
    def is_parked(self):
        ret = IndiMount.is_parked(self)
        if ret != AbstractMount.is_parked(self):
            self.logger.error('It looks like the software maintained stated is'
                              ' different from the Indi maintained state')
        return ret

    @property
    def non_sidereal_available(self):
        return vself._non_sidereal_available

    @non_sidereal_available.setter
    def non_sidereal_available(self, val):
        self._non_sidereal_available = val

    @property #Todo TN, check how to do this in INDI
    def PEC_available(self):
        return self._PEC_available

    @PEC_available.setter
    def PEC_available(self, val):
        self._PEC_available = val

###############################################################################
# Overriding methods for efficiency/consistency
###############################################################################


###############################################################################
# Parameters
###############################################################################

    def _setup_abstract_config(self):
        self.mount_config = {}

###############################################################################
# Mandatory overriden methods
###############################################################################
    def connect(self):  # pragma: no cover
        IndiMount.connect(self)

    def initialize(self, *arg, **kwargs):  # pragma: no cover
        self.logger.debug('initialize, {}, {}'.format(arg, kwargs))
        self._is_initialized = True

    def set_tracking_rate(self, direction='ra', delta=1.0):
        """Sets the tracking rate for the mount """
        self.logger.debug('set_tracking_rate, {}, {}'.format(direction, delta))

    def write(self, cmd):
        self.logger.debug('write {}'.format(cmd))

    def read(self, *args):
        self.logger.debug('read {}'.format(args))

    def _setup_location_for_mount(self):  # pragma: no cover
        """ Sets the current location details for the mount. """
        self.logger.debug('_setup_location_for_mount')

    def _setup_commands(self, commands):  # pragma: no cover
        """ Sets the current location details for the mount. """
        self.logger.debug('_setup_commands {}'.format(commands))

    def _set_zero_position(self):  # pragma: no cover
        """ Sets the current position as the zero (home) position. """
        self.logger.debug('_set_zero_position')

    def _get_command(self, cmd, params=None):  # pragma: no cover
        self.logger.debug('_get_command {}, {}'.format(cmd, params))
        return 'command for {}({})'.format(cmd, params)

    def _mount_coord_to_skycoord(self):  # pragma: no cover
        self.logger.debug('_mount_coord_to_skycoord')

    def _skycoord_to_mount_coord(self):  # pragma: no cover
        self.logger.debug('_skycoord_to_mount_coord')

###############################################################################
# Monitoring related stuff
###############################################################################

    def __str__(self):
        return 'Mount: {}'.format(self.deviceName)

    def __repr__(self):
        return self.__str__()
