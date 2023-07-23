# Numerical stuff
import numpy as np

# Astropy stuff
from astropy.coordinates import get_moon
from astropy.time import Time
from astropy import units as u

# Local stuff
from ObservationPlanner.Scheduler import Scheduler
from utils import listify

# Locally defined constraints
from ObservationPlanner.LocalHorizonConstraint import LocalHorizonConstraint

class DefaultScheduler(Scheduler):

    def __init__(self, ntpServ, obs, config=None, path='.'):
        """ Inherit from the `Base Scheduler` """
        super().__init__(ntpServ, obs, config=config, path=path)


##########################################################################
# Properties
##########################################################################

##########################################################################
# Methods
##########################################################################

    def get_observation(self, time=None, show_all=False,
                        reread_target_file=False):
        """Get a valid observation

        Args:
            time (astropy.time.Time, optional): Time at which scheduler applies,
                defaults to time called
            show_all (bool, optional): Return all valid observations along with
                merit value, defaults to False to only get top value
            reread_fields_file (bool, optional): If the fields file should be
                reread before scheduling occurs, defaults to False.

        Returns:
            tuple or list: A tuple (or list of tuples) with name and score of
            ranked observations
        """
        if reread_target_file:
            self.logger.debug("Rereading target file")
            self.reread_config()

        if time is None:
            time = self.serv_time.get_astropy_time_from_utc() #get_utc()

        # dictionary where key is obs key and value is priority (aka merit)
        # self.current_observation.exp_set_size
        # self.current_observation.current_exp
        # self.current_observation.number_exposures
        # self.current_observation.observing_block
        # if self.current_observation in self.observations.values()
        # self.current_observation.observing_block.number_exposures
        valid_obs = {obs: 1.0 for obs in self.observations}
        best_obs = []
        
        observer = self.obs.getAstroplanObserver()

        for constraint in self.constraints:
            self.logger.info(f"Checking Constraint: {constraint}")
            for obs_key, observation in {k:v for k,v in self.observations.items() if not v.is_done}:
                if obs_key in valid_obs:
                    self.logger.debug(f"\tObservation: {obs_key}")
                    score = constraint.compute_constraint(time, observer,
                        observation.target.coord)
                    # Check if the computed score is a boolean
                    if np.any([isinstance(score, ty) for ty in
                              [bool, np.bool, np.bool_]]):
                        self.logger.debug("\t\tVetoed if false: {}".format(score))
                        # Log vetoed observations
                        if not score:
                            # if not valid, remove from valid_obs
                            del valid_obs[obs_key]
                    else:
                        self.logger.debug('\t\tScore: {:.05f}'.format(score))
                        # if valid, update valid_obs score (def start at 1)
                        valid_obs[obs_key] += score

        # Now add initial priority
        for obs_key, score in valid_obs.items():
            valid_obs[obs_key] = (score +
                self.observations[obs_key].priority)

        # if there are actually valid observation remaining
        if len(valid_obs) > 0:
            # Sort the list by highest score (reverse puts in correct order)
            best_obs = sorted(valid_obs.items(), key=lambda x: x[1])[::-1]

            # Check new best against current_observation
            if (self.current_observation is not None and
                best_obs[0][0] != self.current_observation.id):

                # Favor the current observation if still doable
                end_of_next_set = time + self.current_observation.set_duration
                if self.observation_available(
                        self.current_observation, 
                        Time([time, end_of_next_set])):

                    # If current is better or equal to top, add it to best
                    # but no need to update current_observation
                    if self.current_observation.merit >= best_obs[0][1]:
                        best_obs.insert(0, (self.current_observation.id,
                                            self.current_observation.merit))

            self.current_observation = self.observations[best_obs[0][0]]
            self.current_observation.merit = best_obs[0][1]

        # if valid_obs was empty
        else:
            if self.current_observation is not None:
                # Favor the current observation if still available
                end_of_next_set = time + self.current_observation.set_duration
                if self.observation_available(self.current_observation,
                                              Time([time, end_of_next_set])):

                    self.logger.debug("Reusing {}".format(
                                      self.current_observation))
                    best_obs = [(self.current_observation.id,
                                 self.current_observation.merit)]
                else:
                    self.logger.warning("No valid observations found")
                    self.current_observation = None

        if not show_all and len(best_obs) > 0:
            best_obs = best_obs[0]

        return best_obs


##########################################################################
# Utility Methods
##########################################################################

##########################################################################
# Private Methods
##########################################################################
