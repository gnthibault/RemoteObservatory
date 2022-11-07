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
WAITING_MSG_INTERVAL = 5. * u.second
MAX_FOCUSING_TIME = 15 * 60 * u.second

def on_enter(event_data):
    """Wait for camera autofocus

    Periodically post to the STATUS
    channel and to the debug log.
    """
    #TODO TN DEBUG
    event_data.model.next_state = 'observing'
    return

    model = event_data.model
    model.next_state = 'parking'

    # First thing: if we are not at our first exposure, then assume the focus is still ok
    # and directly go to next step:
    observation = model.manager.current_observation
    if observation.current_exp % observation.number_exposures != 0:
        msg = f"Focusing state, current exposure is {observation.current_exp}, "\
              f"no need to refocus, jumping to next state"
        model.logger.debug(msg)
        model.say(msg)
        model.next_state = 'observing'
        return

    # Try to pause guiding first
    if model.manager.guider is not None:
        msg = f"Going to start focusing, need to pause guiding first"
        model.logger.debug(msg)
        model.say(msg)
        model.manager.guider.set_paused(paused=True)
        model.manager.guider.wait_for_state(one_of_states=["Paused"])

    try:
        model.say("Starting focusing")
        # Before each observation, we should refocus
        maximum_duration = MAX_FOCUSING_TIME
        start_time = model.manager.serv_time.get_astropy_time_from_utc()
        camera_events = model.manager.perform_cameras_autofocus(coarse=False)

        timeout = Timeout(maximum_duration)
        next_status_time = start_time + STATUS_INTERVAL
        next_msg_time = start_time + WAITING_MSG_INTERVAL

        while not all([event.is_set() for event in
                       camera_events.values()]):
            # check for important message in mq
            model.check_messages()
            if model.interrupted:
                model.say("Pre-observation autofocus interrupted!")
                break

            now = model.manager.serv_time.get_astropy_time_from_utc()
            if now >= next_msg_time:
                elapsed_secs = (now - start_time).to(u.second).value
                model.logger.debug(f"State: focusing, elapsed "
                                   f"{round(elapsed_secs)}")
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

    except error.Timeout as e:
        msg = f"Timeout while waiting for focusing: {e}. Something is wrong "\
              f"with camera/focuser, going to park" 
        model.logger.warning(msg)
        model.say(msg)
    except Exception as e:
        model.logger.warning(f"Problem with focusing, {e}: "
                             f"{traceback.format_exc()}")
        model.logger.warning(str(e))
        model.say(f"Exception while focusing {e}")
    else:
        if model.manager.guider is not None:
            msg = f"Finished with focusing, going to resume guiding"
            model.logger.debug(msg)
            model.say(msg)
            model.manager.guider.set_paused(paused=False)
            model.manager.guider.wait_for_state(one_of_states=["Guiding"])

        msg = f"Finished with focusing, going to observe"
        model.logger.debug(msg)
        model.say(msg)
        model.next_state = 'observing'
