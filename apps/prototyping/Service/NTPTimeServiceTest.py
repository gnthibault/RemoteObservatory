# Basic stuff
import logging
import logging.config

# Local stuff : Service
from Service.NTPTimeService import NTPTimeService

if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')
    logger = logging.getLogger('mainLogger')

    # ntp time server
    servTime = NTPTimeService()
    
    print('UTC from NTP is: {}'.format(servTime.get_utc()))
    print('Time from NTP is: {}'.format(servTime.getTimeFromNTP()))
    print('UTC astropy is: {}'.format(servTime.get_astropy_time_from_utc()))
    print('next UTC midnight is: {}'.format(
          servTime.getNextAstropyMidnightInUTC()))

