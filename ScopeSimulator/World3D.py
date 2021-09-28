# Common stuff
import logging
from multiprocessing.pool import ThreadPool

# Numerical stuff
import numpy as np
import scipy.interpolate

# Astronomy stuff
from astropy import units as u
from astropy.coordinates import FK5
from astropy.coordinates import SkyCoord

# meshcat stuff
import meshcat
import meshcat.geometry as g
import meshcat.transformations as tf

# Local stuff
from ScopeSimulator.Catalogs import load_bright_star_5


class World3D():
    """
    Frame: x axis pointing North, y axis pointing Zenith/pole, z axis
    pointing East
    Celestial frame: x axis pointing North, y axis pointing Zenith, Z axis
    pointing East

    From: https://github.com/rdeits/meshcat-python/blob/3460c7fbb8b90f2b577ab9dd29a319dcf879c39a/src/meshcat/geometry.py
    How is a material defined
    class GenericMaterial(Material):
    def __init__(self, color=0xffffff, reflectivity=0.5, map=None,
                 side = 2, transparent = None, opacity = 1.0,
                 linewidth = 1.0,
                 wireframe = False,
                 wireframeLinewidth = 1.0,
                 vertexColors=False,
                 **kwargs):
        super(GenericMaterial, self).__init__()
        self.color = color
        self.reflectivity = reflectivity
        self.map = map
        self.side = side
        self.transparent = transparent
        self.opacity = opacity
        self.linewidth = linewidth
        self.wireframe = wireframe
        self.wireframeLinewidth = wireframeLinewidth
        self.vertexColors = vertexColors
        self.properties = kwargs
    """
    # sky is considered as a sphere centered on origin (assuming topocentric)
    sky_radius = 50.0        #50m
    cardinals_diameter = 0.25 #0.5m
    cardinals_height = 2     #2m
    color_cardinals = {"east": 0xffffff,
                       "west": 0xffffff,
                       "north": 0xff0000,
                       "south": 0xffffff,
                       "zenith": 0xffffff,
                       "nadir": 0xffffff}

    def __init__(self, view3D, gps_coordinates, serv_time=None):
        # serv time encapsulate various time utilities
        self.serv_time = serv_time

        # ground will be attached to the dummy root entity
        self.view3D = view3D

        # Sky will be a rotating frame different from the ground
        self.view3D["sky_jnow"].set_object(
            g.Sphere(self.sky_radius),
            g.MeshLambertMaterial(
                color=0x020458,
                reflectivity=0.01))
        self.sky_transform = tf.rotation_matrix(0, [0, 1, 0])

        # attach ground frame related elements to root entity
        self.make_horizontal_plane()
        self.make_altaz_grid()
        self.make_mount_basement()
        self.make_cardinals()

        # Attach sky frame related elements to sky entity
        self.make_equatorial_grid()
        self.make_stars()

        # Helps define sky frame relative to ground frame (root entity)
        #self.time=QQuaternion()
        #self.latitude = QQuaternion()
        self.set_latitude(gps_coordinates["latitude"])
        self.set_longitude(gps_coordinates["longitude"])
        self.set_celestial_time(self.get_celestial_time())

    def update_celestial_time(self, celestial_time=None):
        if celestial_time is None:
            celestial_time = self.celestial_time
        self.set_celestial_time(celestial_time)

    def get_celestial_time(self):
        """
        Give the AD coordinate of the sky that is at the same location as the
        sun during spring equinox (when it overlays with vernal point)
        :return:
        """
        return self.serv_time.get_astropy_celestial_time(
            longitude=self.longitude)

    def update_sky_transform(self):
        """
           transform the sky entity from reference frame (ground) to celestial
           We recall how is the sky entity frame defined
            - x axis: should be center to vernal point
            - y axis: should be center to 90deg east
            - z axis: should be center to north celestial pole
             RA coordinates, seen from north
             hemisphere, go from vernal (00:00) to east (6:00), ...

           We also recall the main frame definition:
            - x axis pointing North
            - y axis pointing Zenith/pole
            - z axis pointing East

           qlatitude is a quaternion that define rotation around
        """
        #self.sky_transform.setRotation(self.qlatitude * self.qtime)
        pass

    def set_latitude(self, latitude):
        """
           Recall frame:
           Qt3D frame: x axis pointing North, y axis pointing Zenith/pole, z axis
           pointing East
           Celestial frame: x axis pointing South, y axis pointing East, Z axis
           pointing Zenith/pole
           Recall latitude:
           We recall that input latitude is 90deg at north pole and -90 at
           south pole, in this context, we are using a 3D spherical coordinate
           system where angle is 0 at south pole, grow up to 90 at equateur
           and then jump directly at -90 (wtf) in northern hemisphere, and
           decays again to reach 0 again at north pole.
           Displacement to the given latitude coordinate is considered as a
           rotation around z axis: (0,0,1) in the Qt3D frame
        """   
        # self.latitude = latitude
        # if self.latitude < 0.0:
        #     angle = 90.0 - abs(self.latitude)
        # else:
        #     angle = -(90.0 - self.latitude)
        # self.qlatitude = QQuaternion.fromAxisAndAngle(
        #     QVector3D(0.0, 0.0, 1.0),
        #     angle)
        # self.update_sky_transform()
        pass

    def set_longitude(self, longitude):
        """
           Recall frame:
           Qt3D frame: x axis pointing North, y axis pointing Zenith/pole, z axis
           pointing East
           Celestial frame: x axis pointing South, y axis pointing East, Z axis
           pointing Zenith/pole
           Recall latitude:
           We recall that input latitude is 0 at greenwich (UK) and start to
           grow from there, going east (around 3-6 in France) up to +360
           Equivalently one can start from 0, and decrease in negative number
           up to -180 going west.
           In this context, we use the converse definition locally: longitude is 
           defined as rotation around y axis: (0,1,0) of -latitude axis in the
           Qt3D frame
        """   
        self.longitude = longitude
        self.update_sky_transform()

    def set_celestial_time(self, celestial_time):
        """
        We recall that celestial time is
        passant de l'hémisphère Sud à l'hémisphère Nord, c'est le nœud ascendant. Ce dernier est le point vernal (noté γ, parfois g), parfois noté point de l'équinoxe vernal ou point de l'équinoxe de printemps, ou encore point gamma.

Les références du système de coordonnées équatoriales sont d'une part le méridien passant par le point vernal, il définit le méridien zéro pour la mesure des ascensions droites, et d'autre part l'équateur céleste à partir duquel la déclinaison est mesurée (positivement au-dessus de l'équateur, négativement en dessous).

Les coordonnées du point vernal sont l'ascension droite (α) = 0 h (étant situé sur le méridien zéro) et sa déclinaison (δ) est nulle (étant situé sur l'équateur céleste).


        :param celestial_time:  astropy.coordinates.angles.Longitude to be
        simulated
        :return:
        """
        # self.celestial_time = celestial_time
        # angle = float(self.celestial_time.to(u.degree).value)
        # self.qtime = QQuaternion.fromAxisAndAngle(QVector3D(0.0, 1.0, 0.0),
        #                                           angle)
        # self.update_sky_transform()
        pass

    def make_horizontal_plane(self):
        """
           Builds the earth ground, (simple plain green colored plane mesh)

        """
        self.view3D["/Background"].set_property("top_color", [0, 1, 0])
        self.view3D['/Grid'].set_property("visible", True)
        # self.horizontal_plane = QEntity()
        # self.horizontal_mesh = QPlaneMesh()
        # self.horizontal_mesh.setWidth(2 * World3D._sky_radius)
        # self.horizontal_mesh.setHeight(2 * World3D._sky_radius)
        # self.horizontal_mesh.setMeshResolution(QSize(50, 50))
        # #self.horizontal_mesh.setMirrored(True)
        # #self.horizontalTransform = QTransform()
        # #self.horizontalTransform.setMatrix(QTransform.rotateAround(
        # #    QVector3D(0,0,0), 90.0, QVector3D(1.0, 0.0, 0.0)))
        # #self.horizontalTransform.setTranslation(QVector3D(0.0, -10.0, 0.0))
        # self.horizontal_mat = QDiffuseSpecularMaterial()
        # self.horizontal_mat.setAmbient(QColor(0, 128, 0))
        # #self.horizontal_plane.addComponent(self.horizontalTransform)
        # self.horizontal_plane.addComponent(self.horizontal_mat)
        # self.horizontal_plane.addComponent(self.horizontal_mesh)
        # self.horizontal_plane.setParent(self.root_entity)
        pass

    def make_equatorial_grid(self):
        """
           Equatorial grid helps vizualize the spherical coordinate system
           whose main axis is colinear to earth rotation axis
           We choose:
            -18 rings: 1 tick every 10 degrees for the 180 degrees of
              declination. 90 being north pole (close to polar star) and -90
              standing for south pole. 0 degrees is on the celestial equator
            -24 slices: 1 tick every hour for the 24 hours of right ascension
              00h standing for position of sun in background star at spring
              meridian at its highest position (ie intersecting celestial
              equator). This point for origin is also called vernal point.

           One should notice that this ground plane is attached to the sky
           entity

           Documentation for QSphereMesh:
           https://doc.qt.io/qt-5/qt3dextras-qspheremesh.html
           A spherical mesh with 3 properties
           setRadius(float radius)
           setRings(int rings)
           setSlices(int slices)

           Inherits from QGeometryRenderer whose doc is there:
           https://doc.qt.io/qt-5/qt3drender-qgeometryrenderer.html
        """
        # self.equatorial_grid = QEntity()
        # self.equatorial_mesh = QSphereMesh()
        # self.equatorial_mesh.setRadius(World3D._sky_radius)
        # self.equatorial_mesh.setRings(18)
        # self.equatorial_mesh.setSlices(24)
        # self.equatorial_mesh.setPrimitiveType(QGeometryRenderer.Lines)
        # self.equatorial_transform = QTransform()
        # #self.equatorial_transform.setRotationZ(-(90 - 49.29))
        # self.equatorial_mat = QDiffuseSpecularMaterial()
        # self.equatorial_mat.setAmbient(QColor(200,0,0))
        # self.equatorial_grid.addComponent(self.equatorial_transform)
        # self.equatorial_grid.addComponent(self.equatorial_mat)
        # self.equatorial_grid.addComponent(self.equatorial_mesh)
        # self.equatorial_grid.setParent(self.sky_entity)
        pass

    def make_altaz_grid(self):
        """
            Altaz grid helps vizualize the spherical coordinate system whose
            main axis is colinear to the normal to earth sphere at observer
            position
            We choose:
              -18 rings: 1 tick every 10 degrees for the 180 degrees of altitude
               90 standing for zenith and -90 for the nadir
              -36 slices: 1 tick every 10 degrees for the 360 degrees of azimuth
               0 being oriented towards north, and 90 degrees towards east

           One should notice that this altaz grid is attached to the root
           entity
        """
        # self.horizontalGrid = QEntity()
        # self.horizontal_mesh = QSphereMesh()
        # self.horizontal_mesh.setRadius(World3D._sky_radius)
        # self.horizontal_mesh.setRings(18)
        # self.horizontal_mesh.setSlices(36)
        # self.horizontal_mesh.setPrimitiveType(QGeometryRenderer.Lines)
        # self.horizontalTransform = QTransform()
        # self.horizontalTransform.setRotationX(0.0)
        # self.horizontal_mat = QDiffuseSpecularMaterial()
        # self.horizontal_mat.setAmbient(QColor(0,0,200))
        # self.horizontalGrid.addComponent(self.horizontalTransform)
        # self.horizontalGrid.addComponent(self.horizontal_mat)
        # self.horizontalGrid.addComponent(self.horizontal_mesh)
        # self.horizontalGrid.setParent(self.root_entity)
        pass

    def make_mount_basement(self):
        """
           Right at the foot of the observer, we put an image of a compass in
           order to ease understanding of the scene.
           As in the ground horizontal plane, we define a PlaneMesh

           Qt3D frame: x axis pointing North, y axis pointing Zenith/pole, z axis
           pointing East

           One should notice that the "mount basement" is attached to the root
           entity

           Doc for QTextureLoader:
           https://doc.qt.io/qt-5/qt3drender-qtextureloader.html
           Handles the texture loading and setting the texture's properties.

        """
        # # self.svgRenderer = QSvgRenderer()
        # # self.svgRenderer.load('compass.svg')
        # # self.compass = QImage(self.svgRenderer.defaultSize(), QImage.Format_ARGB32)
        # # self.compass_texture = QTexture2D()
        # # self.compass_texture.addTextureImage(self.compass)
        # self.compass_texture = QTextureLoader()
        # self.compass_texture.setMirrored(False)
        # self.compass_texture.setSource(
        #     QUrl.fromLocalFile('ScopeSimulator/data/compass.svg.png'))
        # self.basement_grid = QEntity()
        # # self.basement_mesh = QCylinderMesh()
        # # self.basement_mesh.setRadius(1500.0)
        # # self.basement_mesh.setLength(10.0)
        # # self.basement_mesh.setSlices(360)
        # self.basement_mesh = QPlaneMesh()
        # self.basement_mesh.setWidth(1500.0) #1500mm = 1.5m
        # self.basement_mesh.setHeight(1500.0) #1500mm = 1.5m
        # self.basement_mesh.setMeshResolution(QSize(2, 2))
        # self.basement_transform = QTransform()
        # # move texture just 5mm above ground towards zenith for visibility
        # self.basement_transform.setTranslation(QVector3D(0,20.0,0))
        # self.basement_transform.setRotationY(-90.0)
        # self.basement_mat_back = QDiffuseSpecularMaterial()
        # self.basement_mat_back.setAmbient(QColor(200,200,228))
        # self.basement_mat = QTextureMaterial()
        # self.basement_mat.setTexture(self.compass_texture)
        # self.basement_grid.addComponent(self.basement_transform)
        # self.basement_grid.addComponent(self.basement_mat_back)
        # self.basement_grid.addComponent(self.basement_mat)
        # self.basement_grid.addComponent(self.basement_mesh)
        # self.basement_grid.setParent(self.root_entity)
        pass

    def make_cardinals(self):
        """
           We decide to put some labels on the cardinal points, ie, 
           Nort/East/South/West/Zenith/Nadir
           We recall that this element is connected to the root entity, and we
           also recall frame:
           main frame:
             -index 0 : x axis : red    : pointing North,
             -index 1 : z axis : green   : pointing zenith
             -index 2 : y axis : blue  : pointing zenith
            Warning: everytime you apply a transformation to an object, every subsequent transform will be composed
            hence, applied on the new frame defined from previous transform.
        """
        logging.info("Drawing cardinals...")
        cardinals_transforms = {}
        for card_name in ["east", "west", "north", "south", "zenith", "nadir"]:
            self.view3D["cardinals"][card_name].set_object(
                g.Cylinder(self.cardinals_height, self.cardinals_diameter),
                g.MeshLambertMaterial(color=self.color_cardinals[card_name]))
            # We want cylinder to be above ground
            # By default cylinder is aligned with y axis and centered
            cardinals_transforms[card_name] = (
                tf.translation_matrix([0, 0, self.cardinals_height/2]))

        # Now define specific translations for each cardinal
        cardinals_transforms["east"] = np.dot(
            cardinals_transforms["east"],
            tf.translation_matrix([0, -1*self.sky_radius, 0]))
        cardinals_transforms["west"] = np.dot(
            cardinals_transforms["west"],
            tf.translation_matrix([0, 1*self.sky_radius, 0]))
        cardinals_transforms["north"] = np.dot(
            cardinals_transforms["north"],
            tf.translation_matrix([1*self.sky_radius, 0, 0]))
        cardinals_transforms["south"] = np.dot(
            cardinals_transforms["south"],
            tf.translation_matrix([-1*self.sky_radius, 0, 0]))
        cardinals_transforms["zenith"] = np.dot(
            cardinals_transforms["zenith"],
            tf.translation_matrix([0, 0, 1*self.sky_radius]))
        cardinals_transforms["nadir"] = np.dot(
            cardinals_transforms["nadir"],
            tf.translation_matrix([0, 0, -1*self.sky_radius]))

        # We want cylinder to be colinear with nadir/zenith axis
        # By default cylinder is aligned with y axis and centered
        # We have already corrected for centering, last task is
        # to correct for orientation
        for card_name, card_transform in cardinals_transforms.items():
            # rotate around x to make it stand and aligned with z
            cardinals_transforms[card_name] = np.dot(
                cardinals_transforms[card_name],
                tf.rotation_matrix(np.pi / 2, [1, 0, 0]))

        # Now apply the final transformation
        for card_name, card_transform in cardinals_transforms.items():
            self.view3D["cardinals"][card_name].set_transform(card_transform)

        logging.info("Cardinals drawn")

    def make_stars(self):
        """
           star coordinates from J2000.0 equinox
           the "sky_jnow" scene tree will be populated.
           Assuming that, at departure position (no time, nor lat/lon transform applied):
           - north cardinal is 0 deg RA
           - south cardinal is 180 deg RA
           - zenith cardinal is +90deg Dec
           - nadir cardinal is -90 deg Dec
        """
        # Loads star catalog and render on the sky parent object
        stars = load_bright_star_5('ScopeSimulator/data/bsc5.dat.gz', True)
        stars = self.j2k_to_jnow(stars)
        radius_mag = [2, 1.5, .75, .5, .4, .3, .2]
        mag_to_radius = scipy.interpolate.interp1d(
            range(1, 8),
            radius_mag,
            axis=0,
            kind='quadratic',
            fill_value=(max(radius_mag), min(radius_mag)),
            bounds_error=False,
            assume_sorted=False)
        for star in stars:
            star_id = str(hash(star["nom"]))
            self.view3D["sky_jnow"][star_id].set_object(
                g.Sphere(float(mag_to_radius(float(star['mag'])))),
                g.MeshLambertMaterial(
                    color=0xfafbd7,
                    reflectivity=0.8))
            #We first apply rotation to expected position
            tr = tf.rotation_matrix(star['ra'], [0, 0, 1])
            tr = tr.dot(tf.rotation_matrix(star['de'] / 2, [0, 1, 0]))
            # Then we compose with translation on sky sphere
            tr = tr.dot(tf.translation_matrix([self.sky_radius*0.9, 0, 0]))
            # Now we apply transform
            self.view3D["sky_jnow"][star_id].set_transform(tr)

        #     e = QEntity()
        #     e_star = QSphereMesh()
        #     e_radius = mag_to_radius(float(star['mag']))
        #     e_star.setRadius(e_radius)
        #     e_transform = QTransform()
        #     # project celestial coordinates in radians on 3d cartesian
        #     # coordinates in sky2000 frame, assuming:
        #     # x axis: should be center to vernal point
        #     # y axis: should be center to 90deg east
        #     # z axis: should be center to north celestial pole
        #     # RA coordinates, seen from north
        #     # hemisphere, go from vernal (00:00) to east (6:00), ...
        #     # which is the contrary of radians
        #     ex = ((World3D._sky_radius - 150.0) * np.cos(star['ra']) *
        #           np.cos(star['de']))
        #     ey = ((World3D._sky_radius -150.0) * np.sin(star['ra']) *
        #           np.cos(star['de']))
        #     ez = ((World3D._sky_radius - 150.0) * np.sin(star['de']))
        #     e_transform.setTranslation(QVector3D(ex, ez, ey))
        #     e.addComponent(star_mat)
        #     e.addComponent(e_transform)
        #     e.addComponent(e_star)
        #     e.setParent(self.skyJ2000)


        # define a QObject to attach the stars to
        # self.skyJ2000 = QEntity()
        #
        # # Define star material for nice rendering
        # star_mat = QDiffuseSpecularMaterial()
        # star_mat.setAmbient(QColor(255,255,224))
        # star_mat.setDiffuse(QColor(255,255,224))
        #
        # # Loads star catalog and render on the sky parent object
        # stars = load_bright_star_5('ScopeSimulator/data/bsc5.dat.gz', True)
        # stars = self.j2k_to_jnow(stars)
        # radius_mag = [200, 150, 75, 50, 40, 30, 20]
        # mag_to_radius = scipy.interpolate.interp1d(
        #     range(1,8),
        #     radius_mag,
        #     axis=0,
        #     kind='quadratic',
        #     fill_value=(max(radius_mag), min(radius_mag)),
        #     bounds_error=False,
        #     assume_sorted=False)
        # for star in stars:
        #     e = QEntity()
        #     e_star = QSphereMesh()
        #     e_radius = mag_to_radius(float(star['mag']))
        #     e_star.setRadius(e_radius)
        #     e_transform = QTransform()
        #     # project celestial coordinates in radians on 3d cartesian
        #     # coordinates in sky2000 frame, assuming:
        #     # x axis: should be center to vernal point
        #     # y axis: should be center to 90deg east
        #     # z axis: should be center to north celestial pole
        #     # RA coordinates, seen from north
        #     # hemisphere, go from vernal (00:00) to east (6:00), ...
        #     # which is the contrary of radians
        #     ex = ((World3D._sky_radius - 150.0) * np.cos(star['ra']) *
        #           np.cos(star['de']))
        #     ey = ((World3D._sky_radius -150.0) * np.sin(star['ra']) *
        #           np.cos(star['de']))
        #     ez = ((World3D._sky_radius - 150.0) * np.sin(star['de']))
        #     e_transform.setTranslation(QVector3D(ex, ez, ey))
        #     e.addComponent(star_mat)
        #     e.addComponent(e_transform)
        #     e.addComponent(e_star)
        #     e.setParent(self.skyJ2000)
        #
        # self.skyJ2000.setParent(self.sky_entity)
        pass

    def j2k_to_jnow(self, coords):
        now = self.serv_time.get_astropy_time_from_utc()

        def convert_from_j2k_to_jnow(coord):
            coord_j2k = SkyCoord(ra=coord['ra_degres'] * u.degree,
                                 dec=coord['de_degres'] * u.degree,
                                 frame='icrs',
                                 equinox='J2000.0')
            fk5_now = FK5(equinox=now)
            coord_jnow = coord_j2k.transform_to(fk5_now)
            coord['ra'] = coord_jnow.ra.radian
            coord['de'] = coord_jnow.dec.radian
            coord['ra_degres'] = coord_jnow.ra.degree
            coord['de_degres'] = coord_jnow.dec.degree
            return coord

        with ThreadPool(4) as p:
            p.map(convert_from_j2k_to_jnow, coords)

        return coords