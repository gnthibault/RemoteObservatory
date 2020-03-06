# Generic
from time import sleep
import traceback

# Numerical stuff
import numpy as np

# Astropy
import astropy.units as u

# Local
from Imaging.Image import Image
from Imaging.Image import OffsetError
from utils.error import PointingError

SLEEP_SECONDS = 5.
TIMEOUT_SECONDS = 150.
MAX_NUM_POINTING_IMAGES = 5

max_pointing_error = OffsetError(2*u.arcsec, 2*u.arcsec, 2*u.arcsec)


def on_enter(event_data):
    """Pointing State

    Take 30 second exposure and plate-solve to get the pointing error
    """
    model = event_data.model
    model.next_state = 'parking'

    try:

        img_num = 0
        pointing_error = OffsetError(*(np.inf*u.arcsec,)*3)
        pointing_error_stack = {}

        while (img_num < MAX_NUM_POINTING_IMAGES and
               pointing_error.magnitude > max_pointing_error.magnitude):

            # Eventually adjust by slewing again to the target
            if ( img_num > 0 and 
                 pointing_error.magnitude > max_pointing_error.magnitude):
                model.manager.mount.slew_to_target()

            model.say("Taking pointing picture.")
            observation = model.manager.current_observation
            fits_headers = model.manager.get_standard_headers(
                observation=observation
            )
            fits_headers['POINTING'] = 'True'
            model.logger.debug("Pointing headers: {}".format(fits_headers))
            camera_events = dict()

            for cam_name, camera in model.manager.cameras.items():
                if camera.is_primary:
                    model.logger.debug("Exposing for camera: {}".format(
                                        cam_name))
                    try:
                        # Start the exposures
                        camera_event = camera.take_observation(
                            observation,
                            fits_headers,
                            exp_time=30.*u.second,
                            filename='pointing{:02d}'.format(img_num)
                        )

                        camera_events[cam_name] = camera_event

                    except Exception as e:
                        model.logger.error(f"Problem waiting for images: "
                          f"{e}:{traceback.format_exc()}")

            wait_time = 0.
            while not all([event.is_set() for event in camera_events.values()]):
                model.check_messages()
                if model.interrupted:
                    model.say("Observation interrupted!")
                    break

                model.logger.debug(f"State: pointing, waiting for images: "
                    '{wait_time} seconds')
                model.status()

                if wait_time > TIMEOUT_SECONDS:
                    raise RuntimeError("Timeout waiting for pointing image")

                sleep(SLEEP_SECONDS)
                wait_time += SLEEP_SECONDS

            if model.manager.current_observation is not None:
                #TODO Integrate this feature with our own solver class
                pointing_id, pointing_path = (
                    model.manager.current_observation.last_exposure)
                pointing_image = Image(
                    pointing_path,
                    location=model.manager.earth_location
                )

                pointing_image.solve_field(verbose=True)
                observation.pointing_image = pointing_image
                model.logger.debug("Pointing file: {}".format(pointing_image))
                pointing_error = pointing_image.pointing_error
                model.say("Ok, I have the pointing picture, "
                          "let's see how close we are.")
                model.logger.debug(f"Pointing Coords: "
                                   f"{pointing_image.pointing}")
                msg = f"Pointing Error: {pointing_error}"
                model.logger.debug(msg)
                model.say(msg)
                # update mount with the actual position
                model.manager.mount.sync_to_coord(pointing_image.pointing)
                # update pointing process tracking information
                pointing_error_stack[img_num] = pointing_error
                img_num = img_num + 1
                
        if pointing_error.magnitude > max_pointing_error.magnitude:
            raise PointingError('Pointing accuracy was not good enough after '
                                '{} iterations, pointing error stack was: {}'
                                ''.format(img_num, pointing_error_stack))

        model.next_state = 'tracking'

    except Exception as e:
        msg = ('Hmm, I had a problem checking the pointing error. '
                  'Going to park. {}:{}'.format(e, traceback.format_exc()))
        model.logger.error(msg)
        model.say(msg)
