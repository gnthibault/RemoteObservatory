from transitions import Machine

class GuiderPHD2:
    """
        list of states, according to openPHD2 documentation
    """
    states = ['InitialState', 'BaseState', 'Guiding',   'Paused',      'Calibrating',        'Looping',          'Stopped']
    transitions = [
        { 'trigger': 'AppState', 'source': 'InitialStep', 'dest': 'BaseState' },
        { 'trigger': 'GuideStep', 'source': '*', 'dest': 'Guiding' },
        { 'trigger': 'PausedStart', 'source': '*', 'dest': 'Paused' },
        { 'trigger': 'CalibrationLooping', 'source': '*', 'dest': 'Calibrating' }
        { 'trigger': 'ExposuresLooping', 'source': '*', 'dest': 'Looping' },
        { 'trigger': 'ExposuresStoped', 'source': '*', 'dest': 'Stopped' }
        ]

    def __init__(self, name):
        # Initialize the state machine
        self.machine = Machine(model = self,
                               states = GuiderPHD2.states,
                               transitions = GuiderPHD2.transitions,
                               initial = GuiderPHD2.states[0])

