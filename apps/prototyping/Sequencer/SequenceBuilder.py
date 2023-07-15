# Basic stuff
import logging

# Astropy stuff
from astropy.coordinates import SkyCoord
from astropy.time import Time

# Local Stuff, import Sequence related objects
from Sequencer.AutoDarkStep import AutoDarkCalculator, AutoDarkSequence
from Sequencer.AutoFlatStep import AutoFlatCalculator, AutoFlatSequence
from Sequencer.CommonSteps import MessageStep, RunFunctionStep, ShellCommandStep
from Sequencer.CommonSteps import TelescopeSlewingStep
from Sequencer.CommonSteps import UserInputStep, SequenceCallbacks
from Sequencer.FilterWheelStep import FilterWheelStep
from Sequencer.ShootingSequence import ShootingSequence
from Sequencer.SequenceRunner import SequenceRunner


class SequenceBuilder:
    def __init__(self, camera, filterWheel=None, observatory=None, mount=None,
                 focuser=None, logger=None, asyncWriter=None, useAutoDark=True,
                 useAutoFlat=False):
        self.logger = logger or logging.getLogger(__name__)
        self.camera = camera
        self.filterWheel = filterWheel
        self.observatory = observatory
        self.mount = mount
        self.focuser = focuser
        self.asyncWriter = asyncWriter
        self.sequences = []
        self.useAutoDark = useAutoDark
        self.useAutoFlat = useAutoFlat
        self.autoDarkCalculator = AutoDarkCalculator()
        self.autoFlatCalculator = AutoFlatCalculator()

    def add_telescope_target_slewing(self, target):
        if not (self.mount is None):
            #coord = SkyCoord(SkyCoord.from_name(target, frame="icrs"), equinox=Time('J2000'))
            coord = SkyCoord('19h50m47.6s', '+08d52m12.0s', frame='icrs')
            self.__append(TelescopeSlewingStep(self.mount, coord))

    def add_object_shooting_sequence(self, target, seq_name, exposure, count,
                                     **kwargs):
        """
            
        """
        # First, slew to target
        self.add_telescope_target_slewing(target)

        s = ShootingSequence(logger=self.logger, camera=self.camera,
                             seq_name=seq_name, exposure=exposure, count=count,
                             **kwargs)
        if self.useAutoDark and not (self.autoDarkCalculator is None):
            s.callbacks.add(name="onEachFinished",
                          callback=self.autoDarkCalculator.onEachFinished)
        if not (self.asyncWriter is None):
            s.callbacks.add(name="onEachFinished",
                            callback=self.asyncWriter.AsyncWriteImage)
        return self.__append(s)

    def add_filterwheel_step(self, filterName=None,
                             filterNumber=None):
        f = FilterWheelStep(self.filterWheel,
                            filterName=filterName,
                            filterNumber=filterNumber)
#TODO TN                    onFinished=[
#                           self.focuser.autoFocusSequence]))

        if self.useAutoFlat and self.autoFlatCalculator is not None:
            f.callbacks.add(name='onFinished',
                            callback=self.autoFlatCalculator.onFinished)
        return self.__append(f)

    def add_user_confirmation_prompt(self,
                                     message=UserInputStep.DEFAULT_PROMPT,
                                     onInput=None):
        return self.__append(UserInputStep(message, onInput))

    def add_message_print(self, message, sleepTime=0):
        return self.__append(MessageStep(message, sleepTime))

    def add_shell_command(self, command, shell=False, abortOnFailure=False):
        return self.__append(ShellCommandStep(command, shell, abortOnFailure))

    def add_auto_dark(self, name='Dark', count=None):
        s = AutoDarkSequence(self.camera,
                             self.autoDarkCalculator,
                             name=name, logger=self.logger,
                             count=count) 
        if self.asyncWriter is not None:
            s.callbacks.add(name="onEachFinished",
                            callback=self.asyncWriter.AsyncWriteImage)
        return self.__append(s)

    def add_auto_flat(self, name='Flat', count=16, exposure=None):
        
        def execBeforeFlat(shootingSequence):
            self.logger.debug('SequenceBuilder: Now preparing setup for flat')
            if not (self.mount is None):
                self.mount.park()
            self.observatory.switchOnFlatPannel()
        if not self.autoFlatCalculator:
            self.logger.warning('SequenceBuilder: addAutoFlat should be used '
                                 'along with autoFlatCalculator, default one '
                                 'is assigned')
            self.autoFlatCalculator = AutoFlatCalculator()
        s = AutoFlatSequence(camera=self.camera,
                             filterWheel=self.filterWheel,
                             autoFlatCalculator=self.autoFlatCalculator,
                             logger=self.logger, name=name,
                             count=count,
                             exposure=exposure,
                             onStarted=[execBeforeFlat]) 
        if self.asyncWriter is not None:
            s.callbacks.add(name="onEachFinished",
                            callback=self.asyncWriter.AsyncWriteImage)
        return self.__append(s)

    def add_function(self, f):
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

