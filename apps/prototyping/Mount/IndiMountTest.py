# Basic stuff
import logging
import random
import sys

# Local stuff
from helper.IndiClient import IndiClient
from Mount.IndiMount import IndiMount

#Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':

    # test indi client
    indi_config = {
        "indi_host": "localhost",
        "indi_port": 7624
    }
    indi_cli = IndiClient(config=indi_config)

    # Build the Mount
    mount_config = {
        #"mount_name":"Losmandy Gemini"
        "mount_name": "Telescope Simulator",
        "indi_client": indi_config
    }
    mount = IndiMount(config=mount_config)
    # Set slew ret to be used afterwards
    mount.set_slew_rate('3x')
    slew_rate = mount.get_slew_rate()

    # Get Pier side, not supported by simulator
    ps = mount.get_pier_side()

    # Unpark if you want something useful to actually happen
    mount.unpark()
    print(f"Status of the mount for parking is {mount.is_parked}")

    # Do a slew and track
    #JNow: 15h 20m 40s  71° 46' 13"
    #J2000:  15h 20m 43s  71° 50' 02"
    #AzAlt:   332° 12' 25"  61° 48' 28"
    ra = random.randint(0, 12)
    dec = random.randint(-90, 90)
    c = SkyCoord(ra=ra*u.hourangle, dec=dec*u.degree, frame='icrs')
    print("BEFORE SLEWING --------------------------")
    mount.slew_to_coord_and_track(c)
    print("After SLEWING --------------------------")

    # Check coordinates
    c_true = mount.get_current_coordinates()
    print(f"Coordinates are now: ra:{c_true.ra.to(u.hourangle)}, dec:{c_true.dec.to(u.degree)}")
    print(f"Should be: ra:{c.ra.to(u.hourangle)}, dec:{c.dec.to(u.degree)}")

    # Sync
    ra = random.randint(0, 12)
    dec = random.randint(-90, 90)
    c = SkyCoord(ra=ra*u.hour, dec=dec*u.degree, frame='icrs')
    mount.sync_to_coord(c)

    # Set tracking
    mount.set_track_mode(track_mode='TRACK_SIDEREAL')

    #Do a slew and stop
    c = SkyCoord(ra=10*u.hour, dec=60*u.degree, frame='icrs')
    mount.slew_to_coord_and_stop(c)

    # Park before standby
    mount.park()

