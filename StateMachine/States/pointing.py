# Generic
from time import sleep
import traceback

# Astropy
import astropy.units as u

# Local
from Imaging.Image import Image

wait_interval = 5.
timeout = 150.
num_pointing_images = 1

def on_enter(event_data):
    """Pointing State

    Take 30 second exposure and plate-solve to get the pointing error
    """
    model = event_data.model
    model.next_state = 'parking'

    try:
        model.say("Taking pointing picture.")
        observation = model.manager.current_observation
        fits_headers = model.manager.get_standard_headers(
            observation=observation
        )
        fits_headers['POINTING'] = 'True'
        model.logger.debug("Pointing headers: {}".format(fits_headers))

        for img_num in range(num_pointing_images):
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
                model.say('Ok, I\'ve got the pointing picture, '
                          'let\'s see how close we are.')
                model.logger.debug('Pointing Coords: {}'.format(
                                   pointing_image.pointing))
                model.logger.debug('Pointing Error: {}'.format(
                                   pointing_image.pointing_error))

        model.next_state = 'tracking'

    except Exception as e:
        model.say('Hmm, I had a problem checking the pointing error. '
                  'Going to park. {}:{}'.format(e, traceback.format_exc()))
