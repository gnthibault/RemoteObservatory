from Sequencer.ShootingSequence import ShootingSequence
from Sequencer.CommonSteps import MessageStep
from Sequencer.CommonSteps import RunFunctionStep
from Sequencer.CommonSteps import ShellCommandStep
from Sequencer.CommonSteps import UserInputStep

class SequenceBuilder:
    def __init__(self, camera=None, filterWheel=None):
        self.sequences = []
        #self.autoDarkCalculator = AutoDarkCalculator()
        self.camera = camera
        self.filterWheel = filterWheel


    def addShootingSequence(self, target, exposure, count, autoDark=True):
        return self.__append(
            ShootingSequence(
                camera=self.camera,
                target=target,
                exposure=exposure,
                count=count)) #,
                #on_finished=([self.autoDarkCalculator.sequenceFinished] 
                #             if autoDark else [])))

    def addFilterWheelStep(self, filterName=None, filterNumber=None):
        return self.__append(FilterWheelStep(self.filterWheel,
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

