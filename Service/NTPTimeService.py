# Basic stuff
import copy
import json
import logging
import traceback

# Time stuff
from datetime import datetime
from datetime import timedelta 
import ntplib
import pytz
from tzwhere import tzwhere

# Astropy stuff
from astropy import units as u
from astropy.time import Time as ATime

# Local stuff
from Service.HostTimeService import HostTimeService

class NTPTimeService(HostTimeService):
    """ NTPTime Service: one of the only service class that does not inherit
        from Base, because Base needs a time service. That would generate a
        circular dependency.
        Just in case, we designed a BaseService for this purpose
    """

    def __init__(self, config=None, tz=None):
        """ tz can be obtained by obs.get_time_zone()
        """

        super().__init__(config=config, tz=tz)

        # Get ntp server from config
        cfg = self.config['ntp']
        self.logger.debug('NTPTimeservice config: {}'.format(cfg))
        self.ntpserver = cfg['ntpserver']

        # Finished configuring
        self.logger.debug('Configured NTP Time Service successfully')

    def get_time_stamp_from_ntp(self):
        cli = ntplib.NTPClient()
        res = cli.request(self.ntpserver, version=3, timeout=5)
        return res.tx_time

    def get_utc(self):
        try:
            res = self.get_time_stamp_from_ntp()
            utc = datetime.utcfromtimestamp(res)
            self.logger.debug('NTP Time Service got UTC from server {} : {}'
                              .format(self.ntpserver,utc))
            return pytz.utc.localize(utc, is_dst=None)
        except Exception as e:
            utc = super().get_utc()
            self.logger.error(f"NTP Time Service cannot get UTC from server "
                              f"{self.ntpserver}, because of error : {e}, got "
                              f"UTC from local clock instead: {utc}")
            return utc
