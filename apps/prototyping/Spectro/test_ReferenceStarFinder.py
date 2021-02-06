# Generic imports
import argparse

# Astropy
from astropy import units as u
from astropy.coordinates import  SkyCoord, FK5, AltAz, Angle

#Astroplan
from astroplan import FixedTarget

# Local stuff
from Observatory.ShedObservatory import ShedObservatory
from Service.NTPTimeService import NTPTimeService
from Spectro.ReferenceStarFinder import best_references


def find_reference(target_name="Shelyak"):
    target = FixedTarget.from_name(target_name)
    maxseparation = 5*u.deg
    maxebv = 5
    obs = ShedObservatory()
    serv_time = NTPTimeService()

    #altaz_frame=AltAz(obstime=ATime.now(), location=EarthLocation.from_geodetic(lon=3,lat=40))
    altaz_frame = AltAz(obstime=serv_time.get_astropy_time_from_utc(),
                        location=obs.getAstropyEarthLocation())

    ref = best_references(target, altaz_frame, maxseparation, maxebv)
    print(ref)

if __name__ == '__main__':

    # Get the command line option
    parser = argparse.ArgumentParser(
        description="Find the closest reference star from target")
    parser.add_argument('--target_name','-t', required=True,
        help="name of the target star or object")
    args = parser.parse_args()
    find_reference(target_name=args.target_name)

#launch with
#PYTHONPATH=. python3 ./apps/prototyping/Spectro/test_ReferenceStarFinder.py -t sheliak
