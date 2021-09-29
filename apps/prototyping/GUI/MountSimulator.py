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


class GuiLoop():

    def __init__(self, gps_coord, mount, observatory, serv_time):
        self.gps_coord = gps_coord
        self.mount = mount
        self.observatory = observatory
        self.serv_time = serv_time

    def run(self):
        app = QApplication([])

        # Initialize various widgets/views
        view3D = View3D.View3D(serv_time=self.serv_time)

        # Now initialize main window
        self.main_window = MainWindow(view3D=view3D)

        # We make sure that upon reception of new number from indiserver, the
        # actual virtual mount position gets updated
        indiCli.register_number_callback(
            device_name = self.mount.device_name,
            vec_name = 'EQUATORIAL_EOD_COORD',
            callback = self.update_coord)

        self.main_window.view3D.set_coord(self.gps_coord)
        self.main_window.view3D.initialise_camera()
        self.main_window.view3D.window.show()

        thread = ObservationRun(self.mount)
        thread.start()
        
        # Everything ends when program is over
        status = app.exec_()
        thread.wait()
        sys.exit(status)

    # callback for updating model
    def update_coord(self, coord):
        self.main_window.view3D.model.setHA(coord['RA'])
        self.main_window.view3D.model.setDEC(coord['DEC'])

class WholeSceneVizualizer():
    def __init__(self, mount, gps_coord, observatory, serv_time):
        self.mount = mount
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
        # Now start to do stuff
        self.mount.set_slew_rate('SLEW_FIND')

        # Unpark if you want something useful to actually happen
        self.mount.unpark()

        #Do a slew and stop
        c = SkyCoord(ra=10*u.hour, dec=60*u.degree, frame='icrs')
        self.mount.slew_to_coord_and_stop(c)

        # Park before standby
        self.mount.park()

if __name__ == "__main__":

    # build+connect indi client
    indiCli = Indi3DSimulatorClient()
    indiCli.connect()

    # build utilities
    obs = ShedObservatory()
    gps_coord = obs.get_gps_coordinates()
    serv_time = NTPTimeService()

    # Build the Mount
    mount = IndiMount(indi_client=indiCli,
                      config={"mount_name":"Telescope Simulator"},
                      connect_on_create=True)
    main_loop = WholeSceneVizualizer(
        mount=mount,
        gps_coord=gps_coord,
        observatory=obs,
        serv_time=serv_time)
    main_loop.run()