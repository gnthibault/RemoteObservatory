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
    model.next_state = 'parking'

    model.say("Ok, I'm finding something good to look at...")
    existing_observation = model.manager.current_observation

    # Get the next observation
    try:
        observation = model.manager.get_observation()
        model.logger.info("Observation: {}".format(observation))
    except error.NoObservation as e:
        model.say('No valid observations found. Cannot schedule. '
                  'Going to park.')
    except Exception as e:
        model.logger.warning("Error in scheduling: {}".format(e))
    else:

        if existing_observation and (observation.name == 
                                     existing_observation.name):
            model.say('I am sticking with observation {}'.format(
                      observation.name))
            model.next_state = 'tracking'
        else:
            model.say('Got it! I am going to check out:'
                      '{}'.format(observation.name))

            model.logger.debug('Setting Observation coords: {}'.format(
                               observation.field))
            if model.manager.mount.set_target_coordinates(
                                   observation.field):
                model.next_state = 'slewing'
            else:
                model.logger.warning("Field not properly set. Parking.")
