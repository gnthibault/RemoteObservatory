
def on_enter(event_data):
    """ The unit is tracking the target. Proceed to observations. """
    infos = event_data.model
    infos.next_state = 'parking'

    # If we came from pointing then don't try to adjust
    if event_data.transition.source != 'pointing':
        infos.logger.debug("Checking our tracking")
        try:
            infos.manager.update_tracking()
            infos.logger.debug('Done with tracking adjustment, going to '
                               'observe')
            infos.next_state = 'observing'
        except Exception as e:
            infos.logger.warning("Problem adjusting tracking: {}".format(e))
    else:
        infos.next_state = 'observing'
