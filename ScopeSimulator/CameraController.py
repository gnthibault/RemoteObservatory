# Numerical stuff
import numpy as np

# PyQt stuff
from PyQt5.QtGui import QVector3D
from PyQt5.QtCore import Qt
from PyQt5 import Qt3DExtras
from PyQt5 import Qt3DRender
from PyQt5 import Qt3DLogic
from PyQt5 import Qt3DInput

class CameraController(Qt3DExtras.QOrbitCameraController):

    def __init__(self, parent):
        super().__init__(parent)
        self.frameAction = Qt3DLogic.QFrameAction()
        self.frameAction.triggered.connect(self.mymoveCamera)
        self.addComponent(self.frameAction)
        self.time = 0.0
        self.last = 0.0
        self.calls = 0
        self.kbdevice = Qt3DInput.QKeyboardDevice()
        self.shiftButtonInput = Qt3DInput.QActionInput()
        self.shiftButtonAction = Qt3DInput.QAction()
        self.shiftButtonInput.setButtons([Qt.Key_Shift])
        self.shiftButtonInput.setSourceDevice(self.kbdevice)
        self.shiftButtonAction.addInput(self.shiftButtonInput)

        self.tzposInput = Qt3DInput.QButtonAxisInput()
        self.tzAxis = Qt3DInput.QAxis()
        self.tzposInput.setButtons([Qt.Key_Right])
        self.tzposInput.setScale(1.0)
        self.tzposInput.setSourceDevice(self.kbdevice)
        self.tzAxis.addInput(self.tzposInput)

        self.tznegInput = Qt3DInput.QButtonAxisInput()
        self.tznegInput.setButtons([Qt.Key_Left])
        self.tznegInput.setScale(-1.0)
        self.tznegInput.setSourceDevice(self.kbdevice)
        self.tzAxis.addInput(self.tznegInput)

        self.logicalDevice = Qt3DInput.QLogicalDevice()
        self.logicalDevice.addAction(self.shiftButtonAction)
        self.logicalDevice.addAxis(self.tzAxis)
        self.enabledChanged.connect(self.logicalDevice.setEnabled)

        self.addComponent(self.logicalDevice)
        self.speed = 0.5

    def mymoveCamera(self, dt):
        self.time += dt
        self.calls += 1
        if self.time > self.last + 1.0:
            #print('move camera', self.time, self.calls)
            self.calls = 0
            self.last = self.time
        if self.shiftButtonAction.isActive():
            #print(self.tzAxis.value())
            #self.camera().rollAboutViewCenter(
            #    self.tzAxis.value() * self.lookSpeed() * dt)

            # get 3d camera position
            p = self.camera().position()
            x = p.x()
            y = p.y()
            z = p.z()

            # convert to 2d x=y plan polar coordinates
            r = np.linalg.norm((x, y))
            theta = np.arctan2(y, x)

            # just go away from (0,0) cordinates
            dx = (-1.0 * r * self.speed * dt * np.sin(theta) *
                  self.tzAxis.value())
            dy = r * self.speed * dt * np.cos(theta) * self.tzAxis.value()
            self.camera().translateWorld(QVector3D(dx, dy, 0.0),
                Qt3DRender.QCamera.DontTranslateViewCenter)
