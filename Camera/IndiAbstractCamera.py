# Basic stuff
import io
import os
import threading

# Imaging and Fits stuff
from astropy import units as u
from astropy.io import fits

# Local stuff
from Camera.AbstractCamera import AbstractCamera
from Camera.IndiCamera import IndiCamera

class IndiAbstractCamera(IndiCamera, AbstractCamera):
    def __init__(self, serv_time, config=None, connect_on_create=True):

        # Parent initialization
        AbstractCamera.__init__(self, serv_time=serv_time, **config)

        # device related intialization
        IndiCamera.__init__(self, logger=self.logger, config=config,
                           connect_on_create=connect_on_create)
        self.indi_camera_config = config
        try:
            self.sampling_arcsec = config["sampling_arcsec"]
        except KeyError as e:
            self.sampling_arcsec = None

    def park(self):
        self.logger.debug(f"Parking camera {self.camera_name}")
        self.disconnect()

    def unpark(self):
        self.logger.debug(f"Unparking camera {self.camera_name}")
        self.connect(connect_device=True)

    # TODO TN: setup event based acquisition properly
    def shoot_asyncWithEvent(self, exp_time_sec, filename, exposure_event,
                             **kwargs):
        # If there is no external trigger, then we proceed to handle setup on our side
        external_trigger = kwargs.get("external_trigger", False)
        if not external_trigger:
            # set frame type
            frame_type = kwargs.get("frame_type", "FRAME_LIGHT")
            self.set_frame_type(frame_type)
            # set gain
            gain = kwargs.get("gain", self.gain)
            self.set_gain(gain)
            # set offset
            offset = kwargs.get("offset", self.offset)
            self.set_offset(offset)
            # set temperature
            temperature = kwargs.get("temperature", None)
            if temperature is not None:
                self.set_cooling_on()
                self.set_temperature(temperature)
            self.indi_client.enable_blob()
            # Now shoot
            self.setExpTimeSec(exp_time_sec)
            self.logger.debug(f"Camera {self.camera_name}, about to shoot for {self.exp_time_sec}")
            self.shoot_async()
        # Wether trigger was internal or external, we rely on the last received blob
        self.synchronize_with_image_reception()
        self.logger.debug(f"Camera {self.camera_name}, done with image reception, external trigger {external_trigger}")
        image = self.get_received_image()
        try:
            with open(filename, "wb") as f:
                image.writeto(f, overwrite=True)
        except Exception as e:
            self.logger.error(f"Error while writing file {filename} : {e}")
        exposure_event.set()

    def take_exposure(self, exposure_time, filename, *args, **kwargs):
        """
        Should return an event
        """
        exposure_event = threading.Event()
        w = threading.Thread(target=self.shoot_asyncWithEvent,
                             args=(exposure_time.to(u.second).value,
                                   filename,
                                   exposure_event,
                                   *args),
                             kwargs=kwargs)
        w.start()
        return exposure_event

    def autofocus(self, *args, **kwargs):
        """
        Should return an event and a status
        """
        autofocus_event = threading.Event()
        autofocus_status = [False]
        w = threading.Thread(target=self.autofocus_async,
                             kwargs={"autofocus_event": autofocus_event,
                                     "autofocus_status": autofocus_status})
        self.set_frame_type('FRAME_LIGHT')
        w.start()
        return autofocus_event, autofocus_status

    def take_bias_exposure(self, *args, **kwargs):
        kwargs["frame_type"] = "FRAME_BIAS"
        return self.take_exposure(*args, **kwargs)

    def take_dark_exposure(self, *args, **kwargs):
        kwargs["frame_type"] = "FRAME_DARK"
        return self.take_exposure(*args, **kwargs)

    def take_flat_exposure(self, *args, **kwargs):
        kwargs["frame_type"] = "FRAME_FLAT"
        return self.take_exposure(*args, **kwargs)

    # TODO TN: we decide that IndiCamera takes over AbstractCamera in the
    # case we have diamond like inheritance problem
    def get_config(self):
        return IndiCamera.config
