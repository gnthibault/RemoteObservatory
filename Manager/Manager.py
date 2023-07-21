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

# Local stuff: IndiClient
from helper.IndiClient import IndiClient

# Local stuff: Service
from Service.NovaAstrometryService import NovaAstrometryService
#TODO TN TO BE FIXED
from Service.PanMessagingZMQ import PanMessagingZMQ

# Local stuff: Utils
from utils import error
from utils.config import load_config
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

        # setup guider
        self.logger.info('\tSetting up guider')
        self._setup_guider()

        # setup pointing strategy
        self.logger.info('\tSetting up pointing strategy')
        self._setup_pointer()

        # setup pointing strategy
        self.logger.info('\tSetting up offset pointing strategy')
        self._setup_offset_pointer()

        # Setup observation planner
        self.logger.info('\tSetting up observation planner')
        self._setup_scheduler()

        # Setup vizualization service
        self.logger.info('\tSetting up vizualization service')
        self._setup_vizualization_service()
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
        t0 = self.serv_time.get_astropy_time_from_utc()
        is_dark = self.observer.is_night(t0, horizon=horizon)
        if not is_dark:
            sun_pos = self.observer.altaz(t0, target=get_sun(t0)).alt
            self.logger.debug("Sun {:.02f} > {}".format(sun_pos, horizon))
        return is_dark

    @property
    def sidereal_time(self):
        return self.observer.local_sidereal_time(
            self.serv_time.get_astropy_time_from_utc())

    @property
    def current_observation(self):
        return self.scheduler.current_observation

    @current_observation.setter
    def current_observation(self, new_observation):
        self.scheduler.current_observation = new_observation

##########################################################################
# Methods
##########################################################################

    def send_message(self, data, channel='PANCHAT'):
        self.messaging.send_message(channel, {"data": data})

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
            t = self.serv_time.get_astropy_time_from_utc()
            local_time = str(self.serv_time.get_local_time())

            if self.mount.is_initialized:
                status['mount'] = self.mount.status()

            status['observatory'] = self.observatory.status()
            status['scheduler'] = self.scheduler.status()
            if self.current_observation:
                status['observation'] = self.current_observation.status()

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
            msg = f"Can't get observatory status: {e}-{traceback.format_exc()}"
            self.logger.error(msg)
            raise RuntimeError(msg)
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

    def acquire_calibration(self):
        obs_list = [obs for seq_t, obs in self.scheduler.observed_list.items()]
        target_name_list = [obs.target.name for obs in obs_list]
        self.logger.debug(f"Acquiring calibrations for targets {target_name_list}")

        # List of camera events to wait for to signal exposure is done processing
        camera_events = dict()
        for cam_name, camera in self.acquisition_cameras.items():
            try:
                self.logger.debug(f"Going to start calibration of camera {cam_name}[{camera.uid}]")
                calibration = self._get_calibration(camera)
                cam_event = calibration.calibrate(self.scheduler.observed_list)
                camera_events[cam_name] = cam_event
            except Exception as e:
                self.logger.error(f"Problem trying to calibrate camera {cam_name}, {e}: {traceback.format_exc()}")
        return camera_events

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
        self.scheduler.reset_calibrated_list()

    def observe(self):
        """Take individual images for the current observation

        This method gets the current observation and takes the next
        corresponding exposure.

        """
        # Get observatory metadata
        headers = self.get_standard_headers()

        # All cameras share a similar start time
        headers['start_time'] = self.serv_time.flat_time()

        # List of camera events to wait for to signal exposure is done processing
        camera_events = dict()

        # Take exposure with each camera
        for cam_name, camera in self.acquisition_cameras.items():
            self.logger.debug(f"Exposing for camera: {cam_name}")
            try:
                # Start the exposures
                cam_event = camera.take_observation(
                    observation=self.current_observation, headers=headers)
                camera_events[cam_name] = cam_event
            except Exception as e:
                self.logger.error(f"Problem waiting for images, {e}: {traceback.format_exc()}")
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

    def slew(self):
        """Slew to current target"""
        self.mount.set_slew_rate("3x")
        self.mount.slew_to_target()

    def update_tracking(self):
        """Update tracking with dithering.
        """
        self.mount.set_track_mode('TRACK_SIDEREAL')
        if self.guider is not None:
            self.guider.dither(**self.config['guider']['dither'])

    def points(self, mount, camera, observation, fits_headers):
        """Points precisely to the target
        """
        return self.pointer.points(
            mount=mount,
            camera=camera,
            observation=observation,
            fits_headers=fits_headers)

    def offset_points(self, mount, camera, guiding_camera, guider, observation, fits_headers):
        """Points precisely object to specific area on the sensor
        """
        return self.offset_pointer.offset_points(
            mount=mount,
            camera=camera,
            guiding_camera=guiding_camera,
            guider=guider,
            observation=observation,
            fits_headers=fits_headers)

    def initialize_tracking(self):
        # start each observation by setting up the guider
        try:
            self.mount.set_track_mode('TRACK_SIDEREAL')
            if self.guider is not None:
                self.logger.info("Start guiding")
                if self.guiding_camera is not None:
                    self.guiding_camera.disable_shoot()
                self.guider.guide()
                self.logger.info("Guiding successfully started")
            return True
        except Exception as e:
            self.logger.error('Error while trying to initialize tracking')
            return False

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

        # fetching various informations for the new image
        self.logger.debug(f"Getting headers for : {observation}")
        target = observation.target
        t0 = self.serv_time.get_astropy_time_from_utc()
        moon = get_moon(t0, self.observer.location)
        mnt_coord = self.mount.get_current_coordinates()
        guide_rate = self.mount.get_guide_rate()

        # Filling up header for the new image to be written
        headers = {
            'airmass': self.observer.altaz(t0, target).secz.value,
            'creator': "RemoteObservatory_{}".format(self.__version__),
            'elevation': self.earth_location.height.value,
            'latitude': self.earth_location.lat.value,
            'longitude': self.earth_location.lon.value,
            'moon_fraction': self.observer.moon_illumination(t0),
            'moon_separation': target.coord.separation(moon).value,
            'observer': self.config.get('name', ''),
            'ra_mnt': mnt_coord.ra.to(u.deg).value,
            'ha_mnt': mnt_coord.ra.to(u.hourangle).value,
            'dec_mnt': mnt_coord.dec.to(u.deg).value,
            'track_mode_mnt': self.mount.get_track_mode(),
            'slew_rate_mnt': self.mount.get_slew_rate(),
            'guide_rate_ns_mnt': guide_rate['NS'],
            'guide_rate_we_mnt': guide_rate['WE'],
            #'ha_mnt': self.observer.target_hour_angle(t0, target).value,
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

    def perform_cameras_autofocus(self, camera_list=None, coarse=False):
        """
        Perform autofocus on all cameras with focus capability, or a named
        subset of these. Optionally will perform a coarse autofocus first,
        otherwise will just fine tune focus.
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
            cameras = {cam_name: cam
                       for cam_name, cam in self.autofocus_cameras.items()
                        if cam_name in camera_list}
            if cameras == {}:
                self.logger.warning(f"Passed a list of camera names ({camera_list}) but no matches found")
        else:
            # No cameras specified, will try to autofocus all cameras from
            # self.cameras
            cameras = self.autofocus_cameras

        autofocus_events = dict()
        autofocus_statuses = dict()

        # Start autofocus with each camera
        for cam_name, camera in cameras.items():
            self.logger.debug(f"Autofocusing camera: {cam_name}")
            try:
                assert camera.focuser.is_connected
            except AttributeError:
                msg = f"Camera {cam_name} has no focuser, skipping autofocus"
                self.logger.error(msg)
                raise RuntimeError(msg)
            except AssertionError:
                msg = f"Camera {cam_name} focuser not connected, skipping autofocus"
                self.logger.error(msg)
                raise RuntimeError(msg)
            else:
                try:
                    # Start the autofocus
                    autofocus_status = [False]
                    autofocus_event = camera.autofocus_async(coarse=coarse, autofocus_status=autofocus_status)
                except Exception as e:
                    msg = f"Problem running autofocus: {e}"
                    self.logger.debug(msg)
                    raise RuntimeError(msg)
                else:
                    autofocus_events[cam_name] = autofocus_event
                    autofocus_statuses[cam_name] = autofocus_status

        return autofocus_events, autofocus_statuses

    def open_observatory(self):
        """Open the observatory, if there is one.

        Returns: False if there is a problem opening the observatory,
                 else True if open (or if not exists).
        """
        try:
            self.observatory.open_everything()
            return True
        except Exception as e:
            self.logger.error("Problem opening observatory: {e}")
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
            self.logger.error(f"Problem closing observatory: {e}")
            return False

    def unpark(self):
        try:
            # unpark the mount
            self.mount.unpark()

            # unpark the observatory
            self.observatory.unpark()

            # Launch guider server
            if self.guider is not None:
                self.guider.launch_server()
                self.guider.connect_server()
                self.guider.connect_profile()

            return True
        except Exception as e:
            self.logger.error(f"Problem unparking: {e}")
            return False

    def park(self):
        try:
            #close running guider server and client
            if self.guider is not None:
                self.guider.disconnect_profile()
                self.guider.disconnect_server()

            # park the mount
            self.mount.park()

            # park the observatory
            self.observatory.park()

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

    def _setup_services(self):
        """
            setup various services that are supposed to provide infos/data
        """
        try:
            self._setup_time_service()
            self._setup_weather_service()
            self._setup_messaging()
            self._setup_independant_services()
        except Exception:
            raise RuntimeError('Problem setting up services')

    def _setup_time_service(self):
        """
            setup a service that will provide time
        """
        try:
            time_name = self.config['time_service']['module']
            time_module = load_module('Service.'+time_name)
            self.serv_time = getattr(time_module, time_name)(
                config=self.config['time_service'])
        except Exception:
            raise RuntimeError('Problem setting up time service')

    def _setup_weather_service(self):
        """
            setup a service that will provide weather informations
        """
        try:
            weather_name = self.config['weather_service']['module']
            weather_module = load_module('Service.'+weather_name)
            self.serv_weather = getattr(weather_module, weather_name)(
                config=self.config['weather_service'],
                serv_time=self.serv_time,
                connect_on_create=True,
                loop_on_create=True)
        except Exception:
            raise RuntimeError('Problem setting up weather service')

    def _setup_messaging(self):
        try:
            messaging_name = self.config["messaging_publisher"]['module']
            messaging_module = load_module('Service.'+messaging_name)
            self.messaging = getattr(messaging_module, messaging_name)(
                 config=self.config["messaging_publisher"])
        except Exception:
            raise RuntimeError('Problem setting up messaging service')

    def _setup_independant_services(self):
        self.independant_services = []
        for config in self.config.get("independant_services", []):
            try:
                module_name = config['module']
                module = load_module('Service.'+module_name)
                self.independant_services.append(getattr(module, module_name)(
                     config=config))
            except Exception:
                raise RuntimeError('Problem setting up independant services')

    def _setup_observatory(self):
        """
            setup an observatory that stands for the physical building
        """
        try:
            obs_name = self.config['observatory']['module']
            obs_module = load_module('Observatory.'+obs_name)
            self.observatory = getattr(obs_module, obs_name)(
                config=self.config['observatory'])
        except Exception as e:
            raise RuntimeError(f"Problem setting up observatory: {e}")

    def _setup_mount(self):
        """
            Setup a mount object.
        """
        try:
            mount_name = self.config['mount']['module']
            mount_module = load_module('Mount.'+mount_name)
            self.mount = getattr(mount_module, mount_name)(
                location=self.earth_location,
                serv_time=self.serv_time,
                config=self.config['mount'])
        except Exception as e:
            self.logger.error(f"Cannot load mount module: {e}")
            raise error.MountNotFound(f"Problem setting up mount")

    @property
    def pointing_camera(self):
        return [v for k, v in self.cameras.items() if v.do_pointing][0]

    @property
    def adjust_pointing_camera(self):
        cam_list = [v for k, v in self.cameras.items() if v.do_adjust_pointing]
        if not len(cam_list):
            return None
        return cam_list[0]

    @property
    def guiding_camera(self):
        cam_list = [v for k, v in self.cameras.items() if v.do_guiding]
        if not len(cam_list):
            return None
        return cam_list[0]

    @property
    def acquisition_cameras(self):
        """
        We make sure we always provide cameras in the order of their declaration
        :return:
        """
        cam_od = OrderedDict()
        for k, v in self.cameras.items():
            if v.do_acquisition:
                cam_od[k] = v
        return cam_od

    @property
    def autofocus_cameras(self):
        """
        We make sure we always provide cameras in the order of their declaration
        :return:
        """
        cam_od = OrderedDict()
        for k, v in self.cameras.items():
            if v.do_autofocus:
                cam_od[k] = v
        return cam_od

    def _setup_cameras(self, **kwargs):
        """
            setup camera object(s)

        """
        self.cameras = OrderedDict()

        def setup_cameras():
            try:
                for cam_config in self.config["cameras"]:
                    cam_name = cam_config['module']
                    cam_module = load_module('Camera.'+cam_name)
                    cam = getattr(cam_module, cam_name)(
                        serv_time=self.serv_time,
                        config=cam_config,
                        connect_on_create=True)
                    cam.prepare_shoot()
                    self.cameras[cam.name] = cam
            except Exception as e:
                raise RuntimeError(f"Problem setting up camera: {e}")

        setup_cameras()
        nb_pointing_cameras = len([v for k, v in self.cameras.items() if v.do_pointing])
        if nb_pointing_cameras != 1:
            raise error.CameraNotFound(
                msg=f"Invalid number of pointing cameras {nb_pointing_cameras}. Exiting.", exit=True)
        if len(self.acquisition_cameras) == 0:
            raise error.CameraNotFound(
                msg="No acquisition camera available. Exiting.", exit=True)

    def _setup_guider(self):
        """
            Setup a guider object.
        """
        try:
            if 'guider' in self.config:
                guider_name = self.config['guider']['module']
                guider_module = load_module('Guider.'+guider_name)
                self.guider = getattr(guider_module, guider_name)(
                    config = self.config['guider'])
                # Setup and make sure the Guider is not already acquiring frames
                self.logger.info("Initializing guider")
                self.guider.launch_server()
                self.guider.connect_server()
                self.guider.connect_profile()
        except Exception as e:
            raise RuntimeError(f"Problem setting up guider: {e}")

    def _setup_pointer(self):
        """
            Setup a pointing strategy.
        """
        try:
            if 'pointer' in self.config:
                pointer_name = self.config['pointer']['module']
                pointer_module = load_module('Pointer.'+pointer_name)
                self.pointer = getattr(pointer_module, pointer_name)(
                    config=self.config['pointer'])
        except Exception as e:
            raise RuntimeError(f"Problem setting up pointer: {e}")

    def _setup_offset_pointer(self):
        """
            Setup an offset pointing strategy.
        """
        try:
            if 'offset_pointer' in self.config:
                pointer_name = self.config['offset_pointer']['module']
                pointer_module = load_module('Pointer.'+pointer_name)
                self.offset_pointer = getattr(pointer_module, pointer_name)(
                    config=self.config['offset_pointer'])
        except Exception as e:
            raise RuntimeError(f"Problem setting up offset pointer: {e}")


    def _get_calibration(self, camera):
        """
            Sets up the calibration / calibration acquisition procedure
        """
        calibration = None
        try:
            if 'calibration' in self.config:
                calibration_name = self.config["calibration"]["module"]
                calibration_module = load_module("calibration."+calibration_name)
                calibration = getattr(calibration_module, calibration_name)(
                    camera=camera,
                    config=self.config["calibration"])
        except Exception as e:
            raise RuntimeError(f"Problem setting up calibration: {e}")
        return calibration

    def _setup_scheduler(self):
        """
            Sets up the scheduler that will be used by the observatory
        """
        
        try:
            if 'scheduler' in self.config:
                scheduler_name = self.config['scheduler']['module']
                scheduler_target_file = self.config['scheduler']['target_file']
                scheduler_module = load_module(f"ObservationPlanner.{scheduler_name}")
                self.scheduler = getattr(scheduler_module, scheduler_name)(
                    ntpServ=self.serv_time,
                    obs=self.observatory,
                    config=load_config(config_files=[scheduler_target_file]))
        except Exception as e:
            raise RuntimeError(f"Problem setting up scheduler: {e}")

    def _setup_vizualization_service(self):
        """
            Sets up the vizualization service to be used in the webfrontend
        """

        try:
            if 'vizualization_service' in self.config:
                viz_name = self.config['vizualization_service']['module']
                viz_module = load_module(f"Service.{viz_name}")
                self.vizualization_service = getattr(viz_module, viz_name)(
                    config=self.config['vizualization_service'],
                    mount_device=self.mount,
                    observatory_device=self.observatory.dome_controller)
                self.vizualization_service.start()
        except Exception as e:
            # No need to stop everything just for this service
            self.logger.error(f"Problem setting up vizualization_service: {e}")


