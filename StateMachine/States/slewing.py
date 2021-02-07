def on_enter(event_data):
    """ Once inside the slewing state, set the mount slewing. """
    model = event_data.model
    model.next_state = 'parking'
    try:
        model.logger.debug(f"Inside slew state")

        # Stop guiding in case it was still there
        if model.manager.guider is not None:
            msg = f"Before slewing, about to stop guiding"
            model.logger.debug(msg)
            model.say(msg)
            model.manager.guider.stop_capture()

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
        model.logger.debug(f"Wait a minute, there was a problem slewing. "
                           f"Sending to parking. {e}")
