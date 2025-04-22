# Basic stuff
import logging
import random

# Astropy
#from astroplan import Observer
from astropy.coordinates import EarthLocation,SkyCoord
from astropy import units as u


# local includes
from Mount.IndiAbstractMountSimulator import IndiAbstractMountSimulator
from helper.IndiClient import IndiClient
from Service.NTPTimeService import HostTimeService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')

def test_indiMount():

    config = dict(
        mount_name="Telescope Simulator",
        equatorial_eod="J2000", # JNOW"
        is_simulator=True,
        simulator_settings=dict(
            switches=dict(
                MOUNT_TYPE=["EQ_GEM"],
                SIM_PIER_SIDE=["PS_ON"])
        ),
        indi_client=dict(
            indi_host="localhost",
            indi_port="7624"),
    )

    # test indi virtual camera class
    location = EarthLocation(
        lat=45,
        lon=5,
        height=450,
    )

    mount = IndiAbstractMountSimulator(location=location,
                              serv_time=HostTimeService(),
                              config=config,
                              connect_on_create=False)
    mount.connect(connect_device=True)

    set_track_mode = "TRACK_SIDEREAL"
    mount.set_track_mode(track_mode=set_track_mode)
    track_mode = mount.get_track_mode()
    assert track_mode == set_track_mode

    set_slew_rate = "3x"
    mount.set_slew_rate(set_slew_rate)
    slew_rate = mount.get_slew_rate()
    assert slew_rate == set_slew_rate

    # Get Pier side, only supported by simulator when connected
    ps = mount.get_pier_side()
    assert 'PIER_WEST' in ps
    assert 'PIER_EAST' in ps

    # Unpark if you want something useful to actually happen
    assert mount.is_parked
    mount.unpark()
    assert not mount.is_parked
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
    assert mount.is_parked
