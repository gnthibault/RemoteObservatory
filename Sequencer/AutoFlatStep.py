
# Local Stuff, sequences
from Sequencer.ShootingSequence import ShootingSequence, SequenceCallbacks

# Local stuff : Imaging tools
from Imaging.AsyncWriter import AsyncWriter
from Imaging.FitsWriter import FitsWriter

class AutoFlatCalculator:
    """" Keep track of the different filter used

    Using a callback, it allows to keep track of the various filter used
    so that one can perform the corresponding flats.
    """

    def __init__(self):
        self.reset()

    def onFinished(self, filterWheelStep):
        self.filterNames.add(filterWheelStep.filterWheel.currentFilter()[1])

    def reset(self):
        self.filterNames = set()

    def __str__(self):
        return 'AutoFlatCalculator (filterNames: {})'.format(
            ', '.join(self.filterNames))

    def __repr__(self):
        return self.__str__()

class AutoFlatSequence:
    def __init__(self, camera, filterWheel, autoFlatCalculator, logger=None,
                 name='Flat', count=16, exposure=None, **kwargs):
        self.logger = logger or logging.getLogger(__name__)
        self.camera = camera
        self.filterWheel = filterWheel
        self.autoFlatCalculator = autoFlatCalculator
        self.name = name
        self.count = count
        self.exposure = exposure
        self.callbacks = SequenceCallbacks(**kwargs)

    def run(self):
        self.logger.debug('AutoFlatSequence: Flat Sequence is going to run '
                          'for the following set of filters {}'.format(
                          self.autoFlatCalculator.filterNames))
        self.camera.set_frame_type('FRAME_FLAT')
        for filterName in self.autoFlatCalculator.filterNames:
            self.logger.debug('AutoFlatSequence: processing filter {}'.format(
                              filterName))
            self.filterWheel.setFilter(filterName)
            if self.exposure is None:
                exposure = self.camera.getRelevantFlatDuration(filterName)
            else:
                exposure = self.exposure
            target_name = self.name+'-'+filterName
            seq = ShootingSequence(logger=self.logger, camera=self.camera,
                seq_name=target_name, exposure=exposure, count=self.count)
            seq.callbacks = self.callbacks
            seq.run()
        self.autoFlatCalculator.reset() 
        self.camera.set_frame_type('FRAME_LIGHT')

    def __str__(self):
        return 'AutoFlatSequence (filterNames: {})'.format(
            ', '.join(self.autoFlatCalculator.filterNames))

    def __repr__(self):
        return self.__str__()
