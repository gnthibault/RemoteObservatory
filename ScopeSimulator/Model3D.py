# Numerical tools
import numpy as np

# Astropy stuff
from astropy.coordinates import SkyCoord

# meshcat 3d stuff
import meshcat
import meshcat.geometry as g
import meshcat.transformations as tf

class Model3D():
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
    _model_centers = [[0.0, 0.0, 850.0],
                      [5.0, 0.0, 925.0],
                      [100.0, 0.0, 1005.0],
                      [170.0, 0.0, 1085.0],
                      [-40.0, 0.0, 1225.0]]

    def __init__(self, view3D, serv_time=None):
        super().__init__()
        self.view3D = view3D
        self.serv_time = serv_time
        self.azimuth = 0.0
        self.latitude = 0.0
        self.longitude = 0.0
        self.hemisphere = 'N'
        self.ra = 0.0
        self.DEC = 0.0
        self.crayfordangle = 0.0
        self.crayfordposition = 0.0
        self.world = None
        self.mat = dict()
        self.makeMaterials()

        # Different transformations for different part of the telescope
        self.modeltransform = tf.rotation_matrix(0, [0, 0, 1])
        self.modeltransform.setRotationX(-90.0)
        self.addComponent(self.modeltransform)
        # Transformations (one per depth in the model list)
        self.azimuthtransform = tf.rotation_matrix(0, [0, 0, 1])
        self.latitude_transform = tf.rotation_matrix(0, [0, 0, 1])
        self.ra_transform = tf.rotation_matrix(0, [0, 0, 1])
        self.dec_transform = tf.rotation_matrix(0, [0, 0, 1])
        self.crayford_transform = tf.rotation_matrix(0, [0, 0, 1])
        self.crayford_tube_transform = tf.rotation_matrix(0, [0, 0, 1])
        self.list_transforms=[
            self.azimuthtransform,
            self.latitude_transform,
            self.ra_transform,
            self.dec_transform,
            self.crayford_transform,
            self.crayford_tube_transform]
        self.load_models(Model3D._model_file_mat, self)
        #self.azimuthtransform.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[0], self.azimuth, QVector3D(0,0,1)))
        #self.latitude_transform.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[1], self.latitude,
        #    QVector3D(0.0, 1.0, 0.0)))
        #self.ra_transform.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[2], -self.ra + 90, QVector3D(1,0,0)))
        # self.dec_transform.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[3], -self.DEC + 90, QVector3D(0,0,1)))
        self.set_longitude(self.longitude)
        self.set_latitude(self.latitude)
        self.set_ra(self.ra)
        self.set_dec(self.DEC)
        self.crayford_transform.setMatrix(QTransform.rotateAround(
            Model3D._model_centers[4], self.crayfordangle, QVector3D(1,0,0)))
        self.crayford_tube_transform.setTranslation(QVector3D(
            self.crayfordposition, 0.0, 0.0))

    def makeMaterials(self):
        self.metalgray50 = g.MeshLambertMaterial(
            color=0x808080,
            transparent=False,
            opacity=1.0)
        self.mat['mg50'] = self.metalgray50
        self.metalgray70 = g.MeshLambertMaterial(
            color=int(0.7*255) << 16 + int(0.7*255) << 8 + int(0.7*255),
            transparent=False,
            opacity=1.0)
        self.mat['mg70'] = self.metalgray70
        self.stainless = g.MeshLambertMaterial(
            color=224 << 16 + 223 << 8 + 219,
            transparent=False,
            opacity=1.0)
        self.mat['st'] = self.stainless
        self.whitepaint = g.MeshLambertMaterial(
            color=228 << 16 + 228 << 8 + 228,
            transparent=False,
            opacity=1.0)
        self.mat['wh'] = self. whitepaint
        self.glass = g.MeshLambertMaterial(
            color=0x000066,
            transparent=False,
            opacity=.7)
        self.mat['glass'] = self.glass

    def load_models(self, model_list, base_entity=None):
        if base_entity is None:
            base_entity = self.view3D["mount"]
        for model_object in model_list:
            if type(model_object) == tuple:
                src, mat, trans = model_object
                print('loading model', src)

                # Load mesh into scene structure
                object = g.Mesh(g.StlMeshGeometry.from_file(src))
                if trans is not None:
                    tr = tf.rotation_matrix(0, [0, 0, 1])
                    if 'rotationX' in trans:
                        tr = tr.dot(
                            tf.rotation_matrix(np.deg2rad(trans['rotationX']),
                                               [1,0,0]))
                    if 'rotationY' in trans:
                        tr = tr.dot(
                            tf.rotation_matrix(np.deg2rad(trans['rotationY']),
                                               [0, 1, 0]))
                    if 'rotationZ' in trans:
                        tr = tr.dot(
                            tf.rotation_matrix(np.deg2rad(trans['rotationZ']),
                                               [0, 0, 1]))
                    if 'translation' in trans:
                        tr = tr.dot(
                            tf.translation_matrix(trans['translation']))
                material = self.mat[mat]
                base_entity[src].set_object(object, material)
                base_entity[src].set_transform(tr)
            elif type(model_object) == list:
                e = base_entity
                tr = self.list_transforms.pop(0)
                e.set_transform(tr)
                self.load_models(model_object, e)

    def set_latitude(self, latitude):
        self.latitude = latitude
        if self.latitude < 0.0:
            self.hemisphere = 'S'
        else:
            self.hemisphere = 'N'
        self.latitude_transform.setMatrix(QTransform.rotateAround(
            Model3D._model_centers[1], -self.latitude,
            QVector3D(0.0, 1.0, 0.0)))

    def set_longitude(self, longitude):
        self.longitude = longitude

    def set_ra(self, ra):
        self.ra = ra
        self.ra_transform.setMatrix(QTransform.rotateAround(
            Model3D._model_centers[2], self.ra, QVector3D(1,0,0)))

    def setHA(self, hour):
        hourangle = self.range24(hour + 6.0)
        hourangle = hourangle * 360.0 / 24.0
        self.set_ra(hourangle)

    def set_dec(self, dec):
        self.DEC = 90.0 - dec
        self.dec_transform.setMatrix(QTransform.rotateAround(
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

    def set_coord(self, skypoint, physicalpierside='PIER_EAST'):
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
        self.set_dec(targetdec)
        #print('model ', lst, physicalpierside, ha, targetra, targetdec,
        #    self.celestialra, self.celestialdec)
