# Local stuff
from Sequencer.CommonSteps import SequenceCallbacks

class FilterWheelStep:
    def __init__(self, filterWheel, filterName=None, filterNumber=None,
                 **kwargs):
        self.filterWheel = filterWheel
        self.callbacks = SequenceCallbacks(**kwargs)

        if not filterName and not filterNumber:
            raise RuntimeError('FilterWheelStep: One of filter name or number '
                               'should be defined')

        if filterName:
            self.filterNumber = filterWheel.filters()[filterName]
            self.filterName = filterName
        else:
            self.filterName = filterWheel.filterName(filterNumber)
            self.filterNumber = filterNumber

    def run(self):
        self.callbacks.run('onStarted', self)
        self.filterWheel.setFilterNumber(self.filterNumber)
        self.callbacks.run('onFinished', self)

    def __str__(self):
        return 'Change filter to {0} ({1}) on filter wheel {2}' \
            .format(self.filterName, self.filterNumber, self.filterWheel)

    def __repr__(self):
        return self.__str__()

