# Generic
import threading
import traceback

# Astropy
from astropy.coordinates import SkyCoord

# Local
from utils.error import AstrometrySolverError, ImageAcquisitionError

# Astropy
import astropy.units as u

# Local
from Imaging.Image import OffsetError
from Pointer.OffsetPointer import OffsetPointer

class InvisibleObjectOffsetPointer(OffsetPointer):
    def __init__(self, config=None):
        if config is None:
            config = dict(
                timeout_seconds=300,
                sync_mount_upon_solve=False,
                max_iterations=5,
                max_pointing_error_seconds=2
            )
        super().__init__(config=config)

        self.max_iterations = config["max_iterations"]
        self.max_pointing_error = OffsetError(*(config["max_pointing_error_seconds"] * u.arcsec,) * 3)

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

    def offset_points_async(self, mount, camera, guiding_camera, guider, observation, fits_headers,
                            pointing_event,
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
            # Our first action is to stop guiding
            if guider is not None:
                msg = f"Going to adjust pointing, need to stop guiding"
                self.logger.debug(msg)
                guider.stop_capture()
                try:
                    exp_time_sec = guiding_camera.is_remaining_exposure_time()
                    guiding_camera.synchronize_with_image_reception(exp_time_sec=exp_time_sec)
                except ImageAcquisitionError as e:
                    pass

            img_num = 0
            pointing_error = OffsetError(*(np.inf * u.arcsec,) * 3)
            pointing_error_stack = {}

            while (img_num < self.max_iterations and pointing_error.magnitude > self.max_pointing_error.magnitude):
                pointing_image = self.acquire_pointing(camera, guiding_camera, observation, fits_headers,
                                                       img_num)
                try:
                    # Attempt to solve field
                    pointing_image.solve_field(verbose=True,
                                               gen_hips=False,
                                               remove_extras=False,
                                               skip_solved=False,
                                               use_header_position=True,
                                               sampling_arcsec=camera.sampling_arcsec)
                    # update mount with the actual position
                    if self.sync_mount_upon_solve:
                        mount.sync_to_coord(pointing_image.pointing)
                    px_identified_target = pointing_image.get_center_coordinates()
                except AstrometrySolverError as e:
                    msg = f"Cannot solve image {pointing_image.fits_file} while in offset_pointing state: {e}"
                    self.logger.error(msg)
                    raise RuntimeError(msg)
                    # TODO TN We can decide to assume that main camera is already pointing to the expected object

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
                offset_delta_ra = current_sky_coord_of_target_sensor_position.ra - current_sky_coord_of_target_star.ra
                offset_delta_dec = current_sky_coord_of_target_sensor_position.dec - current_sky_coord_of_target_star.dec
                # adjust by slewing to the opposite of the delta
                current = mount.get_current_coordinates()
                target = SkyCoord(
                    ra=current.ra + pointing_error.delta_ra - offset_delta_ra,
                    dec=current.dec + pointing_error.delta_dec - offset_delta_dec,
                    frame='icrs', equinox='J2000.0')
                # Now adjust by slewing to the specified counter-offseted coordinates
                mount.slew_to_coord(target)

                # update pointing process tracking information
                pointing_error_stack[img_num] = pointing_error
                img_num = img_num + 1

            if pointing_error.magnitude > self.max_pointing_error.magnitude:
                self.logger.error(f"Pointing accuracy was not good enough after "
                                  f"{img_num} iterations, pointing error stack was: "
                                  f"{pointing_error_stack}")
                pointing_status[0] = False
            else:
                self.logger.info(f"Pointing accuracy was estimated good enough after "
                                 f"{img_num} iterations, pointing error stack was: "
                                 f"{pointing_error_stack}")
                if guider is not None:
                    guider.find_star() # Star have changed position, we need to force re-detect stars
                    guider.guide(recalibrate=False)
                    pointing_status[0] = True
        except Exception as e:
            self.logger.error(f"Problem adjusting image: {e}:{traceback.format_exc()}")
        finally:
            pointing_event.set()