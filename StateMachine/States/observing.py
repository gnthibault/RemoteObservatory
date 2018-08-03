# Generic
from time import sleep

wait_interval = 15.
timeout = 900.

def on_enter(event_data):
    """ """
    infos = event_data.model
    infos.next_state = 'parking'

    try:
        infos.logger.debug("Inside of observing state")
        # Start the observing
        #camera_events = infos.manager.observe()

        wait_time = 0.
        #while not all([event.is_set() for event in camera_events.values()]):
        #    infos.check_messages()
        #    if infos.interrupted:
        #        infos.logger.debug("Observation interrupted!")
        #        break

        #    infos.logger.debug('Waiting for images: {} seconds'.format(wait_time))
        #    infos.status()

        #    if wait_time > timeout:
        #        raise RuntimeError('Timeout error')

        #    sleep(wait_interval)
        #    wait_time += wait_interval

    except Exception as e:
        infos.logger.warning('Problem with imaging: {}'.format(e))
    else:
        #infos.manager.current_observation.current_exp += 1
        infos.logger.debug('Finished with observing, going to analyze')
        infos.next_state = 'analyzing'
