def on_enter(event_data):
    """ """
    infos = event_data.model

    if infos.should_retry is False:
        infos.logger.debug('Weather is good and it is dark. Something must '
                           'have gone wrong. Stopping loop.')
        infos.stop_states()
    else:
        # Note: Unit will "sleep" before transition until it is safe
        # to observe again.
        infos.next_state = 'ready'
        infos.reset_observing_run()

    infos.logger.debug("Another successful night!")
