def on_enter(event_data):
    """ """
    model = event_data.model
    model.status()

    observation = model.manager.current_observation

    model.say(f"Analyzing image {observation.current_exp} / {observation.number_exposures}")

    model.next_state = 'observing'

    try:

        model.manager.analyze_recent()

        if model.force_reschedule:
            model.say("Forcing a move to the scheduler")
            model.next_state = 'scheduling'

        # Check for minimum number of exposures
        if observation.current_exp >= observation.number_exposures:
            # Check if we have completed an exposure block
            if observation.current_exp % observation.number_exposures == 0:
                model.next_state = 'scheduling'
    except Exception as e:
        model.logger.error(f"Problem in analyzing: {e}")
        model.next_state = 'parking'
