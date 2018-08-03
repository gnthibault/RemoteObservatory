def on_enter(event_data):
    """
    Once in the `ready` state our unit has been initialized successfully.
    The next step is to schedule something for the night.
    """
    infos = event_data.model
    infos.logger.debug("Ok, I'm all set up and ready to go!")

    if infos.manager.has_ror and not infos.manager.open_ror():
        infos.logger.error("Failed to open the ror while entering state 'ready'")
        infos.next_state = 'parking'
    else:
        infos.manager.mount.unpark()
        infos.next_state = 'scheduling'
