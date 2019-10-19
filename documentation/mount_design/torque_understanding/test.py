
# numerical stuff
import numpy as np

#Unit is useful
import astropy.units as au

class Force:
    """
    In French:
    La force est représentée par un vecteur ayant un point d'application, une
    direction, un sens et une intensité (en newtons)
    In english:
    A force has both magnitude and direction, making it a vector quantity. It is
    measured in the SI unit of newtons and represented by the symbol F
    """
    def __init__(self, direction, magnitude, point_of_application=None):

        self._direction = None
        self._magnitude = None
        self._point_of_application = None

        self.direction = direction
        self.magnitude = magnitude
        self.point_of_application = point_of_application

    @property
    def direction(self):
        return self._direction

    @property
    def magnitude(self):
        return self._magnitude

    @property
    def point_of_application(self):
        return self._point_of_application

    @direction.setter
    def direction(self, direction):
        assert not np.isclose(np.linalg.norm(direction), 0)
        self._direction = (direction.astype(np.float64)/
                           np.linalg.norm(direction.astype(np.float64)))

    @magnitude.setter
    def magnitude(self, magnitude):
        self._magnitude = magnitude.astype(np.float64)

    @point_of_application.setter
    def point_of_application(self, point_of_application):
        self._point_of_application = point_of_application.astype(np.float64)

    def vector(self):
        return self.direction*self.magnitude

def compute_torque(applied_force, torque_application_point_coord,
                   torque_axis_direction=None):
    """
    In French:
    Le moment d'une force par rapport à un point donné est une grandeur physique
    vectorielle traduisant l'aptitude de cette force à faire tourner un système
    mécanique autour de ce point, souvent appelé pivot. Il s'exprime
    habituellement en N·m (newtons-mètres), et peut l'être de manière
    équivalente en joules par radian. Le moment d'un ensemble de forces, et
    notamment d'un couple, est la somme (géométrique) des moments de ces forces.

    La projection du moment (d'une force par rapport à un point) sur un axe
    \Delta (orienté) contenant le point s'appelle moment de la force par rapport
    à l'axe \Delta : c'est une grandeur scalaire algébrique exprimée dans la
    même unité, et traduisant de même la faculté de la force appliquée à faire
    tourner le système mécanique autour de l'axe \Delta, le signe du moment par
    rapport à l'axe traduisant le sens de la rotation par rapport à l'orientation
    choisie de l'axe.

    In english:
    The moment of force, or torque, is a first moment: $\mathbf {\tau } =rF$,
    or, more generally, $\mathbf {r} \times \mathbf {F}$
    Similarly, angular momentum is the 1st moment of momentum:
    \mathbf {L} =\mathbf {r} \times \mathbf {p}.
    Note that momentum itself is not a moment

    :return:
    """
    torque_to_application_point = np.cross(
        applied_force.vector().to(au.newton),
        applied_force.point_of_application.to(au.meter)-
        torque_application_point_coord.to(au.meter)
    )*au.newton*au.meter

    if torque_axis_direction is not None:
        torque_to_axis = np.dot(torque_to_application_point,
            torque_axis_direction/np.linalg.norm(torque_axis_direction)
            )*au.newton*au.meter
        return torque_to_axis
    return torque_to_application_point


torque_application_point_coord = np.array([0, 0, 0]) * au.meter
torque_axis_direction = np.array([0, 1, 0])
force_application_point_coord = np.array([1, 0, 0]) * au.meter
force_direction = np.array([0, 0, 1])
force_mag_in_newton = 1 * au.newton

applied_force = Force(direction=force_direction,
                      magnitude=force_mag_in_newton,
                      point_of_application=force_application_point_coord)

torque = compute_torque(applied_force, torque_application_point_coord, torque_axis_direction)
print(f"Computed torque is {torque}")