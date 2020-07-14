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
    def __init__(self, serv_time, config=None,
                 connect_on_create=True, primary=False):

        # Parent initialization
        AbstractCamera.__init__(self, serv_time=serv_time, primary=primary)

        # device related intialization
        IndiCamera.__init__(self, logger=self.logger, config=config,
                           connect_on_create=connect_on_create)
        self.indi_camera_config = config

    # TODO TN: setup event based acquisition properly
    def shoot_asyncWithEvent(self, exp_time_sec, filename, exposure_event):
        self.setExpTimeSec(exp_time_sec)
        self.shoot_async()
        self.synchronize_with_image_reception() 
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
                                   exposure_event))
        self.set_frame_type('FRAME_LIGHT')
        w.start()
        return exposure_event

    def autofocus(self, *args, **kwargs):
        """
        Should return an event
        """
        autofocus_event = threading.Event()
        w = threading.Thread(target=self.autofocus_async,
                             args=(autofocus_event))
        self.set_frame_type('FRAME_LIGHT')
        w.start()
        return exposure_event

    def take_bias_exposure(self, exposure_time, filename, *args, **kwargs):
        """
        Should return an event
        """
        exposure_event = threading.Event()
        w = threading.Thread(target=self.shoot_asyncWithEvent,
                             args=(exposure_time.to(u.second).value,
                                   filename,
                                   exposure_event))
        self.set_frame_type('FRAME_BIAS')
        w.start()
        return exposure_event

    def take_dark_exposure(self, exposure_time, filename, *args, **kwargs):
        """
        Should return an event
        """
        exposure_event = threading.Event()
        w = threading.Thread(target=self.shoot_asyncWithEvent,
                             args=(exposure_time.to(u.second).value,
                                   filename,
                                   exposure_event))
        self.set_frame_type('FRAME_DARK')
        w.start()
        return exposure_event

    def take_flat_exposure(self, exposure_time, filename, *args, **kwargs):
        """
        Should return an event
        """
        exposure_event = threading.Event()
        w = threading.Thread(target=self.shoot_asyncWithEvent,
                             args=(exposure_time.to(u.second).value,
                                   filename,
                                   exposure_event))
        self.set_frame_type('FRAME_FLAT')
        w.start()
        return exposure_event  

    # TODO TN: we decide that IndiCamera takes over AbstractCamera in the
    # case we have diamond like inheritance problem
    def get_config(self):
        return IndiCamera.config
