# Generic
import logging

# Local
from Base.Base import Base
from utils import error

class AbstractCamera(Base):


    def __init__(self, primary=False, *args,  **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self._image_dir = self.config['directories']['images']
        except KeyError:
            self.logger.error("No images directory. Set image_dir in config")

        self.is_primary = primary

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
            threading.Event: An event to be set when the image is done processing
        """
        # To be used for marking when exposure is complete (see `process_exposure`)
        observation_event = Event()

        exp_time, file_path, image_id, metadata = self._setup_observation(observation,
                                                                          headers,
                                                                          filename,
                                                                          *args,
                                                                          **kwargs)

        exposure_event = self.take_exposure(seconds=exp_time, filename=file_path, *args, **kwargs)

        # Add most recent exposure to list
        if self.is_primary:
            observation.exposure_list[image_id] = file_path

        # Process the exposure once readout is complete
        t = Thread(target=self.process_exposure, args=(metadata, observation_event, exposure_event))
        t.name = '{}Thread'.format(self.name)
        t.start()

        return observation_event

    def take_exposure(self, *args, **kwargs):
        raise NotImplementedError

    def process_exposure(self, info, observation_event, exposure_event=None):
        """
        Processes the exposure.

        If the camera is a primary camera, extract the jpeg image and save metadata to mongo
        `current` collection. Saves metadata to mongo `observations` collection for all images.

        Args:
            info (dict): Header metadata saved for the image
            observation_event (threading.Event): An event that is set signifying that the
                camera is done with this exposure
            exposure_event (threading.Event, optional): An event that should be set
                when the exposure is complete, triggering the processing.
        """
        # If passed an Event that signals the end of the exposure wait for it to be set
        if exposure_event is not None:
            exposure_event.wait()

        image_id = info['image_id']
        seq_id = info['sequence_id']
        file_path = info['file_path']
        self.logger.debug("Processing {}".format(image_id))

        try:
            self.logger.debug("Extracting pretty image")
            img_utils.make_pretty_image(file_path,
                                        title=info['field_name'],
                                        primary=info['is_primary'])
        except Exception as e:
            self.logger.warning('Problem with extracting pretty image: {}'.format(e))

        file_path = self._process_fits(file_path, info)
        try:
            info['exp_time'] = info['exp_time'].value
        except Exception:
            pass

        if info['is_primary']:
            self.logger.debug("Adding current observation to db: {}".format(image_id))
            try:
                self.db.insert_current('observations', info, store_permanently=False)
            except Exception as e:
                self.logger.error('Problem adding observation to db: {}'.format(e))
        else:
            self.logger.debug('Compressing {}'.format(file_path))
            fits_utils.fpack(file_path)

        self.logger.debug("Adding image metadata to db: {}".format(image_id))

        self.db.insert('observations', {
            'data': info,
            'date': current_time(datetime=True),
            'sequence_id': seq_id,
        })

        # Mark the event as done
        observation_event.set()

