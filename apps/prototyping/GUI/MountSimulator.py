# Generic stuff

# Numerical stuff
import numpy as np

# Meshcat stuff
import meshcat

# Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

# Local stuff: rendering tools
from ScopeSimulator.World3D import World3D

# Local stuff : Observatory
from Observatory.ShedObservatory import ShedObservatory
from Service.NTPTimeService import NTPTimeService

# Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

# Local stuff
from ScopeSimulator import Model3D
from helper.Indi3DSimulatorClient import Indi3DSimulatorClient
from Mount.IndiMount import IndiMount
from Observatory.ShedObservatory import ShedObservatory
from Service.NTPTimeService import NTPTimeService


class WholeSceneVizualizer():
    def __init__(self, indi_client, gps_coord, observatory, serv_time):
        self.indi_client = indi_client
        self.gps_coord = gps_coord
        self.observatory = observatory
        self.serv_time = serv_time

        # Create a new visualizer
        self.view3D = meshcat.Visualizer()

        # Build all of the objects
        self.mount3D = Model3D(
            view3D=self.view3D,
            gps_coordinates=self.observatory.get_gps_coordinates(),
            serv_time=self.serv_time)

    def run(self):
        ''' Keep in min that backend thread should not do anything because
            every action should be launched asynchronously from the gui
        '''

        # We make sure that upon reception of new number from indiserver, the
        # actual virtual mount position gets updated
        self.indi_client.register_number_callback(
            device_name=self.mount.device_name,
            vec_name='EQUATORIAL_EOD_COORD',
            callback=self.update_coord)

        self.view3D.open()

    # callback for updating model
    def update_coord(self, coord):
        self.main_window.view3D.model.setHA(coord['RA'])
        self.main_window.view3D.model.setDEC(coord['DEC'])

if __name__ == "__main__":

    # build+connect indi client
    indi_config = {
        "indi_host": "localhost",
        "indi_port": "7624"
    }
    indi_cli = Indi3DSimulatorClient(indi_config)
    indi_cli.connect()

    # build utilities
    obs = ShedObservatory()
    gps_coord = obs.get_gps_coordinates()
    serv_time = NTPTimeService()

    # Build the Mount
    mount_config = {
        "mount_name": "Telescope Simulator",
        "indi_client": indi_config
    }
    mount = IndiMount(config=mount_config,
                      connect_on_create=True)
    main_loop = WholeSceneVizualizer(
        indi_client=indi_cli,
        gps_coord=gps_coord,
        observatory=obs,
        serv_time=serv_time)
    main_loop.run()

    # Now start to do stuff
    mount.set_slew_rate('SLEW_FIND')

    # Unpark if you want something useful to actually happen
    mount.unpark()

    # Do a slew and stop
    c = SkyCoord(ra=10 * u.hour, dec=60 * u.degree, frame='icrs')
    mount.slew_to_coord_and_stop(c)

    # Park before standby
    mount.park()
