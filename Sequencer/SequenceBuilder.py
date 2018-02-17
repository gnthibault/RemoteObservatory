# Basic stuff
import logging

# Local Stuff, import Sequence related objects
from Sequencer.AutoDarkStep import AutoDarkCalculator, AutoDarkSequence
from Sequencer.AutoFlatStep import AutoFlatCalculator, AutoFlatSequence
from Sequencer.CommonSteps import MessageStep, RunFunctionStep, ShellCommandStep
from Sequencer.CommonSteps import UserInputStep, SequenceCallbacks
from Sequencer.FilterWheelStep import FilterWheelStep
from Sequencer.ShootingSequence import ShootingSequence
from Sequencer.SequenceRunner import SequenceRunner


class SequenceBuilder:
    def __init__(self, camera, filterWheel=None, observatory=None, mount=None,
                 focuser=None, logger=None, useAutoDark=True,
                 useAutoFlat=False):
        self.logger = logger or logging.getLogger(__name__)
        self.camera = camera
        self.filterWheel = filterWheel
        self.observatory = observatory
        self.mount = mount
        self.focuser = focuser
        self.sequences = []
        self.useAutoDark = useAutoDark
        self.autoDarkCalculator = AutoDarkCalculator()
        self.autoFlatCalculator = AutoFlatCalculator()


    def addShootingSequence(self, target, exposure, count, **kwargs):
        s = ShootingSequence(logger=self.logger, camera=self.camera,
                             target=target, exposure=exposure, count=count,
                             **kwargs)
        if self.useAutoDark:
            s.callbacks.add(name="onEachFinished",
                          callback=self.autoDarkCalculator.onEachFinished)
        return self.__append(s)

    def addFilterWheelStep(self, filterName=None,
                           filterNumber=None):
        f = FilterWheelStep(self.filterWheel,
                            filterName=filterName,
                            filterNumber=filterNumber)
#                           onFinished=[
#                           self.focuser.autoFocusSequence]))

        if self.autoFlatCalculator:
            f.callbacks.add(name='onFinished',
                            callback=self.autoFlatCalculator.onFinished)
        return self.__append(f)

    def addUserConfirmationPrompt(self, message=UserInputStep.DEFAULT_PROMPT,
                                  onInput = None):
        return self.__append(UserInputStep(message, onInput))

    def addMessageStep(self, message, sleepTime=0):
        return self.__append(MessageStep(message, sleepTime))

    def addShellCommand(self, command, shell=False, abortOnFailure=False):
        return self.__append(ShellCommandStep(command, shell, abortOnFailure))

    def addAutoDark(self, name='Dark', count=None):
        return self.__append(AutoDarkSequence(self.camera,
                                              self.autoDarkCalculator,
                                              name=name, logger=self.logger,
                                              count=count)) 

    def addAutoFlat(self, name='Flat', count=16, exposure=None):
        
        def execBeforeFlat(shootingSequence):
            self.logger.debug('SequenceBuilder: Now preparing setup for flat')
            #if not mount.isParked():
            #    self.mount.gotoParkPosition()
            self.observatory.switchOnFlatPannel()
        if not self.autoFlatCalculator:
            self.logger.error('SequenceBuilder: addAutoFlat should be used '
                              'along with autoFlatCalculator')
            self.autoFlatCalculator = AutoFlatCalculator()
        return self.__append(AutoFlatSequence(camera=self.camera,
                                              filterWheel=self.filterWheel,
                                              autoFlatCalculator=
                                                  self.autoFlatCalculator,
                                              logger=self.logger, name=name,
                                              count=count,
                                              exposure=exposure,
                                              onStarted=[execBeforeFlat])) 

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

