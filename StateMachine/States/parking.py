def on_enter(event_data):
    """ """
    model = event_data.model

    # Clear any current observation
    model.manager.current_observation = None
    model.manager.current_offset_info = None

    model.next_state = 'parked'

    if model.manager.has_ror:
        model.logger.debug('Closing ror')
        if not model.manager.close_ror():
            model.logger.critical('Unable to close ror!')
            model.logger.debug('Unable to close ror!')

    model.logger.debug("Taking it on home and then parking.")
    model.manager.mount.park()
