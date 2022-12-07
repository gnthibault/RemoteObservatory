def on_enter(event_data):
    """ """
    model = event_data.model

    if model.should_retry is False:
        model.say("Weather is good and it is dark. Something must have gone wrong. Stopping loop.")
        model.stop_states()
    else:
        # Note: Unit will "sleep" before transition until it is safe
        # to observe again.
        model.next_state = "ready"
        model.reset_observing_run()

    model.say("Another successful night!")
