# opencv for video capture
import cv2

# PyQt5 stuff
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QThread
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtGui import QImage, QPixmap

class Thread(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, parent=None, url=0):
        super(QThread, self).__init__(parent)
        self.url = url
        self.is_running = True
        self.cap = None

    def stop(self):
        if self.cap is not None:
            self.cap.release()
        self.is_running = False

    def run(self):
        self.cap = cv2.VideoCapture(self.url)
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                convertToQtFormat = QImage(rgbImage.data,
                                           rgbImage.shape[1],
                                           rgbImage.shape[0],
                                           QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)

            if self.isInterruptionRequested():
                self.stop()

class CameraWidget(QFrame):
    """
        From the documentation: The QFrame class is the base class of widgets
        that can have a frame.

    """
    def __init__(self, parent=None, url='rtsp://192.168.1.64/1'):
        super().__init__()
        self.url=url
        self.init_UI()

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

    def close(self):
        self.thread.requestInterruption()
        self.thread.wait()

    def init_UI(self):
        #self.setWindowTitle(self.title)
        #self.setGeometry(self.left, self.top, self.width, self.height)
        #self.resize(1800, 1200)
        # create a label
        self.label = QLabel(self)
        #self.label.move(280, 120)
        #self.label.resize(640, 480)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.label, Qt.AlignCenter)
        self.setLayout(layout)

        # Start acquisition thread
        self.thread = Thread(self, self.url)
        self.thread.changePixmap.connect(self.setImage)
        self.thread.start()
