# Numerical stuff
import numpy as np
import scipy.interpolate

#Astropy Stuff
from astropy.coordinates import AltAz, Angle
from astropy.coordinates import SkyCoord
import astropy.units as u

# Astroplan Stuff
from astroplan import Constraint, is_observable, max_best_rescale


class LocalHorizonConstraint(Constraint):
    """
    Constraint observable target to be above local horizon (user defined)
    """
    def __init__(self, horizon={0:0}, boolean_constraint=True):
        """
        horizon : {azimuth () : horizon altitude()} dictionary
            definition of the local horizon
        """
        self.boolean_constraint = boolean_constraint

        # Hacky jacky: to simulate the "ring" we duplicate data for the range
        # [-360, 0] and [360, 720]
        hor_az = np.array(list(map(float, horizon.keys())), dtype=np.float32)
        hor_az = np.concatenate((hor_az-360, hor_az, hor_az+360))
        hor_alt = np.array(list(map(float, horizon.values())), dtype=np.float32)
        hor_alt = np.concatenate(3*(hor_alt,))

        self.horizon_interpolator = scipy.interpolate.interp1d(
            hor_az, hor_alt, axis=0, kind='quadratic', fill_value='extrapolate',
            assume_sorted=False)

    def altazs_to_horizon_alt(self, altazs):
        return self.horizon_interpolator(altazs.az.wrap_at(360*u.deg).value)*u.deg

    def compute_constraint(self, times, observer, target):
        # First defin the altaz frame for the current observer
        altaz_frame = AltAz(obstime=times,
                            location=observer.location)

        # Then compute altaz for target
        target_altaz = target.transform_to(altaz_frame)

        # Now compute the horizon for each target azimuth
        hor_alt = self.altazs_to_horizon_alt(target_altaz)

        # Calculate separation between target and horizon
        # Targets are automatically converted to SkyCoord objects
        # by __call__ before compute_constraint is called.
        if self.boolean_constraint:
            mask = target_altaz.alt > hor_alt
            return mask
        # if we want to return a non-boolean score
        else:
            print('starting to compute score')
            # rescale the altitude values so that they become
            # scores between zero and one
            rescale = max_best_rescale(target_altaz.alt-hor_alt,
                                       min_val=0*u.deg, max_val=90*u.deg)
            return rescale
