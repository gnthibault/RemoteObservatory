
def on_enter(event_data):
    #TODO TN DEBUG
    #event_data.model.next_state = 'tracking'
    #return
    """Pointing State

    Take 30 second exposure and plate-solve to get the pointing error
    """
    model = event_data.model
    model.status()
    model.next_state = 'parking'

    model.logger.debug("About to starts fine pointing")
    try:
        model.manager.points()
        msg = f"Done with pointing"
        model.logger.debug(msg)
        model.say(msg)
        model.next_state = 'focusing'
    except Exception as e:
        model.logger.warning("Problem adjusting tracking: {}".format(e))


        # Inform that we have changed field
        model.send_message({"name": model.manager.current_observation.name}, channel='FIELD')
        model.next_state = 'tracking'

    except Exception as e:
        msg = (f"Hmm, I had a problem checking the pointing error. "
               f"Going to park. {e}:{traceback.format_exc()}")
        model.logger.error(msg)
        model.say(msg)
