# Generic imports
import logging
import time

# Local code
from Guider import GuiderPHD2

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s') 

config = {
    "host": "localhost",
    "port": 4400,
    "do_calibration": False,
    "profile_name": "",
    "exposure_time_sec": 2,
    "settle": {
        "pixels": 1.5,
        "time": 10,
        "timeout": 60},
    "dither": {
        "pixels": 3.0,
        "ra_only": False}
    }

g = GuiderPHD2.GuiderPHD2(config=config)
g.launch_server()
g.connect()
g.get_connected()
g.set_exposure(2.0)
#g.loop() not needed
g.guide()
# guide for 5 min:
for i in range(5*60):
    g.receive()
    time.sleep(1)

g.disconnect()
g.terminate_server()