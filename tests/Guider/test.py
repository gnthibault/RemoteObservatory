import logging
from Guider import GuiderPHD2
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s') 
g = GuiderPHD2.GuiderPHD2()
g.connect()
g.get_connected()

