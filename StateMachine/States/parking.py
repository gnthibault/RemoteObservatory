def on_enter(event_data):
    """ """
    model = event_data.model
    model.status()

    # Clear any current observation
    model.manager.current_observation = None
    model.manager.current_offset_info = None

    model.next_state = 'parked'

    msg = f"Taking it on home and then parking."
    model.say(msg)
    
    if not model.manager.park():
        msg = f"Unable to park everything"
        model.logger.critical(msg)
        model.say(msg)

    if not model.manager.close_observatory():
        msg = f"Unable to close observatory!"
        model.logger.critical(msg)
        model.say(msg)