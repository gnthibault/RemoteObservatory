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
                gen_hips=False,
                timeout_seconds=150,
                max_iterations=5,
                max_pointing_error_seconds=3
            )

        self.gen_hips        = config["gen_hips"]
        self.timeout_seconds = config["timeout_seconds"]
        self.max_iterations  = config["max_iterations"]
        self.max_pointing_error = OffsetError(*(config["max_pointing_error_seconds"]*u.arcsec,)*3)

    def points(self, mount, camera, observation, fits_headers):
        pointing_event = threading.Event()
        pointing_status = [False]
        w = threading.Thread(target=self.points_async,
                             kwargs={
                                 "mount": mount,
                                 "camera": camera,
                                 "observation": observation,
                                 "fits_headers": fits_headers,
                                 "pointing_event": pointing_event,
                                 "pointing_status": pointing_status})
        w.start()
        return pointing_event, pointing_status

    def points_async(self, mount, camera, observation, fits_headers, pointing_event, pointing_status):
        try:
            img_num = 0
            pointing_error = OffsetError(*(np.inf * u.arcsec,) * 3)
            pointing_error_stack = {}

            while (img_num < self.max_iterations and pointing_error.magnitude > self.max_pointing_error.magnitude):

                # Eventually adjust by slewing again to the target
                if img_num > 0 and pointing_error.magnitude > self.max_pointing_error.magnitude:
                    mount.slew_to_target()

                self.logger.info("Taking pointing picture.")
                observation = observation
                self.logger.debug(f"Pointing headers: {fits_headers}")
                camera_events = dict()

                self.logger.debug(f"Exposing for camera: {camera.name}")
                try:
                    # Start the exposures
                    camera_event = camera.take_observation(
                        observation=observation,
                        headers=fits_headers,
                        filename='pointing{:02d}'.format(img_num),
                        exp_time=camera.pointing_seconds * u.second,
                    )
                except Exception as e:
                    self.logger.error(f"Problem shooting image: {e}:{traceback.format_exc()}")
                    break

                status = camera_event.wait(timeout=self.timeout_seconds)
                if not status:
                    self.logger.error(f"Problem waiting for images: {e}:{traceback.format_exc()}")
                    break

                # TODO Integrate this feature with our own solver class
                pointing_id, pointing_path = (
                    observation.last_pointing)
                pointing_image = Image(pointing_path)

                pointing_image.solve_field(verbose=True, gen_hips=self.gen_hips)
                observation.pointing_image = pointing_image
                self.logger.debug(f"Pointing file: {pointing_image}")
                pointing_error = pointing_image.pointing_error()
                self.logger.info("Ok, I have the pointing picture, let's see how close we are.")
                self.logger.debug(f"Pointing Coords: {pointing_image.pointing}")
                self.logger.debug(f"Pointing Error: {pointing_error}")
                # update mount with the actual position
                mount.sync_to_coord(pointing_image.pointing)
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
                pointing_status[0] = True
        except Exception as e:
            self.logger.error(f"Issue while pointing: {e}")
        finally:
            pointing_event.set()
def on_enter(event_data):
    #TODO TN DEBUG
    #event_data.model.next_state = 'observing'
    #return
    """Offset Pointing State

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
    model = event_data.model
    model.status()
    model.next_state = 'parking'

    if model.manager.adjust_pointing_camera is None:
        model.logger.info(f"No adjust camera settings are set, skipping offset_pointing")
        model.next_state = 'observing'
        return

    # Prepare offset pointing acquisitions
    observation = model.manager.current_observation

    try:
        img_num = 0
        pointing_image = acquire_pointing(model, observation, img_num)
        try:
            # Attempt to solve field
            pointing_image.solve_field(verbose=True, gen_hips=False, remove_extras=False, skip_solved=False)
            # update mount with the actual position
            #if not model.manager.mount.is_simulator:
            #    model.manager.mount.sync_to_coord(pointing_image.pointing)

            # Now analyse the solved image
            px_identified_target = find_best_candidate_star(pointing_image,
                                                            observation.target.coord,
                                                            max_identification_error)
            if px_identified_target is None:
                msg = f"Cannot identify a star from {pointing_image.fits_file} while in offset_pointing state, will "\
                      f"only rely on brightest detected star"
                model.logger.warning(msg)
                px_identified_target = get_brightest_detection(pointing_image)

        except AstrometrySolverError as e:
            msg = f"Cannot solve image {pointing_image.fits_file} while in offset_pointing state: {e}"
            model.logger.warning(msg)
            px_identified_target = get_brightest_detection(pointing_image)

        # # compute offseted coordinates
        # coordinate_to_be_centered = compute_coordinate_to_be_centered(
        #     pointing_image.pointing,
        #     pointing_image.wcs,
        #     model.manager.adjust_pointing_camera.adjust_center_x,
        #     model.manager.adjust_pointing_camera.adjust_center_y,
        #     px_identified_target)

        if model.manager.guider is not None:
            camera = model.manager.adjust_pointing_camera
            # If guider was locked on another star, then restart guiding
            if not model.manager.guider.is_lock_position_close_to(px_target=px_identified_target,
                                                                  max_angle_sep=1*u.arcsec):
                model.manager.guider.stop_capture()
                model.manager.guider.loop()
                half_search_size = camera.adjust_roi_search_size/2
                model.manager.guider.find_star(x=max(0, int(round(px_identified_target[0]-half_search_size))),
                                               y=max(0, int(round(px_identified_target[1]-half_search_size))),
                                               width=camera.adjust_roi_search_size,
                                               height=camera.adjust_roi_search_size)
                model.manager.guider.guide(recalibrate=False,
                                           roi=[int(round(camera.adjust_center_x)),
                                                int(round(camera.adjust_center_y)),
                                                int(round(camera.adjust_roi_search_size)),
                                                int(round(camera.adjust_roi_search_size))])
            model.manager.guider.set_lock_position(camera.adjust_center_x,
                                                   camera.adjust_center_y,
                                                   exact=True,
                                                   wait_reached=True,
                                                   angle_sep_reached=2*u.arcsec)
            # TODO TN we would need a concept of uncertainty based on seeing and sampling here

        # Now adjust by slewing to the specified counter-offseted coordinates
        # model.manager.mount.set_target_coordinates(coordinate_to_be_centered)
        # model.manager.mount.slew_to_target()

        # Ready for observing
        model.next_state = 'observing'

    except Exception as e:
        msg = (f"Hmm, I had a problem pointing to offseted coordinates. Going to park. {e}:{traceback.format_exc()}")
        model.logger.error(msg)
        model.say(msg)

def acquire_pointing(model, observation, img_num):

    model.say("Taking pointing picture.")

    # Prepare offset pointing camera
    camera = model.manager.adjust_pointing_camera
    fits_headers = model.manager.get_standard_headers(observation=observation)
    fits_headers["POINTING"] = "True"

    # # Try to pause guiding if needed
    # if model.manager.guider is not None:
    #     msg = f"Going to start acquisitions for adjust pointing, need to pause guiding acquisition"
    #     model.logger.debug(msg)
    #     model.manager.guider.set_paused(paused=True)
    #     model.manager.guider.wait_for_state(one_of_states=["Paused"])

    external_trigger = (camera is model.manager.guiding_camera)

    camera_events = dict()
    model.logger.debug(f"Exposing for camera: {camera.name}")
    try:
        # Start the exposures
        camera_event = camera.take_observation(
            observation=observation,
            headers=fits_headers,
            filename='adjust_pointing{:02d}'.format(img_num),
            exp_time=camera.adjust_pointing_seconds * u.second,
            external_trigger=external_trigger
        )
        camera_events[camera.name] = camera_event
    except Exception as e:
        model.logger.error(f"Problem waiting for images: {e}:{traceback.format_exc()}")
    wait_time = 0.
    while not all([event.is_set() for event in camera_events.values()]):
        model.check_messages()
        if model.interrupted:
            model.say("Observation interrupted!")
            break
        model.logger.debug(f"State: offset_pointing, waiting for images: {wait_time} seconds")
        model.status()
        if wait_time > TIMEOUT_SECONDS:
            raise RuntimeError("Timeout waiting for pointing image")
        sleep(SLEEP_SECONDS)
        wait_time += SLEEP_SECONDS
    pointing_id, pointing_path = model.manager.current_observation.last_pointing
    pointing_image = Image(
        pointing_path,
        location=model.manager.earth_location
    )
    observation.adjust_pointing_image = pointing_image
    model.logger.debug(f"Pointing file: {pointing_image}")

    # if model.manager.guider is not None:
    #     msg = f"Done with acquisitions for adjust pointing, going to resume guiding"
    #     model.logger.debug(msg)
    #     model.manager.guider.set_paused(paused=False)
    #     model.manager.guider.wait_for_state(one_of_states=["Guiding", "SteadyGuiding"])

    return pointing_image