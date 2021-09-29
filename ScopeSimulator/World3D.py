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
from meshcat.geometry import Geometry
from meshcat.geometry import SceneElement
from meshcat.geometry import Sphere
import meshcat.transformations as tf

# Local stuff
from ScopeSimulator.Catalogs import load_bright_star_5

class Circle(Geometry):
    """
    from https://threejs.org/docs/#api/en/geometries/RingGeometry
    """
    def __init__(self, radius, nb_segment=20):
        """
        innerRadius — Default is 0.5.
        outerRadius — Default is 1.
        thetaSegments — Number of segments. A higher number means the ring will be more round. Minimum is 3. Default is 8.
        phiSegments — Minimum is 1. Default is 1.
        thetaStart — Starting angle. Default is 0.
        thetaLength — Central angle. Default is Math.PI * 2.
        """
        Geometry.__init__(self)
        self.innerRadius = radius
        self.outerRadius = radius
        self.thetaSegments = nb_segment
        self.phiSegments = 1
        self.thetaStart = 0
        self.thetaLength = 2*np.pi

    def lower(self, object_data):
        return {
            u"uuid": self.uuid,
            u"type": u"RingGeometry",
            u"innerRadius": self.innerRadius,
            u"outerRadius": self.outerRadius,
            u"thetaSegments": self.thetaSegments,
            u"phiSegments": self.phiSegments,
            u"thetaStart": self.thetaStart,
            u"thetaLength": self.thetaLength
        }

class SmoothSphere(Sphere):
    def __init__(self, radius, nb_segment=20):
        Geometry.__init__(self)
        self.radius = radius
        self.nb_segment = nb_segment

    def lower(self, object_data):
        return {
            u"uuid": self.uuid,
            u"type": u"SphereGeometry",
            u"radius": self.radius,
            u"widthSegments": self.nb_segment,
            u"heightSegments": self.nb_segment
        }

class PerspectiveCamera(SceneElement):
    """
    Checkout https://threejs.org/docs/#api/en/cameras/PerspectiveCamera
    """
    def __init__(self, fov, aspect, near, far, zoom):
        """
        fov   : Camera frustum vertical field of view, from bottom to top of view, in degrees. Default is 50.
        aspect: Camera frustum aspect ratio, usually the canvas width / canvas height. Default is 1 (square canvas).
        near  : Camera frustum near plane. Default is 0.1. The valid range is greater than 0 and less than the current
                value of the far plane. Note that, unlike for the OrthographicCamera, 0 is not a valid value for a
                PerspectiveCamera's near plane.
        far   : Camera frustum far plane. Default is 2000.
        zoom  : Gets or sets the zoom factor of the camera. Default is 1.
        filmGauge: Film size used for the larger axis. Default is 35 (millimeters). This parameter does not influence
                   the projection matrix unless .filmOffset is set to a nonzero value.
        filmOffset: Horizontal off-center offset in the same unit as .filmGauge. Default is 0.
        focus: Object distance used for stereoscopy and depth-of-field effects. This parameter does not influence
               the projection matrix unless a StereoCamera is being used. Default is 10.
        """
        #super(PerspectiveCamera, self).__init__()
        SceneElement.__init__(self)
        self.aspect = aspect
        self.far = far
        self.filmGauge = 35
        self.filmOffset = 0
        self.focus = 10
        self.fov = fov
        self.near = near
        self.zoom = zoom

    def lower(self):
        data = {
            u"object": {
                u"uuid": self.uuid,
                u"type": u"PerspectiveCamera",
                u"aspect": self.aspect,
                u"far": self.far,
                u"filmGauge": self.filmGauge,
                u"filmOffset": self.filmOffset,
                u"focus": self.focus,
                u"fov": self.fov,
                u"near": self.near,
                u"zoom": self.zoom,
            }
        }
        return data

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
    sky_nb_segment = 1000

    # altaz grid
    altaz_grid_lw = 0.2
    altaz_grid_color = 0xffffff

    # celestial grid
    celestial_grid_lw = 0.2
    celestial_grid_color = 0xff0000

    # Cardinal points
    cardinals_diameter = 0.25
    cardinals_height = 2
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

        # Initialize camera with proper projection
        self.camera = PerspectiveCamera(
            fov=45,
            aspect=1,
            near=1,
            far=1000,
            zoom=1)
        self.view3D['/Cameras/default/rotated'].set_object(self.camera)
        self.view3D['/Cameras/default'].set_transform(
            tf.translation_matrix([0, -1, 0]))
        self.view3D['/Cameras/default/rotated/<object>'].set_property(
            "position", [1, 1, 1])

        # Sky will be a rotating frame different from the ground
        self.view3D["sky_jnow"].set_object(
            SmoothSphere(self.sky_radius, self.sky_nb_segment),
            g.MeshLambertMaterial(
                color=0x020458,
                reflectivity=0.01))
        self.latitude_transform = tf.rotation_matrix(0, [0, 0, 1])
        self.celestial_time_transform = tf.rotation_matrix(0, [0, 0, 1])

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
            longitude=self.longitude_deg)

    def update_sky_transform(self):
        """
           transform the sky entity from reference frame (ground) to celestial
           We recall how is the sky frame should be as follow (after transform)
            - x axis: should be center to vernal point
            - y axis: should be center to 90deg east
            - z axis: should be center to north celestial pole
             RA coordinates, seen from north
             hemisphere, go from vernal (00:00) to east (6:00), ...

           Recall base frame:
             -index 0 : x axis : red    : pointing North,
             -index 1 : z axis : green   : pointing zenith
             -index 2 : y axis : blue  : pointing zenith
        """
        tr = self.latitude_transform
        tr = tr.dot(self.celestial_time_transform)

        self.view3D["sky_jnow"].set_transform(tr)

    def set_latitude(self, latitude_deg):
        """
           Recall base frame:
             -index 0 : x axis : red    : pointing North,
             -index 1 : z axis : green   : pointing zenith
             -index 2 : y axis : blue  : pointing zenith

           Recall latitude:
           We recall that input latitude is 90deg at north pole and -90 at
           south pole

           Sky transformation:
           when sky is initialized:
             -dec 90 is a zenith
             -ra 0 is towards north

            if someone is at +70deg latitude (north), then it means that the
            celestial north pole is at 70 degrees instead of 90. i.e it undergoes
            a rotation of 90-70 around y axis oriented toward west
        """   
        self.latitude = np.deg2rad(latitude_deg)
        self.latitude_transform = tf.rotation_matrix(
            (np.pi/2)-self.latitude,
            [0, 1, 0])
        # if self.latitude < 0.0:
        #     angle = 90.0 - abs(self.latitude)
        # else:
        #     angle = -(90.0 - self.latitude)
        # self.qlatitude = QQuaternion.fromAxisAndAngle(
        #     QVector3D(0.0, 0.0, 1.0),
        #     angle)
        self.update_sky_transform()

    def set_longitude(self, longitude_deg):
        """
           Recall base frame:
             -index 0 : x axis : red    : pointing North,
             -index 1 : z axis : green   : pointing zenith
             -index 2 : y axis : blue  : pointing zenith

           Recall longitude:
           We recall that input longitude is 0 at greenwich (UK) and start to
           grow from there, going east (around 3-6 in France) up to +360
           Equivalently one can start from 0, and decrease in negative number
           up to -180 going west.

          Sky transformation:
           when sky is initialized:
             -dec 90 is a zenith
             -ra 0 is towards north

          If you live at 15 deg longitude, it means that someone at 0 deg longitude will have
          the same star at zenith approx 1 hour after you.
          For instance when it is 23:00 in Paris, it is 22:00 in london
          It means that, for you, the sky is rotated by 15 degrees towards west (if you leave nort hemisphere)

        """
        self.longitude_deg = longitude_deg
        self.set_celestial_time(self.get_celestial_time())

    def set_celestial_time(self, celestial_time):
        """
        We recall what vernal point is:
        vernal point is a location somewhere in aquarius constellation. It stands for the exact position in the sky
        of the sun, at the very moment of the march equinox.

        Viewed from the same location, a star seen at one position in the sky will be seen at the same position on
        another night at the same sidereal time.

        More exactly, sidereal time is the angle, measured along the celestial equator, from the observer's meridian to
         the great circle that passes through the March equinox and both celestial poles, and is usually expressed in
         hours, minutes, and seconds.[2] Common time on a typical clock measures a slightly longer cycle, accounting
         not only for Earth's axial rotation but also for Earth's orbit around the Sun.

         Example: if sidereal time is 1:00:00, then the vernal point (March equinox) was above your head approximately
         one hour ago. (approximately, because earth make a full turn in ~23h56:15)

        :param celestial_time:  astropy.coordinates.angles.Longitude to be simulated
        :return:
        """
        self.celestial_time = celestial_time
        angle = float(self.celestial_time.to(u.rad).value)
        self.celestial_time_transform = tf.rotation_matrix(angle, [0, 0, 1])
        self.update_sky_transform()

    def make_horizontal_plane(self):
        """
           Builds the earth ground, (simple plain green colored plane mesh)

        """
        self.view3D["/Background"].set_property("top_color", [0, 1, 0])
        self.view3D['/Grid'].set_property("visible", True)

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
        # First: we make the declinaison grid
        for dec_deg in np.linspace(-80, 80, 17):
            dec_rad = np.deg2rad(dec_deg)
            radius = np.cos(dec_rad)*self.sky_radius
            height_position = np.sin(dec_rad)*self.sky_radius
            self.view3D["sky_jnow"]["celestial_grid"]["dec"][str(dec_deg)].set_object(
                Circle(radius, nb_segment=self.sky_nb_segment),
                g.MeshLambertMaterial(
                    color=self.celestial_grid_color,
                    transparent=False,
                    opacity=1.0,
                    linewidth=0.,
                    wireframe=True,
                    wireframeLinewidth=self.celestial_grid_lw,
                    vertexColors=False))
            # By default, circle is z aligned, we move to the right position
            self.view3D["sky_jnow"]["celestial_grid"]["dec"][str(dec_deg)].set_transform(
                tf.translation_matrix([0, 0, height_position]))
        # Now right ascension grid
        for ra_deg in np.linspace(0, 165, 12):
            ra_rad = np.deg2rad(ra_deg)
            radius = self.sky_radius
            self.view3D["sky_jnow"]["celestial_grid"]["ra"][str(ra_deg)].set_object(
                Circle(radius, nb_segment=self.sky_nb_segment),
                g.MeshLambertMaterial(
                    color=self.celestial_grid_color,
                    transparent=False,
                    opacity=1.0,
                    linewidth=0.,
                    wireframe=True,
                    wireframeLinewidth=self.celestial_grid_lw,
                    vertexColors=False))
            tr = tf.rotation_matrix(ra_rad, [0, 0, 1])
            tr = tr.dot(tf.rotation_matrix(np.pi/2, [1, 0, 0]))
            self.view3D["sky_jnow"]["celestial_grid"]["ra"][str(ra_deg)].set_transform(tr)

    def make_altaz_grid(self):
        """
            Altaz grid helps vizualize the spherical coordinate system whose
            main axis is colinear to the normal to earth sphere at observer
            position
            We choose:
              -17 rings: 1 tick every 10 degrees for altitude, from -80 to 80.
               90 standing for zenith and -90 for the nadir
              -36 slices: 1 tick every 10 degrees for the 360 degrees of azimuth
               0 being oriented towards north, and 90 degrees towards east

           One should notice that this altaz grid is attached to the root
           entity
        """
        # First: we make the altitude grid
        for altitude_deg in np.linspace(-80, 80, 17):
            altitude_rad = np.deg2rad(altitude_deg)
            radius = np.cos(altitude_rad)*self.sky_radius
            height_position = np.sin(altitude_rad)*self.sky_radius
            self.view3D["altaz_grid"]["alt"][str(altitude_deg)].set_object(
                Circle(radius, nb_segment=self.sky_nb_segment),
                g.MeshLambertMaterial(
                    color=self.altaz_grid_color,
                    transparent=False,
                    opacity=1.0,
                    linewidth=0.,
                    wireframe=True,
                    wireframeLinewidth=self.altaz_grid_lw,
                    vertexColors=False))
            # By default, circle is z aligned, we move to the right position
            self.view3D["altaz_grid"]["alt"][str(altitude_deg)].set_transform(
                tf.translation_matrix([0, 0, height_position]))
        # Now azimut grid
        for azimut_deg in np.linspace(0, 165, 12):
            azimut_rad = np.deg2rad(azimut_deg)
            radius = self.sky_radius
            self.view3D["altaz_grid"]["az"][str(azimut_deg)].set_object(
                Circle(radius, nb_segment=self.sky_nb_segment),
                g.MeshLambertMaterial(
                    color=self.altaz_grid_color,
                    transparent=False,
                    opacity=1.0,
                    linewidth=0.,
                    wireframe=True,
                    wireframeLinewidth=self.altaz_grid_lw,
                    vertexColors=False))
            tr = tf.rotation_matrix(azimut_rad, [0, 0, 1])
            tr = tr.dot(tf.rotation_matrix(np.pi/2, [1, 0, 0]))
            self.view3D["altaz_grid"]["az"][str(azimut_deg)].set_transform(tr)

    # color = 0xffffff, reflectivity = 0.5, map = None,
    # side = 2, transparent = None, opacity = 1.0,
    # linewidth = 1.0,
    # wireframe = False,
    # wireframeLinewidth = 1.0,
    # vertexColors = False,

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
        radius_mag = [.2, .14, .10, .08, .05, .03, .02]
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
            tr = tr.dot(tf.rotation_matrix(star['de'], [0, -1, 0]))
            # Then we compose with translation on sky sphere
            tr = tr.dot(tf.translation_matrix([self.sky_radius*0.99, 0, 0]))
            # Now we apply transform
            self.view3D["sky_jnow"][star_id].set_transform(tr)

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