# Generic
from time import sleep
import threading
import traceback

# Numerical stuff
import numpy as np

# Astropy
from astropy.coordinates import SkyCoord
import astropy.units as u

# Local
from Imaging.Image import Image
from Imaging.SolvedImageAnalysis import find_best_candidate_star, get_brightest_detection
from utils.error import AstrometrySolverError

# Numerical stuff
import numpy as np

# Astropy
import astropy.units as u

# Local
from Base.Base import Base
from Imaging.Image import Image
from Imaging.Image import OffsetError
from utils.error import PointingError

SLEEP_SECONDS = 5.


class StarOffsetPointer(Base):
    def __init__(self, config=None):
        super().__init__()
        if config is None:
            config = dict(
                timeout_seconds=300,
                max_identification_error_seconds=5,
                sync_mount_upon_solve=False,
                use_guider_adjust=True,
                on_star_identification_failure="get_brightest"  # get_brightest or trust_astrometry
            )

        self.timeout_seconds = config["timeout_seconds"]
        self.max_identification_error = config["max_identification_error_seconds"]*u.arcsec
        self.sync_mount_upon_solve = config["sync_mount_upon_solve"]
        self.use_guider_adjust = config["use_guider_adjust"]
        self.on_star_identification_failure = config["on_star_identification_failure"]

    def offset_points(self, mount, camera, guiding_camera, guider, observation, fits_headers):
        pointing_event = threading.Event()
        pointing_status = [False]
        w = threading.Thread(target=self.offset_points_async,
                             kwargs={
                                 "mount": mount,
                                 "camera": camera,
                                 "guiding_camera": guiding_camera,
                                 "guider": guider,
                                 "observation": observation,
                                 "fits_headers": fits_headers,
                                 "pointing_event": pointing_event,
                                 "pointing_status": pointing_status
                             })
        w.start()
        return pointing_event, pointing_status

    def offset_points_async(self, mount, camera, guiding_camera, guider, observation, fits_headers, pointing_event,
                            pointing_status):
        """Offset Pointing

        Mostly useful in spectroscopy, as there should be no reason for offset the center of the field of view from the
        target object of interest in a regular imaging workflow.
        Here the idea is to put the object of interest at a particular area on the sensor, usually the center of the slit in
        slit spectrography experiments

        The idea of the method is to perform an astrometry on camera that features do_adjust_pointing capability,
        and then, try to detect the star from the resolved image that is the closest from the theoretical target
        coordinates, and then move the position of this star on the target area of interest on the sensor (the slit).

        The workflow of this state is the following:
        1: Take an image, and perform astrometric resolution on it
        2: if astrometric resolution is successful, extract all object detections center, and compare to target coordinates
           and jump to step 3. Otherwise jump to step 5
        3: if a star is detected at a distance lower or equal to 3" then compute and slew to the coordinate of the new
           center to be pointed at, taking into account the desired offset so that astrometric coordinates of the detected
           star end up in the slit x,y position, then got to next state. Other wise jump to step 4
        4: No star is detected close to the desired position. We assume the pointing is currently our best estimate,
            we compute and slew to the coordinate of the new center to be pointed at, taking into account the desired offset
            so that current center end up in the slit x,y position, then go to next state.
        5: Astrometric resolution failed, extract all object detections centers, and assume that the brightest star is
           the target. If there is at least one star detected, then we compute and slew to the coordinate of the new center
           to be pointed at, taking into account the desired offset so that current center end up in the slit x,y position,
            then go to next state.
        """
        try:
            try:
                img_num = 0
                pointing_image = self.acquire_pointing(camera, guiding_camera, observation, fits_headers, img_num)
                if camera is None:
                    self.logger.error(f"No adjust camera settings are set, skipping offset_pointing")

                # Attempt to solve field
                pointing_image.solve_field(verbose=True, gen_hips=False, remove_extras=False, skip_solved=False)
                # update mount with the actual position
                if self.sync_mount_upon_solve:
                    mount.sync_to_coord(pointing_image.pointing)

                # Now analyse the solved image
                px_identified_target = find_best_candidate_star(pointing_image,
                                                                observation.target.coord,
                                                                self.max_identification_error)
                if px_identified_target is None:
                    msg = f"Cannot identify a star from {pointing_image.fits_file} while in offset_pointing state, will " \
                          f"only rely on brightest detected star"
                    self.logger.warning(msg)
                    px_identified_target = self.get_default_star_strategy(pointing_image)

            except AstrometrySolverError as e:
                msg = f"Cannot solve image {pointing_image.fits_file} while in offset_pointing state: {e}"
                self.logger.warning(msg)
                px_identified_target = self.get_default_star_strategy(pointing_image)

            if self.use_guider_adjust:
                # If guider was locked on another star, then restart guiding
                if not guider.is_lock_position_close_to(px_target=px_identified_target,
                                                        max_angle_sep=3 * u.arcsec):
                    guider.stop_capture()
                    guider.loop()
                    half_search_size = camera.adjust_roi_search_size / 2
                    guider.find_star(x=max(0, int(round(px_identified_target[0] - half_search_size))),
                                     y=max(0, int(round(px_identified_target[1] - half_search_size))),
                                     width=camera.adjust_roi_search_size,
                                     height=camera.adjust_roi_search_size)
                    guider.guide(recalibrate=False,
                                 roi=[int(round(camera.adjust_center_x)),
                                      int(round(camera.adjust_center_y)),
                                      int(round(camera.adjust_roi_search_size)),
                                      int(round(camera.adjust_roi_search_size))])
                guider.set_lock_position(camera.adjust_center_x,
                                         camera.adjust_center_y,
                                         exact=True,
                                         wait_reached=True,
                                         angle_sep_reached=2 * u.arcsec)
                # TODO TN we would need a concept of uncertainty based on seeing and sampling here
            else:
                # There are some subteleties here: https://astropy-cjhang.readthedocs.io/en/latest/wcs/
                radeg, decdeg = pointing_image.wcs.all_pix2world(
                    camera.adjust_center_x,
                    camera.adjust_center_y,
                    0,  # 0-based indexing
                    ra_dec_order=True)
                current_sky_coord_of_target_sensor_position = SkyCoord(
                    ra=float(radeg) * u.degree,
                    dec=float(decdeg) * u.degree,
                    frame='icrs',
                    equinox='J2000.0')
                radeg, decdeg = pointing_image.wcs.all_pix2world(
                    px_identified_target[0],
                    px_identified_target[1],
                    0,  # 0-based indexing
                    ra_dec_order=True)
                current_sky_coord_of_target_star = SkyCoord(
                    ra=float(radeg) * u.degree,
                    dec=float(decdeg) * u.degree,
                    frame='icrs',
                    equinox='J2000.0')

                pointing_error = pointing_image.pointing_error(
                    pointing_reference_coord=current_sky_coord_of_target_star
                )
                offset_delta_ra = current_sky_coord_of_target_sensor_position.ra-current_sky_coord_of_target_star.ra
                offset_delta_dec = current_sky_coord_of_target_sensor_position.dec-current_sky_coord_of_target_star.dec
                # adjust by slewing to the opposite of the delta
                target = mount.get_current_coordinates()
                target = SkyCoord(
                    ra=target.ra - pointing_error.delta_ra + offset_delta_ra,
                    dec=target.dec - pointing_error.delta_dec + offset_delta_dec,
                    frame='icrs', equinox='J2000.0')
                # Now adjust by slewing to the specified counter-offseted coordinates
                if guider is not None:
                    msg = f"Going to adjust pointing, need to pause guiding, and restart later"
                    self.logger.debug(msg)
                    guider.stop_capture()
                    # guider.set_paused(paused=True)
                    # guider.wait_for_state(one_of_states=["Paused"])
                mount.slew_to_coord(target)
                if guider is not None:
                    guider.loop()
                    half_search_size = camera.adjust_roi_search_size / 2
                    guider.find_star(x=max(0, int(round(px_identified_target[0] - half_search_size))),
                                     y=max(0, int(round(px_identified_target[1] - half_search_size))),
                                     width=camera.adjust_roi_search_size,
                                     height=camera.adjust_roi_search_size)
                    guider.guide(recalibrate=False,
                                 roi=[int(round(camera.adjust_center_x)),
                                      int(round(camera.adjust_center_y)),
                                      int(round(camera.adjust_roi_search_size)),
                                      int(round(camera.adjust_roi_search_size))])
                    # msg = f"Done with moving telescope for adjust pointing, going to resume guiding"
                    # self.logger.debug(msg)
                    # guider.set_paused(paused=False)
                    # guider.wait_for_state(one_of_states=["Guiding", "SteadyGuiding"])
            pointing_status[0] = True
        except Exception as e:
            self.logger.error(f"Problem shooting image: {e}:{traceback.format_exc()}")
        finally:
            pointing_event.set()

    def get_default_star_strategy(self, pointing_image):
        if self.on_star_identification_failure == "get_brightest":
            return get_brightest_detection(pointing_image)
        elif self.on_star_identification_failure == "trust_astrometry":
            return pointing_image.get_center_coordinates()

    def acquire_pointing(self, camera, guiding_camera, observation, fits_headers, img_num):
        self.logger.debug("Taking pointing picture.")
        external_trigger = (camera is guiding_camera)

        self.logger.debug(f"Exposing for camera: {camera.name}")
        try:
            # Start the exposures
            camera_event = camera.take_observation(
                observation=observation,
                headers=fits_headers,
                filename='adjust_pointing{:02d}'.format(img_num),
                exp_time=camera.adjust_pointing_seconds * u.second,
                external_trigger=external_trigger
            )
            status = camera_event.wait(timeout=self.timeout_seconds)
            if not status:
                msg = f"Problem waiting for images: {e}:{traceback.format_exc()}"
                self.logger.error(msg)
                raise RuntimeError(msg)
        except Exception as e:
            self.logger.error(f"Problem waiting for images: {e}:{traceback.format_exc()}")
        pointing_id, pointing_path = observation.last_pointing
        pointing_image = Image(
            pointing_path
        )
        observation.adjust_pointing_image = pointing_image
        self.logger.debug(f"Adjust pointing file: {pointing_image}")

        return pointing_image
