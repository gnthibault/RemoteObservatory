# Generic
import logging
import time

# Astropy
from astropy import units as u
from astropy.coordinates import EarthLocation
from astropy.coordinates import SkyCoord

# Local
from Base.Base import Base
from utils import error

class AbstractMount(Base):

    """
        From panoptes:
        Abstract Base class for controlling a mount. This provides the basic
        functionality for the mounts. Sub-classes should override the
        `initialize` method for mount-specific issues as well as any helper
        methods specific mounts might need. See "NotImplemented Methods"
        section of this module.

        Sets the following properies:

            - self.non_sidereal_available = False
            - self.PEC_available = False
            - self._is_initialized = False

        Args:
            config (dict):
                Custom configuration passed to base mount. This is usually read
                from the main system config.

            commands (dict):
                Commands for the telescope. These are read from a yaml file
                that maps the mount-specific commands to common commands.

            location (EarthLocation):
                An astropy.coordinates.EarthLocation that contains location
                information.

    """

    def __init__(self, location, serv_time, commands=None, logger=None, *args,
                 **kwargs):
        Base.__init__(self, args, kwargs)
        assert isinstance(location, EarthLocation)

        # Needed for time reference
        self.serv_time = serv_time


        #self.logger.debug("Mount config: {}".format(self.mount_config))

        # Set the initial location
        #self._location = location

        # Initial states
        self._is_connected = False
        self._is_initialized = False

        self._is_slewing = False
        self._is_parked = True
        self._at_mount_park = True
        self._is_tracking = False
        self._is_home = False
        self._state = 'Parked'

        self.sidereal_rate = ((360 * u.degree).to(u.arcsec) /
                              (86164 * u.second))
        self.ra_guide_rate = 0.5  # Sidereal
        self.dec_guide_rate = 0.5  # Sidereal
        self._tracking_rate = 1.0  # Sidereal
        self._tracking = 'Sidereal'
        self._movement_speed = ''

        # Set target coordinates
        self._target_coordinates = None

    def status(self):
        status = {}
        try:
            status['tracking_rate'] = '{:0.04f}'.format(self.tracking_rate)
            status['ra_guide_rate'] = self.ra_guide_rate
            status['dec_guide_rate'] = self.dec_guide_rate
            status['movement_speed'] = self.movement_speed

            current_coord = self.get_current_coordinates()
            if current_coord is not None:
                status['current_ra'] = current_coord.ra
                status['current_dec'] = current_coord.dec

            if self.has_target:
                target_coord = self.get_target_coordinates()
                status['mount_target_ra'] = target_coord.ra
                status['mount_target_dec'] = target_coord.dec
        except Exception as e:
            self.logger.debug('Problem getting mount status: {}'.format(e))

        return status


###############################################################################
# Properties
###############################################################################

    @property
    def location(self):
        """ astropy.coordinates.SkyCoord: The location details for the mount.

        When a new location is set,`_setup_location_for_mount` is called, which
        will update the mount with the current location. It is anticipated the
        mount won't change locations while observing so this should only be done
        upon mount initialization.

        """
        return self._location

    @location.setter
    def location(self, location):
        self._location = location
        # If the location changes we need to update the mount
        self._setup_location_for_mount()

    @property
    def is_connected(self):
        """ bool: Checks the serial connection on the mount to determine if
            connection is open
        """
        return self._is_connected

    @property
    def is_initialized(self):
        """ bool: Has mount been initialied with connection """
        return self._is_initialized

    @property
    def is_parked(self):
        """ bool: Mount parked status. """
        return self._is_parked

    @property
    def is_home(self):
        """ bool: Mount home status. """
        return self._is_home

    @property
    def is_tracking(self):
        """ bool: Mount tracking status.  """
        return self._is_tracking

    @property
    def is_slewing(self):
        """ bool: Mount slewing status. """
        return self._is_slewing

    @property
    def state(self):
        """ bool: Mount state. """
        return self._state

    @property
    def movement_speed(self):
        """ bool: Movement speed when button pressed. """
        return self._movement_speed

    @property
    def has_target(self):
        return self._target_coordinates is not None

    @property
    def tracking_rate(self):
        """ bool: Mount tracking rate """
        return self._tracking_rate

    @tracking_rate.setter
    def tracking_rate(self, value):
        """ Set the tracking rate """
        self._tracking_rate = value

###############################################################################
# Methods
###############################################################################
    def set_park_coordinates(self, ha=-170 * u.degree, dec=-10 * u.degree):
        """ Calculates the RA-Dec for the the park position.

        This method returns a location that points the optics of the unit down
        toward the ground.

        The RA is calculated from subtracting the desired hourangle from the
        local sidereal time. This requires a proper location be set.

        Note:
            Mounts usually don't like to track or slew below the horizon so this
                will most likely require a configuration item be set on the
                mount itself.

        Args:
            ha (Optional[astropy.units.degree]): Hourangle of desired parking
                position. Defaults to -165 degrees.
            dec (Optional[astropy.units.degree]): Declination of desired parking
                position. Defaults to -165 degrees.

        Returns:
            park_skycoord (astropy.coordinates.SkyCoord): A SkyCoord object
                representing current parking position.
        """
        self.logger.debug('Setting park position')

        park_time = self.self.serv_time.getAstropyTimeFromUTC()
        park_time.location = self.location

        lst = park_time.sidereal_time('apparent')
        self.logger.debug("LST: {}".format(lst))
        self.logger.debug("HA: {}".format(ha))

        ra = lst - ha
        self.logger.debug("RA: {}".format(ra))
        self.logger.debug("Dec: {}".format(dec))

        self._park_coordinates = SkyCoord(ra, dec)

        self.logger.debug("Park Coordinates RA-Dec: {}".format(
            self._park_coordinates))

    def get_target_coordinates(self):
        """ Gets the RA and Dec for the mount's current target. This does NOT
            necessarily
        reflect the current position of the mount, see
            `get_current_coordinates`.

        Returns:
            astropy.coordinates.SkyCoord:
        """
        return self._target_coordinates

    def set_target_coordinates(self, coords):
        """ Sets the RA and Dec for the mount's current target.

        Args:
            coords (astropy.coordinates.SkyCoord): coordinates specifying
            target location

        Returns:
            bool:  Boolean indicating success
        """

        # Save the skycoord coordinates
        self.logger.debug("Setting target coordinates: {}".format(coords))
        self._target_coordinates = coords
        return True

    def distance_from_target(self):
        """ Get current distance from target

        Returns:
            u.Angle: An angle represeting the current on-sky separation from
            the target
        """
        target = self.get_target_coordinates().coord
        separation = self.get_current_coordinates().separation(target)

        self.logger.debug("Current separation from target: {}".format(
            separation))

        return separation


###############################################################################
# Movement methods
###############################################################################

    def slew_to_coordinates(self, coords, ra_rate=15.0, dec_rate=0.0):
        """ Slews to given coordinates.

        Note:
            Slew rates are not implemented yet.

        Args:
            coords (astropy.SkyCoord): Coordinates to slew to
            ra_rate (Optional[float]): Slew speed - RA tracking rate in
                arcsecond per second. Defaults to 15.0
            dec_rate (Optional[float]): Slew speed - Dec tracking rate in
                arcsec per second. Defaults to 0.0

        Returns:
            bool: indicating success
        """
        assert isinstance(coords, tuple), self.logger.warning(
            'slew_to_coordinates expects RA-Dec coords')
        response = 0
        if not self.is_parked:
            # Set the coordinates
            if self.set_target_coordinates(coords):
                response = self.slew_to_target()
            else:
                self.logger.warning("Could not set target_coordinates")
        else:
            self.logger.warning("Cannot slew when parked")

        return response

    def home_and_park(self):
        """ Convenience method to first slew to the home position and then park.
        """
        if not self.is_parked:
            self.slew_to_home()
            while self.is_slewing:
                time.sleep(5)
                self.logger.debug("Slewing to home, sleeping for 5 seconds")

            # Reinitialize from home seems to always do the trick of getting
            # us to correct side of pier for parking
            self._is_initialized = False
            self.initialize()
            self.park()

            while self.is_slewing and not self.is_parked:
                time.sleep(5)
                self.logger.debug("Slewing to park, sleeping for 5 seconds")

        self.logger.debug("Mount parked")

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
            self.logger.info("Mount is parked")
        elif not self.has_target:
            self.logger.info("Target Coordinates not set")
        else:
            success = self.query('slew_to_target')
            self.logger.debug("Mount response: {}".format(success))
            if success:
                self.logger.debug('Slewing to target')
            else:
                self.logger.warning('Problem with slew_to_target')

        return success

    def slew_to_home(self):
        """ Slews the mount to the home position.

        Note:
            Home position and Park position are not the same thing

        Returns:
            bool: indicating success
        """
        response = 0

        if not self.is_parked:
            self._target_coordinates = None
            response = self.query('slew_to_home')
        else:
            self.logger.info('Mount is parked')

        return response


    def get_ms_offset(self, offset, axis='ra'):
        """ Get offset in milliseconds at current speed

        Args:
            offset (astropy.units.Angle): Offset in arcseconds

        Returns:
             astropy.units.Quantity: Offset in milliseconds at current speed
        """

        rates = {
            'ra': self.ra_guide_rate,
            'dec': self.dec_guide_rate,
        }

        guide_rate = rates[axis]

        return (offset / (self.sidereal_rate * guide_rate)).to(u.ms)
