# Astropy stuff
from astropy.coordinates import SkyCoord

# PyQt stuff
from PyQt5.QtCore import pyqtSlot, QUrl
from PyQt5.QtGui import QColor, QVector3D
from PyQt5.Qt3DCore import QEntity, QTransform
from PyQt5.Qt3DExtras import QMetalRoughMaterial, QDiffuseSpecularMaterial
from PyQt5.Qt3DRender import QMesh

class Model3D(QEntity):
    stl_path = 'ScopeSimulator/stl'
    _model_file_mat = [
        (stl_path+'/leg.stl', 'st', None),
        (stl_path+'/leg.stl', 'st', {'rotationZ': 120.0}),
        (stl_path+'/leg.stl', 'st', {'rotationZ': 240.0}),
        (stl_path+'/basetripod.stl', 'mg70', None),
        [
            (stl_path+'/baseholder.stl', 'mg50', None),
            [
                (stl_path+'/rahousing.stl', 'mg50', None),
                [
                    (stl_path+'/raaxis.stl', 'mg50', None),
                    (stl_path+'/dehousing.stl', 'mg50', None),
                    [
                        (stl_path+'/deaxis.stl', 'mg50', None),
                        (stl_path+'/cwbar.stl', 'st', None),
                        (stl_path+'/dovetail.stl', 'mg70', None),
                        (stl_path+'/refractor.stl', 'wh', None),
                        (stl_path+'/lens.stl', 'glass', None),
                        (stl_path+'/crayford-spacer.stl', 'mg70', None),
                        [
                            (stl_path+'/crayford-cylinder.stl', 'mg70', None),
                            [
                                (stl_path+'/crayford-tube.stl', 'st', None),
                            ]
                        ]
                    ]
                ]
            ]
        ]
    ]
    _model_centers = [QVector3D(0.0, 0.0, 850.0),
                      QVector3D(5.0, 0.0, 925.0),
                      QVector3D(100.0, 0.0, 1005.0),
                      QVector3D(170.0, 0.0, 1085.0),
                      QVector3D(-40.0, 0.0, 1225.0)]

    def __init__(self, parent=None, serv_time=None):
        super().__init__(parent)
        self.serv_time = serv_time
        self.azimuth = 0.0
        self.latitude = 0.0
        self.longitude = 0.0
        self.hemisphere = 'N'
        self.RA = 0.0
        self.DEC = 0.0
        self.crayfordangle = 0.0
        self.crayfordposition = 0.0
        self.world = None
        self.mat = dict()
        self.makeMaterials()
        # Freecad models are up towards z, Qt3D towards y
        self.modeltransform = QTransform()
        self.modeltransform.setRotationX(-90.0)
        self.addComponent(self.modeltransform)
        # Transformations (one per depth in the model list)
        self.azimuthtransform = QTransform()
        self.latitudetransform = QTransform()
        self.RAtransform = QTransform()
        self.DECtransform = QTransform()
        self.crayfordtransform = QTransform()
        self.crayfordtubetransform = QTransform()
        self.listtransforms=[self.azimuthtransform, self.latitudetransform,
                            self.RAtransform, self.DECtransform,
                            self.crayfordtransform, self.crayfordtubetransform
                            ]
        self.loadModels(Model3D._model_file_mat, self)
        #self.azimuthtransform.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[0], self.azimuth, QVector3D(0,0,1)))
        #self.latitudetransform.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[1], self.latitude,
        #    QVector3D(0.0, 1.0, 0.0)))
        #self.RAtransform.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[2], -self.RA + 90, QVector3D(1,0,0)))
        # self.DECtransform.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[3], -self.DEC + 90, QVector3D(0,0,1)))
        self.setLongitude(self.longitude)
        self.setLatitude(self.latitude)
        self.setRA(self.RA)
        self.setDEC(self.DEC)
        self.crayfordtransform.setMatrix(QTransform.rotateAround(
            Model3D._model_centers[4], self.crayfordangle, QVector3D(1,0,0)))
        self.crayfordtubetransform.setTranslation(QVector3D(
            self.crayfordposition, 0.0, 0.0))

    def makeMaterials(self):
        self.metalgray50 = QMetalRoughMaterial()
        self.metalgray50.setBaseColor(QColor(127, 127, 127))
        self.metalgray50.setMetalness(0.7)
        self.metalgray50.setRoughness(0.5)
        self.mat['mg50'] = self.metalgray50
        self.metalgray70 = QMetalRoughMaterial()
        self.metalgray70.setBaseColor(QColor(int(0.7*255),
                                             int(0.7*255),
                                             int(0.7*255)))
        self.metalgray70.setMetalness(0.7)
        self.metalgray70.setRoughness(0.1)
        self.mat['mg70'] = self.metalgray70
        self.stainless = QDiffuseSpecularMaterial()
        self.stainless.setAmbient(QColor(224, 223, 219))
        self.stainless.setDiffuse(QColor(int(0.572*255),
                                         int(0.579*255),
                                         int(0.598*255)))
        self.stainless.setSpecular(QColor(255, 255, int(0.984*255)))
        self.stainless.setShininess(0.9)
        self.mat['st'] = self.stainless
        self.whitepaint = QDiffuseSpecularMaterial()
        self.whitepaint.setAmbient(QColor(228, 228, 228))
        self.whitepaint.setShininess(0.7)
        self.mat['wh'] = self. whitepaint
        self.glass = QDiffuseSpecularMaterial()
        self.glass.setAlphaBlendingEnabled(True)
        self.glass.setAmbient(QColor(0, 0, int(0.4*255)))
        self.glass.setDiffuse(QColor(int(0.0*255),
                                     int(0.0*255),
                                     int(0.4*255),
                                     int(0.7 * 255)))
        #self.glass.setSpecular(QColor(0, 0, int(0.2*255)))
        #self.glass.setShininess(0.99)
        self.mat['glass'] = self.glass

    def loadModels(self, model_list, rootentity=None):
        for model_object in model_list:
            if type(model_object) == tuple:
                src, mat, trans = model_object
                e = QEntity(rootentity)
                mesh = QMesh()
                print('loading model', src)
                mesh.setSource(QUrl.fromLocalFile(src))
                if trans is not None:
                    t = QTransform()
                    if 'rotationX' in trans:
                        t.setRotationX(trans['rotationX'])
                    if 'rotationY' in trans:
                        t.setRotationY(trans['rotationY'])
                    if 'rotationZ' in trans:
                        t.setRotationZ(trans['rotationZ'])
                    if 'translation' in trans:
                        t.translation(QVector3D(trans['translation']))
                    e.addComponent(t)
                e.addComponent(self.mat[mat])
                e.addComponent(mesh)
            elif type(model_object) == list:
                e = QEntity(rootentity)
                t = self.listtransforms.pop(0)
                e.addComponent(t)
                self.loadModels(model_object, e)

    def setWorld(self, world):
        self.world = world

    def setLatitude(self, latitude):
        self.latitude = latitude
        if self.latitude < 0.0:
            self.hemisphere = 'S'
        else:
            self.hemisphere = 'N'
        self.latitudetransform.setMatrix(QTransform.rotateAround(
            Model3D._model_centers[1], -self.latitude,
            QVector3D(0.0, 1.0, 0.0)))

    def setLongitude(self, longitude):
        self.longitude = longitude

    def setRA(self, ra):
        self.RA = ra
        self.RAtransform.setMatrix(QTransform.rotateAround(
            Model3D._model_centers[2], self.RA, QVector3D(1,0,0)))

    def setHA(self, hour):
        hourangle = self.range24(hour + 6.0)
        hourangle = hourangle * 360.0 / 24.0
        self.setRA(hourangle)

    def setDEC(self, dec):
        self.DEC = 90.0 - dec
        self.DECtransform.setMatrix(QTransform.rotateAround(
            Model3D._model_centers[3], self.DEC, QVector3D(0,0,1)))

    def rangeHA(self, ha):
        res = ha
        while (res < -12.0):
            res += 24.0
        while (res >= 12.0):
            res -= 24.0
        return res

    def range24(self, r):
        res = r
        while (res < 0.0):
            res += 24.0
        while (res > 24.0):
            res -= 24.0
        return res

    def range360(self, r):
        res = r
        while (res < 0.0):
            res += 360.0
        while (res > 360.0):
            res -= 360.0
        return res

    def rangeDec(self, decdegrees):
        if ((decdegrees >= 270.0) and (decdegrees <= 360.0)):
            return (decdegrees - 360.0)
        if ((decdegrees >= 180.0) and (decdegrees < 270.0)):
            return (180.0 - decdegrees)
        if ((decdegrees >= 90.0) and (decdegrees < 180.0)):
            return (180.0 - decdegrees)
        return decdegrees

    def setCoord(self, skypoint, physicalpierside='PIER_EAST'):
        self.celestialra = skypoint.ra().Hours()
        self.celestialdec = skypoint.dec().Degrees()
        self.celestialaz = skypoint.az().Degrees()
        self.celestialalt = skypoint.alt().Degrees()
        if self.world:
            lst = self.world.get_gast()
        else:
            lst = self.serv_time.get_gast()
        ha = self.rangeHA(self.celestialra - lst)
        targetra = self.celestialra
        targetdec = self.celestialdec
        if ha < 0.0:
            if (self.hemisphere=='N' and physicalpierside=='PIER_WEST') or (
                self.hemisphere=='S' and physicalpierside=='PIER_EAST'):
                targetra=self.range24(self.celestialra - 12.0)
        else:
            if (self.hemisphere=='N' and physicalpierside=='PIER_WEST') or (
                self.hemisphere=='S' and physicalpierside=='PIER_EAST'):
                targetra=self.range24(self.celestialra - 12.0)
        ha = self.rangeHA(targetra - lst)
        self.setHA(ha)
        if physicalpierside == 'PIER_WEST':
            targetdec = 180.0 - targetdec
        if self.hemisphere == 'S':
            targetdec = 360.0 - targetdec
        if targetdec > 180.0 and physicalpierside == 'PIER_EAST':
            targetdec = -targetdec
        self.setDEC(targetdec)
        #print('model ', lst, physicalpierside, ha, targetra, targetdec,
        #    self.celestialra, self.celestialdec)
