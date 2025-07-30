# Basic stuff
import logging
import random
import sys

# Local stuff
from Mount.Indi10Micron import Indi10Micron
from Service.HostTimeService import HostTimeService

#Astropy stuff
from astropy import units as u
from astropy.coordinates import EarthLocation
from astropy.coordinates import SkyCoord

logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':

    # Build the Mount
    mount_config = dict(
        module="Indi10Micron",
        mount_name="LX200 10micron",
        equatorial_eod="J2000",  # JNOW
        indi_client=dict(
            indi_host="192.168.8.202",
            indi_port=7624))

    mount = Indi10Micron(config=mount_config,
                    location=EarthLocation(lat=43.00 * u.deg,
                                           lon=5.5 * u.deg,
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
    #ra = 15.9
    #dec = 9
    #c = SkyCoord(ra=ra*u.hourangle, dec=dec*u.degree, frame='icrs')
    c = SkyCoord.from_name("Vega")
    print("BEFORE SLEWING --------------------------")
    mount.set_slew_rate('3x')
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

