# Generic imports
import logging
import queue
import threading

# Time stuff
from datetime import datetime
from datetime import timedelta
import pytz
from tzwhere import tzwhere
import time

# Astropy stuff
from astropy import units as u
from astropy.time import Time as ATime

# Meshcat / 3D rendering
import meshcat
# Local stuff: rendering tools
from ScopeSimulator.World3D import World3D
from ScopeSimulator.Mount3D import Mount3D
from ScopeSimulator.Observatory3D import Observatory3D

# Local stuff utilities
from Service.HostTimeService import HostTimeService
from utils import Timeout

class SceneVizualization(threading.Thread):
    def __init__(self, config=None, observatory_device=None, mount_device=None):
        self.logger = logging.getLogger(__name__)
        if config is None:
            config = dict(
                module="SceneVizualization",
                delay_sky_update_s=1,
                delay_moving_objects_s=0.1,
                show_stars=True,
                gps_coord=dict(
                    latitude=45.0,
                    longitude=35.0
                )
            )
        self.config = config

        # Init parent thread
        super().__init__(name="observatory_control_scene_vizualization")

        # Service lifecycle
        # self._stop_event = threading.Event()
        self.do_run = True
        self.delay_sky_update_s = config["delay_sky_update_s"]
        self.delay_moving_objects_s = config["delay_moving_objects_s"]

        # parametrize what is shown
        self.gps_coord = config["gps_coord"]
        self.serv_time = HostTimeService(self.gps_coord)
        self.show_stars = config["show_stars"]

        # Actual Indi device
        self.mount_device = mount_device
        self.observatory_device = observatory_device

        # 3D stuff
        self.view3D = None
        self.world3D = None
        self.observatory = None

    def set_mount(self, mount):
        self.mount_device = mount

    def set_observatory(self, observatory):
        self.observatory_device = observatory

    def init_vizualizer(self):
        # Create a new visualizer
        self.view3D = meshcat.Visualizer()
        # Build all of the objects
        self.world3D = World3D(
            view3D=self.view3D,
            gps_coordinates=self.gps_coord,
            serv_time=self.serv_time,
            show_stars=self.show_stars)
        if self.observatory_device is not None:
            self.observatory = Observatory3D(
                view3D=self.view3D,
                actual_indi_device=self.observatory_device)
        if self.mount_device is not None:
            self.mount = Mount3D(
                view3D=self.view3D,
                gps_coordinates=self.gps_coord,
                serv_time=self.serv_time,
                actual_indi_device=self.mount_device)

    def run(self):
        # Init objects to be rendered
        self.init_vizualizer()
        # Now go
        timeout_sky_update = Timeout(duration=self.delay_sky_update_s)
        timeout_obj_update = Timeout(duration=self.delay_moving_objects_s)
        shortest_update = min(self.delay_sky_update_s, self.delay_moving_objects_s)
        while self.do_run:
            if timeout_sky_update.expired():
                self.world3D.set_celestial_time(
                    self.serv_time.get_astropy_celestial_time(
                        longitude=self.gps_coord["longitude"]))
                if self.mount_device:
                    self.mount.update_celestial_time()
                timeout_sky_update.restart()
            # Proper callbacks was unfortunately not possible with meshcat
            if timeout_obj_update.expired():
                timeout_obj_update.restart()
                if self.observatory_device:
                    try:
                        while True:
                            self.observatory.model_update_q.get(block=True,
                                timeout=shortest_update)()
                    except queue.Empty as e:
                        pass
                if self.mount_device:
                    try:
                        while True:
                            self.mount.model_update_q.get(block=True,
                                timeout=shortest_update)()
                    except queue.Empty as e:
                        pass
            if self.mount_device is None and self.observatory_device is None:
                time.sleep(shortest_update)

    def stop(self):
        self.stop_requested = True
        self.join()
