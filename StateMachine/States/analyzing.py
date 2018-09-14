def on_enter(event_data):
    """ """
    model = event_data.model

    observation = model.manager.current_observation

    model.say("Analyzing image {} / {}".format(observation.current_exp,
                                               observation.min_nexp))

    model.next_state = 'tracking'
    try:

        #model.manager.analyze_recent()

        if model.force_reschedule:
            model.say("Forcing a move to the scheduler")
            model.next_state = 'scheduling'

        # Check for minimum number of exposures
        if observation.current_exp >= observation.min_nexp:
            # Check if we have completed an exposure block
            if observation.current_exp % observation.exp_set_size == 0:
                model.next_state = 'scheduling'
    except Exception as e:
        model.logger.error("Problem in analyzing: {}".format(e))
        model.next_state = 'parking'
