def on_enter(event_data):
    """ Once inside the slewing state, set the mount slewing. """
    infos = event_data.model
    try:
        infos.logger.debug("Inside slew state")

        # Start the mount slewing, should use slew_to_coord_and_track
        infos.manager.slew_to_target()

        # Wait until mount is_tracking, then transition to track state
        infos.logger.debug('I am slewing over to the coordinates to track the '
                           'target.')

        while not infos.manager.mount.is_tracking:
            infos.logger.debug('Slewing to target')
            infos.sleep()

        infos.logger.debug('I am at the target, checking pointing.')
        infos.next_state = 'pointing'

    except Exception as e:
        infos.logger.debug('Wait a minute, there was a problem slewing. '
                           'Sending to parking. {}'.format(e))
