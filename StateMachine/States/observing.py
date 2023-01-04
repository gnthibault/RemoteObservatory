# Generic
import time
import traceback

# Astropy
from astropy import units as u

# Local
from utils import error
from utils import Timeout

SLEEP_SECONDS = 1.0
STATUS_INTERVAL = 10. * u.second
GUIDER_STATUS_INTERVAL = 5. * u.second
WAITING_MSG_INTERVAL = 5. * u.second
MAX_EXTRA_TIME = (60+SLEEP_SECONDS) * u.second

def on_enter(event_data):
    #TODO TN DEBUG
    #event_data.model.manager.guider = None
    """Wait for camera exposures to complete.

    Frequently check for the exposures to complete, the observation to be
    interrupted, messages to be received. Periodically post to the STATUS
    channel and to the debug log.
    """

    model = event_data.model
    model.status()
    model.say("Starting observing")
    model.next_state = 'parking'

    try:
        # Now manage actual acquisition
        maximum_duration = (model.manager.current_observation.time_per_exposure
                            + MAX_EXTRA_TIME)
        start_time = model.manager.serv_time.get_astropy_time_from_utc()
        camera_events = model.manager.observe()

        timeout = Timeout(maximum_duration)
        next_status_time = start_time + STATUS_INTERVAL
        next_guider_status_time = start_time + GUIDER_STATUS_INTERVAL
        next_msg_time = start_time + WAITING_MSG_INTERVAL

        while not all([event.is_set() for event in
                       camera_events.values()]):
            # check for important message in mq
            model.check_messages()
            if model.interrupted:
                model.say("Observation interrupted!")
                break

            now = model.manager.serv_time.get_astropy_time_from_utc()
            if now >= next_msg_time:
                elapsed_secs = (now - start_time).to(u.second).value
                model.logger.debug(f"State: observing, waiting for images: {round(elapsed_secs)}")
                next_msg_time += WAITING_MSG_INTERVAL
                now = model.manager.serv_time.get_astropy_time_from_utc()

            if (now >= next_guider_status_time and
                    model.manager.guider is not None):
                model.manager.guider.receive()
                assert(model.manager.guider.is_guiding_ok())
                next_guider_status_time += GUIDER_STATUS_INTERVAL
                now = model.manager.serv_time.get_astropy_time_from_utc()

            if now >= next_status_time:
                model.status()
                next_status_time += STATUS_INTERVAL

        if timeout.expired():
            raise error.Timeout

        # Sleep for a little bit.
        time.sleep(SLEEP_SECONDS)

    except error.Timeout as e:
        model.logger.warning("Timeout while waiting for images. Something wrong with camera, going to park.")
    except Exception as e:
        model.logger.warning(f"Problem with imaging, {e}: "
                             f"{traceback.format_exc()}")
        model.say("Hmm, I'm not sure what happened with that exposure.")
    else:
        model.manager.current_observation.current_exp += 1
        model.logger.debug('Finished with observing, going to analyze')
        model.next_state = 'analyzing'
