def on_enter(event_data):
    """ """
    infos = event_data.model
    infos.next_state = 'sleeping'
    infos.logger.debug("Recording all the data for the night.")

    # Cleanup existing observations
    try:
        infos.logger.debug("Cleaning data ...")
        #infos.manager.cleanup_observations()
    except Exception as e:
        infos.logger.warning('Problem with cleanup: {}'.format(e))

    infos.logger.debug("Done cleaning up all the recorded data.")
