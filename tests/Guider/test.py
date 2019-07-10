import logging
from Guider import GuiderPHD2
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s') 
g = GuiderPHD2.GuiderPHD2()
g.connect()
g.get_connected()
g.set_exposure(2.0)
#g.loop() not needed
g.guide()
g.disconnect()
