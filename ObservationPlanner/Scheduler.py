#Generic stuff
from collections import OrderedDict
import json
import logging
import os

# Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time

# Astroplan stuff
from astroplan import FixedTarget
from astroplan import is_observable
from astroplan import Observer
from astroplan import ObservingBlock

#Might have to delete after refactoring with ObservationPlanner
from astroplan.constraints import AtNightConstraint
from astroplan.constraints import AirmassConstraint
from astroplan.constraints import TimeConstraint
from astroplan.constraints import MoonSeparationConstraint
from ObservationPlanner.LocalHorizonConstraint import LocalHorizonConstraint

# Local stuff
from Base.Base import Base
#from ObservationPlanner.ObservationPlanner import ObservationPlanner
from ObservationPlanner.Observation import Observation
from utils import is_jsonable
from utils.config import load_config
from utils.config import save_config

class Scheduler(Base):

    # Max value for which a scheduling slot is programmed, otherwise
    # we split into smaller slots
    MaximumSlotDurationSec = 60 * 20 * u.second

    def __init__(self, ntpServ, obs, config=None, path='.'):
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

        super().__init__()

        self.obs = obs
        self.serv_time = ntpServ
        self.observations = dict()
        self._current_observation = None
        self.observed_list = OrderedDict()
        self.calibrated_list = OrderedDict()
        self.constraints = []

        if config is None:
            self.read_config()
        else:
            self.config = config

        self.logger.debug('Config: {}'.format(self.config))

        # Initialize obs planner, that does the main job
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

        self.logger.info(f"Setting new observation to {new_observation}")
        self._current_observation = new_observation

##########################################################################
# Methods
##########################################################################

    def read_config(self):
        self.config = load_config(config_files=['targets'])

    def reread_config(self):
        self.read_config()
        # Initialize a list of targets
        self.initialize_target_list()

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
            tuple or list: A tuple (or list of tuples) with name and score of
            ranked observations
        """
        raise NotImplementedError

    def status(self):
        status =  {
            'constraints': {str(type(i)):(i.__dict__ if is_jsonable(i.__dict__) else "") for i in self.constraints}
        }
        if self.current_observation is not None:
            status['current_observation'] = self.current_observation.status()

    def reset_observed_list(self):
        """Reset the observed list """
        self.logger.debug('Resetting observed list')
        self.observed_list = OrderedDict()

    def reset_calibrated_list(self):
        """Reset the observed list """
        self.logger.debug('Resetting calibrated list')
        self.calibrated_list = OrderedDict()

    def set_observed_to_calibrated(self):
        self.calibrated_list.update(self.observed_list)
        self.reset_observed_list()

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
            self.logger.warning(f"Cannot add  observing_block: "
                                f"{observing_block}")
            self.logger.warning(e)
        else:
            self.observations[observation.id] = observation

    def initialize_constraints(self):
        # Initialize constraints for scheduling
        self.constraints = []

        if "constraints" not in self.config:
            return

        for constraint, constraint_config in self.config['constraints'].items():
            if constraint == 'atnight':
                try:
                    if constraint_config == 'astronomical':
                        self.constraints.append(
                            AtNightConstraint.twilight_astronomical())
                except Exception as e:
                    self.logger.warning(f"Cannot add atnight constraint: {e}")
            if constraint == "maxairmass":
                try:
                    # TODO TN maybe non boolean Airmass Constraint
                    self.constraints.append(
                        AirmassConstraint(max=constraint_config,
                                          boolean_constraint=True))
                except Exception as e:
                    self.logger.warning(f"Cannot add airmass constraint: {e}")
            if constraint == "minmoonseparationdeg":
                try:
                    self.constraints.append(
                        MoonSeparationConstraint(min=constraint_config*u.deg))
                except Exception as e:
                    self.logger.warning(f"Cannot add moon sep constraint: {e}")

        # We also always add the local horizon constraint:
        try:
            self.constraints.append(
                LocalHorizonConstraint(horizon=self.obs.get_horizon(),
                                       boolean_constraint=True))
        except Exception as e:
            self.logger.warning(f"Cannot add horizon constraint: {e}")

    def define_target(self, target_name):
        try:
            target = FixedTarget(
                name=target_name,
                coord=SkyCoord(
                    SkyCoord.from_name(target_name,
                                       frame="icrs"),
                    equinox=Time('J2000')))
        except:
            try:
                #"5h12m43.2s +31d12m43s" is perfectly valid
                target = FixedTarget(name=target_name.replace(" ", ""),
                                     coord=SkyCoord(
                                         target_name,
                                         frame='icrs',
                                         equinox='J2000.0'))
            except:
                raise RuntimeError(f"Scheduler: did not managed to "
                                   f"define target {target_name}")
        return target

    def initialize_target_list(self):
        """Creates valid `Observations` """

        # Start by initializing the generic constraints
        self.initialize_constraints()

        # Now add observation to the list
        if 'targets' not in self.config:
            self.logger.warning('Target list seems to be empty')
            return

        #TODO TN readout time, get that info from camera
        camera_time = 1*u.second
        for target_name, filter_config in self.config['targets'].items():
            target = self.define_target(target_name)
            for filter_name, config in filter_config.items():
                count = config["count"]
                temperature = config["temperature"]
                gain = config["gain"]
                exp_time_sec = config["exp_time_sec"]*u.second
                configuration={
                    'filter': filter_name,
                    'temperature': temperature,
                    'gain': gain
                }
                #TODO TN retrieve priority from the file ?
                priority = 0 if (filter_name == 'Luminance') else 1
                while count > 0:
                    try:
                        # number of image per scheduled "round" of imaging
                        # min number of exposure must be an integer number of times
                        # this number
                        exp_set_size = max(1, min(count,
                            self.MaximumSlotDurationSec//exp_time_sec))
                        #to be fixed
                        #min_nexp = (count+exp_set_size-1)//exp_set_size
                        #min_nexp = min_nexp * exp_set_size
                        b = ObservingBlock.from_exposures(
                                target,
                                priority,
                                exp_time_sec,
                                exp_set_size,
                                camera_time,
                                configuration=configuration,
                                constraints=self.constraints)
                        self.add_observation(b)
                        count -= exp_set_size
                    except AssertionError as e:
                        self.logger.debug(f"Error while adding target : {e}")

##########################################################################
# Utility Methods
##########################################################################

#    def dump_updated_target_list(self, config):
#        config.save_config(path='targets', config=config, overwrite=True)

##########################################################################
# Private Methods
##########################################################################
