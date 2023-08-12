# Generic stuff
import traceback

# Local stuff
from utils import error

def on_enter(event_data):
    """
    In the `scheduling` state we attempt to find a field using our scheduler.
    If field is found, make sure that the field is up right now (the scheduler
    should have taken care of this).
    If observable, set the mount to the field and calls `start_slewing`to
    begin slew.
    If no observable targets are available, park`the unit.
    """
    model = event_data.model
    model.status()
    model.next_state = "parking"

    model.say("Ok, I'm finding something good to look at...")
    existing_observation = model.manager.current_observation

    # Get the next observation
    try:
        observation = model.manager.get_observation()
        model.logger.info(f"Observation: {observation}")
    except error.NoObservation as e:
        model.say("No valid observations found. Cannot schedule. "
                  "Going to park.")
        model.next_state = "parking"
    except Exception as e:
        model.logger.warning(f"Error in scheduling: {e}, "
            f"{traceback.format_exc()}")
    else:

        if existing_observation and (observation.id == 
                                     existing_observation.id):
            model.say(f"I am sticking with observation {observation.id}")
            model.next_state = 'tracking' # TODO TN URGENT, the same logic as for the analyze/update tracking
            # applied here
        else:
            model.say(f"Got it! I am going to check out: {observation.name}")

            model.logger.debug(f"Setting Observation coords: "
                               f"{observation.target.coord}")
            if model.manager.mount.set_target_coordinates(
                               observation.target.coord):
                model.next_state = 'slewing'
            else:
                model.logger.warning("Field not properly set. Parking.")
