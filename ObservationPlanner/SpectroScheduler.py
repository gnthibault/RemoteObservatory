# Numerical stuff
import numpy as np

# Astropy stuff
from astropy.coordinates import AltAz
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import SkyCoord

# Astrophysical informations
from astroquery.simbad import Simbad

# Astroplan stuff
from astroplan import FixedTarget
from astroplan import ObservingBlock

# Local stuff
from ObservationPlanner.Scheduler import Scheduler
from ObservationPlanner.SpectralObservation import SpectralObservation
from utils import listify
from Spectro.OTypes import otypes
from Spectro.ReferenceStarFinder import best_references

# Locally defined constraints
from ObservationPlanner.LocalHorizonConstraint import LocalHorizonConstraint


class SpectroScheduler(Scheduler):

    def __init__(self, ntpServ, obs, config=None, path='.'):
        """ Inherit from the `Base Scheduler` """
        super().__init__(ntpServ, obs, config=config, path=path)

    ##########################################################################
    # Properties
    ##########################################################################

    ##########################################################################
    # Methods
    ##########################################################################
    def define_target(self, target_name):
        target = None
        spinfo = {}
        try:
            simbad = Simbad()
            # standard name of the object type
            simbad.add_votable_fields('otype')
            # list of (secondary) object types for one object
            simbad.add_votable_fields('otypes')
            # spectral type value
            simbad.add_votable_fields('sp')
            # spectral type nature ('s'pectroscopic, 'a'bsorbtion, 'e'mmission
            simbad.add_votable_fields('sp_nature')
            # spectral type quality (A: best, .., E: worst)
            simbad.add_votable_fields('sp_qual')
            # all fields related with the spectral type
            simbad.add_votable_fields('sptype')
            # all fields related with radial velocity and redshift
            simbad.add_votable_fields('velocity')
            # all fields related with the proper motions
            simbad.add_votable_fields('propermotions')
            CDS = simbad.query_object(target_name)
        except:
            CDS = None

        if CDS is not None:  # Object found in SIMBAD, along with all info
            # overview of keywords with the previous votable fields
            # CDS.colnames
            # ['MAIN_ID',
            # 'RA',
            # 'DEC',
            # 'RA_PREC',
            # 'DEC_PREC',
            # 'COO_ERR_MAJA',
            # 'COO_ERR_MINA',
            # 'COO_ERR_ANGLE',
            # 'COO_QUAL',
            # 'COO_WAVELENGTH',
            # 'COO_BIBCODE',
            # 'OTYPE',
            # 'OTYPES',
            # 'RVZ_TYPE',
            # 'RVZ_RADVEL',
            # 'RVZ_ERROR',
            # 'RVZ_QUAL',
            # 'RVZ_WAVELENGTH',
            # 'RVZ_BIBCODE',
            # 'SP_TYPE',
            # 'SP_QUAL',
            # 'SP_TYPE_2',
            # 'SP_QUAL_2',
            # 'SP_BIBCODE',
            # 'OTYPE_2',
            # 'PMRA',
            # 'PMDEC',
            # 'PMRA_PREC',
            # 'PMDEC_PREC',
            # 'PM_ERR_MAJA',
            # 'PM_ERR_MINA',
            # 'PM_ERR_ANGLE',
            # 'PM_QUAL',
            # 'PM_BIBCODE']
            # for sptypes, check 
            # http://simbad.u-strasbg.fr/simbad/sim-display?data=sptypes
            # eventually CDS["SP_TYPE"][0] returns 'B8.5Ib-II'
            ra_h_m_s = np.array([*map(np.float, CDS['RA'][0].split(" "))])
            dec_d_m_s = np.array([*map(np.float, CDS['DEC'][0].split(" "))])
            coord = SkyCoord(
                ra=np.dot(ra_h_m_s, np.array([u.hourangle, u.hourangle / 60, u.hourangle / 3600])).to(u.degree),
                dec=np.dot(dec_d_m_s, np.array([u.degree, u.arcminute, u.arcsecond])),
                frame='icrs',
                equinox='J2000.0')
            target = FixedTarget(name=target_name.replace(" ", ""),
                                 coord=coord)
            spinfo["MAIN_ID"] = CDS['MAIN_ID'][0]
            spinfo["OTYPE"] = CDS['OTYPE'][0]
            spinfo["OTYPES"] = CDS['OTYPES'][0]
            try:
                spinfo["OTYPE_COMMENT"] = otypes[spinfo["OTYPE"]]
            except KeyError:
                spinfo["OTYPE_COMMENT"] = ""
            spinfo["SP_TYPE"] = CDS['SP_TYPE'][0]
            spinfo["RVZ_RADVEL"] = float(CDS['RVZ_RADVEL'][0])
            spinfo["RVZ_TYPE"] = str(CDS['RVZ_TYPE'][0])
        if CDS is None:
            try:
                coord = SkyCoord(SkyCoord.from_name(target_name, parse=True, frame="icrs"), equinox=Time('J2000'))
                target = FixedTarget(name=target_name.replace(" ", ""),
                                     coord=coord)
            except:
                try:
                    # "5h12m43.2s +31d12m43s" is perfectly valid
                    coord = SkyCoord(target_name,
                                     frame='icrs',
                                     equinox='J2000.0')
                    target = FixedTarget(name=target_name.replace(" ", ""),
                                         coord=coord)
                except:
                    raise RuntimeError("SpectroScheduler: did not managed to "
                                       "define target {target_name}")
        return target, spinfo

    def get_best_reference_target(self, observation):
        ob = observation.observing_block
        maxseparation = 15 * u.deg
        maxebv = 1
        altaz_frame = AltAz(obstime=self.serv_time.get_astropy_time_from_utc(),
                            location=self.obs.getAstropyEarthLocation())

        ref_list = best_references(ob.target, altaz_frame, maxseparation, maxebv)
        return ref_list[0]

    def get_spectral_reference_observation(self, observation):
        target_name = self.get_best_reference_target(observation)["Name"]
        # TODO TN: spinfo is actually not used here
        target, spinfo = self.define_target(target_name)
        if "reference_observation" not in self.config:
            self.logger.warning("Empty reference_observation configuration")
            return None
        else:
            config = self.config["reference_observation"]
        count = config["count"]
        temperature = config["temperature"]
        gain = config["gain"]
        exp_time_sec = config["exp_time_sec"] * u.second
        configuration = {
            'temperature': temperature,
            'gain': gain,
            'spinfo': spinfo
        }
        exp_set_size = count
        # TODO TN readout time, get that info from camera
        camera_time = 1 * u.second
        priority = 1
        observing_block = ObservingBlock.from_exposures(
            target,
            priority,
            exp_time_sec,
            exp_set_size,
            camera_time,
            configuration=configuration,
            constraints=self.constraints)
        reference_observation = SpectralObservation(
            observing_block,
            exp_set_size=exp_set_size,
            is_reference_observation=True)
        return reference_observation

    def initialize_target_list(self):
        """Creates valid `Observations` """

        # Start by initializing the generic constraints
        self.initialize_constraints()

        # Now add observation to the list
        if 'targets' not in self.config:
            self.logger.warning('Target list seems to be empty')
            return

        # TODO TN readout time, get that info from camera
        camera_time = 1 * u.second
        for target_name, config in self.config['targets'].items():
            target, spinfo = self.define_target(target_name)
            count = config["count"]
            temperature = config["temperature"]
            gain = config["gain"]
            exp_time_sec = config["exp_time_sec"] * u.second
            configuration = {
                'temperature': temperature,
                'gain': gain,
                'spinfo': spinfo
            }
            # TODO TN retrieve priority from the file ?
            priority = config["priority"]
            while count > 0:
                try:
                    # number of image per scheduled "round" of imaging
                    # min number of exposure must be an integer number of times
                    # this number
                    exp_set_size = max(1, min(count,
                                              self.MaximumSlotDurationSec // exp_time_sec))
                    # to be fixed
                    # min_nexp = (count+exp_set_size-1)//exp_set_size
                    # min_nexp = min_nexp * exp_set_size
                    b = ObservingBlock.from_exposures(
                        target,
                        priority,
                        exp_time_sec,
                        exp_set_size,
                        camera_time,
                        configuration=configuration,
                        constraints=self.constraints)
                    self.add_observation(b, is_reference_observation=False)
                    count -= exp_set_size
                except AssertionError as e:
                    self.logger.debug(f"Error while adding target : {e}")

    def add_observation(self, observing_block, exp_set_size=None,
                        is_reference_observation=False):
        """Adds an `Observation` to the scheduler
        Args:
            target_name (str): Name of the target, should be referenced in a
                               catalog (star, sky object, ...)
        """

        try:
            observation = SpectralObservation(
                observing_block=observing_block,
                is_reference_observation=is_reference_observation)
        except Exception as e:
            self.logger.warning(f"Cannot add  observing_block: "
                                f"{observing_block}")
            self.logger.warning(e)
        else:
            self.observations[observation.id] = observation

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
        # Before doing anything, we want to know if we need to acquire a
        # reference observation
        if self.current_observation is not None:
            # If observation does not feaures a reference yet
            if ((not self.current_observation.is_reference_observation) and
                    (self.current_observation.reference_observation_id is None)):
                current_observation = self.current_observation
                self.current_observation = self.get_spectral_reference_observation(self.current_observation)
                current_observation.reference_observation_id = self.current_observation
                return

        # Favor the current observation if still available
        if reread_target_file:
            self.logger.debug("Rereading target file")
            self.reread_config()

        if time is None:
            time = self.serv_time.get_astropy_time_from_utc()  # get_utc()

        # dictionary where key is obs key and value is priority (aka merit)
        valid_obs = {obs: 1.0 for obs, obs_def in self.observations.items() if not obs_def.is_done}
        best_obs = []

        observer = self.obs.getAstroplanObserver()

        for constraint in self.constraints:
            self.logger.info(f"Checking Constraint: {constraint}")
            for obs_key, observation in self.observations.items():
                if obs_key in valid_obs:
                    self.logger.debug(f"\tObservation: {obs_key}")
                    score = constraint.compute_constraint(time, observer,
                                                          observation.target.coord)
                    # Check if the computed score is a boolean
                    if np.any([isinstance(score, ty) for ty in
                               [bool, np.bool, np.bool_]]):
                        self.logger.debug(f"\t\tVetoed if false: {score}")
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

            # # Check new best against current_observation
            # if (self.current_observation is not None and
            #         best_obs[0][0] != self.current_observation.id):
            #
            #     # Favor the current observation if still doable
            #     end_of_next_set = time + self.current_observation.set_duration
            #     if self.observation_available(
            #             self.current_observation,
            #             Time([time, end_of_next_set])):
            #
            #         # If current is better or equal to top, add it to bestof
            #         # but no need to update current_observation
            #         if self.current_observation.merit >= best_obs[0][1]:
            #             best_obs.insert(0, (self.current_observation.id,
            #                                 self.current_observation.merit))

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
