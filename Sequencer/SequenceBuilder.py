# Basic stuff
import logging

# Local Stuff, import Sequence related objects
from Sequencer.AutoDarkStep import AutoDarkCalculator, AutoDarkSequence
from Sequencer.CommonSteps import MessageStep
from Sequencer.CommonSteps import RunFunctionStep
from Sequencer.CommonSteps import ShellCommandStep
from Sequencer.CommonSteps import UserInputStep
from Sequencer.FilterWheelStep import FilterWheelStep
from Sequencer.ShootingSequence import ShootingSequence
from Sequencer.SequenceRunner import SequenceRunner


class SequenceBuilder:
    def __init__(self, logger=None, useAutoDark=True):
        self.logger = logger or logging.getLogger(__name__)
        self.sequences = []
        self.useAutoDark = useAutoDark
        self.autoDarkCalculator = AutoDarkCalculator()


    def addShootingSequence(self, shootingSeq):
        if self.useAutoDark:
            shootingSeq.callbacks.add(name="onEachFinished",
                callback=self.autoDarkCalculator.onEachFinished)
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

    def addAutoDark(self, camera, name='Dark', count=None):
        return self.__append(AutoDarkSequence(camera,
                                              self.autoDarkCalculator,
                                              name=name, logger=self.logger,
                                              count=count)) 

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

