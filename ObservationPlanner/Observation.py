# Generic
from collections import OrderedDict
import logging

# Astropy
from astropy import units as u

# Local
from Base.Base import Base
from ObservationPlanner.Field import Field


class Observation(Base):

    def __init__(self, observing_block):
        """ An observation of a given target.

        An observation consists of a minimum number of exposures (`min_nexp`)
        that must be taken at a set exposure time (`exp_time`). These exposures
        come in sets of a certain size (`exp_set_size`) where the minimum
        number of exposures  must be an integer multiple of the set size.

        Note:
            An observation may consist of more exposures than `min_nexp` but
            exposures will always come in groups of `exp_set_size`.

        Arguments:

        Keyword Arguments:
        """
        Base.__init__(self)


        assert exp_time > 0.0, self.logger.error('Exposure time (exp_time) '
            'must be greater than 0')

        assert min_nexp % exp_set_size == 0, self.logger.error('Minimum number'
            ' of exposures (min_nexp) must be multiple of set size '
            '(exp_set_size)')

        assert float(priority) > 0.0, self.logger.error('Priority must be 1.0 '
            'or larger')

        self.field = field

        self.current_exp = 0

        self.exp_time = exp_time
        self.min_nexp = min_nexp
        self.exp_set_size = exp_set_size
        self.exposure_list = OrderedDict()

        self.priority = float(priority)

        self._min_duration = self.exp_time * self.min_nexp
        self._set_duration = self.exp_time * self.exp_set_size

        self.pointing_image = None

        self._seq_time = None

        self.merit = 0.0

        self.logger.debug("Observation created: {}".format(self))


###############################################################################
# Properties
###############################################################################

    @property
    def minimum_duration(self):
        """ Minimum amount of time to complete the observation """
        return self._min_duration

    @property
    def set_duration(self):
        """ Amount of time per set of exposures """
        return self._set_duration

    @property
    def name(self):
        """ Name of the `~pocs.scheduler.field.Field` associated with the 
            observation
        """
        return self.field.name

    @property
    def seq_time(self):
        """ The time at which the observation was selected by the scheduler

        This is used for path name construction
        """
        return self._seq_time

    @seq_time.setter
    def seq_time(self, time):
        self._seq_time = time

    @property
    def first_exposure(self):
        """ Return the latest exposure information

        Returns:
            tuple: `image_id` and full path of most recent exposure from the
                    primary camera
        """
        try:
            return list(self.exposure_list.items())[0]
        except IndexError:
            self.logger.warning("No exposure available")

    @property
    def last_exposure(self):
        """ Return the latest exposure information

        Returns:
            tuple: `image_id` and full path of most recent exposure from the
                   primary camera
        """
        try:
            return list(self.exposure_list.items())[-1]
        except IndexError:
            self.logger.warning("No exposure available")


###############################################################################
# Methods
###############################################################################

    def reset(self):
        """Resets the exposure values for the observation """
        self.logger.debug("Resetting observation {}".format(self))

        self.current_exp = 0
        self.merit = 0.0
        self.seq_time = None

    def status(self):
        """ Observation status

        Returns:
            dict: Dictonary containing current status of observation
        """

        try:
            equinox = self.field.coord.equinox.value
        except AttributeError:
            equinox = self.field.coord.equinox
        except Exception as e:
            equinox = 'J2000'

        status = {
            'current_exp': self.current_exp,
            'dec_mnt': self.field.coord.dec.value,
            'equinox': equinox,
            'exp_set_size': self.exp_set_size,
            'exp_time': self.exp_time.value,
            'field_dec': self.field.coord.dec.value,
            'field_name': self.name,
            'field_ra': self.field.coord.ra.value,
            'merit': self.merit,
            'min_nexp': self.min_nexp,
            'minimum_duration': self.minimum_duration.value,
            'priority': self.priority,
            'ra_mnt': self.field.coord.ra.value,
            'seq_time': self.seq_time,
            'set_duration': self.set_duration.value,
        }

        return status


###############################################################################
# Private Methods
###############################################################################

    def __str__(self):
        return ('{}: {} exposures in blocks of {}, minimum {}, priority '
                '{:.0f}'.format(self.field, self.exp_time, self.exp_set_size,
                                self.min_nexp, self.priority))
