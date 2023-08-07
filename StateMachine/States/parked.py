
def on_enter(event_data):
    """ """
    model = event_data.model
    model.status()
    model.logger.debug(f"Entering parking state")

    has_valid_observations = model.manager.scheduler.has_valid_observations

    if has_valid_observations:
        if model.is_safe():
            if model.should_retry is False:
                model.say(f"Done retrying for this run, going to clean up and shut down!")
                model.next_state = "housekeeping"
            else:  # runs if there is an error causing a shutdown
                model.say(f"Now going to get ready for observation round")
                model.next_state = 'ready'
        else:  # Normal end of night
            model.say(f"Cleaning up for the night")
            model.next_state = 'housekeeping'
    else:
        model.say("No observations found.")
        # TODO Should check if we are close to morning and if so do some morning
        # calibration frames rather than just waiting for 30 minutes then
        # shutting down.
        model.say(f"Going to stay parked for half an hour then will try again.")

        while True:
            model.sleep(delay=60)  # 30 minutes = 1800 seconds
            # We might have shutdown during previous sleep.
            if not model.connected:
                break
            elif model.is_safe():
                model.reset_observing_run()
                model.next_state = 'ready'
                break
            elif model.is_dark() is False:
                model.logger.debug(f"Looks like it is not dark anymore. Going to clean up.")
                model.next_state = 'housekeeping'
                break
            else:
                model.say(f"Does not looks like it is safe now, waiting another 30 minutes.")
