# Generic
import logging
import os
from threading import Event
from threading import Thread

# Astropy
import astropy.units as u

# Local
from Base.Base import Base
from Imaging import fits as fits_utils
from utils import error

class AbstractCamera(Base):

    def __init__(self, serv_time, primary=False, *args,  **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self._image_dir = self.config['directories']['images']
        except KeyError:
            self.logger.error("No images directory. Set image_dir in config")

        self.serv_time = serv_time
        self.is_primary = primary
        self.filter_type = 'no-filter'
        self._file_extension = 'fits'
        self._serial_number = '0123456789'

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

###############################################################################
# Methods
###############################################################################

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

        (exp_time, gain, temperature, file_path, image_id, metadata,
            is_pointing) = self._setup_observation(observation,
                                                   headers,
                                                   filename,
                                                   *args,
                                                   **kwargs)
        kwargs["gain"] = gain
        kwargs["temperature"] = temperature
        exposure_event = self.take_exposure(exposure_time=exp_time,
            filename=file_path, *args, **kwargs)

        # Add most recent exposure to list
        if self.is_primary:
            observation.exposure_list[image_id] = file_path
        if is_pointing:
            observation.pointing_list[image_id] = file_path

        # Process the exposure once readout is complete
        t = Thread(target=self.process_exposure, args=(metadata,
                   observation_event, exposure_event))
        t.name = f"{self.name}Thread"
        t.start()

        return observation_event

    def _setup_observation(self, observation, headers, filename, **kwargs):
        if headers is None:
            headers = {}

        start_time = headers.get('start_time', self.serv_time.flat_time())

        # Get the filepath
        image_dir = "{}/targets/{}/{}/{}".format(
            self._image_dir,
            observation.name,
            self.uid,
            observation.seq_time,
        )
        os.makedirs(image_dir, exist_ok=True)

        # Get full file path with filename
        if filename is None:
            file_path = "{}/{}.{}".format(image_dir, start_time,
                                          self.file_extension)
        else:
            # Add extension
            if '.' not in filename:
                filename = '{}.{}'.format(filename, self.file_extension)

            # Add directory
            if '/' not in filename:
                filename = '{}/{}'.format(image_dir, filename)

            file_path = filename

        image_id = '{}_{}_{}'.format(
            self.config['name'],
            self.uid,
            start_time
        )
        self.logger.debug("image_id: {}".format(image_id))

        sequence_id = '{}_{}_{}'.format(
            self.config['name'],
            self.uid,
            observation.seq_time
        )

        # check if it is a pointing image
        is_pointing = ('POINTING' in headers) and (headers["POINTING"] == "True")

        # get values
        exp_time = kwargs.get('exp_time', observation.time_per_exposure)
        gain = observation.configuration["gain"]
        temperature = observation.configuration["temperature"]
        filter_name = observation.configuration.get("filter", "no-filter")

        # Camera metadata
        metadata = {
            'camera_name': self.name,
            'observation_id': observation.id,
            'camera_uid': self.uid,
            'target_name': observation.name,
            'file_path': file_path,
            'filter': filter_name,
            'image_id': image_id,
            'is_primary': self.is_primary,
            'sequence_id': sequence_id,
            'start_time': start_time,
            'exp_time': exp_time,
            'temperature_degC' : temperature
        }
        metadata.update(headers)
        return (exp_time, gain, temperature, file_path, image_id, metadata,
            is_pointing)

    def take_calibration(self, temperature, gain, exp_time, headers=None,
                  calibration_ref=None, calibration_name="unknown_calibration",
                  observations=None, filename=None, *args, **kwargs):
        # To be used for marking when exposure is complete
        # (see `process_calibration`)
        calib_event = Event()

        file_path, metadata = self._setup_calibration(temperature,
           gain,  exp_time, headers, calibration_ref, calibration_name,
           observations, filename, *args, **kwargs)
 
        exposure_event = self.take_calibration_exposure(exposure_time=exp_time,
            filename=file_path, *args, **kwargs)

        # Process the exposure once readout is complete
        t = Thread(target=self.process_calibration, args=(metadata,
            calib_event, exposure_event))
        t.name = f"{self.name}_Thread"
        t.start()

        return calib_event

    def get_calibration_directory(self, temperature, gain, exp_time,
        calibration_ref=None, filename=None,
        calibration_name='unknown_calibration'):
        if headers is None:
            headers = {}
        if calibration_ref is None:
            calibration_name += ('-' + calibration_ref)

        start_time = headers.get('start_time', self.serv_time.flat_time())

        # Get the filepath
        image_dir = "{}/calibration/{}/{}".format(
            self._image_dir,
            calibration_name,
            self.uid
        )
        os.makedirs(image_dir, exist_ok=True)

        # Get full file path with filename
        if filename is None:
            file_path = "{}/{}_{}_{}_{}.{}".format(image_dir,
                                          start_time,
                                          temperature,
                                          gain,
                                          exp_time.to(u.second).value,
                                          self.file_extension)
        else:
            # Add extension
            if '.' not in filename:
                filename = '{}.{}'.format(filename, self.file_extension)

            # Add directory
            if '/' not in filename:
                filename = '{}/{}'.format(image_dir, filename)

            file_path = filename
        return file_path

    def _setup_calibration(self, temperature, gain, exp_time,
                                headers=None, calibration_ref=None,
                                calibration_name='unknown_calibration',
                                observations=[], filename=None, **kwargs):
        """
            parameter can be temperature for dark or filter for flat ?
        """
        file_path = self.get_calibration_directory(temperature, gain,
            exp_time, calibration_ref, calibration_name, filename)

        # Camera metadata
        metadata = {
            'camera_name': self.name,
            'camera_uid': self.uid,
            'calibration_name': calibration_name,
            'file_path': file_path,
            'image_id': image_id,
            'is_primary': self.is_primary,
            'sequence_id': sequence_id,
            'start_time': start_time,
            'exp_time' : exp_time.to(u.second).value,
            'gain': gain,
            'temperature_degC': temperature.to(u.Celsius).value,
            'observation_ids': [o.id for o in observations]
        }
        metadata.update(headers)
        return file_path, metadata

    def take_exposure(self, *args, **kwargs):
        """ Must be implemented"""
        raise NotImplementedError

    def take_calibration_exposure(self, *args, **kwargs):
        try:
            exp_meth = f"take_{kwargs['calibration_name']}_exposure"
            return self.__getattribute__(exp_meth)(*args, **kwargs)
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

        If the camera is a primary camera, extract the jpeg image and save
        metadata to mongo `current` collection. Saves metadata to mongo
        `observations` collection for all images.

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
        title=info['target_name']
        primary=info['is_primary']
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

        if info['is_primary']:
            self.logger.debug(f"Adding current observation to db: {image_id}")
            try:
                self.db.insert_current('observations', info,
                                       store_permanently=False)
            except Exception as e:
                self.logger.error(f"Problem adding observation to db: {e}")
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
        """
        # If passed an Event that signals the end of the exposure wait for it
        # to be set
        if exposure_event is not None:
            exposure_event.wait()

        image_id = info['image_id']
        seq_id = info['sequence_id']
        title = info['target_name']
        primary = info['is_primary']
        observation_ids = info['observation_ids']
        del info['observation_ids']
        self.logger.debug(f"Processing {image_id}")

        file_path = self._process_fits(file_path, info)
        try:
            info['exp_time'] = info['exp_time'].to(u.second).value
        except Exception as e:
            self.logger.error(f"Problem getting exp_time information: {e}")

        if info['is_primary']:
            self.logger.debug("Adding current calibration to db: {}".format(
                              image_id))
            try:
                self.db.insert_current('calibrations', info,
                                       store_permanently=False)
            except Exception as e:
                self.logger.error(f"Problem adding calibration to db: {e}")
        else:
            self.logger.debug(f"Compressing {file_path}")
            fits_utils.fpack(file_path)

        self.logger.debug(f"Adding image metadata to db: {image_id}")

        # We are actually looping on each observation, so that a calibration is
        # actually featured once per observation
        if len(observation_ids)<1:
            observation_ids=[""]
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

