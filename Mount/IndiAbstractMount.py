# Basic stuff
import io
import json
import logging
import traceback

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
    def __init__(self, location, serv_time,
                 config=None, connect_on_create=True):

        # device related intialization
        IndiMount.__init__(self, config=config,
                           connect_on_create=False)
        # setup AbstractMount config
        self._setup_abstract_config()
        #Setup AbstractMount
        AbstractMount.__init__(self, location=location,
                               serv_time=serv_time, **config)

        if connect_on_create:
            self.connect()

###############################################################################
# Overriding Properties
###############################################################################

    @property
    def is_parked(self):
        ret = IndiMount.is_parked.fget(self)
        if ret != AbstractMount.is_parked.fget(self):
            self.logger.error('It looks like the software maintained state is'
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
    def connect(self, connect_device=True):  # pragma: no cover
        IndiMount.connect(self, connect_device=connect_device)

    def disconnect(self):
        if not self.is_parked:
            try:
                IndiMount.park(self)
                self._is_parked = True
                self.disconnect()  # Disconnect indi server
            except Exception as e:
                self.logger.warning('Problem with park')
                # by default, we assume that mount is in the "worst" situation

        IndiMount.disconnect(self)

    def initialize(self, *arg, **kwargs):  # pragma: no cover
        self.logger.debug(f"Initializing mount with args {arg}, {kwargs}")
        self.connect()
        self._is_initialized = True

    def park(self):
        """ Slews to the park position and parks the mount.
        Note:
            When mount is parked no movement commands will be accepted.
        Returns:
            bool: indicating success
        """
        self.logger.debug(f"Mount {self.device_name} about to park")
        try:
            if self.is_initialized:
                IndiMount.park(self)
            self._is_parked = True
            self.disconnect() # Disconnect indi server
            self.stop_indi_server()
            self._is_initialized = False
        except Exception as e:
            self.logger.warning('Problem with park')
            # by default, we assume that mount is in the "worst" situation
            self._is_parked = False
            return False
        self.logger.debug(f"Mount {self.device_name} successfully parked")
        return self.is_parked

    def unpark(self):
        """ Unparks the mount. Does not do any movement commands but makes
            them available again.
        Returns:
            bool: indicating success
        """
        self.logger.debug(f"Mount {self.device_name} about to unpark with a reset-like behaviour")
        self.park()
        self.start_indi_server()
        self.start_indi_driver()
        self.connect(connect_device=True)
        self.initialize()
        self._is_initialized = False
        self._is_parked = False
        self.logger.debug(f"Mount {self.device_name} successfully unparked")

    def initialize(self):
        self.logger.debug("Initializing from IndiAbstractMount")
        IndiMount.unpark(self)
        self.logger.debug("Successfully initialized from IndiAbstractMount")

    def slew_to_coord(self, coord):
        self.slew_to_coord_and_track(self, coord)

    def get_current_coordinates(self):
        return IndiMount.get_current_coordinates(self)

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
                self.slew_to_coord_and_track(target)
                success = True
                self._is_slewing = False
                self._is_tracking = True
            except Exception as e:
                self.logger.error(f"Error in slewing to target: {e}, {traceback.format_exc()}")
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
