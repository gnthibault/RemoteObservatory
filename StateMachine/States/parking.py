def on_enter(event_data):
    """ """
    model = event_data.model

    # Clear any current observation
    model.manager.current_observation = None
    model.manager.current_offset_info = None

    model.next_state = 'parked'

    model.logger.debug("Taking it on home and then parking.")
    model.manager.park()
    
    if not model.manager.observatory.close_everything():
        model.logger.critical('Unable to close dome!')
        model.logger.debug('Unable to close dome!')


