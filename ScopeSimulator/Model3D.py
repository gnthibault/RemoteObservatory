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
    model_file_mat = [
        (stl_path + '/leg.stl', 'st', None),
        (stl_path + '/leg.stl', 'st', {'rotationZ': 120.0}),
        (stl_path + '/leg.stl', 'st', {'rotationZ': 240.0}),
        (stl_path + '/basetripod.stl', 'mg70', None),
        [
            (stl_path + '/baseholder.stl', 'mg50', None),
            [
                (stl_path + '/rahousing.stl', 'mg50', None),
                [
                    (stl_path + '/raaxis.stl', 'mg50', None),
                    (stl_path + '/dehousing.stl', 'mg50', None),
                    [
                        (stl_path + '/deaxis.stl', 'mg50', None),
                        (stl_path + '/cwbar.stl', 'st', None),
                        (stl_path + '/dovetail.stl', 'mg70', None),
                        (stl_path + '/refractor.stl', 'wh', None),
                        (stl_path + '/lens.stl', 'glass', None),
                        (stl_path + '/crayford-spacer.stl', 'mg70', None),
                        [
                            (stl_path + '/crayford-cylinder.stl', 'mg70', None),
                            [
                                (stl_path + '/crayford-tube.stl', 'st', None),
                            ]
                        ]
                    ]
                ]
            ]
        ]
    ]
    model_centers = {
        "azimut_alignment": [0.0, 0.0, 850.0],
        "polar_alignment": [5.0, 0.0, 925.0],
        "ra_axis": [100.0, 0.0, 1005.0],
        "dec_axis": [170.0, 0.0, 1085.0],
        "crayford": [-40.0, 0.0, 1225.0]}

    def __init__(self, view3D, gps_coordinates, serv_time=None):
        self.view3D = view3D
        self.serv_time = serv_time
        self.azimuth = 0.0
        self.latitude = 0.0
        self.longitude = 0.0
        self.hemisphere = 'N'
        self.ra = 0.0
        self.dec = 0.0
        self.crayford_angle = 0.0
        self.crayford_position = 0.0
        self.world = None
        self.mat = dict()
        self.makeMaterials()

        # Different transformations for different part of the telescope
        self.modeltransform = tf.rotation_matrix(0, [0, 0, 1])
        self.modeltransform.setRotationX(-90.0)
        self.addComponent(self.modeltransform)

        # Transformations (one per depth in the model list)
        self.transforms = {
            "azimut": None,
            "latitude": None,
            "ra": None,
            "dec": None,
            "crayford": None,
            "crayford_tube": None
        }
        self.list_transforms = [self.transforms[entry] for entry in [
            "azimut",
            "latitude",
            "ra",
            "dec",
            "crayford",
            "crayford_tube"]]
        self.load_models(Model3D.model_file_mat, self.view3D["mount"])
        # self.azimuthtransform.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[0], self.azimuth, QVector3D(0,0,1)))
        # self.latitude.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[1], self.latitude,
        #    QVector3D(0.0, 1.0, 0.0)))
        # self.ra.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[2], -self.ra + 90, QVector3D(1,0,0)))
        # self.dec.setMatrix(QTransform.rotateAround(
        #    Model3D._model_centers[3], -self.dec + 90, QVector3D(0,0,1)))
        self.set_latitude(gps_coordinates["latitude"])
        self.set_longitude(gps_coordinates["longitude"])
        self.set_ra(self.ra)
        self.set_dec(self.dec)
        self.transforms["crayford"] = tf.rotation_matrix(0, [0, 0, 1])
        # .setMatrix(QTransform.rotateAround(
        # Model3D.model_centers["crayford"], self.crayford_angle, QVector3D(1,0,0)))
        self.transforms["crayford_tube"] = tf.translation_matrix([0, 0, 0])
        # .setTranslation(QVector3D(
        # self.crayford_position, 0.0, 0.0))

    def makeMaterials(self):
        self.metalgray50 = g.MeshLambertMaterial(
            color=0x808080,
            transparent=False,
            opacity=1.0)
        self.mat['mg50'] = self.metalgray50
        self.metalgray70 = g.MeshLambertMaterial(
            color=int(0.7 * 255) << 16 + int(0.7 * 255) << 8 + int(0.7 * 255),
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
        self.mat['wh'] = self.whitepaint
        self.glass = g.MeshLambertMaterial(
            color=0x000066,
            transparent=False,
            opacity=.7)
        self.mat['glass'] = self.glass

    def load_models(self, model_list, base_entity):
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
                                               [1, 0, 0]))
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
            elif isinstance(model_object, list):
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
        self.transforms["latitude"] = tf.rotation_matrix(
            -self.latitude,
            Model3D.model_centers["polar_alignment"])

    def set_longitude(self, longitude):
        self.longitude = longitude

    def set_ra(self, ra):
        self.ra = ra
        self.transforms["ra"] = tf.rotation_matrix(0, [0, 0, 1])
        # self.ra.setMatrix(QTransform.rotateAround(
        #    Model3D.model_centers["ra_axis"], self.ra, QVector3D(1,0,0)))

    def setHA(self, hour):
        hourangle = self.range24(hour + 6.0)
        hourangle = hourangle * 360.0 / 24.0
        self.set_ra(hourangle)

    def set_dec(self, dec):
        self.dec = 90.0 - dec
        self.transforms["dec"] = tf.rotation_matrix(0, [0, 0, 1])
        # self.dec.setMatrix(QTransform.rotateAround(
        #    Model3D.model_centers["dec_axis"], self.dec, QVector3D(0,0,1)))

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

    def set_coord(self, skypoint, pier_side='PIER_EAST'):
        celestial_ra = skypoint.ra().Hours()
        celestial_dec = skypoint.dec().Degrees()
        # In case one wants to implement altaz later on
        # celestial_az = skypoint.az().Degrees()
        # celestial_alt = skypoint.alt().Degrees()
        lst = self.serv_time.get_gast()
        ha = self.rangeHA(celestial_ra - lst)
        target_ra = celestial_ra
        target_dec = celestial_dec
        if ha < 0.0:
            if (self.hemisphere == 'N' and pier_side == 'PIER_WEST') or (
                    self.hemisphere == 'S' and pier_side == 'PIER_EAST'):
                target_ra = self.range24(celestial_ra - 12.0)
        else:
            if (self.hemisphere == 'N' and pier_side == 'PIER_WEST') or (
                    self.hemisphere == 'S' and pier_side == 'PIER_EAST'):
                target_ra = self.range24(celestial_ra - 12.0)
        ha = self.rangeHA(target_ra - lst)
        self.setHA(ha)
        if pier_side == 'PIER_WEST':
            target_dec = 180.0 - target_dec
        if self.hemisphere == 'S':
            target_dec = 360.0 - target_dec
        if target_dec > 180.0 and pier_side == 'PIER_EAST':
            target_dec = -target_dec
        self.set_dec(target_dec)
        # print('model ', lst, pier_side, ha, target_ra, target_dec,
        #    celestial_ra, celestial_dec)
