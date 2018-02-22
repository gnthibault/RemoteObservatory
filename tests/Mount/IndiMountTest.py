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
    c = SkyCoord(ra=11.5*u.hour, dec=78.9*u.degree, frame='icrs')
    mount.slewToCoordAndTrack(c)
    mount.park()
    mount.unPark()

