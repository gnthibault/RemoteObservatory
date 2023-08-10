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
WAITING_MSG_INTERVAL = 15. * u.second
MAX_POINTING_TIME = 900.


def on_enter(event_data):
    #TODO TN DEBUG
    #event_data.model.next_state = 'tracking'
    #return
    """Pointing State

    Take 30 second exposure and plate-solve to get the pointing error
    """
    model = event_data.model
    model.status()
    model.next_state = 'parking'

    model.logger.debug("About to starts fine pointing")
    try:
        observation = model.manager.current_observation
        # Before each observation, we make sure we point at the right target
        model.say(f"Starts pointing to observation: {observation}")
        fits_headers = model.manager.get_standard_headers(observation=observation)
        fits_headers["POINTING"] = "True"
        start_time = model.manager.serv_time.get_astropy_time_from_utc()
        pointing_event, pointing_status = model.manager.points(
            mount=model.manager.mount,
            camera=model.manager.pointing_camera,
            observation=observation,
            fits_headers=fits_headers
        )

        timeout = Timeout(MAX_POINTING_TIME)
        next_status_time = start_time + STATUS_INTERVAL
        next_msg_time = start_time + WAITING_MSG_INTERVAL

        while not pointing_event.is_set():

            # check for important message in mq
            model.check_messages()
            if model.interrupted:
                model.say("Pre-observation pointing interrupted!")
                break

            now = model.manager.serv_time.get_astropy_time_from_utc()
            if now >= next_msg_time:
                elapsed_secs = (now - start_time).to(u.second).value
                model.logger.debug(f"State: pointing, elapsed {round(elapsed_secs)}")
                next_msg_time += WAITING_MSG_INTERVAL
                now = model.manager.serv_time.get_astropy_time_from_utc()

            if now >= next_status_time:
                model.status()
                next_status_time += STATUS_INTERVAL
                now = model.manager.serv_time.get_astropy_time_from_utc()

            if timeout.expired():
                raise error.Timeout

            # Sleep for a little bit.
            time.sleep(SLEEP_SECONDS)

        if not pointing_status[0]:
            raise Exception("Pointing has failed")

    except error.Timeout as e:
        msg = f"Timeout while waiting for pointing: {e}. Something is wrong, going to park"
        model.logger.warning(msg)
        model.say(msg)
    except Exception as e:
        msg = (f"Problem with pointing: {e}:{traceback.format_exc()}")
        model.logger.error(msg)
        model.say(msg)
    else:
        msg = f"Done with pointing"
        model.logger.debug(msg)
        model.say(msg)
        model.next_state = 'tracking'
