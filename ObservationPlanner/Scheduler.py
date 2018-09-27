#Generic stuff
from collections import OrderedDict
import json
import logging
import os

# Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

# Astroplan stuff
from astroplan import FixedTarget
from astroplan import is_observable
from astroplan import Observer
from astroplan import ObservingBlock

# Local stuff
from Base.Base import Base
#from ObservationPlanner.ObservationPlanner import ObservationPlanner
from ObservationPlanner.Observation import Observation


class Scheduler(Base):

    # Max value for which a scheduling slot is programmed, otherwise
    # we split into smaller slots
    MaximumSlotDurationSec = 300

    def __init__(self, ntpServ, obs, config_file_name=None, path='.'):
        """Loads `~pocs.scheduler.field.Field`s from a field

        Note:
            We convert the targetList from the config file into a list of
            observations

            Further `Observations` should be added directly via the
            `add_observation` method.

        Args:
            obs : The observatory, provides the physical location the
                scheduling will take place from.
            fields_list (list, optional): A list of valid field configurations.
            config_file (str): YAML file containing field parameters.
            constraints (list, optional): List of `Constraints` to apply to each
                observation.
            *args: Arguments to be passed to `PanBase`
            **kwargs: Keyword args to be passed to `PanBase`

            Description of some attributes:

        current_observation:    
        The observation that is currently selected by the scheduler
        Upon setting a new observation the `seq_time` is set to the current time
        and added to the `observed_list`. An old observation is reset (so that
        it can be used again - see `~pocs.scheduler.observation.reset`). If the
        new observation is the same as the old observation, nothing is done. The
        new observation can also be set to `None` to specify there is no current
        observation.
        """

        Base.__init__(self)

        if config_file_name is None:
            self.config_file_name = './conf_files/TargetList.json'
        else:
            self.config_file_name = config_file_name

        self.obs = obs
        self.serv_time = ntpServ
        self.target_list = dict()
        self.observations = dict()
        self._current_observation = None
        self.observed_list = OrderedDict()
        self.constraints = []

        # Initialize obse planner, that does the main job
        #self.obs_planner = ObservationPlanner(ntpServ, obs, config_file, path)

        # Initialize a list of targets
        self.initialize_target_list()


##########################################################################
# Properties
##########################################################################

    @property
    def has_valid_observations(self):
        return len(self.observations.keys()) > 0

    @property
    def has_valid_observations(self):
        return len(self.observations.keys()) > 0

    @property
    def current_observation(self):
        """The observation that is currently selected by the scheduler

        Upon setting a new observation the `seq_time` is set to the current time
        and added to the `observed_list`. An old observation is reset (so that
        it can be used again - see `~pocs.scheduelr.observation.reset`). If the
        new observation is the same as the old observation, nothing is done. The
        new observation can also be set to `None` to specify there is no current
        observation.
        """
        return self._current_observation

    @current_observation.setter
    def current_observation(self, new_observation):
        if self.current_observation is None:
            # If we have no current observation but do need a new one, set
            # seq_time and add to the list
            if new_observation is not None:
                # Set the new seq_time for the observation
                new_observation.seq_time = self.serv_time.flat_time()

                # Add the new observation to the list
                self.observed_list[new_observation.seq_time] = new_observation
        else:
            # If no new observation, simply reset the current
            if new_observation is None:
                self.current_observation.reset()
            else:
                # If we have a new observation, check if same as old observation
                if self.current_observation.id != new_observation.id:
                    self.current_observation.reset()
                    new_observation.seq_time = self.serv_time.flat_time()

                    # Add the new observation to the list
                    self.observed_list[new_observation.seq_time] = (
                        new_observation)

        self.logger.info("Setting new observation to {}".format(
            new_observation))
        self._current_observation = new_observation

##########################################################################
# Methods
##########################################################################

    def clear_available_observations(self):
        """Reset the list of available observations"""
        # Clear out existing list and observations
        self.current_observation = None
        self.observations = {}

    def get_observation(self, time=None, show_all=False):
        """Get a valid observation

        Args:
            time (astropy.time.Time, optional): Time at which scheduler applies,
                defaults to time called
            show_all (bool, optional): Return all valid observations along with
                merit value, defaults to False to only get top value

        Returns:
            tuple or list: A tuple (or list of tuples) with name and score of ranked observations
        """
        raise NotImplementedError

    def status(self):
        return {
            #'constraints': self.constraints,
            'current_observation': self.current_observation,
        }

    def reset_observed_list(self):
        """Reset the observed list """
        self.logger.debug('Resetting observed list')
        self.observed_list = OrderedDict()

    def observation_available(self, observation, time_range):
        """Check if observation is available at given time

        Args:
            observation (pocs.scheduler.observation): An Observation object
            time (astropy.time.Time): The time at which to check observation

        """
        return  is_observable(self.constraints,
                              self.obs.getAstroplanObserver(),
                              [observation.observing_block.target],
                              time_range=time_range)


    def add_observation(self, observing_block):
        """Adds an `Observation` to the scheduler
        Args:
            target_name (str): Name of the target, should be referenced in a
                               catalog (star, sky object, ...)
        """

        try:
            observation = Observation(observing_block)
        except Exception as e:
            self.logger.warning('Skipping invalid observing_block: {}'.format(
                                observing_block))
            self.logger.warning(e)
        else:
            self.observations[observation.id] = observation

    def initialize_target_list(self):
        """Reads the field file and creates valid `Observations` """
        if self.config_file_name is not None:
            self.logger.debug('Reading target lists from file: {}'.format(
                              self.config_file_name))

            if not os.path.exists(self.config_file_name):
                raise FileNotFoundError

            # Get config from json
            with open(self.config_file_name) as json_file:
                self.target_list = json.load(json_file)
                self.logger.debug('Target list: {}'.format(self.target_list))

        # Now add observation to the list
        if self.target_list is None:
            self.logger.warning('Target list seems to be empty')
            return

        #TODO TN readout time, get that info from camera
        camera_time = 1*u.second
        for target_name, config in self.target_list.items():
            #target = FixedTarget.from_name(target_name)
            target = FixedTarget(SkyCoord(5.33*u.deg, 46.0*u.deg))
            for filter_name, (count, exp_time_sec) in config.items():
                # We split big observing blocks into smaller blocks for better
                # granularity
                while count > 0:
                    l_count = max(1, min(count,
                        self.MaximumSlotDurationSec//exp_time_sec))
                    exp_time = exp_time_sec*u.second
                
                    #TODO TN retrieve priority from the file ?
                    priority = 0 if (filter_name=='Luminance') else 1

                    try:
                        b = ObservingBlock.from_exposures(
                                target, priority, exp_time, l_count,
                                camera_time,
                                configuration={'filter': filter_name},
                                constraints=self.constraints)
                        self.add_observation(b)
                        count -= l_count
                
                    except AssertionError as e:
                        self.logger.debug("Error whil adding target : {}"
                                          "".format(e))

##########################################################################
# Utility Methods
##########################################################################

##########################################################################
# Private Methods
##########################################################################
