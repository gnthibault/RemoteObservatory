# Generic
from collections import OrderedDict
import logging

# Astropy
from astropy import units as u

# Local
from Base.Base import Base

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

        # Initialize thyself
        self.observing_block = observing_block
        self.current_exp = 0
        self.merit = 0 #Merit is != priority: highest is scheduled first
        self.exp_set_size = self.number_exposures
        #self.exp_time = exp_time
        #self.min_nexp = min_nexp
        self.exposure_list = OrderedDict()
        self.pointing_list = OrderedDict()
        self.pointing_image = None
        self.adjust_pointing_image = None
        self._seq_time = None
        self.id = self.name+'_'+str(hash(self))

        self.logger.debug(f"Observation created: {self}")


###############################################################################
# Properties
###############################################################################

    @property
    def set_duration(self):
        """ Amount of time per set of exposures """
        return (self.number_exposures *
                self.time_per_exposure)

    @property
    def configuration(self):
        return self.observing_block.configuration

    @property
    def name(self):
        """ Name of the `~pocs.scheduler.field.Field` associated with the 
            observation
        """
        name = self.observing_block.target.name
        return name if name else 'default_target_name'

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
    def is_done(self):
        """ Return True if at least one block has been completed

        Returns:
            bool: True if at least one block has been completed
        """
        return self.current_exp >= self.number_exposures

    @property
    def first_exposure(self):
        """ Return the latest exposure information

        Returns:
            tuple: `image_id` and full path of most recent exposure from an acquisition camera
        """
        try:
            return list(self.exposure_list.items())[0]
        except IndexError:
            self.logger.warning("No exposure available")

    @property
    def last_exposure(self):
        """ Return the latest exposure information

        Returns:
            tuple: `image_id` and full path of most recent exposure from an acquisition camera
        """
        try:
            return list(self.exposure_list.items())[-1]
        except IndexError:
            self.logger.warning("No exposure available")

    @property
    def last_pointing(self):
        """ Return the latest exposure information

        Returns:
            tuple: `image_id` and full path of most recent exposure from the
                   pointing camera
        """
        try:
            return list(self.pointing_list.items())[-1]
        except IndexError:
            self.logger.warning("No pointing available")

    @property
    def time_per_exposure(self):
        return self.observing_block.time_per_exposure

    @property
    def number_exposures(self):
        return self.observing_block.number_exposures

    @property
    def target(self):
        return self.observing_block.target

    @property
    def priority(self):
        return self.observing_block.priority

###############################################################################
# Methods
###############################################################################

    def reset(self):
        """Resets the exposure values for the observation
        """
        self.logger.debug(f"Resetting observation {self}")

        self.current_exp = 0
        self.merit = 0.0
        self.seq_time = None

    def status(self):
        """ Observation status

        Returns:
            dict: Dictonary containing current status of observation
        """

        try:
            equinox = self.target.coord.equinox.value
        except AttributeError:
            equinox = self.target.coord.equinox
        except Exception as e:
            equinox = 'J2000'

        status = {
            'current_exp': self.current_exp,
            'equinox': equinox,
            'number_exposure': self.number_exposures,
            'time_per_exposure': self.time_per_exposure.to(u.second).value,
            'total_exposure': self.set_duration.to(u.second).value,
            'field_name': self.name,
            'field_ra': self.target.coord.ra.to(u.deg).value,
            'field_ha': self.target.coord.ra.to(u.hourangle).value,
            'field_dec': self.target.coord.dec.to(u.deg).value,
            'merit': self.merit,
            'priority': self.priority,
            'seq_time': self.seq_time,
        }

        return status


###############################################################################
# Private Methods
###############################################################################

    def __str__(self):
        return (f"{self.target}: {self.number_exposures} exposures, time per exposure {self.time_per_exposure}, "
                f"priority {self.priority}")
