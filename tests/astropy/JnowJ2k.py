from datetime import datetime
from astropy.coordinates import SkyCoord, FK5
from astropy.time import Time
import astropy.units as u

fk5_now = FK5(equinox=Time.now())
coord_J2k = SkyCoord(ra=1*u.deg, dec=89*u.deg, frame="icrs") 
coord_now = coord_J2k.transform_to(fk5_now)

print("J2KCoord is {} and JNow coord is {}".format(coord_J2k, coord_now))
