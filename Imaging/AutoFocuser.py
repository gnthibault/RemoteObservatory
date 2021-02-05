# Generic stuff
from copy import copy
import os
from threading import Event
from threading import Thread

# Numerical stuff
from astropy.modeling import models, fitting
import numpy as np
import skimage.morphology

# Viz
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.colors as colours
from matplotlib.figure import Figure
from matplotlib import cm as colormap

# Local stuff
from Base.Base import Base

class AutoFocuser(Base):
    """
    Base class for autofocusing

    Args:
        camera (Camera, optional): camera that this focuser is associated with.
        initial_position (int, optional): if given the focuser will move to this position
            following initialisation.
        autofocus_range ((int, int) optional): Coarse & fine focus sweep range, in encoder units
        autofocus_step ((int, int), optional): Coarse & fine focus sweep steps, in encoder units
        autofocus_seconds (scalar, optional): Exposure time for focus exposures
        autofocus_size (int, optional): Size of square central region of image to use, default
            500 x 500 pixels.
        autofocus_keep_files (bool, optional): If True will keep all images taken during focusing.
            If False (default) will delete all except the first and last images from each focus run.
        autofocus_take_dark (bool, optional): If True will attempt to take a dark frame before the
            focus run, and use it for dark subtraction and hot pixel masking, default True.
        autofocus_merit_function (str/callable, optional): Merit function to use as a focus metric,
            default vollath_F4
        autofocus_merit_function_kwargs (dict, optional): Dictionary of additional keyword arguments
            for the merit function.
        autofocus_structuring_element (int, optional): Number of iterations of dilation to perform on the
            saturated pixel mask (determine size of masked regions), default 10
    """

    def __init__(self,
                 camera=None,
                 initial_position=None,
                 autofocus_seconds=None,
                 autofocus_size=None,
                 autofocus_keep_files=None,
                 autofocus_take_dark=None,
                 autofocus_merit_function=None,
                 autofocus_merit_function_kwargs=None,
                 autofocus_structuring_element=None,
                 *args, **kwargs):
        super().__init__(self, args, kwargs)

        self.camera = camera

        if initial_position is None:
            self._position = None
        else:
            self._position = int(initial_position)

        if self.camera.focuser is not None:
            self.autofocus_range = {
                "coarse" : self.camera.focuser.autofocus_range["coarse"],
                "fine" : self.camera.focuser.autofocus_range["fine"]}
        else:
            self.autofocus_range = None

        if self.camera.focuser is not None:
            self.autofocus_step = {
                "coarse": self.camera.focuser.autofocus_step["coarse"],
                "fine": self.camera.focuser.autofocus_step["fine"]}
        else:
            self.autofocus_step = None

        if self.camera is not None:
            self.autofocus_seconds = self.camera.autofocus_seconds
        if self.camera is not None:
            self.autofocus_size = self.camera.autofocus_size

        self.autofocus_keep_files = autofocus_keep_files
        self.autofocus_take_dark = autofocus_take_dark
        self.autofocus_merit_function = autofocus_merit_function
        self.autofocus_merit_function_kwargs = autofocus_merit_function_kwargs
        self.autofocus_structuring_element = autofocus_structuring_element

        self.logger.debug(f"AutoFocuser successfully created with camera "
                          f"{self.camera.device_name} and focuser "
                          f"{self.camera.focuser.device_name}")

##################################################################################################
# Properties
##################################################################################################
    @property
    def uid(self):
        """ Serial number of the focuser """
        raise NotImplementedError

    @property
    def model(self):
        """ Model of the focuser """
        raise NotImplementedError

    @property
    def name(self):
        """ Name of the focuser """
        raise NotImplementedError

    @property
    def position(self):
        """ Current encoder position of the focuser """
        return self._position

    @position.setter
    def position(self, position):
        """ Move focusser to new encoder position """
        self.move_to(position)

    @property
    def min_position(self):
        """ Get position of close limit of focus travel, in encoder units """
        raise NotImplementedError

    @property
    def max_position(self):
        """ Get position of far limit of focus travel, in encoder units """
        raise NotImplementedError

##################################################################################################
# Methods
##################################################################################################

    def move_to(self, position):
        """ Move focuser to new encoder position """
        raise NotImplementedError

    def move_by(self, increment):
        """ Move focuser by a given amount """
        return self.move_to(self.position + increment)

    def autofocus(self,
                  seconds=None,
                  focus_range=None,
                  focus_step=None,
                  thumbnail_size=None,
                  keep_files=None,
                  take_dark=None,
                  merit_function=None,
                  merit_function_kwargs=None,
                  structuring_element=None,
                  coarse=False,
                  make_plots=False,
                  blocking=False):
        """
        Focuses the camera using the specified merit function. Optionally performs
        a coarse focus to find the approximate position of infinity focus, which
        should be followed by a fine focus before observing.

        Args:
            seconds (scalar, optional): Exposure time for focus exposures, if not
                specified will use value from config.
            focus_range (dictionary, optional): Coarse & fine focus sweep range, in
                encoder units. Specify to override values from config.
            focus_step (dictionary, optional): Coarse & fine focus sweep steps, in
                encoder units. Specify to override values from config.
            thumbnail_size (int, optional): Size of square central region of image
                to use, default 500 x 500 pixels.
            keep_files (bool, optional): If True will keep all images taken
                during focusing. If False (default) will delete all except the
                first and last images from each focus run.
            take_dark (bool, optional): If True will attempt to take a dark frame
                before the focus run, and use it for dark subtraction and hot
                pixel masking, default True.
            merit_function (str/callable, optional): Merit function to use as a
                focus metric, default vollath_F4.
            merit_function_kwargs (dict, optional): Dictionary of additional
                keyword arguments for the merit function.
            structuring_element (int, optional): Number of iterations of dilation to perform on the
                saturated pixel mask (determine size of masked regions), default 10
            coarse (bool, optional): Whether to perform a coarse focus, otherwise will perform
                a fine focus. Default False.
            make_plots (bool, optional: Whether to write focus plots to images folder, default
                False.
            blocking (bool, optional): Whether to block until autofocus complete, default False.

        Returns:
            threading.Event: Event that will be set when autofocusing is complete

        Raises:
            ValueError: If invalid values are passed for any of the focus parameters.
        """
        self.logger.debug('Starting autofocus')
        assert self.camera.is_connected, self.logger.error(
            f"Camera {self.camera} must be connected for autofocus")
        assert self.camera.focuser.is_connected, self.logger.error(
            f"Focuser {self.camera.focuser} must be connected for autofocus")

        if not focus_range:
            if self.autofocus_range:
                focus_range = self.autofocus_range
            else:
                raise ValueError(f"No focus_range specified, aborting autofocus"
                                 f" of {self.camera}")

        if not focus_step:
            if self.autofocus_step:
                focus_step = self.autofocus_step
            else:
                raise ValueError("No focus_step specified, aborting autofocus "
                                 f"of {self.camera}")

        if not seconds:
            if self.autofocus_seconds:
                seconds = self.autofocus_seconds
            else:
                raise ValueError(f"No focus exposure time specified, aborting "
                                 f"autofocus of {self.camera}")

        if not thumbnail_size:
            if self.autofocus_size:
                thumbnail_size = self.autofocus_size
            else:
                raise ValueError(f"No focus thumbnail size specified, aborting"
                                 f" autofocus of {self.camera}")

        if keep_files is None:
            if self.autofocus_keep_files:
                keep_files = True
            else:
                keep_files = False

        if take_dark is None:
            if self.autofocus_take_dark is not None:
                take_dark = self.autofocus_take_dark
            else:
                take_dark = False

        if not merit_function:
            if self.autofocus_merit_function:
                merit_function = self.autofocus_merit_function
            else:
                merit_function = 'vollath_F4'

        if not merit_function_kwargs:
            if self.autofocus_merit_function_kwargs:
                merit_function_kwargs = self.autofocus_merit_function_kwargs
            else:
                merit_function_kwargs = {}

        if structuring_element is None:
            if self.autofocus_structuring_element is not None:
                structuring_element = self.autofocus_structuring_element
            else:
                structuring_element = skimage.morphology.diamond(radius=10)

        # Set up the focus parameters
        focus_event = Event()
        focus_params = {
            'seconds': seconds,
            'focus_range': focus_range,
            'focus_step': focus_step,
            'thumbnail_size': thumbnail_size,
            'keep_files': keep_files,
            'take_dark': take_dark,
            'merit_function': merit_function,
            'merit_function_kwargs': merit_function_kwargs,
            'structuring_element': structuring_element,
            'coarse': coarse,
            'make_plots': make_plots,
            'focus_event': focus_event,
        }
        focus_thread = Thread(target=self._autofocus, kwargs=focus_params)
        focus_thread.start()
        if blocking:
            focus_event.wait()
        return focus_event

    def get_thumbnail(self, seconds, thumbnail_size):
        fits = self.camera.get_thumbnail(seconds, thumbnail_size)
        try:
            image = fits.data
        except:
            image = fits[0].data
        return image

    def _autofocus(self,
                   seconds,
                   focus_range,
                   focus_step,
                   thumbnail_size,
                   keep_files,
                   take_dark,
                   merit_function,
                   merit_function_kwargs,
                   structuring_element,
                   make_plots,
                   coarse,
                   focus_event,
                   *args,
                   **kwargs):
        """Private helper method for calling autofocus in a Thread.

        See public `autofocus` for information about the parameters.
        """
        focus_type = 'fine'
        if coarse:
            focus_type = 'coarse'

        initial_focus = self.position
        self.logger.debug(f"Beginning {focus_type} autofocus of {self.camera}"
                          f" - initial position: {initial_focus}")

        # Set up paths for temporary focus files, and plots if requested.
        image_dir = self.config['directories']['images']
        start_time = self.db.serv_time.flat_time()
        file_path_root = os.path.join(image_dir,
                                      'focus',
                                      self.camera.name,
                                      start_time)
        os.makedirs(file_path_root, exist_ok=True)

        # dark_thumb = None
        # if take_dark:
        #     dark_path = os.path.join(file_path_root,
        #                              '{}.{}'.format('dark', self.camera.file_extension))
        #     self.logger.debug('Taking dark frame {} on camera {}'.format(dark_path, self.camera))
        #     try:
        #         dark_thumb = self.get_thumbnail(seconds,
        #                                                 dark_path,
        #                                                 thumbnail_size,
        #                                                 keep_file=True,
        #                                                 dark=True)
        #         # Mask 'saturated' with a low threshold to remove hot pixels
        #         dark_thumb = self.mask_saturated(dark_thumb, threshold=0.3)
        #     except TypeError:
        #         self.logger.warning("Camera {} does not support dark frames!".format(self.camera))

        # Take an image before focusing, grab a thumbnail from the centre and add it to the plot
        # initial_fn = "{}_{}_{}.{}".format(initial_focus,
        #                                   focus_type,
        #                                   "initial",
        #                                   self.camera.file_extension)
        # initial_path = os.path.join(file_path_root, initial_fn)
        #
        initial_thumbnail = self.get_thumbnail(seconds, thumbnail_size)

        # Set up encoder positions for autofocus sweep, truncating at focus travel
        # limits if required.
        if coarse:
            focus_range = focus_range["coarse"]
            focus_step = focus_step["coarse"]
        else:
            focus_range = focus_range["fine"]
            focus_step = focus_step["fine"]

        self.logger.debug(f"Initial focus is {initial_focus} minus range/2 "
                          f"gives {initial_focus - focus_range / 2}")
        self.logger.debug(f"Initial focus is {initial_focus} plus range/2 gives "
                          f"{initial_focus + focus_range / 2}")
        self.logger.debug(f"Min position is {self.min_position} and "
                          f"Max position is {self.max_position}")
        self.logger.debug(f"Focus step is {focus_step}")

        focus_positions = np.arange(max(initial_focus - focus_range / 2, self.min_position),
                                    min(initial_focus + focus_range / 2, self.max_position) + 1,
                                    focus_step, dtype=np.int)
        self.logger.debug(f"Autofocuser {self}  is going to sweep over the "
                          f"following positions for autofocusing "
                          f"{focus_positions}")
        n_positions = len(focus_positions)

        thumbnails = np.zeros((n_positions, thumbnail_size, thumbnail_size),
                              dtype=initial_thumbnail.dtype)
        masks = np.empty((n_positions, thumbnail_size, thumbnail_size),
                         dtype=np.bool)
        metric = np.empty(n_positions)

        # Take and store an exposure for each focus position.
        for i, position in enumerate(focus_positions):
            # Move focus, updating focus_positions with actual encoder position after move.
            focus_positions[i] = self.move_to(position)

            # Take exposure
            # focus_fn = "{}_{:02d}.{}".format(focus_positions[i], i, self.camera.file_extension)
            # file_path = os.path.join(file_path_root, focus_fn)
            #
            thumbnail = self.get_thumbnail(seconds, thumbnail_size)
            masks[i] = self.mask_saturated(thumbnail).mask
            # if dark_thumb is not None:
            #     thumbnail = thumbnail - dark_thumb
            thumbnails[i] = thumbnail

        master_mask = masks.any(axis=0)
        master_mask = skimage.morphology.binary_dilation(master_mask,
            selem=structuring_element)

        # Apply the master mask and then get metrics for each frame.
        for i, thumbnail in enumerate(thumbnails):
            thumbnail = np.ma.array(thumbnail, mask=master_mask)
            metric[i] = self.focus_metric(
                thumbnail, merit_function, **merit_function_kwargs)
        fitted = False

        # Find best values
        ibest = metric.argmin()

        if ibest == 0 or ibest == (n_positions - 1):
            # TODO: have this automatically switch to coarse focus mode if this happens
            self.logger.warning(f"Best focus outside sweep range, aborting "
                                f"autofocus on {self.camera}!")
            best_focus = focus_positions[ibest]

        elif not coarse:
            # Fit data around the maximum value to determine best focus position.
            # Initialise models
            shift = models.Shift(offset=-focus_positions[ibest])
            poly = models.Polynomial1D(degree=4, c0=1, c1=0, c2=-1e-2, c3=0, c4=-1e-4,
                                       fixed={'c0': True, 'c1': True, 'c3': True})
            #poly = models.Polynomial1D(degree=2)
            scale = models.Scale(factor=metric[ibest])
            reparameterised_polynomial = shift | poly | scale

            # Initialise fitter
            fitter = fitting.LevMarLSQFitter()

            # Select data range for fitting. Tries to use points on both side of
            # max, if in range.
            margin = max(3, np.int(np.ceil(n_positions/3)))
            fitting_indices = (max(ibest - margin, 0), min(ibest + margin, n_positions - 1))

            # Fit models to data
            fit = fitter(reparameterised_polynomial,
                         focus_positions[fitting_indices[0]:fitting_indices[1] + 1],
                         metric[fitting_indices[0]:fitting_indices[1] + 1])

            best_focus = -fit.offset_0
            fitted = True

            # Guard against fitting failures, force best focus to stay within sweep range
            min_focus = focus_positions[0]
            max_focus = focus_positions[-1]
            if best_focus < min_focus:
                self.logger.warning(f"Fitting failure: best focus {best_focus} "
                                    f"below sweep limit {min_focus}")
                best_focus = focus_positions[1]

            if best_focus > max_focus:
                self.logger.warning(f"Fitting failure: best focus {best_focus} "
                                    f"above sweep limit {max_focus}")
                best_focus = focus_positions[-2]

        else:
            # Coarse focus, just use max value.
            best_focus = focus_positions[ibest]

        # This allows to remove effects of backlas
        reset_focus = self.move_to(focus_positions[0])
        final_focus = self.move_to(best_focus)

        #final_fn = "{}_{}_{}.{}".format(final_focus,
        #                                focus_type,
        #                                "final",
        #                                self.camera.file_extension)
        final_thumbnail = self.get_thumbnail(seconds, thumbnail_size)

        if make_plots:
            initial_thumbnail = self.mask_saturated(initial_thumbnail)
            final_thumbnail = self.mask_saturated(final_thumbnail)
            #if dark_thumb is not None:
            #    initial_thumbnail = initial_thumbnail - dark_thumb
            #    final_thumbnail = final_thumbnail - dark_thumb

            fig, ax = plt.subplots(1,3,figsize=(22, 7))

            im1 = ax[0].imshow(initial_thumbnail, interpolation='none',
                             cmap=self.get_palette(), norm=colours.LogNorm())
            fig.colorbar(im1,  ax=ax[0])
            ax[0].set_title('Initial focus position: {}'.format(initial_focus))
            ax[1].plot(focus_positions, metric, 'bo', label='{}'.format(merit_function))
            if fitted:
                fs = np.linspace(focus_positions[fitting_indices[0]],
                                 focus_positions[fitting_indices[1]],
                                 100)
                ax[1].plot(fs, fit(fs), 'b-', label='Polynomial fit')

            ax[1].set_xlim(focus_positions[0] - focus_step / 2, focus_positions[-1] + focus_step / 2)
            u_limit = 1.10 * metric.max()
            l_limit = min(0.95 * metric.min(), 1.05 * metric.min())
            ax[1].set_ylim(l_limit, u_limit)
            ax[1].vlines(initial_focus, l_limit, u_limit, colors='k', linestyles=':',
                         label='Initial focus')
            ax[1].vlines(best_focus, l_limit, u_limit, colors='k', linestyles='--',
                         label='Best focus')

            ax[1].set_xlabel('Focus position')
            ax[1].set_ylabel('Focus metric')

            ax[1].set_title(f"{self.camera.name} {focus_type} focus at "
                            f"{start_time}")
            ax[1].legend(loc='best')

            im3 = ax[2].imshow(final_thumbnail, interpolation='none',
                             cmap=self.get_palette(), norm=colours.LogNorm())
            fig.colorbar(im3, ax=ax[2])
            ax[2].set_title('Final focus position: {}'.format(final_focus))
            plot_path = os.path.join(file_path_root, '{}_focus.png'.format(focus_type))

            fig.tight_layout()
            latest_path = '{}/latest_focus.jpg'.format(
                self.config['directories']['images'])
            fig.savefig(plot_path, transparent=False)
            fig.savefig(latest_path, transparent=False)

            # explicitly close and delete figure
            fig.clf()
            del fig

            self.logger.info(f"{focus_type.capitalize()} focus plot for camera "
                             f"{self.camera.name} written to {plot_path}")

        self.logger.debug(f"Autofocus of {self.camera.name} complete - final "
                          f"focus position: {final_focus}")

        if focus_event:
            focus_event.set()

        return initial_focus, final_focus

    def _add_fits_keywords(self, header):
        header.set('FOC-NAME', self.name, 'Focuser name')
        header.set('FOC-MOD', self.model, 'Focuser model')
        header.set('FOC-ID', self.uid, 'Focuser serial number')
        header.set('FOC-POS', self.position, 'Focuser position')
        return header

    def focus_metric(self, data, merit_function='vollath_F4', **kwargs):
        """Compute the focus metric.

        Computes a focus metric on the given data using a supplied merit function.
        The merit function can be passed either as the name of the function (must be
        defined in this module) or as a callable object. Additional keyword arguments
        for the merit function can be passed as keyword arguments to this function.

        Args:
            data (numpy array) -- 2D array to calculate the focus metric for.
            merit_function (str/callable) -- Name of merit function (if in
                pocs.utils.images) or a callable object.

        Returns:
            scalar: result of calling merit function on data
        """
        if isinstance(merit_function, str):
            try:
                merit_function = self.__getattribute__(merit_function)
            except KeyError:
                raise KeyError(f"Focus merit function {merit_function} not "
                               f"found in AutoFocuser")

        return merit_function(data, **kwargs)


    def vollath_F4(self, data, axis=None):
        """Compute F4 focus metric

        Computes the F_4 focus metric as defined by Vollath (1998) for the given 2D
        numpy array. The metric can be computed in the y axis, x axis, or the mean of
        the two (default).

        Arguments:
            data (numpy array) -- 2D array to calculate F4 on.
            axis (str, optional, default None) -- Which axis to calculate F4 in. Can
                be 'Y'/'y', 'X'/'x' or None, which will calculate the F4 value for
                both axes and return the mean.

        Returns:
            float64: Calculated F4 value for y, x axis or both
        """
        if axis == 'Y' or axis == 'y':
            return self._vollath_F4_y(data)
        elif axis == 'X' or axis == 'x':
            return self._vollath_F4_x(data)
        elif not axis:
            return (self._vollath_F4_y(data) + self._vollath_F4_x(data)) / 2
        else:
            raise ValueError(f"axis must be one of 'Y', 'y', 'X', 'x' or None, "
                             f"got {axis}!")


    def mask_saturated(self, data, saturation_level=None, threshold=0.9,
                       dtype=np.float64):
        if not saturation_level:
            try:
                # If data is an integer type use iinfo to compute machine limits
                dynamic = self.camera.dynamic
            except ValueError:
                # Not an integer type. Assume for now we have 16 bit data
                dynamic = 2 ** 16
            saturation_level = threshold * (dynamic - 1)

        # Convert data to masked array of requested dtype, mask values above saturation level
        return np.ma.array(data, mask=(data > saturation_level), dtype=dtype)


    def _vollath_F4_y(self, data):
        A1 = (data[1:] * data[:-1]).mean()
        A2 = (data[2:] * data[:-2]).mean()
        return A1 - A2


    def _vollath_F4_x(self, data):
        A1 = (data[:, 1:] * data[:, :-1]).mean()
        A2 = (data[:, 2:] * data[:, :-2]).mean()
        return A1 - A2

    def get_palette(self, cmap='inferno'):
        """Get a palette for drawing.

        Returns a copy of the colormap palette with bad pixels marked.

        Args:
            cmap (str, optional): Colormap to use, default 'inferno'.

        Returns:
            `matplotlib.cm`: The colormap.
        """
        palette = copy(getattr(colormap, cmap))

        # Mark bad pixels (e.g. saturated)
        # when using vmin or vmax and a normalizer.
        palette.set_over('w', 1.0)
        palette.set_under('k', 1.0)
        palette.set_bad('g', 1.0)

        return palette

    def __str__(self):
        return f"Focuser {self.name} (uid {self.uid}) model {self.model}"
