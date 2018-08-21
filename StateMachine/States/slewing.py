def on_enter(event_data):
    """ Once inside the slewing state, set the mount slewing. """
    model = event_data.model
    try:
        model.logger.debug("Inside slew state")

        # Start the mount slewing, should use slew_to_coord_and_track
        model.manager.slew_to_target()

        # Wait until mount is_tracking, then transition to track state
        model.logger.debug('I am slewing over to the coordinates to track the '
                           'target.')

        while not model.manager.mount.is_tracking:
            model.logger.debug('Slewing to target')
            model.sleep()

        model.logger.debug('I am at the target, checking pointing.')
        model.next_state = 'pointing'

    except Exception as e:
        model.logger.debug('Wait a minute, there was a problem slewing. '
                           'Sending to parking. {}'.format(e))
