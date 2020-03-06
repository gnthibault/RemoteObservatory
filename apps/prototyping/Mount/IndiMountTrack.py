# Basic stuff
import logging
import logging.config
import sys

# Local stuff : IndiClient
from helper.IndiClient import IndiClient

# Local stuff : Mount
from Mount.IndiMount import IndiMount

#Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

if __name__ == '__main__':
    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    # Instanciate mount with the right parameters
    config = dict(
        mount_name='Telescope Simulator',
        indi_client=dict(
            indi_host="localhost",
            indi_port="7624")
        )
    mount = IndiMount(config=config, connect_on_create=True)

    # Set slew rate to be used afterwards
    sr = mount.get_slew_rate()
    mount.set_slew_rate('4x')
    sr = mount.get_slew_rate()

    # Set track rate to be used afterwards
    tr = mount.get_track_mode()
    mount.set_track_mode('TRACK_SIDEREAL')
    tr = mount.get_track_mode()

    # Get Pier side, not supported by simulator
    #ps = mount.get_pier_side()

    # Unpark if you want something useful to actually happen
    mount.unpark()

    # Do a slew and track
    c = SkyCoord(ra=11.5*u.hour, dec=78.9*u.degree, frame='icrs')
    mount.slew_to_coord_and_track(c)

    # Check coordinates
    c = mount.get_current_coordinates()
    print('Coordinates are now: {}'.format(c))
