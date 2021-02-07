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
MAX_CALIBRATION_TIME = 60 * 60 * u.second

def on_enter(event_data):
    """Wait for system calibration

    Periodically post to the STATUS
    channel and to the debug log.
    """

    model = event_data.model
    model.next_state = 'housekeeping'

    try:
        model.say("Starting calibrations acquisition")
        maximum_duration = MAX_CALIBRATION_TIME
        start_time = model.manager.serv_time.get_astropy_time_from_utc()
        calibration_over_events = model.manager.acquire_calibration()

        timeout = Timeout(maximum_duration)
        next_status_time = start_time + STATUS_INTERVAL
        next_msg_time = start_time + WAITING_MSG_INTERVAL

        while not all([event.is_set() for event in
                       calibration_over_events.values()]):
            # check for important message in mq
            model.check_messages()
            if model.interrupted:
                model.say("Post-observation calibration interrupted!")
                break

            now = model.manager.serv_time.get_astropy_time_from_utc()
            if now >= next_msg_time:
                elapsed_secs = (now - start_time).to(u.second).value
                model.logger.debug(f"State: calib_acq, elapsed "
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
        msg = f"Timeout while waiting for calibration acquisition: {e}."\
              f"Something is wrong with the system, going back to housekeeping" 
        model.logger.warning(msg)
        model.say(msg)
    except Exception as e:
        msg = f"Problem with calibration acquisition, {e}: {traceback.format_exc()}"
        model.logger.warning(msg)
        model.say(f"Exception while acquiring calibration {e}")
    else:
        msg = f"Finished with calibration acquisition, going to housekeeping"
        model.logger.debug(msg)
        model.say(msg)
        model.next_state = 'housekeeping'
