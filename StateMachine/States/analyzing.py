def on_enter(event_data):
    """ """
    infos = event_data.model

    #observation = pocs.manager.current_observation

    #pocs.say("Analyzing image {} / {}".format(observation.current_exp,
    #                                           observation.min_nexp))

    infos.next_state = 'tracking'
    try:

        #pocs.manager.analyze_recent()

        #if pocs.force_reschedule:
        #    pocs.say("Forcing a move to the scheduler")
        #    pocs.next_state = 'scheduling'

        # Check for minimum number of exposures
        #if observation.current_exp >= observation.min_nexp:
        #    # Check if we have completed an exposure block
        #    if observation.current_exp % observation.exp_set_size == 0:
        #        pocs.next_state = 'scheduling'
        infos.logger.debug('Doing stuff in analyzing state')
    except Exception as e:
        infos.logger.error("Problem in analyzing: {}".format(e))
        infos..next_state = 'parking'
