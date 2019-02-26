# Generic
from collections import OrderedDict
from datetime import datetime
from glob import glob
import logging
import os
import time
import traceback

# Asynchronous stuff
from threading import Event
from threading import Thread

# Astropy
from astropy import units as u
from astropy.coordinates import EarthLocation
from astropy.coordinates import get_moon
from astropy.coordinates import get_sun

# Astroplan
from astroplan import Observer

# Local stuff: Base
from Base.Base import Base

# Local stuff: Guider
from Guider.GuiderPHD2 import GuiderPHD2

# Local stuff: IndiClient
from helper.IndiClient import IndiClient

# Local stuff: Observation planning
from ObservationPlanner.DefaultScheduler import DefaultScheduler

# Local stuff: Observatory
from Observatory.ShedObservatory import ShedObservatory

# Local stuff: Service
from Service.WUGWeatherService import WUGWeatherService
from Service.NTPTimeService import NTPTimeService
from Service.NovaAstrometryService import NovaAstrometryService

# Local stuff: Utils
from utils import error

#from pocs.utils import images as img_utils
from utils import load_module


class Manager(Base):

    def __init__(self, *args, **kwargs):
        """Main Observatory manager class

        Starts up the observatory. Reads config file, sets up location,
        dates, mount, cameras, and weather station
        """
        Base.__init__(self)
        self.logger.info('Initializing observatory manager')

        # Image directory and other ios
        self.logger.info('\tSetting up main image directory')
        self._setup_image_directory()

        # setup indi client
        self.logger.info('\tSetting up indi client')
        self._setup_indi_client()

        # setup web services
        self.logger.info('\tSetting up web services')
        self._setup_services()

        # Setup physical obervatory related informations
        self.logger.info('\tSetting up observatory')
        self._setup_observatory()

        # Setup telescope mount
        self.logger.info('\tSetting up mount')
        self._setup_mount()

        # Setup camera(s)
        self.logger.info('\tSetting up cameras')
        self._setup_cameras()

        # Setup filter wheel
        self.logger.info('\tSetting up filterwheel')
        self._setup_filterwheel()

        # setup guider
        self.logger.info('\tSetting up guider')
        self.setup_guider()

        # Setup observation planner
        self.logger.info('\tSetting up observation planner')
        self._setup_scheduler()

        self.logger.info('\t Observatory initialized')

##########################################################################
# Properties
##########################################################################

    @property
    def observer(self):
        return self.observatory.getAstroplanObserver()

    @property
    def earth_location(self):
        return self.observatory.getAstropyEarthLocation()

    @property
    def is_dark(self):
        horizon = -18 * u.degree

        t0 = self.serv_time.getAstropyTimeFromUTC()
        is_dark = self.observer.is_night(t0, horizon=horizon)

        if not is_dark:
            sun_pos = self.observer.altaz(t0, target=get_sun(t0)).alt
            self.logger.debug("Sun {:.02f} > {}".format(sun_pos, horizon))

        return is_dark

    @property
    def sidereal_time(self):
        return self.observer.local_sidereal_time(
            self.serv_time.getAstropyTimeFromUTC())

    @property
    def primary_camera(self):
        return self._primary_camera

    @primary_camera.setter
    def primary_camera(self, cam):
        cam.is_primary = True
        self._primary_camera = cam

    @property
    def current_observation(self):
        return self.scheduler.current_observation

    @current_observation.setter
    def current_observation(self, new_observation):
        self.scheduler.current_observation = new_observation

##########################################################################
# Methods
##########################################################################

    def initialize(self):
        """Initialize the observatory and connected hardware """
        self.logger.debug("Initializing mount")
        self.mount.initialize()
        self.observatory.initialize()

    def power_down(self):
        """Power down the observatory. Currently does nothing
        """
        self.logger.debug("Shutting down observatory")
        self.mount.deinitialize()
        self.observatory.deinitialize()

    def status(self):
        """Get status information for various parts of the observatory
        """
        status = {}
        try:
            t = self.serv_time.getAstropyTimeFromUTC()
            local_time = str(self.serv_time.getLocalTimeFromNTP())

            if self.mount.is_initialized:
                status['mount'] = self.mount.status()
                status['mount']['current_ha'] = self.observer.target_hour_angle(
                    t, self.mount.get_current_coordinates())
                if self.mount.has_target:
                    status['mount']['mount_target_ha'] = (
                        self.observer.target_hour_angle(t, 
                            self.mount.get_target_coordinates()))

            status['observatory'] = self.observatory.status()

            if self.current_observation:
                status['observation'] = self.current_observation.status()
                status['observation']['field_ha'] = (
                    self.observer.target_hour_angle(t,
                        self.current_observation.target))

            evening_astro_time = self.observer.twilight_evening_astronomical(t,
                                 which='next')
            morning_astro_time = self.observer.twilight_morning_astronomical(t,
                                 which='next')

            status['observer'] = {
                'siderealtime': str(self.sidereal_time),
                'utctime': t,
                'localtime': local_time,
                'local_evening_astro_time': evening_astro_time,
                'local_morning_astro_time': morning_astro_time,
                'local_sun_set_time': self.observer.sun_set_time(t),
                'local_sun_rise_time': self.observer.sun_rise_time(t),
                'local_moon_alt': self.observer.moon_altaz(t).alt,
                'local_moon_illumination': self.observer.moon_illumination(t),
                'local_moon_phase': self.observer.moon_phase(t),
            }

        except Exception as e:  # pragma: no cover
            self.logger.warning("Can't get observatory status: {}-{}".format(e,
                traceback.format_exc()))
        return status

    def get_observation(self, *args, **kwargs):
        """Gets the next observation from the scheduler

        Returns:
            observation (pocs.scheduler.observation.Observation or None): An
                an object that represents the obervation to be made

        Raises:
            error.NoObservation: If no valid observation is found
        """

        self.logger.debug("Getting observation for observatory")

        # If observation list is empty or a reread is requested
        if (self.scheduler.has_valid_observations is False or
                kwargs.get('reread_fields_file', False)):
            self.scheduler.initialize_target_list()

        # This will set the `current_observation`
        self.scheduler.get_observation(*args, **kwargs)

        if self.current_observation is None:
            self.scheduler.clear_available_observations()
            raise error.NoObservation("No valid observations found")

        return self.current_observation

    def cleanup_observations(self):
        """Cleanup observation list

        Loops through the `observed_list` performing cleanup tasks. Resets
        `observed_list` when done

        upload_images = False

        for seq_time, observation in self.scheduler.observed_list.items():
            self.logger.debug("Housekeeping for {}".format(observation))

            for cam_name, camera in self.cameras.items():
                self.logger.debug('Cleanup for camera {} [{}]'.format(
                    cam_name, camera.uid))

            #    dir_name = "{}/fields/{}/{}/{}/".format(
            #        self.config['directories']['images'],
            #        observation.field.field_name,
            #        camera.uid,
            #        seq_time,
            #    )

            #    img_utils.clean_observation_dir(dir_name)

                if upload_images is True:
                    self.logger.debug("Uploading directory to cloud storage")
            #        img_utils.upload_observation_dir(pan_id, dir_name)

            self.logger.debug('Cleanup finished')

        self.scheduler.reset_observed_list()
        """
        self.logger.warning("TODO TN SHOULD CLEANUP THE DATA HERE")

    def observe(self):
        """Take individual images for the current observation

        This method gets the current observation and takes the next
        corresponding exposure.

        """
        # Get observatory metadata
        headers = self.get_standard_headers()

        # All cameras share a similar start time
        headers['start_time'] = self.serv_time.flat_time()

        # List of camera events to wait for to signal exposure is done
        # processing
        camera_events = dict()

        # Take exposure with each camera
        for cam_name, camera in self.cameras.items():
            self.logger.debug("Exposing for camera: {}".format(cam_name))

            try:
                # Start the exposures
                cam_event = camera.take_observation(
                    observation=self.current_observation, headers=headers)

                camera_events[cam_name] = cam_event

            except Exception as e:
                self.logger.error("Problem waiting for images, {}: {}".format(
                    e, traceback.format_exc()))

        return camera_events

    def analyze_recent(self):
        """Analyze the most recent exposure

        Compares the most recent exposure to the reference exposure and
        determines the offset between the two.

        Returns:
            dict: Offset information
        """
        # Clear the offset info
        self.current_offset_info = None

        pointing_image = self.current_observation.pointing_image

        try:
            # Get the image to compare
            image_id, image_path = self.current_observation.last_exposure

            #current_image = Image(image_path, location=self.earth_location)

            #solve_info = current_image.solve_field()

            #self.logger.debug("Solve Info: {}".format(solve_info))

            # Get the offset between the two
            #self.current_offset_info = current_image.compute_offset(
            #    pointing_image)
            #self.logger.debug('Offset Info: {}'.format(
            #    self.current_offset_info))

            # Store the offset information
            #self.db.insert('offset_info', {
            #    'image_id': image_id,
            #    'd_ra': self.current_offset_info.delta_ra.value,
            #    'd_dec': self.current_offset_info.delta_dec.value,
            #    'magnitude': self.current_offset_info.magnitude.value,
            #    'unit': 'arcsec',
            #})

        except error.SolveError:
            self.logger.warning("Can't solve field, skipping")
        except Exception as e:
            self.logger.warning("Problem in analyzing: {}".format(e))

        return self.current_offset_info

    def update_tracking(self):
        """Update tracking with rate adjustment.

        The `current_offset_info` contains information about how far off
        the center of the current image is from the pointing image taken
        at the start of an observation. This offset info is given in arcseconds
        for the RA and Dec.

        A mount will accept guiding adjustments in number of milliseconds
        to move in a specified direction, where the direction is either `east/west`
        for the RA axis and `north/south` for the Dec.

        Here we take the number of arcseconds that the mount is offset and,
        via the `mount.get_ms_offset`, find the number of milliseconds we
        should adjust in a given direction, one for each axis.

        Uses the `rate_adjustment` key from the `self.current_offset_info`
        
        if self.current_offset_info is not None:
            self.logger.debug("Updating the tracking")

            # find the number of ms and direction for Dec axis
            dec_offset = self.current_offset_info.delta_dec
            dec_ms = self.mount.get_ms_offset(dec_offset, axis='dec')
            if dec_offset >= 0:
                dec_direction = 'north'
            else:
                dec_direction = 'south'

            # find the number of ms and direction for RA axis
            ra_offset = self.current_offset_info.delta_ra
            ra_ms = self.mount.get_ms_offset(ra_offset, axis='ra')
            if ra_offset >= 0:
                ra_direction = 'west'
            else:
                ra_direction = 'east'

            dec_ms = abs(dec_ms.value) * 1.5  # TODO(wtgee): Figure out why 1.5
            ra_ms = abs(ra_ms.value) * 1.

            # Ensure we don't try to move for too long
            max_time = 99999

            # Correct the Dec axis (if offset is large enough)
            if dec_ms > max_time:
                dec_ms = max_time

            if dec_ms >= 50:
                self.logger.info("Adjusting Dec: {} {:0.2f} ms {:0.2f}".format(
                    dec_direction, dec_ms, dec_offset))
                if dec_ms >= 1. and dec_ms <= max_time:
                    self.mount.query('move_ms_{}'.format(
                        dec_direction), '{:05.0f}'.format(dec_ms))

                # Adjust tracking for up to 30 seconds then fail if not done.
                start_tracking_time = self.serv_time.getAstropyTimeFromUTC()
                while self.mount.is_tracking is False:
                    if (self.serv_time.getAstropyTimeFromUTC() -
                            start_tracking_time).sec > 30:
                        raise Exception('Trying to adjust Dec tracking for '
                                        'more than 30 seconds')

                    self.logger.debug("Waiting for Dec tracking adjustment")
                    time.sleep(0.1)

            # Correct the RA axis (if offset is large enough)
            if ra_ms > max_time:
                ra_ms = max_time

            if ra_ms >= 50:
                self.logger.info("Adjusting RA: {} {:0.2f} ms {:0.2f}".format(
                    ra_direction, ra_ms, ra_offset))
                if ra_ms >= 1. and ra_ms <= max_time:
                    self.mount.query('move_ms_{}'.format(
                        ra_direction), '{:05.0f}'.format(ra_ms))

                # Adjust tracking for up to 30 seconds then fail if not done.
                start_tracking_time = self.serv_time.getAstropyTimeFromUTC()
                while self.mount.is_tracking is False:
                    if (self.serv_time.getAstropyTimeFromUTC() - 
                            start_tracking_time).sec > 30:
                        raise Exception('Trying to adjust RA tracking for '
                                        'more than 30 seconds')

                    self.logger.debug("Waiting for RA tracking adjustment")
                    time.sleep(0.1)
        """
        if self.guider is not None:
            self.guider.dither(*self.config['guider']['dither'])


    def initialize_tracking(self):
        # start each observation by setting up the guider
        if model.manager.guider is not None:
            model.logger.info("Starting guider before observing")
            model.manager.guider.reset_guiding()
            model.manager.guider.guide()

    def get_standard_headers(self, observation=None):
        """Get a set of standard headers

        Args:
            observation (`~pocs.scheduler.observation.Observation`, optional): The
                observation to use for header values. If None is given, use
                the `current_observation`.

        Returns:
            dict: The standard headers
        """
        if observation is None:
            observation = self.current_observation

        assert observation is not None, self.logger.warning(
            "No observation, can't get headers")

        target = observation.target
        self.logger.debug("Getting headers for : {}".format(observation))
        t0 = self.serv_time.getAstropyTimeFromUTC()
        moon = get_moon(t0, self.observer.location)

        headers = {
            'airmass': self.observer.altaz(t0, target).secz.value,
            'creator': "RemoteObservatoryV{}".format(self.__version__),
            'elevation': self.earth_location.height.value,
            'ha_mnt': self.observer.target_hour_angle(t0, target).value,
            'latitude': self.earth_location.lat.value,
            'longitude': self.earth_location.lon.value,
            'moon_fraction': self.observer.moon_illumination(t0),
            'moon_separation': target.coord.separation(moon).value,
            'observer': self.config.get('name', ''),
            'origin': 'gnthibault',
            #'tracking_rate_ra': self.mount.getTrackRate()
            #TODO TN is that stuff worth implementing ?
        }

        # Add observation metadata
        headers.update(observation.status())
        # Explicitly convert EQUINOX to float
        try:
            equinox = float(headers['equinox'].replace('J', ''))
        except BaseException:
            equinox = 2000.  # We assume J2000
        headers['equinox'] = equinox
        return headers

    def autofocus_cameras(self, camera_list=None, coarse=False):
        """
        Perform autofocus on all cameras with focus capability, or a named
        subset of these. Optionally will perform a coarse autofocus first,
        otherwise will just fine tune focus.

        Args:
            camera_list (list, optional): list containing names of cameras to
                autofocus.
            coarse (bool, optional): Whether to performan a coarse autofocus
                before fine tuning, default False.

        Returns:
            dict of str:threading_Event key:value pairs, containing camera
                names and corresponding Events which will be set when the
                camera completes autofocus.
        """
        if camera_list:
            # Have been passed a list of camera names, extract dictionary
            # containing only cameras named in the list
            cameras = {cam_name: self.cameras[
                cam_name] for cam_name in camera_list if cam_name in
                self.cameras.keys()}

            if cameras == {}:
                self.logger.warning('Passed a list of camera names ({}) but no'
                                    ' matches found'.format(camera_list))
        else:
            # No cameras specified, will try to autofocus all cameras from
            # self.cameras
            cameras = self.cameras

        autofocus_events = dict()

        # Start autofocus with each camera
        for cam_name, camera in cameras.items():
            self.logger.debug("Autofocusing camera: {}".format(cam_name))

            try:
                assert camera.focuser.is_connected
            except AttributeError:
                self.logger.debug('Camera {} has no focuser, skipping '
                                  'autofocus'.format(cam_name))
            except AssertionError:
                self.logger.debug('Camera {} focuser not connected, skipping '
                                  'autofocus'.format(cam_name))
            else:
                try:
                    # Start the autofocus
                    autofocus_event = camera.autofocus(coarse=coarse)
                except Exception as e:
                    self.logger.error(
                        "Problem running autofocus: {}".format(e))
                else:
                    autofocus_events[cam_name] = autofocus_event

        return autofocus_events

    def open_observatory(self):
        """Open the observatory, if there is one.

        Returns: False if there is a problem opening the observatory,
                 else True if open (or if not exists).
        """
        try:
            self.observatory.open_everything()
            return True
        except Exception as e:
            self.logger.error(
                "Problem opening observatory: {}".format(e))
            return False

    def close_observatory(self):
        """Close the observatory, if there is one.

        Returns: False if there is a problem closing the observatory,
                 else True if closed (or if not exists).
        """
        try:
            # close actual dome + everything managed by obsy
            self.observatory.close_everything()

            return True
        except Exception as e:
            self.logger.error(
                "Problem closing observatory: {}".format(e))
            return False

    def unpark(self)
        try:
            # unpark the mount
            self.mount.unpark()

            # unpark the observatory
            self.observatory.unpark()

            #connect guider server and client
            if self.guider is not None:
                self.guider.launch_server()
                self.guider.connect()

            return True
        except Exception as e:
            self.logger.error(
                "Problem parking: {}".format(e))
            return False

    def park(self)
        try:
            # park the mount
            self.mount.park()

            # park the observatory
            self.observatory.park()

            #close running guider server and client
            if self.guider is not None:
                self.guider.disconnect()
                self.guider.terminate_server()

            return True
        except Exception as e:
            self.logger.error(
                "Problem parking: {}".format(e))
            return False

##########################################################################
# Private Methods
##########################################################################

    def _setup_image_directory(self, path='.'):
        self._image_dir = self.config['directories']['images']

    def _setup_indi_client(self):
        """
            setup the indi client that will communicate with devices
        """
        try:
            #TODO TN: at some point, this is going to be removed, and each
            # device will instanciate its own client, depending on which machine
            # the physical device is attached to
            self.indi_client = IndiClient(config=self.config['indiclient'])
            self.indi_client.connect()
        except Exception:
            raise RuntimeError('Problem setting up indi client')

    def _setup_services(self):
        """
            setup various services that are supposed to provide infos/data
        """
        try:
            self.serv_time = NTPTimeService()
            #self.serv_weather = WUGWeatherService()
            #self.serv_astrometry = NovaAstrometryService(configFileName='local')
            #self.serv_astrometry.login()

        except Exception:
            raise RuntimeError('Problem setting up services')


    def _setup_observatory(self):
        """
            setup an observatory that stands for the physical building
        """
        try:
            self.observatory = ShedObservatory(
                config = self.config['observatory'])
        except Exception:
            raise RuntimeError('Problem setting up observatory')

    def _setup_mount(self):
        """
            Setup a mount object.
        """
        try:
            mount_name = self.config['mount']['module']
            mount_module = load_module('Mount.'+mount_name)
            self.mount = getattr(mount_module, mount_name)(
                indiClient = self.indi_client,
                location = self.earth_location,
                serv_time = self.serv_time,
                config = self.config['mount'])

        except Exception as e:
            self.logger.warning("Cannot load mount module: {}".format(e))
            raise error.MountNotFound('Problem setting up mount')

    def _setup_cameras(self, **kwargs):
        """
            setup camera object(s)

        """
        self.cameras = OrderedDict()
        try:
            cam_name = self.config['camera']['module']
            cam_module = load_module('Camera.'+cam_name)
            cam = getattr(cam_module, cam_name)(
                serv_time=self.serv_time,
                indiClient=self.indi_client,
                config = self.config['camera'],
                primary=True,
                connectOnCreate=True)
            cam.prepareShoot()
 
        except Exception as e:
            raise RuntimeError('Problem setting up camera: {}'.format(e))

        self.primary_camera = cam
        self.cameras[cam.name] = cam

        if len(self.cameras) == 0:
            raise error.CameraNotFound(
                msg="No cameras available. Exiting.", exit=True)

    # TODO TN: filterwheel should be relative to a camera
    def _setup_filterwheel(self):
        """
            Setup a filterwheel object.
        """
        try:
            if 'filterwheel' in self.config:
                fw_name = self.config['filterwheel']['module']
                fw_module = load_module('FilterWheel.'+fw_name)
                self.filterwheel = getattr(fw_module, fw_name)(
                    indiClient = self.indi_client,
                    config = self.config['filterwheel'],
                    connectOnCreate=True)
        except Exception:
            raise RuntimeError('Problem setting up filterwheel')

    def _setup_guider(self):
        """
            Setup a guider object.
        """
        try:
            if 'guider' in self.config:
                guider_exposure = self.config['guider']['exposure']
                guider_settle = self.confi['guider']['settle']
                self.guider = GuiderPHD2()
#                self.guider = self.config['guider'], connect_on_create=True)
                self.guider.set_exposure(guider_exposure)
                self.guider.set_settle(*guider_settle)
        except Exception:
            raise RuntimeError('Problem setting up guider')


    def _setup_scheduler(self):
        """
            Sets up the scheduler that will be used by the observatory
        """
        
        try:
            self.scheduler = DefaultScheduler(ntpServ=self.serv_time,
                                              obs=self.observatory)
        except Exception:
            raise RuntimeError('Problem setting up observation planner')

