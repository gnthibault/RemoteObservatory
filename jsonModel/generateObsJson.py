import json
import numpy as np


class HorizonDefinition:
    """ assign an altitude (in deg [0,90[) for each azimut of your site

    azimut goes from 0 (north), to 360 degree clockwise (N, Ne, S, NW)
    """
    def __init__(self):
        a=range(360)
        b=np.ones(len(a))*30
        self.horizon = dict((azimut,altitude) for azimut, altitude in zip(a,b))

    def addObstacle(self, startAzimut, azimutRange, altitude):
        for azimut in range(startAzimut,(startAzimut+azimutRange)):
            self.horizon[azimut%360]=altitude

# Define your own horizon by adding obstacles
horizon = HorizonDefinition()
horizon.addObstacle(250,90,75)

# coordinate contains informations related to observatory position on earth
coordinate = { "gpsCoordinates":  {
                   "latitude": 49.4344,
                   "longitude": 5.1377
                   },
               "altitudeMeter": 400,
               "horizon": horizon.horizon,
               "ownerName": "John Doe"
             }
with open('ShedObservatory.json', 'w') as fp:
    json.dump(coordinate, fp)
