def on_enter(event_data):
    """
    Once in the `ready` state our unit has been initialized successfully.
    The next step is to schedule something for the night.
    """
    model = event_data.model
    model.logger.debug("Ok, I'm all set up and ready to go!")

    if not model.manager.observatory.open_everything():
        model.logger.error('Failed to open observatory while entering state'
                           'ready')
        model.next_state = 'parking'
    else:
        model.manager.mount.unpark()
        model.next_state = 'scheduling'
