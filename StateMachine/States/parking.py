def on_enter(event_data):
    """ """
    infos = event_data.model

    # Clear any current observation
    infos.manager.current_observation = None
    infos.manager.current_offset_info = None

    infos.next_state = 'parked'

    if infos.manager.has_ror:
        infos.logger.debug('Closing ror')
        if not infos.manager.close_ror():
            infos.logger.critical('Unable to close ror!')
            infos.logger.debug('Unable to close ror!')

    infos.logger.debug("Taking it on home and then parking.")
    infos.manager.mount.park()
