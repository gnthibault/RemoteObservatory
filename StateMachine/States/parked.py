
def on_enter(event_data):
    """ """
    model = event_data.model
    model.logger.debug("Entering parking state")

    has_valid_observations = model.manager.scheduler.has_valid_observations

    if has_valid_observations:
        if model.is_safe():
            if model.should_retry is False or model.run_once is True:
                model.logger.debug('Done retrying for this run, going to '
                                   'clean up and shut down!')
                model.next_state = 'housekeeping'
            else:  # runs if there is an error causing a shutdown
                model.logger.debug("Now going to perform a new try")
                model.next_state = 'ready'
        else:  # Normal end of night
            model.logger.debug("Cleaning up for the night")
            model.next_state = 'housekeeping'
    else:
        model.logger.debug("No observations found.")
        # TODO Should check if we are close to morning and if so do some morning
        # calibration frames rather than just waiting for 30 minutes then
        # shutting down.
        if model.run_once is False:
            model.logger.debug('Going to stay parked for half an hour then '
                               'will try again.')

            while True:
                model.sleep(delay=1800)  # 30 minutes = 1800 seconds

                # We might have shutdown during previous sleep.
                if not model.connected:
                    break
                elif model.is_safe():
                    model.reset_observing_run()
                    model.next_state = 'ready'
                    break
                elif model.is_dark() is False:
                    model.logger.debug('Looks like it is not dark anymore. '
                                       'Going to clean up.')
                    model.next_state = 'housekeeping'
                    break
                else:
                    model.logger.debug('Does not looks like it is safe now, '
                                       'waiting another 30 minutes.')
        else:
            model.logger.debug('Only wanted to run once so cleaning up!')
            model.next_state = 'housekeeping'
