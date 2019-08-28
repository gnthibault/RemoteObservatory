# Common stuff
import math
import struct

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

class DPolynom:

    def __init__(self):
        self.coeffs = None

    def setCoeffs(self, lcoeffs):
        self.coeffs = lcoeffs

    def eval(self, x):
        v = 0.0
        for ic in range(len(self.coeffs) - 1, -1, -1):
            v = x * v + self.coeffs[ic]
        return v

    def derive(self):
        d = DPolynom()
        dc = [i * self.coeffs[i] for i in range(1, len(self.coeffs))]
        d.setCoeffs(dc)
        return d

    def integrate(self):
        ip = DPolynom()
        ipc = [self.coeffs[i] / (i + 1) for i in range(len(self.coeffs))]
        ipc = [0.0] + ipc
        ip.setCoeffs(ipc)
        return ip

    def mul(self, other):
        mp = DPolynom()
        mpc = [0.0 for i in range(len(self.coeffs) + len(other.coeffs))]
        for i in range(len(self.coeffs)):
            for j in range(len(other.coeffs)):
                mpc[i+j] += self.coeffs[i] * other.coeffs[j]
        mp.setCoeffs(mpc)
        return mp

class starMaterial(QMaterial):
    """
       Implements QMaterial interface 
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        starEffect = QEffect(self)
        starTechnique = QTechnique(self)
        starRenderPass = QRenderPass(self)
        starShaderProgram = QShaderProgram(self)
        starRenderState = QPointSize(self)
        # Defines color (white) and visibility (wether it is discarder or not)
        starShaderProgram.setShaderCode(
            QShaderProgram.Vertex,
            QShaderProgram.loadSource(QUrl.fromLocalFile(
                'ScopeSimulator/shaders/pointcloud.vert')))
        # Defines ?
        starShaderProgram.setShaderCode(
            QShaderProgram.Fragment, 
            QShaderProgram.loadSource(QUrl.fromLocalFile(
                'ScopeSimulator/shaders/pointcloud.frag')))
        starRenderPass.setShaderProgram(starShaderProgram)
        starRenderState.setSizeMode(QPointSize.Programmable)
        starRenderPass.addRenderState(starRenderState)
        starTechnique.addRenderPass(starRenderPass)
        filterKey = QFilterKey()
        filterKey.setName('renderingStyle')
        filterKey.setValue('forward')
        starTechnique.addFilterKey(filterKey)
        starTechnique.graphicsApiFilter().setApi(QGraphicsApiFilter.OpenGL)
        starTechnique.graphicsApiFilter().setMajorVersion(3)
        starTechnique.graphicsApiFilter().setMinorVersion(3)
        starTechnique.graphicsApiFilter().setProfile(
            QGraphicsApiFilter.CoreProfile)
        #starTechnique.graphicsApiFilter().setProfile(
        #    QGraphicsApiFilter.NoProfile)
        starEffect.addTechnique(starTechnique)
        super().setEffect(starEffect)

class PointGeometry(QGeometry):

    def __init__(self, parent=None):
        super().__init__(parent)
        posAttribute = QAttribute(self)
        self.vertexBuffer = QBuffer(self)
        posAttribute.setName(QAttribute.defaultPositionAttributeName())
        posAttribute.setVertexBaseType(QAttribute.Float)
        posAttribute.setVertexSize(3)
        posAttribute.setAttributeType(QAttribute.VertexAttribute)
        posAttribute.setBuffer(self.vertexBuffer)
        posAttribute.setByteOffset(0)
        posAttribute.setByteStride((3 + 1) * 4) # float32 is 4 bytes
        #posAttribute.setDivisor(1)
        self.addAttribute(posAttribute)
        self.positionAttribute = posAttribute
        radiusAttribute = QAttribute(self)
        radiusAttribute.setName('radius')
        radiusAttribute.setVertexBaseType(QAttribute.Float)
        radiusAttribute.setVertexSize(1)
        radiusAttribute.setAttributeType(QAttribute.VertexAttribute)
        radiusAttribute.setBuffer(self.vertexBuffer)
        radiusAttribute.setByteOffset(3 * 4) # float32 is 4 bytes
        #posAttribute.setByteStride(0)
        radiusAttribute.setByteStride((3 + 1) * 4) # float32 is 4 bytes
        #radiusAttribute.setDivisor(1)
        self.addAttribute(radiusAttribute)
        self.radiusAttribute = radiusAttribute

class World3D():
    """
    Qt3D frame: x axis pointing North, y axis pointing Zenith/pole, z axis
    pointing East
    Celestial frame: x axis pointing South, y axis pointing East, Z axis
    pointing Zenith/pole
    """
    # raw first order
    _m_celestial_qt = QMatrix3x3([-1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0])

    # _m_celestial is its proper inverse
    _sky_radius = 50000.0

    def __init__(self, parent=None, serv_time=None):
        self.serv_time = serv_time
        self.rootEntity = QEntity(parent)
        self.skyEntity = QEntity(self.rootEntity)
        self.skyTransform = QTransform()
        self.skyEntity.addComponent(self.skyTransform)
        self.make_horizontal_plane()
        self.make_equatorial_grid()
        self.make_altaz_grid()
        self.make_mount_basement()
        self.makeCardinals()
        #self.makeStars()
        self.makeStarsPoints()
        self.qtime=QQuaternion()
        self.qlongitude = QQuaternion()
        self.qlatitude = QQuaternion()
        self.setLatitude(90.0)
        self.setLongitude(0.0)
        self.set_gast(self.get_gast())
        #self.makeEcliptic()
        self.celestialintervalms = 1 * 1000
        self.celestialacceleration = 1
        self.celestialtimer = QTimer()
        self.celestialtimer.setInterval(
            self.celestialintervalms / self.celestialacceleration)
        self.celestialtimer.setSingleShot(False)
        self.celestialtimer.timeout.connect(self.updateCeletialTime)
        self.celestialtimer.start()

    def updateCeletialTime(self):
        gast = self.gast + (self.celestialintervalms / 1000) / (60*60)
        self.set_gast(gast)

    def get_gast(self):
        return self.getCelestialTime()

    def getCelestialTime(self):
        return self.serv_time.get_gast()

    def updateSkyTransform(self):
        self.skyTransform.setRotation(self.qlatitude * self.qlongitude *
            self.qtime)

    def setLatitude(self, latitude):
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
        self.latitude = latitude
        if self.latitude < 0.0:
            angle = 90.0 - abs(self.latitude)
        else:
            angle = -(90.0 - self.latitude)
        self.qlatitude = QQuaternion.fromAxisAndAngle(QVector3D(0.0, 0.0, 1.0),
                                                      angle)
        self.updateSkyTransform()

    def setLongitude(self, longitude):
        """
           Recall frame:
           Qt3D frame: x axis pointing North, y axis pointing Zenith/pole, z axis
           pointing East
           Celestial frame: x axis pointing South, y axis pointing East, Z axis
           pointing Zenith/pole
           Recall latitude:
           We recall that input latitude is 0 at greenwich (UK) and start to
           grow from there, going east (around 3-6 in France, up to +360
           Equivalently one can start from 0, and decrease in negative number
           up to -180 going west.
           In this context, we use the converse definition locally: longitude is 
           defined as rotation around y axis: (0,1,0) of -latitude axis in the
           Qt3D frame
        """   
        self.longitude = longitude
        angle = -self.longitude
        self.qlongitude = QQuaternion.fromAxisAndAngle(QVector3D(0.0, 1.0, 0.0),
                                                       angle)
        self.updateSkyTransform()

    def set_gast(self, gast):
        #print('Setting GAST', gast)
        self.gast = gast
        angle = -self.gast * 360.0 / 24.0
        self.qtime = QQuaternion.fromAxisAndAngle(QVector3D(0.0, 1.0, 0.0),
                                                  angle)
        self.updateSkyTransform()

    def make_horizontal_plane(self):
        """
           Builds the earth ground, (simple plain green colored plane mesh)
           One need to set Width and Height to define the mesh, plus material

           One should notice that this ground plane is attached to the root
           entity
        """
        self.horizontalPlane = QEntity()
        self.horizontalMesh = QPlaneMesh()
        self.horizontalMesh.setWidth(2 * World3D._sky_radius)
        self.horizontalMesh.setHeight(2 * World3D._sky_radius)
        self.horizontalMesh.setMeshResolution(QSize(50, 50))
        #self.horizontalMesh.setMirrored(True)
        #self.horizontalTransform = QTransform()
        #self.horizontalTransform.setMatrix(QTransform.rotateAround(
        #    QVector3D(0,0,0), 90.0, QVector3D(1.0, 0.0, 0.0)))
        #self.horizontalTransform.setTranslation(QVector3D(0.0, -10.0, 0.0))
        self.horizontalMat = QDiffuseSpecularMaterial()
        self.horizontalMat.setAmbient(QColor(0, 128, 0))
        #self.horizontalPlane.addComponent(self.horizontalTransform)
        self.horizontalPlane.addComponent(self.horizontalMat)
        self.horizontalPlane.addComponent(self.horizontalMesh)
        self.horizontalPlane.setParent(self.rootEntity)

    def make_equatorial_grid(self):
        """
           Equatorial grid helps vizualize the spherical coordinate system
           whose main axis is colinear to earth rotation axis
           We choose:
            -18 rings: 1 tick every 10 degrees for the 180 degrees of
              declination. 90 being north pole (close to polar star) and -90
              standing for south pole. 0 degrees is on the celestial equateur
            -24 slices: 1 tick every hour for the 24 hours of right ascencion
              00h standing for position of sun in background star at spring
              meridian at its highest position (ie intersecting celestial
              equateur). This point for origin is also called vernal point.

           One should notice that this ground plane is attached to the sky
           entity
        """
        self.equatorialGrid = QEntity()
        self.equatorialMesh = QSphereMesh()
        self.equatorialMesh.setRadius(World3D._sky_radius)
        self.equatorialMesh.setRings(18)
        self.equatorialMesh.setSlices(24)
        self.equatorialMesh.setPrimitiveType(QGeometryRenderer.Lines)
        self.equatorialTransform = QTransform()
        #self.equatorialTransform.setRotationZ(-(90 - 49.29))
        self.equatorialMat = QDiffuseSpecularMaterial()
        self.equatorialMat.setAmbient(QColor(200,0,0))
        self.equatorialGrid.addComponent(self.equatorialTransform)
        self.equatorialGrid.addComponent(self.equatorialMat)
        self.equatorialGrid.addComponent(self.equatorialMesh)
        self.equatorialGrid.setParent(self.skyEntity)

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
        """
        self.horizontalGrid = QEntity()
        self.horizontalMesh = QSphereMesh()
        self.horizontalMesh.setRadius(World3D._sky_radius)
        self.horizontalMesh.setRings(18)
        self.horizontalMesh.setSlices(36)
        self.horizontalMesh.setPrimitiveType(QGeometryRenderer.Lines)
        self.horizontalTransform = QTransform()
        self.horizontalTransform.setRotationX(0.0)
        self.horizontalMat = QDiffuseSpecularMaterial()
        self.horizontalMat.setAmbient(QColor(0,0,200))
        self.horizontalGrid.addComponent(self.horizontalTransform)
        self.horizontalGrid.addComponent(self.horizontalMat)
        self.horizontalGrid.addComponent(self.horizontalMesh)
        self.horizontalGrid.setParent(self.rootEntity)

    def make_mount_basement(self):
        """
           Right at the foot of the observer, we put an image of a compass in
           order to ease understanding of the scene.
           As in the ground horizontal plane, we define a PlaneMesh

           We recall that this element is connected to the root entity, and we
           also recall frame:
           Qt3D frame: x axis pointing North, y axis pointing Zenith/pole, z axis
           pointing East
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
        self.basementGrid = QEntity()
        # self.basement_mesh = QCylinderMesh()
        # self.basement_mesh.setRadius(1500.0)
        # self.basement_mesh.setLength(10.0)
        # self.basement_mesh.setSlices(360)
        self.basement_mesh = QPlaneMesh()
        self.basement_mesh.setWidth(1500.0)
        self.basement_mesh.setHeight(1500.0)
        self.basement_mesh.setMeshResolution(QSize(2, 2))
        self.basement_transform = QTransform()
        self.basement_transform.setTranslation(QVector3D(0,20.0,0))
        self.basement_transform.setRotationY(-90.0)
        self.basementMatBack = QDiffuseSpecularMaterial()
        self.basementMatBack.setAmbient(QColor(200,200,228))
        self.basementMat = QTextureMaterial()
        self.basementMat.setTexture(self.compass_texture)
        self.basementGrid.addComponent(self.basement_transform)
        self.basementGrid.addComponent(self.basementMatBack)
        self.basementGrid.addComponent(self.basementMat)
        self.basementGrid.addComponent(self.basement_mesh)
        self.basementGrid.setParent(self.rootEntity)

    def makeCardinals(self):
        """
           We decide to put some labels on the cardinal points, ie, 
           Nort/East/South/West/Zenith/Nadir
           Each cardinal is defined as a 3-uplet:
               -name string
               -translation in Qvector
               -rotation around X,Y,Z axis
           We recall that this element is connected to the root entity, and we
           also recall frame:
           Qt3D frame: x axis pointing North, y axis pointing Zenith/pole, z axis
           pointing East
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
        self.textMat = QDiffuseSpecularMaterial()
        self.textMat.setAmbient(QColor(200,200,228))
        self.cardinals = QEntity()
        for cpoint in cardinals:
            e = QEntity()
            eText = QExtrudedTextMesh()
            eText.setText(cpoint[0])
            eText.setDepth(0.45)
            eText.setFont(font)
            eTransform = QTransform()
            eTransform.setTranslation(cpoint[1])
            eTransform.setRotationX(cpoint[2][0])
            eTransform.setRotationY(cpoint[2][1])
            eTransform.setRotationZ(cpoint[2][2])
            eTransform.setScale(1000.0)
            e.addComponent(self.textMat)
            e.addComponent(eTransform)
            e.addComponent(eText)
            e.setParent(self.cardinals)
        self.cardinals.setParent(self.rootEntity)

    def makeStars(self):
        # star coordinates in J2000.0 equinox,no proper motion
        # transform for precession-nutation as defined by IAU2006
        # see http://www-f1.ijs.si/~ramsak/KlasMeh/razno/zemlja.pdf page 8
        # not accurate for more than +-7000 years
        jd = self.serv_time.get_jd()
        self.skyJ2000 = QEntity()
        self.transformJ2000 = QTransform()
        m = self.matPrecessNut(jd)
        qPrecessNut = QQuaternion.fromRotationMatrix(m)
        qqt=QQuaternion.fromRotationMatrix(World3D._m_celestial_qt)
        self.transformJ2000.setRotation(qqt*qPrecessNut)
        self.skyJ2000.addComponent(self.transformJ2000)
        radius_mag = [150.0, 100.0, 70.0, 50, 40, 30.0]
        stars = load_bright_star_5('ScopeSimulator/data/bsc5.dat.gz', True)
        starmat = QDiffuseSpecularMaterial()
        starmat.setAmbient(QColor(255,255,224))
        starmat.setDiffuse(QColor(255,255,224))

        for star in stars:
            e = QEntity()
            eStar = QSphereMesh()
            eradius = (radius_mag[int(star['mag'] - 1)] if 
                int(star['mag'] - 1) < 6 else 20.0)
            eStar.setRadius(eradius)
            eTransform = QTransform()
            ex = ((World3D._sky_radius - 150.0) * math.cos(star['ra']) *
                  math.cos(star['de']))
            ey = ((World3D._sky_radius -150.0) * math.sin(star['de']))
            ez = ((World3D._sky_radius -150.0) * math.sin(star['ra']) *
                  math.cos(star['de']))
            #print(ex, ey ,ez)
            eTransform.setTranslation(QVector3D(ex, ez, ey))
            e.addComponent(starmat)
            e.addComponent(eTransform)
            e.addComponent(eStar)
            e.setParent(self.skyJ2000)

        self.skyJ2000.setParent(self.skyEntity)

    def makeStarsPoints(self):
        jd = self.serv_time.get_jd()
        self.skyJ2000 = QEntity()
        self.transformJ2000 = QTransform()
        m = self.matPrecessNut(jd)
        qPrecessNut = QQuaternion.fromRotationMatrix(m)
        qqt=QQuaternion.fromRotationMatrix(World3D._m_celestial_qt)
        self.transformJ2000.setRotation(qqt*qPrecessNut)
        #self.transformJ2000.setRotation(qqt)
        self.skyJ2000.addComponent(self.transformJ2000)
        radius_mag = [150.0, 100.0, 70.0, 50, 40, 30.0]
        stars = load_bright_star_5('ScopeSimulator/data/bsc5.dat.gz', True)
        starmat = starMaterial()
        #starmat = QDiffuseSpecularMaterial()
        #starmat.setAmbient(QColor(255,255,224))
        #starmat.setDiffuse(QColor(255,255,224))
        print('Star Effect', starmat.effect())
        print('Star Technique', starmat.effect().techniques()[0])
        self.skyJ2000.addComponent(starmat)
        #points = QByteArray(3 * FLOAT_SIZE * len(stars), 'b\x00')
        points = QByteArray()
        for star in stars:
            eradius = (radius_mag[int(star['mag'] - 1)] if
                       int(star['mag'] - 1) < 6 else 20.0)
            ex = ((World3D._sky_radius - 150.0) * math.cos(star['ra']) *
                   math.cos(star['de']))
            ey = (World3D._sky_radius -150.0) * math.sin(star['de'])
            ez = ((World3D._sky_radius -150.0) * math.sin(star['ra']) *
                  math.cos(star['de']))
            points.append(struct.pack('f', ex))
            points.append(struct.pack('f', ez))
            points.append(struct.pack('f', ey))
            points.append(struct.pack('f', eradius))
        pointGeometryRenderer = QGeometryRenderer()
        pointGeometry = PointGeometry(pointGeometryRenderer)
        pointGeometry.vertexBuffer.setData(points)
        pointGeometry.positionAttribute.setCount(len(stars))
        pointGeometry.radiusAttribute.setCount(len(stars))
        pointGeometryRenderer.setPrimitiveType(QGeometryRenderer.Points)
        pointGeometryRenderer.setGeometry(pointGeometry)
        #pointGeometryRenderer.setFirstInstance(0)
        pointGeometryRenderer.setInstanceCount(1)
        #pointGeometryRenderer.setVertexCount(len(stars))
        self.skyJ2000.addComponent(pointGeometryRenderer)
        self.skyJ2000.setParent(self.skyEntity)

    def makeEcliptic(self):
        for j in range(-12, 14):
            # ecliptic pole
            skyEcliptic = QEntity()
            transformEcliptic = QTransform()
            m = self.matPrecessNut(2451545.0 + 365.25 * j * 1000)
            mcio = self.matCIOLocator(2451545.0 + 365.25 * j * 1000)
            qEcliptic = QQuaternion.fromRotationMatrix(m)
            qCIO = QQuaternion.fromRotationMatrix(mcio)
            qp=QQuaternion.fromRotationMatrix(World3D._m_celestial_qt)
            transformEcliptic.setRotation(qp*qEcliptic*qCIO)
            skyEcliptic.addComponent(transformEcliptic)
            eclmat = QDiffuseSpecularMaterial()
            eclmat.setAmbient(QColor(255,20,20))
            eclmat.setDiffuse(QColor(255,20,20))
            e = QEntity()
            ePole = QSphereMesh()
            eradius = 300.0
            ePole.setRadius(eradius)
            eTransform = QTransform()
            ex = ((World3D._sky_radius - 150.0) * math.cos(math.radians(0.0)) *
                  math.cos(math.radians(90.0)))
            ey = ((World3D._sky_radius -150.0) * math.sin(math.radians(90.0)))
            ez = ((World3D._sky_radius -150.0) * math.sin(math.radians(0.0)) *
                  math.cos(math.radians(90.0)))
            #print(ex, ey ,ez)
            eTransform.setTranslation(QVector3D(ex, ez, ey))
            e.addComponent(eclmat)
            e.addComponent(eTransform)
            e.addComponent(ePole)
            e.setParent(skyEcliptic)
            skyEcliptic.setParent(self.skyEntity)

    def matPrecessNut(self, jd):
        J2000 = 2451545.0
        t = jd - J2000
        t = t / 36525 #julian century
        x = -0.016617 + t * (2004.191898 + t * (-0.4297829 + t * (-0.19861834 +
            t * (0.000007578 + t * (0.0000059285)))))
        y = -0.006951 + t * (-0.025896 + t * (-22.4072747 + t * (0.00190059 +
            t * (0.001112526 + t * (0.0000001358)))))
        x = x * 2.0 * math.pi / (360.0 * 60.0 * 60)
        y = y * 2.0 * math.pi / (360.0 * 60.0 * 60.0)
        #print(x,y)
        #z = math.sqrt(1 - x*x - y*y)
        #b = 1 / (1 + z)
        b = 0.5 + (x*x + y*y) / 8.0
        m = QMatrix3x3([1.0 - b*x*x, -b*x*y, x, -b*x*y, 1.0 -b*y*y, y, -x, -y,
                       1.0 - b*(x*x+y*y)])
        return m

    def matCIOLocator(self, jd):
        J2000 = 2451545.0
        t = jd - J2000
        t = t / 36525 #julian century
        x = -0.016617 + t * (2004.191898 + t * (-0.4297829 + t * (-0.19861834 +
            t * (0.000007578 + t * (0.0000059285)))))
        y = -0.006951 + t * (-0.025896 + t * (-22.4072747 + t * (0.00190059 +
            t * (0.001112526 + t * (0.0000001358)))))
        xt = x * 2.0 * math.pi / (360.0 * 60.0 * 60)
        yt = y * 2.0 * math.pi / (360.0 * 60.0 * 60.0)
        x0 = -0.016617
        y0 = -0.006951
        xt0 = x0 * 2.0 * math.pi / (360.0 * 60.0 * 60)
        yt0 = y0 * 2.0 * math.pi / (360.0 * 60.0 * 60.0)
        xc = [-0.016617, 2004.191898, -0.4297829, -0.19861834, 0.000007578 ,
              0.0000059285]
        yc = [-0.006951, -0.025896, -22.4072747, 0.00190059, 0.001112526,
              0.0000001358]
        px = DPolynom()
        px.setCoeffs(xc)
        py=DPolynom()
        py.setCoeffs(yc)
        dpx=px.derive()
        spx=dpx.mul(py)
        ispx = spx.integrate()
        ixt = ispx.eval(t)
        ixt0 = ispx.eval(0.0)
        ixt = ixt * 2.0 * math.pi / (360.0 * 60.0 * 60)
        ixt0 = ixt0 * 2.0 * math.pi / (360.0 * 60.0 * 60.0)
        s = - 0.5 * (xt * yt - xt0 * yt0) + (ixt - ixt0) - 0.0145606
        m = QMatrix3x3([math.cos(s), -math.sin(s), 0.0, math.sin(s),
                        math.cos(s), 0, 0, 0, 1.0])
        return m
        
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QVector3D
    from PyQt5.Qt3DExtras import Qt3DWindow, QOrbitCameraController
    import sys
    app=QApplication(sys.argv)
    view = Qt3DWindow()
    view.defaultFrameGraph().setClearColor(QColor(37,37,39))
    view.show()
    world = World3D()
    camera = view.camera()
    camera.lens().setPerspectiveProjection(45.0, 16.0 / 9.0, 0.1, 100000.0)
    #camera.lens().setOrthographicProjection(-50000,50000, 0, 50000, 0, 100000.0)
    camera.setPosition(QVector3D(0.0, 750.0, 3000.0))
    camera.setViewCenter(QVector3D(0.0, 0.0, 0.0))
    camController = QOrbitCameraController(world.rootEntity)
    camController.setLinearSpeed(500.0)
    camController.setLookSpeed(120.0)
    camController.setCamera(camera)
    view.setRootEntity(world.rootEntity)
    app.exec_()
