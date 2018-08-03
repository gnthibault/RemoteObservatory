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
    infos = event_data.model
    infos.next_state = 'parking'

    if infos.run_once and len(infos.manager.scheduler.observed_list) > 0:
        infos.logger.debug('Looks like we only wanted to run once, parking now')
    else:

        infos.logger.debug("Ok, I'm finding something good to look at...")
        existing_observation = infos.manager.current_observation

        # Get the next observation
        try:
            observation = infos.manager.get_observation()
            infos.logger.info("Observation: {}".format(observation))
        except error.NoObservation as e:
            infos.logger.debug('No valid observations found. Cannot schedule. '
                               'Going to park.')
        except Exception as e:
            infos.logger.warning("Error in scheduling: {}".format(e))
        else:

            if existing_observation and (observation.name == 
                                         existing_observation.name):
                infos.logger.debug('I am sticking with observation {}'.format(
                                   observation.name))
                infos.next_state = 'tracking'
            else:
                infos.logger.debug('Got it! I am going to check out:'
                                   '{}'.format(observation.name))

                infos.logger.debug('Setting Observation coords: {}'.format(
                                   observation.field))
                if infos.manager.mount.set_target_coordinates(
                                       observation.field):
                    infos.next_state = 'slewing'
                else:
                    infos.logger.warning("Field not properly set. Parking.")
