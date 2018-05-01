# Basic stuff
import logging
import logging.config
import threading
import sys

sys.path.append('.')

# Miscellaneous
import io
from astropy.io import fits

# Local stuff : Service
from Service.NTPTimeService import NTPTimeService

# Local stuff : Observatory
from Observatory.ShedObservatory import ShedObservatory

# Local stuff : observation planner
from ObservationPlanner.ObservationPlanner import ObservationPlanner


if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')
    logger = logging.getLogger('mainLogger')

    obs = ShedObservatory(logger=logger)

    # ntp time server
    servTime = NTPTimeService(logger=logger)
    
    # ObservationPlanner
    obsPlanner = ObservationPlanner(logger=logger, ntpServ=servTime, obs=obs)
    #configFileName='test.json')
    print('Target list is {}'.format(obsPlanner.getTargetList()))
    obsPlanner.showObservationPlan()

