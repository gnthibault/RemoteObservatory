# Generic
import logging
import os
from threading import Event
from threading import Thread

# Astropy
import astropy.units as u

# Numerical tool
import numpy as np

# Local
from Base.Base import Base
from Imaging import fits as fits_utils
from utils import error

class AbstractCamera(Base):

    def __init__(self, serv_time, *args,  **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self._image_dir = self.config['directories']['images']
        except KeyError:
            self.logger.error("No images directory. Set image_dir in config")

        self.serv_time = serv_time
        self.do_acquisition = kwargs.get("do_acquisition", False)
        self.do_guiding = kwargs.get("do_guiding", False)
        self.do_pointing = kwargs.get("do_pointing", False)
        self.do_adjust_pointing = kwargs.get("do_adjust_pointing", False)
        self.do_autofocus = kwargs.get("do_autofocus", False)

        self.camera_name = kwargs["camera_name"]
        self.filter_type = 'no-filter'
        self._file_extension = 'fits'
        self._serial_number = '0123456789'

        self._is_initialized = False

###############################################################################
# Properties
###############################################################################

    @property
    def uid(self):
        """ A six-digit serial number for the camera """
        return self._serial_number

    @property
    def file_extension(self):
        """ File extension for images saved by camera """
        return self._file_extension
 
    @property
    def uid(self):
        """ A six-digit serial number for the camera """
        return self._serial_number[0:6]

    @property
    def is_initialized(self):
        """ bool: Has mount been initialized with connection """
        return self._is_initialized

###############################################################################
# Methods
###############################################################################

    def park(self):
        self.logger.debug(f"Parking camera {self.camera_name}")

    def unpark(self):
        self.logger.debug(f"Unparking camera {self.camera_name}")

    def take_observation(self, observation, headers=None, filename=None,
                         *args, **kwargs):
        """Take an observation

        Gathers various header information, sets the file path, and calls
            `take_exposure`. Also creates a `threading.Event` object and a
            `threading.Thread` object. The Thread calls `process_exposure`
            after the exposure had completed and the Event is set once
            `process_exposure` finishes.

        Args:
            observation (~pocs.scheduler.observation.Observation): Object
                describing the observation
            headers (dict, optional): Header data to be saved along with the
                                      file.
            filename (str, optional): pass a filename for the output FITS file 
                                      to overrride the default file naming
                                      system
            **kwargs (dict): Optional keyword arguments (`exp_time`)

        Returns:
            threading.Event: An event to be set when the image is done
                             processing
        """
        # To be used for marking when exposure is complete
        # (see `process_exposure`)
        observation_event = Event()

        (exp_time, gain, offset, temperature, file_path, image_id, metadata,
            is_pointing) = self._setup_observation(observation,
                                                   headers,
                                                   filename,
                                                   *args,
                                                   **kwargs)
        kwargs["gain"] = gain
        kwargs["offset"] = offset
        kwargs["temperature"] = temperature
        exposure_event = self.take_exposure(
            exposure_time=exp_time,
            filename=file_path,
            *args, **kwargs)

        # Add most recent exposure to list
        if self.do_acquisition and not is_pointing:
            observation.exposure_list[image_id] = file_path
        if is_pointing:
            observation.pointing_list[image_id] = file_path

        # Process the exposure once readout is complete
        t = Thread(target=self.process_exposure, args=(metadata,
                   observation_event, exposure_event))
        t.name = f"{self.camera_name}Thread"
        t.start()

        return observation_event

    def _setup_observation(self, observation, headers, filename, **kwargs):
        if headers is None:
            headers = {}

        start_time = headers.get('start_time', self.serv_time.flat_time())

        # Get the filepath
        image_dir = os.path.join(
            self._image_dir,
            "targets",
            observation.name.replace(" ", "_"),
            self.uid,
            observation.seq_time
        )
        os.makedirs(image_dir, exist_ok=True)

        # Get full file path with filename
        if filename is None:
            file_path = os.path.join(image_dir, start_time) + "." + self.file_extension
        else:
            # Add extension
            if '.' not in filename:
                filename = '{}.{}'.format(filename, self.file_extension)
            # Add directory
            if '/' not in filename:
                filename = os.path.join(image_dir, filename)
            file_path = filename

        image_id = '{}_{}_{}'.format(
            self.camera_name,
            self.uid,
            start_time
        )
        self.logger.debug(f"image_id: {image_id}")
        sequence_id = observation.seq_time

        # check if it is a pointing image
        is_pointing = ('POINTING' in headers) and (headers["POINTING"] == "True")

        # get values
        exp_time = kwargs.get('exp_time', observation.time_per_exposure)
        gain = observation.configuration["gain"]
        offset = observation.configuration["offset"]
        temperature = observation.configuration["temperature"]
        filter_name = observation.configuration.get("filter", "no-filter")

        # Camera metadata
        metadata = {
            'camera_name': self.camera_name,
            'observation_id': observation.id,
            'camera_uid': self.uid,
            'target_name': observation.name,
            'file_path': file_path,
            'filter': filter_name,
            'image_id': image_id,
            'sequence_id': sequence_id,
            'start_time': start_time,
            'exp_time': exp_time,
            'temperature_degC': temperature
        }
        metadata.update(headers)
        return (exp_time, gain, offset, temperature, file_path, image_id, metadata, is_pointing)

    def take_calibration(self,
                         temperature,
                         gain,
                         offset,
                         exp_time,
                         headers=None,
                         calibration_seq_id=None,
                         calibration_name="unknown_calibration",
                         observations=None,
                         filename=None,
                         *args, **kwargs):
        # To be used for marking when exposure is complete
        # (see `process_calibration`)
        calib_event = Event()

        file_path, metadata = self._setup_calibration(
            temperature=temperature,
            gain=gain,
            offset=offset,
            exp_time=exp_time,
            headers=headers,
            calibration_seq_id=calibration_seq_id,
            calibration_name=calibration_name,
            observations=observations,
            filename=filename,
            *args, **kwargs)
 
        exposure_event = self.take_calibration_exposure(
            filename=file_path,
            temperature=temperature,
            gain=gain,
            offset=offset,
            exposure_time=exp_time,
            headers=headers,
            calibration_seq_id=calibration_seq_id,
            calibration_name=calibration_name,
            observations=observations,
            *args, **kwargs)

        # Process the exposure once readout is complete
        t = Thread(target=self.process_calibration,
                   args=(metadata, calib_event, exposure_event))
        t.name = f"{self.camera_name}_Thread"
        t.start()

        return calib_event

    def get_calibration_directory(self,
                                  temperature,
                                  gain,
                                  offset,
                                  exp_time,
                                  headers,
                                  calibration_seq_id=None,
                                  calibration_name='unknown_calibration',
                                  filename=None):

        start_time = headers.get('start_time', self.serv_time.flat_time())

        # Get the directory path
        image_dir = os.path.join(
            self._image_dir,
            "calibrations",
            calibration_name,
            self.uid)
        if calibration_name == "dark":
            if temperature is None:
                temperature = self.get_temperature()
            image_dir = os.path.join(
                image_dir,
                f"temp_deg_{temperature}",
                f"gain_{gain}",
                f"offset_{offset}",
                f"exp_time_sec_{exp_time.to(u.second).value}")
        if calibration_seq_id is not None:
            image_dir = os.path.join(
                image_dir,
                calibration_seq_id)
        os.makedirs(image_dir, exist_ok=True)

        # Get full file path with filename
        if filename is None:
            file_path = f"{image_dir}/{start_time}.{self.file_extension}"
        else:
            # Add extension
            if '.' not in filename:
                filename = f"{filename}.{self.file_extension}"
            # Add directory
            if '/' not in filename:
                filename = os.path.join(image_dir, filename)

            file_path = filename
        return file_path

    def _setup_calibration(self,
                           temperature,
                           gain,
                           offset,
                           exp_time,
                           headers=None,
                           calibration_seq_id=None,
                           calibration_name='unknown_calibration',
                           observations=[],
                           filename=None,
                           *args, **kwargs):
        """
            parameter can be temperature for dark or filter for flat ?
        """
        if headers is None:
            headers = {}
        start_time = headers.get('start_time', self.serv_time.flat_time())

        file_path = self.get_calibration_directory(
            temperature=temperature,
            gain=gain,
            offset=offset,
            exp_time=exp_time,
            headers=headers,
            calibration_seq_id=calibration_seq_id,
            calibration_name=calibration_name,
            filename=filename)

        # Image primary key
        image_id = '{}_{}_{}'.format(
            self.camera_name,
            self.uid,
            start_time
        )
        # Sequence primary key, if available
        sequence_id = calibration_seq_id

        #TODO TN URGENT: MISSING IMAGE_ID AND SEQUENCE_ID
        metadata = {
            'camera_name': self.camera_name,
            'camera_uid': self.uid,
            'calibration_name': calibration_name,
            'file_path': file_path,
            'image_id': image_id,
            'sequence_id': sequence_id,
            'start_time': start_time,
            'exp_time': exp_time.to(u.second).value,
            'gain': gain,
            'offset': offset,
            'temperature_degC': temperature if temperature else "no_target",
            'observation_ids': [o.id for o in observations]
        }
        metadata.update(headers)
        return file_path, metadata

    def take_exposure(self, *args, **kwargs):
        """ Must be implemented"""
        raise NotImplementedError

    def take_calibration_exposure(self, calibration_name, *args, **kwargs):
        try:
            exp_method = f"take_{calibration_name}_exposure"
            return self.__getattribute__(exp_method)(*args, **kwargs)
        except KeyError as e:
            self.logger.debug(f"calibration exposure falling back to normal "
                              f"exposure because of: {e}")
            return self.take_exposure(*args, **kwargs)
        except AttributeError as e:
            self.logger.debug(f"calibration exposure falling back to normal "
                              f"exposure because of: {e}")
            return self.take_exposure(*args, **kwargs)

    def take_bias_exposure(self, *args, **kwargs):
        return self.take_exposure(*args, **kwargs)

    def take_dark_exposure(self, *args, **kwargs):
        return self.take_exposure(*args, **kwargs)

    def take_flat_exposure(self, *args, **kwargs):
        return self.take_exposure(*args, **kwargs)

    def get_temperature(self):
        """ Must be implemented"""
        return np.NaN

    def process_exposure(self, info, observation_event, exposure_event=None):
        """
        Processes the exposure.

        Initially, there was a test on wether the camera was a primary camera or not. In the case of a primary camera,
        we extracted the jpeg image and saved metadata to mongo `current` collection.
        For all camera (prim+non-prim), we saved metadata to mongo `observations` collection.
        Now, we save the metadata to all collections
        #TODO TN URGENT

        Args:
            info (dict): Header metadata saved for the image
            observation_event (threading.Event): An event that is set
                signifying that the camera is done with this exposure
            exposure_event (threading.Event, optional): An event that should be
                set when the exposure is complete, triggering the processing.
        """
        # If passed an Event that signals the end of the exposure wait for it
        # to be set
        if exposure_event is not None:
            exposure_event.wait()

        image_id = info['image_id']
        observation_id = info['observation_id']
        file_path = info['file_path']
        title = info['target_name']
        self.logger.debug(f"Processing {image_id}")

        try:
            latest_path = f"{self._image_dir}/latest.jpg"
            fits_utils.update_thumbnail(file_path, latest_path)
        except Exception as e:
            self.logger.warning(f"Problem with extracting pretty image: {e}")

        file_path = self._process_fits(file_path, info)
        try:
            info['exp_time'] = info['exp_time'].to(u.second).value
        except Exception as e:
            self.logger.error(f"Problem getting exp_time information: {e}")

        # if info['is_acquisition']:
        #     self.logger.debug(f"Adding current observation to db: {image_id}")
        #     try:
        self.db.insert_current('observations', info, store_permanently=False)
        #     except Exception as e:
        #         self.logger.error(f"Problem adding observation to db: {e}")
        #else:
            #self.logger.debug(f"Compressing {file_path}")
            #fits_utils.fpack(file_path)
            #TODO TN I don't understand the rationale here.
            #It generates an error when tryin to read pointing image

        self.logger.debug(f"Adding image metadata to db: {image_id}")
        self.db.insert('observations', {
            'data': info,
            'date': self.serv_time.get_utc(),
            'observation_id': observation_id,
        })

        # Mark the event as done
        observation_event.set()

    def process_calibration(self, info, observation_event, exposure_event=None):
        """
        image_id: unique image identifier crafted out ouf Camera name, camera uid, and time stamp like "CCD Simulator_012345_20221206T174910"
        sequence_id:
        target_name: optional like "M31"
        observation_ids: list of identifiers of a prior acquisition to which the calibration refers to like ['HD3360_8781756692625']
        """
        # If passed an Event that signals the end of the exposure wait for it
        # to be set
        if exposure_event is not None:
            exposure_event.wait()
        image_id = info['image_id']
        seq_id = info['sequence_id']
        file_path = info['file_path']
        title = info.get('target_name', "no-target")
        observation_ids = info['observation_ids']
        del info['observation_ids']
        info['exp_time'] = info['exp_time']
        self.logger.debug(f"Processing {image_id}")
        file_path = self._process_fits(file_path, info)

        # if info['is_acquisition']:
        #     self.logger.debug(f"Adding current calibration to db: {image_id}")
        #     try:
        self.db.insert_current('calibrations', info,
                               store_permanently=False)
        #     except Exception as e:
        #         self.logger.error(f"Problem adding calibration to db: {e}")
        # else:
        #     self.logger.debug(f"Compressing {file_path}")
        #     fits_utils.fpack(file_path)

        self.logger.debug(f"Adding image metadata to db: {image_id}")

        # We are actually looping on each observation, so that a calibration is
        # actually featured once per observation
        if len(observation_ids) < 1:
            observation_ids = [""]
        for observation_id in observation_ids:
            self.db.insert('calibrations', {
                'data': info,
                'date': self.serv_time.get_utc(),
                'observation_id': observation_id,
            })

        # Mark the event as done
        observation_event.set()

    def _process_fits(self, file_path, info):
        """
        Add FITS headers from info the same as images.cr2_to_fits()
        """
        self.logger.debug(f"Updating FITS headers: {file_path}")
        fits_utils.update_headers(file_path, info)
        return file_path