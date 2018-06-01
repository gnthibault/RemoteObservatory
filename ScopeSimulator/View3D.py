# Generic stuff
import sys
sys.path.append('/home/gnthibault/projects/RemoteObservatory')

# PyQt stuff
from PyQt5.QtGui import QColor, QVector3D
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.Qt3DExtras import Qt3DWindow, QOrbitCameraController
from PyQt5.Qt3DCore import QEntity

# Indi
from indi.client.qt.skypoint import SkyPoint

# Local stuff: 3d 
from ScopeSimulator.CameraController import CameraController
from ScopeSimulator.Model3D import Model3D
from ScopeSimulator.World3D import World3D

class View3D(QObject):
    _default_clear_color = QColor(97, 97, 99)
    def __init__(self, parent=None):
        super().__init__()
        self.window = Qt3DWindow(parent)
        self.setClearColor(View3D._default_clear_color)
        self.rootEntity = QEntity()
        self.world = World3D(self.rootEntity)
        self.model = Model3D(self.rootEntity)
        self.model.setWorld(self.world)
        self.initialiseCamera()
        self.window.setRootEntity(self.rootEntity)
        self.scope = None

    def setClearColor(self, color):
        self.clearColor = color
        self.window.defaultFrameGraph().setClearColor(self.clearColor)

    def initialiseCamera(self):
        # Camera pinhole model definition
        self.window.camera().lens().setPerspectiveProjection(
            45.0, 16.0 / 9.0, 0.1, 100000.0)
        self.window.camera().setPosition(QVector3D(0.0, 1750.0, -3000.0))
        self.window.camera().setViewCenter(QVector3D(0.0, 1000.0, 0.0))
        #camera.setUpVector(QVector3D(0.0, 0.0, 1.0))

        # Camera controls
        self.camController = QOrbitCameraController(self.rootEntity)
        #camController = Qt3DExtras.QFirstPersonCameraController(scene)
        #self.camController = CameraController(self.rootEntity)
        self.camController.setLinearSpeed(500.0)
        self.camController.setLookSpeed(180.0)
        self.camController.setCamera(self.window.camera())

    def set_coord(self, coord):
        latitude = coord['latitude']
        longitude = coord['longitude']
        self.world.setLatitude(latitude)
        self.model.setLatitude(latitude)
        self.world.setLongitude(longitude)
        self.model.setLongitude(longitude)

    #def setTelescope(self, gdi):
        #if self.scope is not None:
        #    return
        #self.scope = gdi
        #geo_coord = self.scope.getProperty('GEOGRAPHIC_COORD')
        #lat = INDI.IUFindNumber(geo_coord, 'LAT')
        #lon = INDI.IUFindNumber(geo_coord, 'LONG')
        #self.setLatitude(lat.value)
        #self.setLongitude(lon.value)
        #prop_utc = self.scope.getProperty('TIME_UTC')
        #utc = INDI.IUFindText(prop_utc, 'UTC')
        #time_utc = INDI.f_scan_sexa(utc.text.split('T')[1])*15.0
        #print('UTC', utc.text, time_utc)
        #self.pierside = self.scope.getProperty('TELESCOPE_PIER_SIDE')
        #self.scope.newCoord.connect(self.setCoord)

    @pyqtSlot(SkyPoint)
    def setCoord(self, skypoint):
        pon = INDI.IUFindOnSwitch(self.pierside)
        p = 'PIER_WEST' if  pon.name == 'PIER_WEST' else 'PIER_EAST'
        self.model.setCoord(skypoint, p)

    #def removeTelescope(self):
    #    if self.scope is None:
    #        return
    #    self.scope.newCoord.disconnect(self.setCoord)
    #    self.scope = None

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app=QApplication(sys.argv)
    view = View3D()
    #view.setLatitude(50.17)
    #view.setLongitude(123.04)
    view.window.show()
    app.exec_()
