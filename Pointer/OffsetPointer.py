# Generic
import traceback

# Astropy
import astropy.units as u

# Local
from Base.Base import Base
from Imaging.Image import Image

class OffsetPointer(Base):
    def __init__(self, config=None):
        super().__init__()
        if config is None:
            config = dict(
                timeout_seconds=300,
                sync_mount_upon_solve=False
            )

        self.timeout_seconds = config["timeout_seconds"]
        self.sync_mount_upon_solve = config["sync_mount_upon_solve"]

    def acquire_pointing(self, camera, guiding_camera, observation, fits_headers, img_num):
        self.logger.debug("Taking pointing picture.")
        # external_trigger = (camera is guiding_camera)

        self.logger.debug(f"Exposing for camera: {camera.name}")
        try:
            # Start the exposures
            camera_event = camera.take_observation(
                observation=observation,
                headers=fits_headers,
                filename='adjust_pointing{:02d}'.format(img_num),
                exp_time=camera.adjust_pointing_seconds * u.second,
                # external_trigger=external_trigger
            )
            status = camera_event.wait(timeout=self.timeout_seconds)
            if not status:
                msg = f"Problem waiting for images: {traceback.format_exc()}"
                self.logger.error(msg)
                raise RuntimeError(msg)
        except Exception as e:
            self.logger.error(f"Problem waiting for images: {e}")
        pointing_id, pointing_path = observation.last_pointing
        pointing_image = Image(
            pointing_path
        )
        observation.adjust_pointing_image = pointing_image
        self.logger.debug(f"Adjust pointing file: {pointing_image}")

        return pointing_image