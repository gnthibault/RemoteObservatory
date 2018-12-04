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
    def __init__(self, serv_time, indiClient, config_filename=None,
                 connectOnCreate=True, primary=False):

        # Parent initialization
        AbstractCamera.__init__(self, serv_time=serv_time, primary=primary)

        # device related intialization
        IndiCamera.__init__(self, indiClient=indiClient, logger=self.logger,
                           config_filename=config_filename,
                           connectOnCreate=connectOnCreate)

    # TODO TN: setup event based acquisition properly
    def shootAsyncWithEvent(self, exp_time_sec, filename, exposure_event):
        self.setExpTimeSec(exp_time_sec)
        self.shootAsync()
        self.synchronizeWithImageReception() 
        image = self.getReceivedImage()
        try:
            with open(filename, "wb") as f:
                image.writeto(f, overwrite=True)
        except Exception as e:
            self.logger.error('Error while writing file {} : {}'
                              ''.format(filename,e))
        exposure_event.set()

    def take_exposure(self, exposure_time, filename, *args, **kwargs):
        """
        Should return an event
        """
        exposure_event = threading.Event()
        w = threading.Thread(target=self.shootAsyncWithEvent,
                             args=(exposure_time.to(u.second).value,
                                   filename,
                                   exposure_event))
        self.set_frame_type('FRAME_LIGHT')
        w.start()
        return exposure_event

    def take_bias_exposure(self, exposure_time, filename, *args, **kwargs):
        """
        Should return an event
        """
        exposure_event = threading.Event()
        w = threading.Thread(target=self.shootAsyncWithEvent,
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
        w = threading.Thread(target=self.shootAsyncWithEvent,
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
        w = threading.Thread(target=self.shootAsyncWithEvent,
                             args=(exposure_time.to(u.second).value,
                                   filename,
                                   exposure_event))
        self.set_frame_type('FRAME_FLAT')
        w.start()
        return exposure_event  
