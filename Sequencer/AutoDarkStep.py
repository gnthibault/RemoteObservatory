
# Local Stuff, sequences
from Sequencer.ShootingSequence import ShootingSequence, SequenceCallbacks

# Local stuff : Imaging tools
from Imaging.AsyncWriter import AsyncWriter
from Imaging.FitsWriter import FitsWriter

class AutoDarkCalculator:
    """" Keep track of the different exposure times

    Using a callback, it allows to keep track of the various exposure time
    so that one can perform the corresponding dark.
    """

    def __init__(self):
        self.reset()

    def onEachFinished(self, shootingSequence, index):
        if shootingSequence.exposure in self.exposures:
            self.exposures[shootingSequence.exposure] += 1
        else:
            self.exposures[shootingSequence.exposure] = 1

    def getRelevantCount(self, exposure):
        #2400 sec is 45 minutes
        maxTimeSec = 2400
        maxFiles = 200
        if maxTimeSec//max(exposure,1) > maxFiles:
            return maxFiles
        else:
            return maxTimeSec//max(exposure,1)

    def reset(self):
        self.exposures = {}

class AutoDarkSequence:
    def __init__(self, camera, autoDarkCalculator, logger=None,
                 name='Dark', count=None, **kwargs):
        self.logger = logger or logging.getLogger(__name__)
        self.camera = camera
        self.autoDarkCalculator = autoDarkCalculator
        self.name = name
        self.count = count
        self.callbacks = SequenceCallbacks(**kwargs)

    def run(self):
        self.logger.debug('Dark Sequence is going to run')
        self.camera.setFrameType('FRAME_DARK')
        for exposure in self.autoDarkCalculator.exposures:
            if self.count is None:
                count = self.autoDarkCalculator.getRelevantCount(exposure)
            else:
                count = self.count
            #TODO TN duration or camera gain should apear in the name
            seq_name = self.name+'-'+str(exposure)+'s'
            seq = ShootingSequence(logger=self.logger, camera=self.camera,
                seq_name=seq_name, exposure=exposure, count=count)
            seq.callbacks = self.callbacks
            seq.run()
        self.autoDarkCalculator.reset() 
        self.camera.setFrameType('FRAME_LIGHT')

    def __str__(self):
        return 'AutoDarkSequence (exposures: {})'.format(
            ', '.join(self.autoDarkCalculator.exposures))

    def __repr__(self):
        return self.__str__()
