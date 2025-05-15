# Numerical tools
import numpy as np
import queue

# meshcat 3d stuff
import meshcat
import meshcat.geometry as g
import meshcat.transformations as tf
from meshcat.geometry import Box, Cylinder, Sphere

class Observatory3D:

    def __init__(self, view3D, actual_indi_device=None):
        self.view3D = view3D

        # Scaling factor to make sure the telescope fits
        self.main_scaling_factor = 1.3

        # When no stl model is available, define shape for obs body
        self.obs_width = 2*1000       # 2m
        self.obs_depth = 2*1000       # 2m
        self.obs_height = 1.6*1000    # 1.6m

        # Those are loading parameters for body stl
        self.body_load_rotation = tf.rotation_matrix(np.deg2rad(0), [0, 0, 1])
        self.body_load_translation = tf.translation_matrix([0, 0, 1205])

        # Generic parameters for obs body
        self.obs_body_color = 0x686868

        # When no stl model is available, define shape for dome
        self.dome_radius = 0.9 * 1000 # 0.9m

        # Those are loading parameters for dome stl, dome opening is supposed to face north
        self.dome_load_rotation = np.dot(tf.rotation_matrix(np.deg2rad(180), [0, 1, 0]),
                                         tf.rotation_matrix(np.deg2rad(180), [0, 0, 1]))
        self.dome_load_translation = tf.translation_matrix([0, 0, -1450])

        # Generic parameters for dome
        self.obs_dome_color = 0xd3d3d3

        # Operating utilties
        self.orientation_transform = tf.rotation_matrix(0, [0, 0, 1])
        self.dome_rotation_axis = []
        self.dome_frame_position = []

        # indi device
        self.actual_indi_device = actual_indi_device
        # Insane setup just because of: https://github.com/rdeits/meshcat-python/issues/110
        self.model_update_q = queue.Queue()
        # Ok build the object
        self.build_observatory()

    def build_observatory(self):
        #self.build_observatory_body()
        self.build_observatory_body_from_stl()
        self.build_dome_from_stl()
        self.apply_transforms()
        self.register_callbacks() # Issue https://github.com/rdeits/meshcat-python/issues/110

    def build_observatory_body(self):
        """
        """
        observatory_shape = Box(lengths=[
            self.obs_width,
            self.obs_depth,
            self.obs_height])
        observatory_material = g.MeshLambertMaterial(
            color=self.obs_body_color,
            reflectivity=0.01)
        # Set and attach observatory body to frame
        body_from_frame_position = tf.translation_matrix([
            0,
            0,
            self.obs_height/2])
        self.view3D["observatory/body"].set_object(
            observatory_shape,
            observatory_material)
        self.view3D["observatory/body"].set_transform(
            body_from_frame_position)

    def build_observatory_body_from_stl(self):
        observatory_shape = g.StlMeshGeometry.from_file(
            "ScopeSimulator/data/observatory_body.stl")
        observatory_material = g.MeshLambertMaterial(
            color=self.obs_body_color,
            reflectivity=0.01)
        self.view3D["observatory/body"].set_object(
            observatory_shape,
            observatory_material)
        # Scale the stl we just received, because our world is in mm
        scaling = tf.scale_matrix(0.001*self.main_scaling_factor)

        # Set and attach observatory body to frame
        body_from_frame_position = np.dot(
            self.body_load_rotation,
            self.body_load_translation)
        self.view3D["observatory/body"].set_transform(
            np.dot(
                scaling,
                body_from_frame_position))

    def get_dome_object_def(self):
        dome_shape = Sphere(radius=self.dome_radius)
        dome_material = g.MeshLambertMaterial(
            color=self.obs_dome_color,
            reflectivity=0.01)
        return dome_shape, dome_material

    def get_dome_object_def_from_stl(self, shutter_status=None):
        if shutter_status is None:
            shutter_status = self.is_dome_open
        if shutter_status:
            stl_file_path = "ScopeSimulator/data/dome_open.stl"
        else:
            stl_file_path = "ScopeSimulator/data/dome_closed.stl"
        dome_shape = g.StlMeshGeometry.from_file(stl_file_path)
        dome_material = g.MeshLambertMaterial(
            color=self.obs_dome_color,
            reflectivity=0.01)
        # self.view3D["observatory/body"].set_object(
        #     dome_shape,
        #     dome_material)
        return dome_shape, dome_material

    def build_dome(self):
        """

        """
        # We start by building a frame for the dome rotation
        self.view3D[f"observatory/body/dome_frame"].set_object(
            Sphere(radius=0))
        self.dome_frame_position = tf.translation_matrix([
            0,
            0,
            self.obs_height/2])
        self.view3D[f"observatory/body/dome_frame"].set_transform(self.dome_frame_position)
        self.dome_rotation_axis = [0, 0, 1]

        # Set and attach dome to frame
        dome_from_frame_position = tf.translation_matrix([
            0,
            0,
            0])
        self.view3D[f"observatory/body/dome_frame/dome"].set_object(
            *self.get_dome_object_def())
        self.view3D[f"observatory/body/dome_frame/dome"].set_transform(
            dome_from_frame_position)

        # Set and attach marker to frame
        marker_length = 0.1
        marker_from_frame_position = tf.translation_matrix([
            0,
            self.dome_radius,
            0])
        self.view3D[f"observatory/body/dome_frame/marker"].set_object(
            Cylinder(height=marker_length, radius=0.1),
            g.MeshLambertMaterial(
                color=0xff0000,
                reflectivity=0.01)
        )
        self.view3D[f"observatory/body/dome_frame/marker"].set_transform(
            marker_from_frame_position)

    def build_dome_from_stl(self):
        """

        """
        # We start by building a frame for the dome rotation
        self.view3D[f"observatory/body/dome_frame"].set_object(
            Sphere(radius=0))
        self.dome_frame_position = np.dot(
            tf.translation_matrix([0, 0, self.obs_height/2]),
            tf.rotation_matrix(np.deg2rad(90), [0, 0, -1]))
        self.view3D[f"observatory/body/dome_frame"].set_transform(self.dome_frame_position)
        self.dome_rotation_axis = [0, 0, -1]

        # Set and attach dome to frame
        dome_from_frame_position = np.dot(
            self.dome_load_rotation,
            self.dome_load_translation)
        self.view3D[f"observatory/body/dome_frame/dome"].set_object(
            *self.get_dome_object_def_from_stl(shutter_status=self.is_dome_open))
        self.view3D[f"observatory/body/dome_frame/dome"].set_transform(
            dome_from_frame_position)

    def apply_transforms(self):
        self.orientation_transform = tf.rotation_matrix(
            np.deg2rad(270+0), [0, 0, 1])
        self.view3D["observatory"].set_transform(self.orientation_transform)

    def apply_dome_rotation(self, angle_degree):
        rotating_dome_transform = np.dot(
            self.dome_frame_position,
            tf.rotation_matrix(
                np.deg2rad(angle_degree), self.dome_rotation_axis))
        self.view3D[f"observatory/body/dome_frame"].set_transform(
            rotating_dome_transform)

    def apply_shutter_status(self, shutter_status):
        self.view3D[f"observatory/body/dome_frame/dome"].set_object(
            *self.get_dome_object_def_from_stl(shutter_status=shutter_status))

    @property
    def is_dome_open(self):
        return self.actual_indi_device.is_open

    def register_callbacks(self):
        def dome_position_callback(dome_position_vector):
            self.model_update_q.put_nowait(lambda: self.update_dome_position(dome_position_vector))

        self.actual_indi_device.register_vector_handler_to_client(
            vector_name="ABS_DOME_POSITION",
            handler_name="observatory3d_dome_pos_update",
            callback=dome_position_callback)

        def shutter_status_callback(shutter_status_vector):
            self.model_update_q.put_nowait(lambda: self.update_shutter_status(shutter_status_vector))

        self.actual_indi_device.register_vector_handler_to_client(
            vector_name="DOME_SHUTTER",
            handler_name="observatory3d_shutter_status_update",
            callback=shutter_status_callback)

    def update_dome_position(self, dome_position_vector):
        angle = [float(i.getValue()) for i in dome_position_vector.getNumber() if i.isNameMatch("DOME_ABSOLUTE_POSITION")][0]
        self.apply_dome_rotation(angle)

    def update_shutter_status(self, shutter_status_vector):
        shutter_status = [i.getStateAsString() for i in shutter_status_vector.getSwitch() if i.isNameMatch("SHUTTER_OPEN")][0] == "On"

        if shutter_status_vector.getStateAsString() == "On":
            self.apply_shutter_status(shutter_status=shutter_status)