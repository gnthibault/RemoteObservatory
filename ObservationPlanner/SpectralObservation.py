# Generic
from collections import OrderedDict
import logging

# Astropy
from astropy import units as u

# Local
from ObservationPlanner.Observation import Observation

class SpectralObservation(Observation):

    def __init__(self,
                 observing_block,
                 exp_set_size=None,
                 is_reference_observation=False):
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
        super().__init__(observing_block=observing_block,
                         exp_set_size=exp_set_size)

        # Important to know if corresponds to a reference acquisition or not
        self.is_reference_observation=is_reference_observation
        self.reference_observation_id = None

        # Initialize thyself
        self.logger.debug(f"SpectralObservation created: {self}")


###############################################################################
# Properties
###############################################################################

###############################################################################
# Methods
###############################################################################
