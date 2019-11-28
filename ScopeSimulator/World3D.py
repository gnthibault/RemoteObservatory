# Common stuff
import struct
from multiprocessing.pool import ThreadPool

# Numerical stuff
import numpy as np
import scipy.interpolate

# Astronomy stuff
from astropy import units as u
from astropy.coordinates import FK5
from astropy.coordinates import SkyCoord

# PyQt stuff
from PyQt5.QtGui import QColor, QVector3D, QImage, QFont
from PyQt5.QtGui import QQuaternion, QMatrix3x3
from PyQt5.QtCore import QSize, QUrl, QByteArray, QTimer
from PyQt5.Qt3DCore import QEntity, QTransform
from PyQt5.Qt3DExtras import QPlaneMesh, QSphereMesh, QCylinderMesh
from PyQt5.Qt3DExtras import QDiffuseSpecularMaterial, QTextureMaterial
from PyQt5.Qt3DExtras import QText2DEntity, QExtrudedTextMesh
from PyQt5.Qt3DRender import QGeometry, QGeometryRenderer,QAttribute, QBuffer
from PyQt5.Qt3DRender import QTexture2D, QTextureLoader, QMaterial, QEffect
from PyQt5.Qt3DRender import QRenderPass, QShaderProgram, QPointSize
from PyQt5.Qt3DRender import QTechnique, QFilterKey, QGraphicsApiFilter
from PyQt5.QtSvg import QSvgRenderer

# Local stuff
from ScopeSimulator.Catalogs import load_bright_star_5

class StarMaterial(QMaterial):
    """
       Implements QMaterial interface 
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        star_effect = QEffect(self)
        star_technique = QTechnique(self)
        star_render_pass = QRenderPass(self)
        star_shader_program = QShaderProgram(self)
        star_render_state = QPointSize(self)
        # Defines color (white) and visibility (wether it is discarded or not)
        star_shader_program.setShaderCode(
            QShaderProgram.Vertex,
            QShaderProgram.loadSource(QUrl.fromLocalFile(
                'ScopeSimulator/shaders/pointcloud.vert')))
        # Defines ?
        star_shader_program.setShaderCode(
            QShaderProgram.Fragment, 
            QShaderProgram.loadSource(QUrl.fromLocalFile(
                'ScopeSimulator/shaders/pointcloud.frag')))
        star_render_pass.setShaderProgram(star_shader_program)
        star_render_state.setSizeMode(QPointSize.Programmable)
        star_render_pass.addRenderState(star_render_state)
        star_technique.addRenderPass(star_render_pass)
        filter_key = QFilterKey()
        filter_key.setName('renderingStyle')
        filter_key.setValue('forward')
        star_technique.addFilterKey(filter_key)
        star_technique.graphicsApiFilter().setApi(QGraphicsApiFilter.OpenGL)
        star_technique.graphicsApiFilter().setMajorVersion(3)
        star_technique.graphicsApiFilter().setMinorVersion(3)
        star_technique.graphicsApiFilter().setProfile(
            QGraphicsApiFilter.CoreProfile)
        #star_technique.graphicsApiFilter().setProfile(
        #    QGraphicsApiFilter.NoProfile)
        star_effect.addTechnique(star_technique)
        super().setEffect(star_effect)

class PointGeometry(QGeometry):

    def __init__(self, parent=None):
        super().__init__(parent)
        pos_attribute = QAttribute(self)
        self.vertex_buffer = QBuffer(self)
        pos_attribute.setName(QAttribute.defaultPositionAttributeName())
        pos_attribute.setVertexBaseType(QAttribute.Float)
        pos_attribute.setVertexSize(3)
        pos_attribute.setAttributeType(QAttribute.VertexAttribute)
        pos_attribute.setBuffer(self.vertex_buffer)
        pos_attribute.setByteOffset(0)
        pos_attribute.setByteStride((3 + 1) * 4) # float32 is 4 bytes
        #pos_attribute.setDivisor(1)
        self.add_attribute(pos_attribute)
        self.positionAttribute = pos_attribute
        radius_attribute = QAttribute(self)
        radius_attribute.setName('radius')
        radius_attribute.setVertexBaseType(QAttribute.Float)
        radius_attribute.setVertexSize(1)
        radius_attribute.setAttributeType(QAttribute.VertexAttribute)
        radius_attribute.setBuffer(self.vertex_buffer)
        radius_attribute.setByteOffset(3 * 4) # float32 is 4 bytes
        #pos_attribute.setByteStride(0)
        radius_attribute.setByteStride((3 + 1) * 4) # float32 is 4 bytes
        #radius_attribute.setDivisor(1)
        self.add_attribute(radius_attribute)
        self.radius_attribute = radius_attribute

class World3D():
    """
    About Qentity, doc from: https://doc.qt.io/qt-5/qt3dcore-qentity.html
    By itself a Qt3DCore::QEntity is an empty shell. The behavior of a
    Qt3DCore::QEntity object is defined by the Qt3DCore::QComponent objects it
    references. Each Qt3D backend aspect will be able to interpret and process
    an Entity by recognizing which components it is made up of. One aspect may
    decide to only process entities composed of a single Qt3DCore::QTransform
    component whilst another may focus on Qt3DInput::QMouseHandler.

    Qt3D frame: x axis pointing North, y axis pointing Zenith/pole, z axis
    pointing East
    Celestial frame: x axis pointing North, y axis pointing Zenith, Z axis
    pointing East
    """
    # _m_celestial is its proper inverse
    _m_celestial_qt = QMatrix3x3([ 1.0, 0.0, 0.0,
                                   0.0, 1.0, 0.0,
                                   0.0, 0.0, 1.0])

    # sky is considered as a sphere centered on origin (assuming topocentric)
    _sky_radius = 50000.0  #500000mm = 50m

    def __init__(self, parent=None, serv_time=None, auto_update=False):
        # serv time encapsulate various time utilities
        self.serv_time = serv_time

        # ground will be attached to the dummy root entity
        self.root_entity = QEntity(parent)

        # Sky entity will be a rotating frame different from the ground
        self.sky_entity = QEntity(self.root_entity)
        self.sky_transform = QTransform()
        self.sky_entity.addComponent(self.sky_transform)

        # attach ground frame related elements to root entity
        self.make_horizontal_plane()
        self.make_altaz_grid()
        self.make_mount_basement()
        self.make_cardinals()

        # Attach sky frame related elements to sky entity
        self.make_equatorial_grid()
        self.make_stars()

        # Helps define sky frame relative to ground frame (root entity)
        self.qtime=QQuaternion()
        self.qlatitude = QQuaternion()
        self.set_latitude(45.0)
        self.set_longitude(5.0)
        self.set_celestial_time(self.get_celestial_time())

        # Initialize update frequency
        if auto_update:
            self.celestial_interval_ms = 1 * 1000
            self.celestial_timer = QTimer()
            self.initialize_refresh_timer()

    def initialize_refresh_timer(self):
        self.celestial_timer.setInterval(
            self.celestial_interval_ms)
        self.celestial_timer.setSingleShot(False)
        self.celestial_timer.timeout.connect(self.update_celestial_time)
        self.celestial_timer.start()

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
        self.sky_transform.setRotation(self.qlatitude * self.qtime)

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
        self.latitude = latitude
        if self.latitude < 0.0:
            angle = 90.0 - abs(self.latitude)
        else:
            angle = -(90.0 - self.latitude)
        self.qlatitude = QQuaternion.fromAxisAndAngle(
            QVector3D(0.0, 0.0, 1.0),
            angle)
        self.update_sky_transform()

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
        :param celestial_time:  astropy.coordinates.angles.Longitude to be
        simulated
        :return:
        """
        self.celestial_time = celestial_time
        angle = float(self.celestial_time.to(u.degree).value)
        self.qtime = QQuaternion.fromAxisAndAngle(QVector3D(0.0, 1.0, 0.0),
                                                  angle)
        self.update_sky_transform()

    def make_horizontal_plane(self):
        """
           Builds the earth ground, (simple plain green colored plane mesh)
           One need to set Width and Height to define the mesh, plus material

           One should notice that this ground plane is attached to the root
           entity

           Documentation for plane mesh:
           https://doc.qt.io/qt-5/qt3dextras-qplanemesh.html
           A square planar mesh. One can set height, width and resolution:
           Holds the plane resolution. The width and height values of this
           property specify the number of vertices generated for the mesh in the
           respective dimensions.

           doc for QDiffuseSpecularMaterial:
           https://doc.qt.io/qt-5/qt3dextras-qdiffusespecularmaterial.html
           The QDiffuseSpecularMaterial class provides a default implementation
           of the phong lighting effect.
           The phong lighting effect is based on the combination of 3 lighting
           components ambient, diffuse and specular. The relative strengths of
           these components are controlled by means of their reflectivity
           coefficients which are modelled as RGB triplets:
           Ambient is the color that is emitted by an object without any other
           light source. Diffuse is the color that is emitted for rought surface
           reflections with the lights. Specular is the color emitted for shiny
           surface reflections with the lights.
           The shininess of a surface is controlled by a float property.
           This material uses an effect with a single render pass approach and
           performs per fragment lighting. Techniques are provided for OpenGL 2,
           OpenGL 3 or above as well as OpenGL ES 2.
        """
        self.horizontal_plane = QEntity()
        self.horizontal_mesh = QPlaneMesh()
        self.horizontal_mesh.setWidth(2 * World3D._sky_radius)
        self.horizontal_mesh.setHeight(2 * World3D._sky_radius)
        self.horizontal_mesh.setMeshResolution(QSize(50, 50))
        #self.horizontal_mesh.setMirrored(True)
        #self.horizontalTransform = QTransform()
        #self.horizontalTransform.setMatrix(QTransform.rotateAround(
        #    QVector3D(0,0,0), 90.0, QVector3D(1.0, 0.0, 0.0)))
        #self.horizontalTransform.setTranslation(QVector3D(0.0, -10.0, 0.0))
        self.horizontal_mat = QDiffuseSpecularMaterial()
        self.horizontal_mat.setAmbient(QColor(0, 128, 0))
        #self.horizontal_plane.addComponent(self.horizontalTransform)
        self.horizontal_plane.addComponent(self.horizontal_mat)
        self.horizontal_plane.addComponent(self.horizontal_mesh)
        self.horizontal_plane.setParent(self.root_entity)

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
        self.equatorial_grid = QEntity()
        self.equatorial_mesh = QSphereMesh()
        self.equatorial_mesh.setRadius(World3D._sky_radius)
        self.equatorial_mesh.setRings(18)
        self.equatorial_mesh.setSlices(24)
        self.equatorial_mesh.setPrimitiveType(QGeometryRenderer.Lines)
        self.equatorial_transform = QTransform()
        #self.equatorial_transform.setRotationZ(-(90 - 49.29))
        self.equatorial_mat = QDiffuseSpecularMaterial()
        self.equatorial_mat.setAmbient(QColor(200,0,0))
        self.equatorial_grid.addComponent(self.equatorial_transform)
        self.equatorial_grid.addComponent(self.equatorial_mat)
        self.equatorial_grid.addComponent(self.equatorial_mesh)
        self.equatorial_grid.setParent(self.sky_entity)

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
        self.horizontalGrid = QEntity()
        self.horizontal_mesh = QSphereMesh()
        self.horizontal_mesh.setRadius(World3D._sky_radius)
        self.horizontal_mesh.setRings(18)
        self.horizontal_mesh.setSlices(36)
        self.horizontal_mesh.setPrimitiveType(QGeometryRenderer.Lines)
        self.horizontalTransform = QTransform()
        self.horizontalTransform.setRotationX(0.0)
        self.horizontal_mat = QDiffuseSpecularMaterial()
        self.horizontal_mat.setAmbient(QColor(0,0,200))
        self.horizontalGrid.addComponent(self.horizontalTransform)
        self.horizontalGrid.addComponent(self.horizontal_mat)
        self.horizontalGrid.addComponent(self.horizontal_mesh)
        self.horizontalGrid.setParent(self.root_entity)

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
        # self.svgRenderer = QSvgRenderer()
        # self.svgRenderer.load('compass.svg')
        # self.compass = QImage(self.svgRenderer.defaultSize(), QImage.Format_ARGB32)
        # self.compass_texture = QTexture2D()
        # self.compass_texture.addTextureImage(self.compass)
        self.compass_texture = QTextureLoader()
        self.compass_texture.setMirrored(False)
        self.compass_texture.setSource(
            QUrl.fromLocalFile('ScopeSimulator/data/compass.svg.png'))
        self.basement_grid = QEntity()
        # self.basement_mesh = QCylinderMesh()
        # self.basement_mesh.setRadius(1500.0)
        # self.basement_mesh.setLength(10.0)
        # self.basement_mesh.setSlices(360)
        self.basement_mesh = QPlaneMesh()
        self.basement_mesh.setWidth(1500.0) #1500mm = 1.5m
        self.basement_mesh.setHeight(1500.0) #1500mm = 1.5m
        self.basement_mesh.setMeshResolution(QSize(2, 2))
        self.basement_transform = QTransform()
        # move texture just 5mm above ground towards zenith for visibility
        self.basement_transform.setTranslation(QVector3D(0,20.0,0))
        self.basement_transform.setRotationY(-90.0)
        self.basement_mat_back = QDiffuseSpecularMaterial()
        self.basement_mat_back.setAmbient(QColor(200,200,228))
        self.basement_mat = QTextureMaterial()
        self.basement_mat.setTexture(self.compass_texture)
        self.basement_grid.addComponent(self.basement_transform)
        self.basement_grid.addComponent(self.basement_mat_back)
        self.basement_grid.addComponent(self.basement_mat)
        self.basement_grid.addComponent(self.basement_mesh)
        self.basement_grid.setParent(self.root_entity)

    def make_cardinals(self):
        """
           We decide to put some labels on the cardinal points, ie, 
           Nort/East/South/West/Zenith/Nadir
           Each cardinal is defined as a 3-uplet:
               -name string
               -translation in Qvector to be applied first
               -rotation around X,Y,Z axis to be applied in the translated frame
                ie, in order to show the letters the right way)
           We recall that this element is connected to the root entity, and we
           also recall frame:
           Qt3D frame: x axis pointing North, y axis pointing Zenith/pole, z axis
           pointing East

           we always but labels 20mm above ground for visibility and 100 mm
           within the sky radius for visibility as well
        """
        cardinals = [
            ('North',
                QVector3D(World3D._sky_radius - 100.0, 20.0, 0.0),
                (0.0, -90.0, 0.0)),
            ('South',
                QVector3D(-(World3D._sky_radius - 100.0), 20.0, 0.0),
                (0.0, 90.0, 0.0)),
            ('East',
                QVector3D(0.0, 20.0, World3D._sky_radius - 100.0),
                (0.0, 180.0, 0.0)),
            ('West',
                QVector3D(0.0, 20.0, -(World3D._sky_radius - 100.0)),
                (0.0, 0.0, 0.0)),
            ('Zenith',
                QVector3D(0.0, World3D._sky_radius - 100.0, 0.0),
                (90.0, 0.0, 0.0)),
            ('Nadir',
                QVector3D(0.0, -(World3D._sky_radius - 100.0), 0.0),
                (-90.0, 0.0, 0.0)),]
        font = QFont('Helvetica', 32)
        self.text_mat = QDiffuseSpecularMaterial()
        self.text_mat.setAmbient(QColor(200,200,228))
        self.cardinals = QEntity()
        for cpoint in cardinals:
            e = QEntity()
            e_text = QExtrudedTextMesh()
            e_text.setText(cpoint[0])
            e_text.setDepth(0.45)
            e_text.setFont(font)
            e_transform = QTransform()
            e_transform.setTranslation(cpoint[1])
            e_transform.setRotationX(cpoint[2][0])
            e_transform.setRotationY(cpoint[2][1])
            e_transform.setRotationZ(cpoint[2][2])
            e_transform.setScale(1000.0)
            e.addComponent(self.text_mat)
            e.addComponent(e_transform)
            e.addComponent(e_text)
            e.setParent(self.cardinals)
        self.cardinals.setParent(self.root_entity)

    def make_stars(self):
        """
           star coordinates in J2000.0 equinox, and proper motion
           transform for precession-nutation as defined by IAU2006
           see http://www-f1.ijs.si/~ramsak/KlasMeh/razno/zemlja.pdf page 8
        """
        # define a QObject to attach the stars to
        self.skyJ2000 = QEntity()

        # Define star material for nice rendering
        star_mat = QDiffuseSpecularMaterial()
        star_mat.setAmbient(QColor(255,255,224))
        star_mat.setDiffuse(QColor(255,255,224))

        # Loads star catalog and render on the sky parent object
        stars = load_bright_star_5('ScopeSimulator/data/bsc5.dat.gz', True)
        stars = self.j2k_to_jnow(stars)
        radius_mag = [200, 150, 75, 50, 40, 30, 20]
        mag_to_radius = scipy.interpolate.interp1d(
            range(1,8),
            radius_mag,
            axis=0,
            kind='quadratic',
            fill_value=(max(radius_mag), min(radius_mag)),
            bounds_error=False,
            assume_sorted=False)
        for star in stars:
            e = QEntity()
            e_star = QSphereMesh()
            e_radius = mag_to_radius(float(star['mag'])) 
            e_star.setRadius(e_radius)
            e_transform = QTransform()
            # project celestial coordinates in radians on 3d cartesian
            # coordinates in sky2000 frame, assuming:
            # x axis: should be center to vernal point
            # y axis: should be center to 90deg east
            # z axis: should be center to north celestial pole
            # RA coordinates, seen from north
            # hemisphere, go from vernal (00:00) to east (6:00), ...
            # which is the contrary of radians
            ex = ((World3D._sky_radius - 150.0) * np.cos(star['ra']) *
                  np.cos(star['de']))
            ey = ((World3D._sky_radius -150.0) * np.sin(star['ra']) *
                  np.cos(star['de']))
            ez = ((World3D._sky_radius - 150.0) * np.sin(star['de']))
            e_transform.setTranslation(QVector3D(ex, ez, ey))
            e.addComponent(star_mat)
            e.addComponent(e_transform)
            e.addComponent(e_star)
            e.setParent(self.skyJ2000)

        self.skyJ2000.setParent(self.sky_entity)

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

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QVector3D
    from PyQt5.Qt3DExtras import Qt3DWindow, QOrbitCameraController
    import sys
    from Service.NTPTimeService import NTPTimeService
    app=QApplication(sys.argv)
    view = Qt3DWindow()
    view.defaultFrameGraph().setClearColor(QColor(37,37,39))
    view.show()
    world = World3D(parent=None, serv_time=NTPTimeService())
    camera = view.camera()
    camera.lens().setPerspectiveProjection(45.0, 16.0 / 9.0, 0.1, 100000.0)
    #camera.lens().setOrthographicProjection(-50000,50000, 0, 50000, 0, 100000.0)
    camera.setPosition(QVector3D(0.0, 750.0, 3000.0))
    camera.setViewCenter(QVector3D(0.0, 0.0, 0.0))
    camController = QOrbitCameraController(world.root_entity)
    camController.setLinearSpeed(500.0)
    camController.setLookSpeed(120.0)
    camController.setCamera(camera)
    view.setRootEntity(world.root_entity)
    app.exec_()
