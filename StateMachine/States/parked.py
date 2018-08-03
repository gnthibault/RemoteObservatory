
def on_enter(event_data):
    """ """
    infos = event_data.model
    infos.logger.debug("Entering parking state")

    has_valid_observations = infos.manager.scheduler.has_valid_observations

    if has_valid_observations:
        if infos.is_safe():
            if infos.should_retry is False or infos.run_once is True:
                infos.logger.debug('Done retrying for this run, going to '
                                   'clean up and shut down!')
                infos.next_state = 'housekeeping'
            else:  # runs if there is an error causing a shutdown
                infos.logger.debug("Now going to perform a new try")
                infos.next_state = 'ready'
        else:  # Normal end of night
            infos.logger.debug("Cleaning up for the night")
            infos.next_state = 'housekeeping'
    else:
        infos.logger.debug("No observations found.")
        # TODO Should check if we are close to morning and if so do some morning
        # calibration frames rather than just waiting for 30 minutes then
        # shutting down.
        if infos.run_once is False:
            infos.logger.debug('Going to stay parked for half an hour then '
                               'will try again.')

            while True:
                infos.sleep(delay=1800)  # 30 minutes = 1800 seconds

                # We might have shutdown during previous sleep.
                if not infos.connected:
                    break
                elif infos.is_safe():
                    infos.reset_observing_run()
                    infos.next_state = 'ready'
                    break
                elif infos.is_dark() is False:
                    infos.logger.debug('Looks like it is not dark anymore. '
                                       'Going to clean up.')
                    infos.next_state = 'housekeeping'
                    break
                else:
                    infos.logger.debug('Seems to be bad weather. '
                                       'waiting another 30 minutes.')
        else:
            infos.logger.debug('Only wanted to run once so cleaning up!')
            infos.next_state = 'housekeeping'
