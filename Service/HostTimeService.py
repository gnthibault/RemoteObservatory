# Basic stuff
import copy
import json
import logging
import traceback

# Time stuff
from datetime import datetime
from datetime import timedelta 
import pytz
from tzwhere import tzwhere

# Astropy stuff
from astropy import units as u
from astropy.time import Time as ATime

# Local stuff
from Service.BaseService import BaseService

class HostTimeService(BaseService):
    """ HostTimeService: one of the only service class that does not inherit
        from Base, because Base needs a time service. That would generate a
        circular dependency.
        Just in case, we designed a BaseService for this purpose
    """
    DEFAULT_TIMEZONE_STR = 'Europe/Paris'

    def __init__(self, config=None, tz=None):
        """ tz can be obtained by obs.get_time_zone()
        """

        BaseService.__init__(self, config=config)

        try:
            #try to get timezone from config file
            self.gps = dict(latitude = self.config['observatory']['latitude'],
                            longitude = self.config['observatory']['longitude'])
        except:
            self.gps = None

        if tz is not None:
            try:
                utc_test = datetime.utcnow()
                test = utc_test.astimezone(self.timezone)
            except Exception as e:
                self.logger.warning(f"HostTimeService: wrong tz format provided {e}")
                self.tz = None
            else:
                self.tz = tz
        else:
            try:
                timezone_str = self.config['observatory']['timezone']
                self.tz = pytz.timezone(timezone_str)
            except Exception as e:
                try:
                    # Now find the timezone from the gps coordinate
                    tzw = tzwhere.tzwhere()
                    timezone_str = tzw.tzNameAt(self.gps['latitude'],
                                                self.gps['longitude'])
                    self.tz = pytz.timezone(timezone_str)
                except Exception as e:
                    self.logger.warning(f"HostTimeService: cannot get tz from config {e}")
                    self.tz = None

        # Finished configuring
        self.logger.debug('Configured Host Time Service successfully')

    @property
    def timezone(self):
        if self.tz is not None:
            return self.tz
        else:
            return pytz.timezone(self.DEFAULT_TIMEZONE_STR)

    def get_utc(self):
        """
        return: UTC from local computer
        """
        utc=datetime.utcnow()
        return pytz.utc.localize(utc, is_dst=None)

    def get_local_time(self):
        return self.convert_to_local_time(self.get_utc())

    def get_local_date(self):
        return self.get_local_time().date()

    def get_astropy_time_from_utc(self):
        return ATime(self.get_utc())
        #return ATime(self.get_utc(),
        #    location=self.obs.getAstropyEarthLocation())

    def convert_to_local_time(self, utc_time):
        #If naive time, set to utc by default
        if utc_time.tzinfo is None:
            utc_dt = pytz.utc.localize(utc_time, is_dst=None)
        else:
            utc_dt = copy.deepcopy(utc_time)
        return utc_dt.astimezone(self.timezone)

    def convert_to_utc_time(self, local_time):
        #If naive time, set to local by default
        if local_time.tzinfo is None:
            local_dt = self.timezone.localize(local_time, is_dst=None)
        else:
            local_dt = copy.deepcopy(local_time)
        return local_dt.astimezone(pytz.utc)

    def get_next_local_midnight_in_utc(self, target_date=None):
        if target_date is None:
            target_date = self.get_local_time().date()
        midnight = datetime(2000,1,1).time()
        next_midnight = (datetime.combine(target_date, midnight) +
                         timedelta(days=1))
        return self.convert_to_utc_time(next_midnight)

    def get_next_noon_after_next_midnight_in_utc(self, target_date=None):
        next_midnight = self.getNextMidnightInUTC(target_date)
        next_noon = next_midnight + timedelta(hours=12)
        return self.convert_to_utc_time(next_noon)

    def get_astropy_celestial_time(self, longitude=None):
        """ returns approximate sidereal time
        """
        if longitude is None:
            longitude = self.gps['longitude']*u.deg
        utc = self.get_astropy_time_from_utc()
        if self.gps is not None:
            return utc.sidereal_time( kind='apparent',
                longitude=longitude)
        return utc.sidereal_time(kind='apparent')

    def get_jd(self):
        return self.get_astropy_time_from_utc().jd

    def flat_time(self):
        """
            Given an astropy Time, flatten to have no extra chars besides
            integers
        """
        t = self.get_astropy_time_from_utc()
        return t.isot.replace('-', '').replace(':', '').split('.')[0]

