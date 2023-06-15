# Common import
import subprocess
import sys
import time

class SequenceCallbacks:
    def __init__(self, **kwargs):
        self.callbacks = kwargs

    def add(self, name, callback):
        if name not in self.callbacks:
            self.callbacks[name] = []
        self.callbacks[name].append(callback)

    def run(self, name, *args, **kwargs):
        if name not in self.callbacks:
            return
        for callback in self.callbacks[name]:
            callback(*args, **kwargs)

class MessageStep:
    # message can be either a string, or a function returning a string

    def __init__(self, message, sleepTime=0):
        self.message = message
        self.sleepTime = sleepTime

    def run(self):
        message = self.message() if callable(self.message) else self.message

        print(message)
        if self.sleepTime > 0:
            time.sleep(self.sleepTime)
    
    def __str__(self):
        return 'Print message'

    def __repr__(self):
        return self.__str__()

class RunFunctionStep:
    def __init__(self, _function):
        self.function = _function

    def run(self):
        self.function()
    
    def __str__(self):
        return 'Run python function'

    def __repr__(self):
        return self.__str__()

class ShellCommandStep:
    def __init__(self, arguments, shell=False, abortOnFailure=False):
        self.arguments = arguments
        self.shell = shell
        self.abortOnFailure = abortOnFailure

    def run(self):
        print('Running shell command {}'.format(self.arguments))
        exit_code = subprocess.call(self.arguments, shell=self.shell)
        message = 'Shell command exited with status {}'.format(exit_code)
        if exit_code != 0 and self.abortOnFailure:
            raise RuntimeError(message)
        else:
            print(message)
    
    def __str__(self):
        return 'Run shell command {0}'.format(self.arguments)

    def __repr__(self):
        return self.__str__()

class UserInputStep:
    DEFAULT_PROMPT = 'Press Enter to continue'

    # the onInput callback, if specified, will be called with the user
    # entered input
    def __init__(self, prompt=DEFAULT_PROMPT, onInput=None):
        self.prompt = prompt
        self.onInput = onInput

    def run(self):
        user_input = None
        if sys.version_info[0] < 3:
            user_input = raw_input(self.prompt)
        else:
            user_input = input(self.prompt)
        if self.onInput:
            self.onInput(user_input)
    
    def __str__(self):
        return 'Wait for user confirmation'

    def __repr__(self):
        return self.__str__()

class TelescopeSlewingStep:
    def __init__(self, mount, coord):
        self.mount = mount
        self.coord = coord

    def run(self):
        self.mount.slew_to_coord_and_track(self.coord)
 

    def __str__(self):
        return 'Telescope mount {} slewing to coordinates {}'.format(
                self.mount, self.coord)

    def __repr__(self):
        return self.__str__()

