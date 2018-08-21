# Generic
from time import sleep

wait_interval = 15.
timeout = 900.

def on_enter(event_data):
    """ """
    model = event_data.model
    model.next_state = 'parking'

    try:
        model.logger.debug("Inside of observing state")
        # Start the observing
        #camera_events = model.manager.observe()

        wait_time = 0.
        #while not all([event.is_set() for event in camera_events.values()]):
        #    model.check_messages()
        #    if model.interrupted:
        #        model.logger.debug("Observation interrupted!")
        #        break

        #    model.logger.debug('Waiting for images: {} seconds'.format(wait_time))
        #    model.status()

        #    if wait_time > timeout:
        #        raise RuntimeError('Timeout error')

        #    sleep(wait_interval)
        #    wait_time += wait_interval

    except Exception as e:
        model.logger.warning('Problem with imaging: {}'.format(e))
    else:
        #model.manager.current_observation.current_exp += 1
        model.logger.debug('Finished with observing, going to analyze')
        model.next_state = 'analyzing'
