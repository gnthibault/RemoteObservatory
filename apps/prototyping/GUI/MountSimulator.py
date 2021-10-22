# Generic stuff

# Meshcat stuff
import meshcat

# Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

# Local stuff: 3D rendering tools
# from ScopeSimulator.Model3D import Model3D
from ScopeSimulator.World3D import World3D

# Local stuff
# from helper.Indi3DSimulatorClient import Indi3DSimulatorClient
from Mount.IndiMount import IndiMount
from Observatory.ShedObservatory import ShedObservatory
from Service.NTPTimeService import NTPTimeService

class WholeSceneVizualizer():
    def __init__(self, gps_coord, observatory, serv_time, indi_client):
        self.gps_coord = gps_coord
        self.observatory = observatory
        self.serv_time = serv_time
        self.indi_client = indi_client

        # Create a new visualizer
        self.view3D = meshcat.Visualizer()
        # Build the "base world" objects
        self.world3D = World3D(
            view3D=self.view3D,
            gps_coordinates=self.observatory.get_gps_coordinates(),
            serv_time=self.serv_time)
        # Build the telescope object
        # self.telescope = Model3D(
        #     view3D=self.view3D,
        #     gps_coordinates=self.observatory.get_gps_coordinates(),
        #     serv_time=self.serv_time)

    def run(self):
        ''' Keep in min that backend thread should not do anything because
            every action should be launched asynchronously from the gui
        '''

        # We make sure that upon reception of new number from indiserver, the
        # actual virtual mount position gets updated
        # self.indi_client.register_number_callback(
        #     device_name=self.mount.device_name,
        #     vec_name='EQUATORIAL_EOD_COORD',
        #     callback=self.update_coord)

        self.view3D.open()

    # callback for updating model
    # def update_coord(self, coord):
    #     self.telescope.setRA(coord['RA'])
    #     self.telescope.setDEC(coord['DEC'])

if __name__ == "__main__":
    # Build the observatory
    obs = ShedObservatory()
    serv_time = NTPTimeService()
    gps_coord = obs.get_gps_coordinates()

    # Build indi client
    indi_config = {
        "indi_host": "localhost",
        "indi_port": "7624"
    }
    # indi_cli = Indi3DSimulatorClient(indi_config)
    # indi_cli.connect()

    # Build the Mount
    # mount_config = {
    #     "mount_name": "Telescope Simulator",
    #     "indi_client": indi_config
    # }
    # mount = IndiMount(config=mount_config,
    #                   connect_on_create=True)

    # Run main utility
    # main_loop = WholeSceneVizualizer(
    #     gps_coord=gps_coord,
    #     observatory=obs,
    #     serv_time=serv_time,
    #     indi_client=indi_cli)
    # main_loop.run()

    # Unpark if you want something useful to actually happen
    # mount.unpark()

    # Now start to do stuff
    # mount.set_slew_rate('SLEW_FIND')

    # Do a slew and stop
    # c = SkyCoord(ra=10 * u.hour, dec=60 * u.degree, frame='icrs')
    # mount.slew_to_coord_and_stop(c)

    # Park before standby
    # mount.park()
