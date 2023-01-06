# Generic stuff

# Meshcat stuff
import meshcat

# Local stuff: rendering tools
from ScopeSimulator.World3D import World3D

# Local stuff : Observatory
from Observatory.Observatory import Observatory
from Service.NTPTimeService import NTPTimeService


class WholeSceneVizualizer():
    def __init__(self, gps_coord, observatory, serv_time):
        self.gps_coord = gps_coord
        self.observatory = observatory
        self.serv_time = serv_time

        # Create a new visualizer
        self.view3D = meshcat.Visualizer()
        # Build all of the objects
        self.world3D = World3D(
            view3D=self.view3D,
            gps_coordinates=self.observatory.get_gps_coordinates(),
            serv_time=self.serv_time)

    def run(self):
        self.view3D.open()

    # callback for updating model
    # def update_coord(self, coord):
    #     self.main_window.view3D.model.setHA(coord['RA'])
    #     self.main_window.view3D.model.setDEC(coord['DEC'])

if __name__ == "__main__":
    # Build the observatory
    obs = Observatory()
    serv_time = NTPTimeService()
    gps_coord = obs.get_gps_coordinates()
    main_loop = WholeSceneVizualizer(
        gps_coord=gps_coord,
        observatory=obs,
        serv_time=serv_time)
    main_loop.run()