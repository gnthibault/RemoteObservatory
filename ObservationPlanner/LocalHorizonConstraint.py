# Numerical stuff
import numpy as np

#Astropy Stuff
from astropy.coordinates import AltAz
from astropy.coordinates import SkyCoord
import astropy.units as AU

# Astroplan Stuff
from astroplan import Constraint, is_observable, max_best_rescale


class LocalHorizonConstraint(Constraint):
    """
    Constraint observable target to be above local horizon (user defined)
    """
    def __init__(self, horizon, altitude=0, boolean_constraint=True):
        """
        horizon : {azimuth () : horizon altitude()} dictionary
            definition of the local horizon
        """
        self.boolean_constraint = boolean_constraint
        self.hor_az = np.sort(list(map(int,horizon.keys())))
        self.hor_alt = (np.array([int(horizon[i]) for i in self.hor_az])*
                        AU.deg)
        #self.hor_alt = np.zeros(360)*AU.deg

        self.altitude = altitude*AU.deg

    def altazs_to_horizon_alt(self, altazs):
        hor_alt = self.hor_alt[(altazs.az/AU.deg).astype(np.int)]
        return (hor_alt).squeeze()

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
            mask = target_altaz.alt > hor_alt+self.altitude
            return mask
        # if we want to return a non-boolean score
        else:
            print('starting to compute score')
            # rescale the altitude values so that they become
            # scores between zero and one
            rescale = max_best_rescale(target_altaz.alt-hor_alt,
                                       min_val=self.altitude, max_val=90*AU.deg)
            return rescale
