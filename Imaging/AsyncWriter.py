# Basic stuff
import threading


class AsyncWriter:
    """ Allows to perform asynchronous writes """

    def __init__(self, writer):
        self.writer = writer

    def AsyncWriteImage(self, shooter, index):
        w = threading.Thread(target=self.writer.writeWithTag,
                             args=(shooter.camera.getReceivedImage()))
        w.start()

