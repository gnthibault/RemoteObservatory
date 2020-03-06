def on_enter(event_data):
    """ Once inside the slewing state, set the mount slewing. """
    model = event_data.model
    try:
        model.logger.debug(f"Inside slew state")

        # Wait until mount is_tracking, then transition to track state
        model.logger.debug(f"I am slewing over to the coordinates to track "
                           f"the target.")

        # Start the mount slewing, should use slew_to_coord_and_track
        model.manager.slew()

        msg = f"I am at the target, checking pointing."
        model.logger.debug(msg)
        model.say(msg)
        model.next_state = 'pointing'

    except Exception as e:
        model.logger.debug('Wait a minute, there was a problem slewing. '
                           'Sending to parking. {}'.format(e))
