# Basic stuff
import os
import time

# Local stuff : Service
from Observatory.IndiDomeController import IndiDomeController
from Mount.IndiMount import IndiMount
from Service.SceneVizualization import SceneVizualization

if __name__ == '__main__':

    # Observatory
    config = dict(
        dome_name="Dome Simulator",
        dome_movement_timeout_s=600,
        indi_client=dict(
            indi_host="localhost",
            indi_port=7624)
    )
    dome = IndiDomeController(config=config)

    # Mount
    # mount_config = dict(
    #     mount_name="Telescope Simulator",
    #     indi_client=dict(
    #         indi_host="localhost",
    #         indi_port=7624)
    # )
    # mount = IndiMount(config=mount_config)
    mount_config = dict(
        mount_name="Telescope Simulator",
        equatorial_eod="J2000",
        is_simulator=True,
        indi_client=dict(
            indi_host="localhost",
            indi_port=7624)
    )
    from Service.HostTimeService import HostTimeService
    from Mount.IndiAbstractMount import IndiAbstractMount
    from astropy.coordinates import EarthLocation
    from astropy import units as u
    mount = IndiAbstractMount(location=EarthLocation(lat=45.67*u.deg,
                             lon=5.67*u.deg,
                             height=150*u.m),
                serv_time=HostTimeService(),
                config=mount_config)

    # Scene vizualizer
    config = dict(
        module="SceneVizualization",
        delay_sky_update_s=1,
        delay_moving_objects_s=0.05,
        show_stars=True,
        gps_coord=dict(
            latitude=45.67,
            longitude=5.67
        )
    )
    s = SceneVizualization(config=config,
                           mount_device=mount,
                           observatory_device=dome)
    s.start()
    # for i in range(3600):
    #     time.sleep(1)
    #     s.observatory.apply_dome_rotation(i)
    # This cannot be launched from another thread
