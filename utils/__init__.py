# Generic stuff
import os
import re
import shutil
import subprocess
import time

# Astropy stuff
from astropy import units as u
from astropy.coordinates import AltAz
from astropy.coordinates import ICRS
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astropy.utils import resolve_name

# This is a streamlined variant of PySerial's serialutil.Timeout.
class Timeout(object):
    """Simple timer object for tracking whether a time duration has elapsed.

    Attribute `is_non_blocking` is true IFF the duration is zero.
    """

    def __init__(self, duration):
        """Initialize a timeout with given duration (seconds)."""
        assert duration >= 0
        self.is_non_blocking = (duration == 0)
        self.duration = duration
        self.restart()

    def expired(self):
        """Return a boolean, telling if the timeout has expired."""
        return self.time_left() <= 0

    def time_left(self):
        """Return how many seconds are left until the timeout expires."""
        if self.is_non_blocking:
            return 0
        else:
            delta = self.target_time - time.monotonic()
            if delta > self.duration:
                # clock jumped, recalculate
                self.restart()
                return self.duration
            else:
                return max(0, delta)

    def restart(self):
        """Restart the timed duration."""
        self.target_time = time.monotonic() + self.duration


def listify(obj):
    """ Given an object, return a list

    Always returns a list. If obj is None, returns empty list,
    if obj is list, just returns obj, otherwise returns list with
    obj as single member.

    Returns:
        list:   You guessed it.
    """
    if obj is None:
        return []
    else:
        return obj if isinstance(obj, (list, type(None))) else [obj]


def get_free_space(dir=None):
    if dir is None:
        dir = os.getenv('PANDIR')

    _, _, free_space = shutil.disk_usage(dir)
    free_space = (free_space * u.byte).to(u.gigabyte)
    return free_space


def load_module(module_name):
    """ Dynamically load a module

    Returns:
        module: an imported module name
    """
    try:
        module = resolve_name(module_name)
    except ImportError:
        raise RuntimeError('Module Not Found: {}'.format(module_name))

    return module


def altaz_to_radec(alt, az, location, obstime, *args, **kwargs):
    """ Convert alt/az degrees to RA/Dec SkyCoord

    Args:
        alt (int, optional): Altitude, defaults to 35
        az (int, optional): Azimute, defaults to 90 (east)
        location (None, required): A ~astropy.coordinates.EarthLocation
            location must be passed.
        obstime (None, optional): Time for object, defaults to `current_time`

    Returns:
        `astropy.coordinates.SkyCoord: FK5 SkyCoord
    """
    verbose = kwargs.get('verbose', False)

    if verbose:
        print("Getting coordinates for Alt {} Az {}, from {} at {}".format(
            alt, az, location, obstime))

    altaz = AltAz(obstime=obstime, location=location, alt=alt * u.deg, az=az * u.deg)
    return SkyCoord(altaz.transform_to(ICRS))
