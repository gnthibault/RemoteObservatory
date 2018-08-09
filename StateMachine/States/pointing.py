# Generic
from time import sleep

# Local
#from pocs.images import Image

wait_interval = 3.
timeout = 150.

num_pointing_images = 1

def on_enter(event_data):
    """Pointing State

    Take 30 second exposure and plate-solve to get the pointing error
    """
    infos = event_data.model
    infos.next_state = 'parking'

    try:
        infos.logger.debug("Taking pointing picture.")
        observation = infos.manager.current_observation
        fits_headers = infos.manager.get_standard_headers(
            observation=observation
        )
        fits_headers['POINTING'] = 'True'
        infos.logger.debug("Pointing headers: {}".format(fits_headers))

        for img_num in range(num_pointing_images):
            camera_events = dict()

            for cam_name, camera in infos.manager.cameras.items():
                if camera.is_primary:
                    infos.logger.debug("Exposing for camera: {}".format(
                                        cam_name))
                    try:
                        # Start the exposures
                        camera_event = camera.take_observation(
                            observation,
                            fits_headers,
                            exp_time=30.,
                            filename='pointing{:02d}'.format(img_num)
                        )

                        camera_events[cam_name] = camera_event

                    except Exception as e:
                        infos.logger.error('Problem waiting for images: '
                                           '{}'.format(e))

            wait_time = 0.
            while not all([event.is_set() for event in camera_events.values()]):
                infos.check_messages()
                if infos.interrupted:
                    infos.logger.debug("Observation interrupted!")
                    break

                infos.logger.debug('Waiting for images: {} seconds'.format(
                                   wait_time))
                infos.status()

                if wait_time > timeout:
                    raise RuntimeError("Timeout waiting for pointing image")

                sleep(wait_interval)
                wait_time += wait_interval

            if infos.manager.current_observation is not None:
                #TODO Integrate this feature with our own solver class
                #pointing_id, pointing_path = (
                #    infos.manager.current_observation.last_exposure)
                #pointing_image = Image(
                #    pointing_path,
                #    location=infos.manager.earth_location
                #)

                #pointing_image.solve_field()
                #observation.pointing_image = pointing_image
                #infos.logger.debug("Pointing file: {}".format(pointing_image))
                #infos.logger.debug('Pointing Coords: {}',
                #                   pointing_image.pointing)
                #infos.logger.debug('Pointing Error: {}',
                #                   pointing_image.pointing_error)
                infos.logger.debug('Analyzing and checking pointing image')

        infos.next_state = 'tracking'

    except Exception as e:
        infos.logger.debug('Hmm, I had a problem checking the pointing error. '
                           'Going to park. {}'.format(e))