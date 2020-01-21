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
MAX_FOCUSING_TIME = 5 * 60 * u.second

def on_enter(event_data):
    """Wait for camera autofocus

    Periodically post to the STATUS
    channel and to the debug log.
    """

    model = event_data.model
    model.say("Starting focusing")
    model.next_state = 'parking'

    try:
        # Before each observation, we should refocus
        maximum_duration = MAX_FOCUSING_TIME
        start_time = model.manager.serv_time.get_astropy_time_from_utc()
        camera_events = model.manager.autofocus_cameras(coarse=False)

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
        model.logger.warning("Timeout while waiting for focusing. Something is"
                             "wrong either with camera/focuser, going to park")
    except Exception as e:
        model.logger.warning(f"Problem with focusing, {e}: "
                             f"{traceback.format_exc()}")
        model.say("Problem while focusing")
    else:
        model.logger.debug('Finished with focusing, going to observe')
        model.next_state = 'observing'
