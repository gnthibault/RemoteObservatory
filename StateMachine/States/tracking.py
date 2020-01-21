
def on_enter(event_data):
    """ The unit is tracking the target. Proceed to observations. """
    model = event_data.model
    model.next_state = 'parking'

    # If we came from pointing then don't try to dither
    if event_data.transition.source != 'pointing':
        model.logger.debug("Checking our tracking")
        try:
            # most likely setup dithering
            model.manager.update_tracking()
            model.logger.debug('Done with tracking adjustment, going to '
                               'observe')
            model.next_state = 'observing'
        except Exception as e:
            model.logger.warning("Problem adjusting tracking: {}".format(e))
    else:
        try:
            if model.manager.initialize_tracking():
                model.next_state = 'observing'
        except Exception as e:
            model.logger.warning("Problem initializing tracking: {}".format(e))
