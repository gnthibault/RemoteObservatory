def on_enter(event_data):
    """ """
    model = event_data.model
    model.next_state = 'sleeping'
    model.say("Recording all the data for the night.")

    # Cleanup existing observations
    try:
        model.logger.debug("Cleaning data ...")
        #model.manager.cleanup_observations()
    except Exception as e:
        model.logger.warning('Problem with cleanup: {}'.format(e))

    model.say("Done cleaning up all the recorded data.")
