# Numerical tools
import numpy as np
import os
import queue
from functools import reduce

# Astropy coord
from astropy import units as u

# meshcat 3d stuff
import meshcat
import meshcat.geometry as g
import meshcat.transformations as tf # rotation_matrix arguments are angle, direction, src_point
from meshcat.geometry import Box, Cylinder, Geometry, Sphere

class Mount3D:

    def __init__(self, view3D, gps_coordinates, serv_time, actual_indi_device=None):
        # World
        self.view3D = view3D
        self.gps_coord = gps_coordinates
        self.serv_time = serv_time
        self.last_ra_angle_astropy = 0*u.hourangle
        # External data
        self.stl_path = "ScopeSimulator/data"

        # Pier
        #mount.get_pier_side() returns {'PIER_WEST': 'Off', 'PIER_EAST': 'On'}
        self.last_pier_side = "PIER_WEST"
        # When no stl model is available, define shape for telescope
        self.mount_pier_radius = 150
        self.mount_pier_height = 1500
        self.mount_pier_color = 0xa2a2a2

        # Main scaling factor for the whole setup atop the pier
        self.main_setup_scaling = 2

        # Mount
        self.base_holder = dict(obj=os.path.join(self.stl_path, "baseholder.stl"), color=0x000000,
                                transform=np.dot(tf.rotation_matrix(np.deg2rad(0), [1, 0, 0]),
                                                 tf.translation_matrix([0, 0, -475])))
        self.ra_housing = dict(obj=os.path.join(self.stl_path, "rahousing.stl"), color=0xffffff,
                               transform=np.dot(tf.translation_matrix([0, 0, 0]),
                                                tf.rotation_matrix(np.deg2rad(0), [0, 0, 1])))
        self.ra_axis = dict(obj=os.path.join(self.stl_path, "raaxis.stl"), color=None,
                            transform=np.dot(tf.translation_matrix([0, 0, 0]),
                                             tf.rotation_matrix(np.deg2rad(0), [0, 0, 1])))
        self.de_housing = dict(obj=os.path.join(self.stl_path, "dehousing.stl"), color=0x1a1a1a,
                               transform=np.dot(tf.translation_matrix([-35, 0, 0]),
                                                tf.rotation_matrix(np.deg2rad(0), [0, 0, 1])))
        self.de_axis = dict(obj=os.path.join(self.stl_path, "deaxis.stl"), color=0x883333,
                            transform=np.dot(tf.translation_matrix([0, 0, 0]),
                                             tf.rotation_matrix(np.deg2rad(0), [0, 0, 1])))
        self.cw_bar = dict(obj=os.path.join(self.stl_path, "cwbar.stl"), color=None,
                           transform=np.dot(tf.translation_matrix([0, 0, 0]),
                                           tf.rotation_matrix(np.deg2rad(0), [0, 0, 1])))
        self.dovetail = dict(obj=os.path.join(self.stl_path, "dovetail.stl"), color=None,
                             transform=np.dot(tf.translation_matrix([0, 0, 0]),
                                              tf.rotation_matrix(np.deg2rad(0), [0, 0, 1])))
        self.counter_weight = dict(obj=Cylinder(height=80, radius=80), color=0xa0a0a0,
                                   transform=np.dot(tf.translation_matrix([170, 0, 800]),
                                                    tf.rotation_matrix(np.deg2rad(90), [1, 0, 0])))

        self.mount_latitude_rotation_axis = [0, 1, 0]
        self.mount_latitude_application_point = [0, 0, 925]
        self.mount_ra_rotation_axis = [1, 0, 0]
        self.mount_ra_application_point = [0, 0, 990]
        self.mount_de_rotation_axis = [0, 0, 1]
        self.mount_de_application_point = [170, 0, 0]

        # Telescope
        # When no stl model is available, define shape for telescope
        # self.telescope_diameter = 200
        # self.telescope_length = 650
        # self.telescope_type = "newton200_800"
        # self.telescope_color = 0xd3d3d3
        self.tube = dict(obj=os.path.join(self.stl_path, "tube.stl"), color=0xffffff,
                         transform=reduce(np.dot,
                                          [tf.scale_matrix(5),
                                           tf.translation_matrix([25, 0, 244]),
                                           tf.rotation_matrix(np.deg2rad(90), [0, 1, 0]),
                                           tf.rotation_matrix(np.deg2rad(90), [0, 0, 1]),
                                           tf.translation_matrix([-30, 20, -30])]))
        self.laser_pointer = dict(obj=Cylinder(height=6000, radius=0.5), color=0x00ff00,
                                  transform=np.dot(tf.translation_matrix([30.5, -19.5, 3005]),
                                                   tf.rotation_matrix(np.deg2rad(90), [1, 0, 0])))
        # mount - indi device
        self.actual_indi_device = actual_indi_device
        # Insane setup just because of: https://github.com/rdeits/meshcat-python/issues/110
        self.model_update_q = queue.Queue()

        # Ok build the object
        self.build_whole_setup()

    def build_object(self, obj_path, obj, color, transform):
        if isinstance(obj, Geometry):
            object_shape = obj
        else:
            object_shape = g.StlMeshGeometry.from_file(obj)
        object_material = g.MeshLambertMaterial(color=color, reflectivity=0.01)
        self.view3D[obj_path].set_object(object_shape, object_material)
        # Scale the stl we just received, because our world is in mm
        scaling = tf.scale_matrix(1)
        # Set and attach object to frame
        self.view3D[obj_path].set_transform(np.dot(scaling, transform))

    def build_whole_setup(self):
        self.build_pier()
        self.build_mount()
        self.build_telescope()
        self.apply_init_transforms()
        self.register_callbacks() # Issue https://github.com/rdeits/meshcat-python/issues/110

    def build_pier(self):
        pier_shape = Cylinder(height=self.mount_pier_height, radius=self.mount_pier_radius)
        pier_material = g.MeshLambertMaterial(
            color=self.mount_pier_color,
            reflectivity=0.01)
        # Set and attach mount pier to frame
        pier_from_frame_rotation = tf.rotation_matrix(np.deg2rad(90), [
            1,
            0,
            0])
        pier_from_frame_translation = tf.translation_matrix([
            0,
            0,
            self.mount_pier_height/2])
        pier_from_frame_position = np.dot(pier_from_frame_translation, pier_from_frame_rotation)
        # Scale, because our world is in mm
        scaling = tf.scale_matrix(0.001)
        self.view3D["telescope/pier"].set_object(
            pier_shape,
            pier_material)
        self.view3D["telescope/pier"].set_transform(
            np.dot(scaling, pier_from_frame_position))
        # We also set a virtual object to be used as a frame to keep consistency in terms of main world frame
        self.view3D["telescope/pier/frame"].set_object(g.Sphere(radius=0))
        self.view3D["telescope/pier/frame"].set_transform(np.dot(
            np.linalg.inv(pier_from_frame_rotation),
            tf.scale_matrix(self.main_setup_scaling)))

    def build_mount(self):
        self.build_object(obj_path="telescope/pier/frame/base_holder",
                              **self.base_holder)
        self.build_object(obj_path="telescope/pier/frame/base_holder/ra_housing",
                              **self.ra_housing)
        self.build_object(obj_path="telescope/pier/frame/base_holder/ra_housing/ra_axis",
                              **self.ra_axis)
        self.build_object(obj_path="telescope/pier/frame/base_holder/ra_housing/ra_axis/de_housing",
                              **self.de_housing)
        self.build_object(obj_path="telescope/pier/frame/base_holder/ra_housing/ra_axis/de_housing/de_axis",
                              **self.de_axis)
        self.build_object(obj_path="telescope/pier/frame/base_holder/ra_housing/ra_axis/de_housing/de_axis/cw_bar",
                              **self.cw_bar)
        self.build_object(obj_path="telescope/pier/frame/base_holder/ra_housing/ra_axis/de_housing/de_axis/cw_bar/dovetail",
                              **self.dovetail)
        self.build_object(obj_path="telescope/pier/frame/base_holder/ra_housing/ra_axis/de_housing/de_axis/cw_bar/counterweight",
                              **self.counter_weight)

    def build_telescope(self):
        self.build_object(obj_path="telescope/pier/frame/base_holder/ra_housing/ra_axis/de_housing/de_axis/cw_bar/dovetail/tube",
                              **self.tube)
        self.build_object(obj_path="telescope/pier/frame/base_holder/ra_housing/ra_axis/de_housing/de_axis/cw_bar/dovetail/tube/laser_pointer",
                              **self.laser_pointer)

    def apply_latitude_transform(self, angle_deg=0):
        self.view3D["telescope/pier/frame/base_holder/ra_housing"].set_transform(tf.rotation_matrix(
            np.deg2rad(-angle_deg),
            self.mount_latitude_rotation_axis,
            self.mount_latitude_application_point))

    def apply_ra_transform(self, angle_deg=0):
        self.view3D["telescope/pier/frame/base_holder/ra_housing/ra_axis"].set_transform(tf.rotation_matrix(
            np.deg2rad(angle_deg),
            self.mount_ra_rotation_axis,
            self.mount_ra_application_point))

    def apply_celestial_ra_transform(self, angle_astropy=None):
        if angle_astropy is None:
            angle_astropy = self.last_ra_angle_astropy
        self.last_ra_angle_astropy = angle_astropy
        # Celestial time is basically the current RA at the meridian
        celestial_time = self.get_celestial_time()
        # We need to manage pier side.
        # Basically, if ra coordinate is "past" the meridian, on the west, ie, positive celestial_time-angle_astropy,
        # then we should have the head of the mount looking at east, and the tube looking west
        #
        # First, get angle from meridian, positive value means target is past the meridian on the west
        from_meridian_angle_degree = (celestial_time-angle_astropy).to(u.degree).value
        # the mechanical axis at 0 points 90 degree away from the meridian on the east side
        # You need to add 90 degree to be at the meridian
        if self.last_pier_side == "PIER_WEST": #PIER_WEST means pointing east, most likely we are before the meridian
            angle_ra = 270 - from_meridian_angle_degree
        else: #PIER_EAST means pointing west, most likely we are before the meridian
            angle_ra = 90 - from_meridian_angle_degree
        # Command mechanical axis
        angle_deg = angle_ra
        self.apply_ra_transform(angle_deg=angle_deg)

    def apply_celestial_de_transform(self, angle_astropy):
        # the mechanical axis at 0 points 90 degree away from the meridian on the east side
        # You need to add 90 degree to be at the meridian
        if self.last_pier_side == "PIER_WEST":
            angle_de = -90 + angle_astropy.to(u.degree).value
        else:
            angle_de = 90 - angle_astropy.to(u.degree).value

        self.apply_de_transform(angle_deg=angle_de)

    def apply_de_transform(self, angle_deg=0):
        self.view3D["telescope/pier/frame/base_holder/ra_housing/ra_axis/de_housing/de_axis"].set_transform(tf.rotation_matrix(
            np.deg2rad(angle_deg),
            self.mount_de_rotation_axis,
            self.mount_de_application_point))

    def apply_init_transforms(self):
        self.apply_latitude_transform(self.gps_coord["latitude"])

    def register_callbacks(self):
        """
         Issue https://github.com/rdeits/meshcat-python/issues/110
        :return:
        """

        def telescope_position_callback(telescope_position_vector):
            self.model_update_q.put_nowait(lambda: self.update_telescope_position(telescope_position_vector))

        self.actual_indi_device.register_vector_handler_to_client(
            vector_name="EQUATORIAL_EOD_COORD",
            handler_name="observatory3d_telescope_position_update",
            callback=telescope_position_callback)

        def pier_side_callback(pier_side_vector):
            self.model_update_q.put_nowait(lambda: self.update_pier_side(pier_side_vector))

        self.actual_indi_device.register_vector_handler_to_client(
            vector_name="TELESCOPE_PIER_SIDE",
            handler_name="observatory3d_pier_side_update",
            callback=pier_side_callback)

    def update_telescope_position(self, telescope_position_vector):
        ra_angle = [float(i.getValue()) for i in telescope_position_vector.getNumber() if i.isNameMatch("RA")][0]*u.hourangle
        de_angle = [float(i.getValue()) for i in telescope_position_vector.getNumber() if i.isNameMatch("DEC")][0]*u.degree
        self.apply_celestial_ra_transform(angle_astropy=ra_angle)
        self.apply_celestial_de_transform(angle_astropy=de_angle)

    def update_pier_side(self, pier_side_vector):
        pier_side = [i.getName() for i in pier_side_vector.getSwitch() if i.getStateAsString()=="On"][0]

        if pier_side_vector.getStateAsString() == "On":
            self.last_pier_side = pier_side

    def get_celestial_time(self):
        """
        Give the AD coordinate of the sky that is at the same location as the
        sun during spring equinox (when it overlays with vernal point)
        :return:
        """
        return self.serv_time.get_astropy_celestial_time(
            longitude=self.gps_coord["longitude"])

    def update_celestial_time(self):
        self.apply_celestial_ra_transform()