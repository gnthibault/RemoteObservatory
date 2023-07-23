
def on_enter(event_data):
    #TODO TN DEBUG
    #event_data.model.next_state = 'focusing'
    #return

    """ The unit is tracking the target. Proceed to observations. """
    model = event_data.model
    model.status()
    model.next_state = 'parking'

    # If we came from pointing then don't try to dither
    if event_data.transition.source != 'pointing':
        model.logger.debug("Checking our tracking")
        try:
            # most likely setup dithering
            model.manager.update_tracking()
            msg = f"Done with tracking adjustment, going to focus"
            model.logger.debug(msg)
            model.say(msg)
            model.next_state = 'focusing'
        except Exception as e:
            model.logger.warning(f"Problem adjusting tracking: {e}")
    else:
        try:
            if model.manager.initialize_tracking():
                msg = f"Tracking successfully initialized, going to focus"
                model.logger.debug(msg)
                model.say(msg)
                model.next_state = 'focusing'
        except Exception as e:
            model.logger.warning(f"Problem initializing tracking: {e}")
