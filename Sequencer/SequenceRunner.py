import itertools

class SequenceRunner:
    def __init__(self, sequenceDef):
        self.sequenceDef = sequenceDef

    def start(self):
        totalSeconds = sum([s.totalSeconds for s in
                            self.sequenceDef['sequences']
                            if hasattr(s, 'totalSeconds')])

        print('== Starting sequences: total exposure time={0} seconds'.format(
            totalSeconds))

        for sequence in self.sequenceDef['sequences']:
            self.__run_sequence(sequence)

    def __run_sequence(self, sequence):
        if hasattr(sequence, 'callbacks'):
            sequence.callbacks.add('on_started', self.__log_sequence_started)
            sequence.callbacks.add('on_finished', self.__log_sequence_finished)
            sequence.callbacks.add('on_each_finished', 
                                   self.__log_sequence_each_finished)
        sequence.run()

    def __log_sequence_started(self, sequence):
        print('++++ Sequence {0} started: exposure time: {1}s'.format(
            sequence.name, sequence.totalSeconds))

    def __log_sequence_finished(self, sequence):
        print('++++ Sequence {0} finished: exposure time: {1}s'.format(
            sequence.name, sequence.totalSeconds))

    def __log_sequence_each_finished(self, sequence, number, file_name):
        print('****** Sequence {0}: {1} of {2} finished, elapsed: {3}s,'
            ' remaining: {4}s (total: {5}s)'.format(sequence.name, number+1,
                                                    sequence.count,
                                                    sequence.shot_seconds,
                                                    sequence.remaining_seconds,
                                                    sequence.totalSeconds))
