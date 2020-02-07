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
    def is_connected(self):
        """ Is the camera available vai gphoto2 """
        return self._connected

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
            **kwargs (dict): Optional keyword arguments (`exp_time`, dark)

        Returns:
            threading.Event: An event to be set when the image is done
                             processing
        """
        # To be used for marking when exposure is complete
        # (see `process_exposure`)
        observation_event = Event()

        exp_time, file_path, image_id, metadata = self._setup_observation(
            observation, headers, filename, *args, **kwargs)
       
        exposure_event = self.take_exposure(exposure_time=exp_time,
            filename=file_path, *args, **kwargs)

        # Add most recent exposure to list
        if self.is_primary:
            observation.exposure_list[image_id] = file_path

        # Process the exposure once readout is complete
        t = Thread(target=self.process_exposure, args=(metadata,
            observation_event, exposure_event))
        t.name = '{}Thread'.format(self.name)
        t.start()

        return observation_event

    def _setup_observation(self, observation, headers, filename, **kwargs):
        if headers is None:
            headers = {}

        start_time = headers.get('start_time', self.serv_time.flat_time())

        # Get the filepath
        image_dir = "{}/targets/{}/{}/{}".format(
            self.config['directories']['images'],
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

        # Camera metadata
        metadata = {
            'camera_name': self.name,
            'camera_uid': self.uid,
            'target_name': observation.name,
            'file_path': file_path,
            'filter': self.filter_type,
            'image_id': image_id,
            'is_primary': self.is_primary,
            'sequence_id': sequence_id,
            'start_time': start_time,
        }
        metadata.update(headers)

        exp_time = kwargs.get('exp_time', observation.time_per_exposure)

        metadata['exp_time'] = exp_time.to(u.second).value

        return exp_time, file_path, image_id, metadata

    def take_dark(self, temperature, exp_time, headers=None,
                  calibration_ref=None, filename=None,
                  *args, **kwargs):
        # To be used for marking when exposure is complete
        # (see `process_calibration`)
        dark_event = Event()

        file_path, metadata = self._setup_dark_calibration(temperature,
            exp_time, headers, calibration_ref, filename,
            *args, **kwargs)
 
        exposure_event = self.take_dark_exposure(exposure_time=exp_time,
            filename=file_path, *args, **kwargs)

        # Process the exposure once readout is complete
        t = Thread(target=self.process_calibration, args=(metadata,
            dark_event, exposure_event))
        t.name = '{}Thread'.format(self.name)
        t.start()

        return dark_event

    def get_dark_calibration_directory(self, temperature, exp_time,
                                calibration_ref=None, filename=None):
        calibration_name='dark'
        if headers is None:
            headers = {}
        if calibration_ref is None:
            calibration_name += ('-' + calibration_ref)

        start_time = headers.get('start_time', self.serv_time.flat_time())

        # Get the filepath
        image_dir = "{}/calibration/{}/{}/{}/{}".format(
            self.config['directories']['images'],
            calibration_name,
            self.uid,
            temperature,
            exp_time.to(u.second).value
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
        return file_path

    def _setup_dark_calibration(self, temperature, exp_time,
                                headers=None, calibration_ref=None,
                                filename=None, **kwargs):
        """
            parameter can be temperature for dark or filter for flat ?
        """
        file_path = self.get_dark_calibration_directory(temperature, exp_time,
            calibration_ref, filename)

        # Camera metadata
        metadata = {
            'camera_name': self.name,
            'camera_uid': self.uid,
            'target_name': 'dark_calibration',
            'file_path': file_path,
            'image_id': image_id,
            'is_primary': self.is_primary,
            'sequence_id': sequence_id,
            'start_time': start_time,
            'exp_time' : exp_time.to(u.second).value,
            'temperature_target_degC' : temperature.to(u.Celsius).value,
            'temperature_actual_degC' : self.get_temperature().to(u.Celsius).value
        }
        metadata.update(headers)
        return file_path, metadata

    def take_exposure(self, *args, **kwargs):
        """ Must be implemented"""
        raise NotImplementedError
    def take_bias_exposure(self, *args, **kwargs):
        return take_exposure(args, kwargs)
    def take_dark_exposure(self, *args, **kwargs):
        return take_exposure(args, kwargs)
    def take_flat_exposure(self, *args, **kwargs):
        return take_exposure(args, kwargs)
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
        seq_id = info['sequence_id']
        file_path = info['file_path']
        title=info['target_name']
        primary=info['is_primary']
        self.logger.debug("Processing {}".format(image_id))

        try:
            latest_path = '{}/latest.jpg'.format(
                self.config['directories']['images'])
            fits_utils.update_thumbnail(file_path, latest_path)
        except Exception as e:
            self.logger.warning('Problem with extracting pretty image: '
                                '{}'.format(e))

        file_path = self._process_fits(file_path, info)
        try:
            info['exp_time'] = info['exp_time'].value
        except Exception:
            pass

        if info['is_primary']:
            self.logger.debug("Adding current observation to db: {}".format(
                              image_id))
            try:
                self.db.insert_current('observations', info,
                                       store_permanently=False)
            except Exception as e:
                self.logger.error('Problem adding observation to db: {}'
                                  ''.format(e))
        else:
            self.logger.debug('Compressing {}'.format(file_path))
            fits_utils.fpack(file_path)

        self.logger.debug("Adding image metadata to db: {}".format(image_id))

        self.db.insert('observations', {
            'data': info,
            'date': self.serv_time.get_utc(),
            'sequence_id': seq_id,
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
        title=info['target_name']
        primary=info['is_primary']
        self.logger.debug("Processing {}".format(image_id))

        file_path = self._process_fits(file_path, info)
        try:
            info['exp_time'] = info['exp_time'].value
        except Exception:
            pass

        if info['is_primary']:
            self.logger.debug("Adding current calibration to db: {}".format(
                              image_id))
            try:
                self.db.insert_current('calibrations', info,
                                       store_permanently=False)
            except Exception as e:
                self.logger.error('Problem adding calibration to db: {}'
                                  ''.format(e))
        else:
            self.logger.debug('Compressing {}'.format(file_path))
            fits_utils.fpack(file_path)

        self.logger.debug("Adding image metadata to db: {}".format(image_id))

        self.db.insert('calibrations', {
            'data': info,
            'date': self.serv_time.get_utc(),
            'sequence_id': seq_id,
        })

        # Mark the event as done
        observation_event.set()
    def _process_fits(self, file_path, info):
        """
        Add FITS headers from info the same as images.cr2_to_fits()
        """
        self.logger.debug("Updating FITS headers: {}".format(file_path))
        fits_utils.update_headers(file_path, info)
        return file_path

