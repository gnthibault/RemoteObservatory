# Basic stuff
import io
import json
import logging
import traceback

# Indi stuff
import PyIndi

# Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord, FK5
from astropy.time import Time

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
    def __init__(self, indi_client, location, serv_time,
                 config=None, connect_on_create=True):

        # device related intialization
        IndiMount.__init__(self, indi_client=indi_client,
                           config=config, 
                           connect_on_create=False)
        # setup AbstractMount config
        self._setup_abstract_config()
        #Setup AbstractMount
        AbstractMount.__init__(self, location=location,
                               serv_time=serv_time)

        if connect_on_create:
            self.connect()

###############################################################################
# Overriding Properties
###############################################################################

    @property
    def is_parked(self):
        ret = IndiMount.is_parked.fget(self)
        if ret != AbstractMount.is_parked.fget(self):
            self.logger.error('It looks like the software maintained stated is'
                              ' different from the Indi maintained state')
        return ret

    @property
    def non_sidereal_available(self):
        return self._non_sidereal_available

    @non_sidereal_available.setter
    def non_sidereal_available(self, val):
        self._non_sidereal_available = val

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
    def connect_driver(self):  # pragma: no cover
        IndiMount.connect_driver(self)

    def connect(self):  # pragma: no cover
        IndiMount.connect(self)
        self._is_connected = True

    def disconnect(self):
        if not self.is_parked:
            self.park()

        self._is_connected = False

    def initialize(self, *arg, **kwargs):  # pragma: no cover
        self.logger.debug('Initializing mount with args {}, {}'.format(
                          arg, kwargs))
        self.connect()
        self._is_initialized = True

    def park(self):
        """ Slews to the park position and parks the mount.
        Note:
            When mount is parked no movement commands will be accepted.
        Returns:
            bool: indicating success
        """
        try:
            IndiMount.park(self)
            self._is_parked = True
        except Exception as e:
            self.logger.warning('Problem with park')
            # by default, we assume that mount is in the "worst" situation
            self._is_parked = False
            return False

        return self.is_parked

    def unpark(self):
        """ Unparks the mount. Does not do any movement commands but makes
            them available again.
        Returns:
            bool: indicating success
        """
        IndiMount.unpark(self)
        self._is_parked = False

    def slew_to_target(self):
        """ Slews to the current _target_coordinates

        Args:
            on_finish(method):  A callback method to be executed when mount has
            arrived at destination

        Returns:
            bool: indicating success
        """
        success = False

        if self.is_parked:
            self.logger.warning("Mount is parked, cannot slew")
        elif not self.has_target:
            self.logger.warning("Target Coordinates not set, cannot slew")
        else:
            try:
                was_tracking = self.is_tracking
                was_slewing = self.is_slewing
                self._is_tracking = False
                self._is_slewing = True

                target = self.get_target_coordinates()
                IndiMount.slew_to_coord_and_track(self,
                    self.get_target_coordinates())
                success = True
                self._is_slewing = False
                self._is_tracking = True
            except Exception as e:
                self.logger.error("Error in slewing to target: {}, {}"
                    "".format(e, traceback.format_exc()))
                self._is_slewing = was_slewing
                self._is_tracking = was_tracking
                success = False
        return success

###############################################################################
# Monitoring related stuff
###############################################################################

    def __str__(self):
        return 'Mount: {}'.format(self.device_name)

    def __repr__(self):
        return self.__str__()
