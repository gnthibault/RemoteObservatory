# Basic stuff
import logging
import logging.config
import sys

sys.path.append('.')

# Local stuff : IndiClient
from helper.IndiClient import IndiClient

# Local stuff : Mount
from Mount.IndiVirtualMount import IndiVirtualMount

#Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')
    logger = logging.getLogger('mainLogger')

    # test indi client
    indiCli = IndiClient(logger=logger)
    indiCli.connect()

    # Now test Mount
    mount = IndiVirtualMount(logger=logger, indiClient=indiCli,
                             configFileName=None, connectOnCreate=True)
    mount.set_slew_rate('SLEW_FIND')

    # Do a slew and track
    c = SkyCoord(ra=11.5*u.hour, dec=78.9*u.degree, frame='icrs')
    mount.slew_to_coord_and_track(c)

    # Sync
    c = SkyCoord(ra=11.53*u.hour, dec=79*u.degree, frame='icrs')
    mount.sync_to_coord(c)

    #Do a slew and stop
    c = SkyCoord(ra=10*u.hour, dec=60*u.degree, frame='icrs')
    mount.slew_to_coord_and_stop(c)

    #Park/unpark
    mount.park()
    mount.unPark()
