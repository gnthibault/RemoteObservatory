# Astropy
from astropy import units as u

# Local
from ObservationPlanner.Horizon import Horizon

class BaseConstraint:
    """
        Base class for constraint intended to be used in astroplan scheduler
    """
    def __init__(self, weight=1.0, default_score=0.0, *args, **kwargs):
        """ Base constraint

        Each constraint consists of a `get_score` method that is responsible
        for determining a score for a particular target and observer at a given
        time. The `score` is then multiplied by the `weight` of the constraint.

        Args:
            weight (float, optional): The weight of the observation, which will
                be multipled by the score
            default_score (float, optional): The starting score for observation
            *args (TYPE): Description
            **kwargs (TYPE): Description
        """

        assert isinstance(weight, float), \
            self.logger.error("Constraint weight must be a float greater than 0.0")
        assert weight >= 0.0, \
            self.logger.error("Constraint weight must be a float greater than 0.0")

        self.weight = weight
        self._score = default_score

    def get_score(self, time, observer, target):
        raise NotImplementedError


class Altitude(BaseConstraint):

    """ Implements altitude constraints for a horizon """

    def __init__(self, horizon=None, *args, **kwargs):
        """Create an Altitude constraint from a valid `Horizon`. """
        super().__init__(*args, **kwargs)
        assert isinstance(horizon, Horizon)
        self.horizon_line = horizon.horizon_line

    def get_score(self, time, observer, observation, **kwargs):
        veto = False
        score = self._score

        target = observation.field

        # Note we just get nearest integer
        target_az = int(observer.altaz(time, target=target).az.value)
        target_alt = observer.altaz(time, target=target).alt.degree

        # Determine if the target altitude is above or below the determined
        # minimum elevation for that azimuth
        min_alt = self.horizon_line[target_az]
        if target_alt < min_alt:
            self.logger.debug("\t\tBelow minimum altitude: {:.02f} < {:.02f}", target_alt, min_alt)
            veto = True
        else:
            score = 100
        return veto, score * self.weight

    def __str__(self):
        return "Altitude"


class Duration(BaseConstraint):

    @u.quantity_input(horizon=u.degree)
    def __init__(self, horizon, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.horizon = horizon

    def get_score(self, time, observer, observation, **kwargs):
        veto = False
        score = self._score

        target = observation.field

        veto = not observer.target_is_up(time, target, horizon=self.horizon)

        end_of_night = kwargs.get('end_of_night',
                                  observer.tonight(time=time, horizon=-18 * u.degree)[1])

        if not veto:
            # Get the next meridian flip
            target_meridian = observer.target_meridian_transit_time(
                time, target,
                which='next')

            # If it flips before end_of_night it hasn't flipped yet so
            # use the meridian time as the end time
            if target_meridian < end_of_night:

                # If target can't meet minimum duration before flip, veto
                if time + observation.minimum_duration > target_meridian:
                    self.logger.debug("\t\tObservation minimum can't be met before meridian flip")
                    veto = True

            # else:
            # Get the next set time
            target_end_time = observer.target_set_time(
                time, target,
                which='next',
                horizon=self.horizon)

            # If end_of_night happens before target sets, use end_of_night
            if target_end_time > end_of_night:
                self.logger.debug("\t\tTarget sets past end_of_night, using end_of_night")
                target_end_time = end_of_night

            # Total seconds is score
            score = (target_end_time - time).sec
            if score < observation.minimum_duration.value:
                veto = True

            # Normalize the score based on total possible number of seconds
            score = score / (end_of_night - time).sec

        return veto, score * self.weight

    def __str__(self):
        return "Duration above {}".format(self.horizon)


class MoonAvoidance(BaseConstraint):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_score(self, time, observer, observation, **kwargs):
        veto = False
        score = self._score

        try:
            moon = kwargs['moon']
        except KeyError:
            self.logger.error("Moon must be set")

        moon_sep = moon.separation(observation.field.coord).value

        # This would potentially be within image
        if moon_sep < 15:
            self.logger.debug("\t\tMoon separation: {:.02f}".format(moon_sep))
            veto = True
        else:
            score = (moon_sep / 180)

        return veto, score * self.weight

    def __str__(self):
        return "Moon Avoidance"


class AlreadyVisited(BaseConstraint):

    """ Simple Already Visited Constraint

    A simple already visited constraint that determines if the given `observation`
    has already been visited before. If given `observation` has already been
    visited then it will not be considered for a call to become the `current observation`.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_score(self, time, observer, observation, **kwargs):
        veto = False
        score = self._score

        observed_list = kwargs.get('observed_list')

        observed_field_list = [obs.field for obs in observed_list.values()]

        if observation.field in observed_field_list:
            veto = True

        return veto, score * self.weight

    def __str__(self):
        return "Already Visited"
