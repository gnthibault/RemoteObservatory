
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

class ShootingSequence:
    def __init__(self, camera, target, exposure, count, **kwargs):
        self.camera = camera
        self.target = target
        self.count = count
        self.exposure = exposure
        self.callbacks = SequenceCallbacks(**kwargs)
        self.finished = 0

    def run(self):
        self.callbacks.run('onStarted', self)
        for index in range(0, self.count):
            self.callbacks.run('onEachStarted', self, index)
            self.camera.setExpTimeSec(self.exposure)
            self.camera.shootAsync()
            self.camera.synchronizeWithImageReception()
            self.finished += 1
            self.callbacks.run('onEachFinished', self, index)
        self.callbacks.run('onFinished', self)

    @property
    def totalSeconds(self):
        return self.exposure * self.count

    @property
    def shot_seconds(self):
        return self.finished * self.exposure

    @property
    def remaining_seconds(self):
        return self.remaining_shots * self.exposure

    @property
    def remaining_shots(self):
        return self.count - self.finished

    @property
    def nextIndex(self):
        return self.finished

    @property
    def last_index(self):
        return self.nextIndex - 1

    def __str__(self):
        return 'Sequence, target {0}: {1} {2}s exposure (total exp time: {3}s)'\
            +', start index: {4}'.format(self.target, self.count, self.exposure,
                                         self.totalSeconds)

    def __repr__(self):
        return self.__str__()
