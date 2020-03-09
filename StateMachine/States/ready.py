def on_enter(event_data):
    """
    Once in the `ready` state our unit has been initialized successfully.
    The next step is to schedule something for the night.
    """
    model = event_data.model
    model.logger.debug("Ok, I'm all set up and ready to go!")
    model.next_state = 'parking'

    # First open physical builing if applicable
    if not model.manager.open_observatory():
        model.logger.error('Failed to open observatory while entering state'
                           'ready')
        model.next_state = 'parking'
        return

    # Then unpark / initialize everything if applicable
    if not model.manager.unpark():
        model.logger.error('Failed to unpark observatory while entering '
                           'state ready')
        model.next_state = 'parking'
        return

    model.next_state = 'scheduling'
