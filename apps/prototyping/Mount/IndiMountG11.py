# Basic stuff
import logging
import random
import sys

# Local stuff
from Mount.IndiG11 import IndiG11
from Service.HostTimeService import HostTimeService

#Astropy stuff
from astropy import units as u
from astropy.coordinates import EarthLocation
from astropy.coordinates import SkyCoord

logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':

    # Build the Mount
    mount_config = dict(
        module="IndiG11",
        mount_name="Losmandy Gemini",
        equatorial_eod="J2000",  # JNOW
        indi_client=dict(
            indi_host="localhost",
            indi_port=7625))

    mount = IndiG11(config=mount_config,
                    location=EarthLocation(lat=45.67 * u.deg,
                                           lon=5.67 * u.deg,
                                           height=550 * u.m),
                    serv_time=HostTimeService())
    mount.connect(connect_device=True)
    # Get Pier side, not supported by simulator
    ps = mount.get_pier_side()

    # Unpark if you want something useful to actually happen
    mount.unpark()
    print(f"Status of the mount for parking is {mount.is_parked}")

    # Do a slew and track
    #JNow: 15h 20m 40s  71° 46' 13"
    #J2000:  15h 20m 43s  71° 50' 02"
    #AzAlt:   332° 12' 25"  61° 48' 28"
    ra = 20
    dec = 45
    c = SkyCoord(ra=ra*u.hourangle, dec=dec*u.degree, frame='icrs')
    print("BEFORE SLEWING --------------------------")
    mount.slew_to_coord_and_track(c)
    print("After SLEWING --------------------------")

    # Check coordinates
    c_true = mount.get_current_coordinates()
    print(f"Coordinates are now: ra:{c_true.ra.to(u.hourangle)}, dec:{c_true.dec.to(u.degree)}")
    print(f"Should be: ra:{c.ra.to(u.hourangle)}, dec:{c.dec.to(u.degree)}")

    # Set tracking
    mount.set_track_mode(track_mode='TRACK_SIDEREAL')

    # Park before standby
    mount.park()

