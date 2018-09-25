# Astropy stuff
from astropy.coordinates import get_moon
from astropy.time import Time
from astropy import units as u

#Might have to delete after refactoring with ObservationPlanner
from astroplan.constraints import AtNightConstraint
from astroplan.constraints import AirmassConstraint
from astroplan.constraints import TimeConstraint
from astroplan.constraints import MoonSeparationConstraint

# Local stuff
from ObservationPlanner.Scheduler import Scheduler
from utils import listify


class DefaultScheduler(Scheduler):

    def __init__(self, ntpServ, obs, config_file_name=None, path='.'):
        """ Inherit from the `Base Scheduler` """
        Scheduler.__init__(self, ntpServ, obs, config_file_name=None, path='.')

        self.constraints = [
            AirmassConstraint(max=3, boolean_constraint=True),
            AtNightConstraint.twilight_astronomical(),
            MoonSeparationConstraint(min=45*AU.deg),
            LocalHorizonConstraint(horizon=self.obs.get_horizon(),
                                           boolean_constraint=True)]

##########################################################################
# Properties
##########################################################################

##########################################################################
# Methods
##########################################################################

    def get_observation(self, time=None, show_all=False, reread_target_file=False):
        """Get a valid observation

        Args:
            time (astropy.time.Time, optional): Time at which scheduler applies,
                defaults to time called
            show_all (bool, optional): Return all valid observations along with
                merit value, defaults to False to only get top value
            reread_fields_file (bool, optional): If the fields file should be reread
                before scheduling occurs, defaults to False.

        Returns:
            tuple or list: A tuple (or list of tuples) with name and score of ranked observations
        """
        if reread_fields_file:
            self.logger.debug("Rereading target file")
            self.initialize_target_list()

        if time is None:
            time = self.ntpServ.getUTCFromNTP()

        valid_obs = {obs: 1.0 for obs in self.observations}
        best_obs = []
        
        observer = self.obs.getAstroplanObserver()

        common_properties = {
            'end_of_night': observer.tonight(time=time, horizon=-18 * u.degree)[-1],
            'moon': get_moon(time, observer.location),
            'observed_list': self.observed_list
        }

        for constraint in self.constraints:
            self.logger.info("Checking Constraint: {}".format(constraint))
            for obs_name, observation in self.observations.items():
                if obs_name in valid_obs:
                    self.logger.debug("\tObservation: {}".format(obs_name))

                    veto, score = constraint.get_score(
                        time, observer, observation, **common_properties)

                    self.logger.debug("\t\tScore: {:.05f}\tVeto: {}".format(score, veto))

                    if veto:
                        self.logger.debug("\t\t{} vetoed by {}".format(obs_name, constraint))
                        del valid_obs[obs_name]
                        continue

                    valid_obs[obs_name] += score

        # Now add initial priority
        for obs_name, score in valid_obs.items():
            valid_obs[obs_name] += self.observations[obs_name].priority

        if len(valid_obs) > 0:
            # Sort the list by highest score (reverse puts in correct order)
            best_obs = sorted(valid_obs.items(), key=lambda x: x[1])[::-1]
            top_obs = best_obs[0]

            # Check new best against current_observation
            if (self.current_observation is not None and
                    self.observation[top_obs[0]].name !=
                        self.current_observation.name):

                # Favor the current observation if still available
                end_of_next_set = time + self.current_observation.set_duration
                if self.observation_available(
                        self.current_observation, 
                        Time([time, end_of_next_set])):

                    # If current is better or equal to top, use it
                    if self.current_observation.merit >= top_obs[1]:
                        best_obs.insert(0, self.current_observation)

            # Set the current
            self.current_observation = self.observations[top_obs[0]]
            self.current_observation.merit = top_obs[1]
        else:
            if self.current_observation is not None:
                # Favor the current observation if still available
                end_of_next_set = time + self.current_observation.set_duration
                if self.observation_available(self.current_observation,
                                              Time([time, end_of_next_set])):

                    self.logger.debug("Reusing {}".format(
                                      self.current_observation))
                    best_obs = [(self.current_observation.name,
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
