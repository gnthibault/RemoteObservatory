def on_enter(event_data):
    """ """
    model = event_data.model
    model.next_state = 'sleeping'
    model.say("Recording all the data for the night.")

    # Cleanup existing observations
    try:
        if len(model.manager.scheduler.observed_list)>0:
            # observed observations will be moved to calibrated_list when done
            model.logger.debug("Observed list is not cleared, there might be"
                               "calibration acquisitions to perform")
            model.next_state = "calib_acq"
        else:
            model.logger.debug("Cleaning data ...")
            model.manager.cleanup_observations()
            model.say("Done cleaning up all the recorded data.")
    except Exception as e:
        model.logger.warning('Problem with cleanup: {}'.format(e))


