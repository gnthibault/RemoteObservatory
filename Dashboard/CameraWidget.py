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

    def run(self):
        cap = cv2.VideoCapture(self.url)
        while True:
            ret, frame = cap.read()
            if ret:
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                convertToQtFormat = QImage(rgbImage.data,
                                           rgbImage.shape[1],
                                           rgbImage.shape[0],
                                           QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)

class CameraWidget(QFrame):
    def __init__(self, parent=None, url='rtsp://192.168.1.64/1'):
        super().__init__()
        self.url=url
        self.init_UI()

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

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
        th = Thread(self, self.url)
        th.changePixmap.connect(self.setImage)
        th.start()
