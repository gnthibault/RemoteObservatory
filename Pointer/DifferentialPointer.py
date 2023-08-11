# Generic
from time import sleep
import threading
import traceback

# Numerical stuff
import numpy as np

# Astropy
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.coordinates import ICRS

# Local
from Base.Base import Base
from Imaging.Image import Image
from Imaging.Image import OffsetError
from utils.error import PointingError

SLEEP_SECONDS = 5.

class DifferentialPointer(Base):
    def __init__(self, config=None):
        super().__init__()
        if config is None:
            config = dict(
                gen_hips=False,
                timeout_seconds=150,
                max_iterations=5,
                max_pointing_error_seconds=3
            )

        self.gen_hips = config["gen_hips"]
        self.timeout_seconds = config["timeout_seconds"]
        self.max_iterations = config["max_iterations"]
        self.max_pointing_error = OffsetError(*(config["max_pointing_error_seconds"]*u.arcsec,)*3)

    def points(self, mount, camera, observation, fits_headers):
        pointing_event = threading.Event()
        pointing_status = [False]
        w = threading.Thread(target=self.points_async,
                             kwargs={
                                 "mount": mount,
                                 "camera": camera,
                                 "observation": observation,
                                 "fits_headers": fits_headers,
                                 "pointing_event": pointing_event,
                                 "pointing_status": pointing_status
                             })
        w.start()
        return pointing_event, pointing_status

    def points_async(self, mount, camera, observation, fits_headers, pointing_event, pointing_status):
        try:
            img_num = 0
            pointing_error = OffsetError(*(np.inf * u.arcsec,) * 3)
            pointing_error_stack = {}

            while (img_num < self.max_iterations and pointing_error.magnitude > self.max_pointing_error.magnitude):

                self.logger.info("Taking pointing picture.")
                observation = observation
                self.logger.debug(f"Pointing headers: {fits_headers}")
                camera_events = dict()

                self.logger.debug(f"Exposing for camera: {camera.name}")
                try:
                    # Start the exposures
                    camera_event = camera.take_observation(
                        observation=observation,
                        headers=fits_headers,
                        filename='pointing{:02d}'.format(img_num),
                        exp_time=camera.pointing_seconds * u.second,
                    )
                except Exception as e:
                    self.logger.error(f"Problem shooting image: {e}:{traceback.format_exc()}")
                    break

                status = camera_event.wait(timeout=self.timeout_seconds)
                if not status:
                    self.logger.error(f"Problem waiting for images: {traceback.format_exc()}")
                    break

                # TODO Integrate this feature with our own solver class
                pointing_id, pointing_path = (
                    observation.last_pointing)
                pointing_image = Image(pointing_path)

                solve_params = dict(
                    verbose=True,
                    gen_hips=self.gen_hips,
                    sampling_arcsec=camera.sampling_arcsec,
                    downsample=camera.subsample_astrometry)
                if img_num > 0:
                    solve_params["use_header_position"] = True
                pointing_image.solve_field(**solve_params)
                observation.pointing_image = pointing_image
                self.logger.debug(f"Pointing file: {pointing_image}")
                pointing_error = pointing_image.pointing_error()
                self.logger.info("Ok, I have the pointing picture, let's see how close we are.")
                self.logger.debug(f"Pointing Coords: {pointing_image.pointing}")
                self.logger.debug(f"Pointing Error: {pointing_error}")
                # adjust by slewing again to correct the delta
                target = mount.get_current_coordinates()
                target = SkyCoord(
                    ra=target.ra-pointing_error.delta_ra,
                    dec=target.dec-pointing_error.delta_dec,
                    frame='icrs', equinox='J2000.0')
                mount.slew_to_coord(target)
                # update pointing process tracking information
                pointing_error_stack[img_num] = pointing_error
                img_num = img_num + 1

            if pointing_error.magnitude > self.max_pointing_error.magnitude:
                self.logger.error(f"Pointing accuracy was not good enough after "
                                  f"{img_num} iterations, pointing error stack was: "
                                  f"{pointing_error_stack}")
                pointing_status[0] = False
            else:
                self.logger.info(f"Pointing accuracy was estimated good enough after "
                                 f"{img_num} iterations, pointing error stack was: "
                                 f"{pointing_error_stack}")
                pointing_status[0] = True
        except Exception as e:
            self.logger.error(f"Issue while pointing: {e}")
        finally:
            pointing_event.set()