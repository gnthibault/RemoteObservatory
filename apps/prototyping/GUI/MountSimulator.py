# Generic stuff

# Meshcat stuff
import meshcat

# Astropy stuff
from astropy.utils.iers import conf
conf.auto_max_age = None
from astropy import units as u
from astropy.coordinates import SkyCoord

# Local stuff: 3D rendering tools
from ScopeSimulator.Model3D import Model3D
from ScopeSimulator.World3D import World3D

# Local stuff
from Mount.IndiMount import IndiMount
from Observatory.ShedObservatory import ShedObservatory
from Service.NTPTimeService import NTPTimeService

class WholeSceneVizualizer():
    def __init__(self, gps_coord, observatory, serv_time):
        self.gps_coord = gps_coord
        self.observatory = observatory
        self.serv_time = serv_time

        # Create a new visualizer
        self.view3D = meshcat.Visualizer()
        # Build the "base world" objects
        # self.world3D = World3D(
        #     view3D=self.view3D,
        #     gps_coordinates=self.observatory.get_gps_coordinates(),
        #     serv_time=self.serv_time)
        # Build the telescope object
        self.telescope = Model3D(
            view3D=self.view3D,
            gps_coordinates=self.observatory.get_gps_coordinates(),
            serv_time=self.serv_time)

    def run(self):
        ''' Keep in min that backend thread should not do anything because
            every action should be launched asynchronously from the gui
        '''
        self.view3D.open()

    # callback for updating model
    def update_coord(self, vector, indi):
        if vector.name == "EQUATORIAL_EOD_COORD":
            coord = vector.to_dict()
            print(f"VIZUALIZER GOT COORD {coord}")
            #self.telescope.set_ra(float(coord['RA']))
            #self.telescope.set_dec(float(coord['DEC']))

if __name__ == "__main__":
    # Build the observatory
    obs = ShedObservatory()
    serv_time = NTPTimeService()
    gps_coord = obs.get_gps_coordinates()

    # Build scene vizualizer
    main_loop = WholeSceneVizualizer(
        gps_coord=gps_coord,
        observatory=obs,
        serv_time=serv_time)

    # Build the Mount
    mount_config = {
        "mount_name": "Telescope Simulator",
        "indi_client": {
            "indi_host": "localhost",
            "indi_port": 7624
        }
    }
    mount = IndiMount(config=mount_config,
                      connect_on_create=False)
    mount.number_def_handler = main_loop.update_coord
    mount.connect()

    # Run main utility
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
