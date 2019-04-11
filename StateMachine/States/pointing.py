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

wait_interval = 5.
timeout = 150.
max_num_pointing_images = 5
max_pointing_error = OffsetError(14*u.arcsec, 14*u.arcsec, 20*u.arcsec)

def on_enter(event_data):
    """Pointing State

    Take 30 second exposure and plate-solve to get the pointing error
    """
    model = event_data.model
    model.next_state = 'parking'

    try:

        img_num = 0
        pointing_error = OffsetError(*(np.inf*u.arcsec,)*3)

        while (img_num < max_num_pointing_images and
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
                        model.logger.error('Problem waiting for images: '
                            '{}:{}'.format(e,traceback.format_exc()))

            wait_time = 0.
            while not all([event.is_set() for event in camera_events.values()]):
                model.check_messages()
                if model.interrupted:
                    model.say("Observation interrupted!")
                    break

                model.logger.debug('Waiting for images: {} seconds'.format(
                                   wait_time))
                model.status()

                if wait_time > timeout:
                    raise RuntimeError("Timeout waiting for pointing image")

                sleep(wait_interval)
                wait_time += wait_interval

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
                model.say('Ok, I\'ve got the pointing picture, '
                          'let\'s see how close we are.')
                model.logger.debug('Pointing Coords: {}'.format(
                                   pointing_image.pointing))
                model.logger.debug('Pointing Error: {}'.format(
                                   pointing_error))
                # update mount with the actual position
                model.manager.mount.sync_to_coord(pointing_image.pointing)
                

        model.next_state = 'tracking'

    except Exception as e:
        model.say('Hmm, I had a problem checking the pointing error. '
                  'Going to park. {}:{}'.format(e, traceback.format_exc()))
