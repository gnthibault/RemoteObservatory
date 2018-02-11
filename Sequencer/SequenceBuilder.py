from Sequencer.ShootingSequence import ShootingSequence
from Sequencer.CommonSteps import MessageStep
from Sequencer.CommonSteps import RunFunctionStep
from Sequencer.CommonSteps import ShellCommandStep
from Sequencer.CommonSteps import UserInputStep
from Sequencer.SequenceRunner import SequenceRunner
from Sequencer.FilterWheelStep import FilterWheelStep

class SequenceBuilder:
    def __init__(self):
        self.sequences = []
        #self.autoDarkCalculator = AutoDarkCalculator()


    def addShootingSequence(self, shootingSeq):
        return self.__append(shootingSeq)

    def addFilterWheelStep(self, filterWheel, filterName=None,
                           filterNumber=None):
        return self.__append(FilterWheelStep(filterWheel,
                                             filterName=filterName,
                                             filterNumber=filterNumber))

    def addUserConfirmationPrompt(self, message=UserInputStep.DEFAULT_PROMPT,
                                  onInput = None):
        return self.__append(UserInputStep(message, onInput))

    def addMessageStep(self, message, sleepTime=0):
        return self.__append(MessageStep(message, sleepTime))

    def addShellCommand(self, command, shell=False, abortOnFailure=False):
        return self.__append(ShellCommandStep(command, shell, abortOnFailure))

    #def addAutoDark(self, count=10):
    #    return self.__append(AutoDarkSequence(self.camera,
    #                                          self.autoDarkCalculator,count)) 

    def addFunction(self, f):
        return self.__append(RunFunctionStep(f))

    def start(self):
        sequenceDef = {
            'sequences': self.sequences
        }
        sequenceRunner = SequenceRunner(sequenceDef)
        sequenceRunner.start()

    def __append(self, item):
        self.sequences.append(item)
        return item

