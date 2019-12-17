# Generic stuff
from threading import Event
from threading import Thread

# Numerical stuff
import numpy as np

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
        autofocus_mask_dilations (int, optional): Number of iterations of dilation to perform on the
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
                 autofocus_mask_dilations=None,
                 *args, **kwargs):
        super().__init__(self, args, kwargs)

        if initial_position is None:
            self._position = None
        else:
            self._position = int(initial_position)

        if self._camera.focuser is not None:
            self.autofocus_range = (
                int(self._camera.focuser.autofocus_range["coarse"]),
                int(self._camera.focuser.autofocus_range["fine"]))
        else:
            self.autofocus_range = None

        if autofocus_step:
            self.autofocus_step = (
                int(self._camera.focuser.autofocus_step["coarse"]),
                int(self._camera.focuser.autofocus_step["fine"]))
        else:
            self.autofocus_step = None

        self.autofocus_seconds = autofocus_seconds
        self.autofocus_size = autofocus_size
        self.autofocus_keep_files = autofocus_keep_files
        self.autofocus_take_dark = autofocus_take_dark
        self.autofocus_merit_function = autofocus_merit_function
        self.autofocus_merit_function_kwargs = autofocus_merit_function_kwargs
        self.autofocus_mask_dilations = autofocus_mask_dilations

        self._camera = camera

        self.logger.debug(f"AutoFocuser successfully created with camera "
                          f"{self._camera.device_name} and focuser "
                          f"{self._camera.focuser.device_name}")

##################################################################################################
# Properties
##################################################################################################
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
                  mask_dilations=None,
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
            focus_range (2-tuple, optional): Coarse & fine focus sweep range, in
                encoder units. Specify to override values from config.
            focus_step (2-tuple, optional): Coarse & fine focus sweep steps, in
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
            mask_dilations (int, optional): Number of iterations of dilation to perform on the
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
        assert self._camera.is_connected, self.logger.error(
            f"Camera {self._camera} must be connected for autofocus")
        assert self._camera.focuser.is_connected, self.logger.error(
            f"Focuser {self._camera.focuser} must be connected for autofocus")

        if not focus_range:
            if self.autofocus_range:
                focus_range = self.autofocus_range
            else:
                raise ValueError(f"No focus_range specified, aborting autofocus"
                                 f" of {self._camera}")

        if not focus_step:
            if self.autofocus_step:
                focus_step = self.autofocus_step
            else:
                raise ValueError("No focus_step specified, aborting autofocus "
                                 f"of {self._camera}")

        if not seconds:
            if self.autofocus_seconds:
                seconds = self.autofocus_seconds
            else:
                raise ValueError(f"No focus exposure time specified, aborting "
                                 f"autofocus of {self._camera}")

        if not thumbnail_size:
            if self.autofocus_size:
                thumbnail_size = self.autofocus_size
            else:
                raise ValueError(f"No focus thumbnail size specified, aborting"
                                 f" autofocus of {self._camera}")

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

        if mask_dilations is None:
            if self.autofocus_mask_dilations is not None:
                mask_dilations = self.autofocus_mask_dilations
            else:
                mask_dilations = 10

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
            'mask_dilations': mask_dilations,
            'coarse': coarse,
            'make_plots': make_plots,
            'focus_event': focus_event,
        }
        focus_thread = Thread(target=self._autofocus, kwargs=focus_params)
        focus_thread.start()
        if blocking:
            focus_event.wait()
        return focus_event

    def _autofocus(self,
                   seconds,
                   focus_range,
                   focus_step,
                   thumbnail_size,
                   keep_files,
                   take_dark,
                   merit_function,
                   merit_function_kwargs,
                   mask_dilations,
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
        self.logger.debug(f"Beginning {focus_type} autofocus of {self._camera}"
                          f" - initial position: {initial_focus}")

        # Set up paths for temporary focus files, and plots if requested.
        # image_dir = self.config['directories']['images']
        # start_time = self.serv_time.get_current_time(flatten=True)
        # file_path_root = os.path.join(image_dir,
        #                               'focus',
        #                               self._camera.uid,
        #                               start_time)

        # dark_thumb = None
        # if take_dark:
        #     dark_path = os.path.join(file_path_root,
        #                              '{}.{}'.format('dark', self._camera.file_extension))
        #     self.logger.debug('Taking dark frame {} on camera {}'.format(dark_path, self._camera))
        #     try:
        #         dark_thumb = self._camera.get_thumbnail(seconds,
        #                                                 dark_path,
        #                                                 thumbnail_size,
        #                                                 keep_file=True,
        #                                                 dark=True)
        #         # Mask 'saturated' with a low threshold to remove hot pixels
        #         dark_thumb = focus_utils.mask_saturated(dark_thumb, threshold=0.3)
        #     except TypeError:
        #         self.logger.warning("Camera {} does not support dark frames!".format(self._camera))

        # Take an image before focusing, grab a thumbnail from the centre and add it to the plot
        # initial_fn = "{}_{}_{}.{}".format(initial_focus,
        #                                   focus_type,
        #                                   "initial",
        #                                   self._camera.file_extension)
        # initial_path = os.path.join(file_path_root, initial_fn)
        #
        initial_thumbnail = self._camera.get_thumbnail(
            seconds, initial_path, thumbnail_size, keep_file=True)

        # Set up encoder positions for autofocus sweep, truncating at focus travel
        # limits if required.
        if coarse:
            focus_range = focus_range[0]
            focus_step = focus_step[0]
        else:
            focus_range = focus_range[1]
            focus_step = focus_step[1]

        focus_positions = np.arange(max(initial_focus - focus_range / 2, self.min_position),
                                    min(initial_focus + focus_range / 2, self.max_position) + 1,
                                    focus_step, dtype=np.int)
        n_positions = len(focus_positions)

        thumbnails = np.zeros((n_positions, thumbnail_size, thumbnail_size),
                              dtype=initial_thumbnail.dtype)
        masks = np.empty((n_positions, thumbnail_size, thumbnail_size), dtype=np.bool)
        metric = np.empty(n_positions)

        # Take and store an exposure for each focus position.
        for i, position in enumerate(focus_positions):
            # Move focus, updating focus_positions with actual encoder position after move.
            focus_positions[i] = self.move_to(position)

            # Take exposure
            # focus_fn = "{}_{:02d}.{}".format(focus_positions[i], i, self._camera.file_extension)
            # file_path = os.path.join(file_path_root, focus_fn)
            #
            thumbnail = self._camera.get_thumbnail(
                seconds, file_path, thumbnail_size, keep_file=keep_files)
            masks[i] = focus_utils.mask_saturated(thumbnail).mask
            # if dark_thumb is not None:
            #     thumbnail = thumbnail - dark_thumb
            thumbnails[i] = thumbnail

        # master_mask = masks.any(axis=0)
        # master_mask = binary_dilation(master_mask, iterations=mask_dilations)

        # Apply the master mask and then get metrics for each frame.
        for i, thumbnail in enumerate(thumbnails):
            thumbnail = np.ma.array(thumbnail, mask=master_mask)
            metric[i] = focus_utils.focus_metric(
                thumbnail, merit_function, **merit_function_kwargs)

        fitted = False

        # Find maximum values
        imax = metric.argmax()

        if imax == 0 or imax == (n_positions - 1):
            # TODO: have this automatically switch to coarse focus mode if this happens
            self.logger.warning(
                "Best focus outside sweep range, aborting autofocus on {}!".format(self._camera))
            best_focus = focus_positions[imax]

        elif not coarse:
            # Fit data around the maximum value to determine best focus position.
            # Initialise models
            shift = models.Shift(offset=-focus_positions[imax])
            poly = models.Polynomial1D(degree=4, c0=1, c1=0, c2=-1e-2, c3=0, c4=-1e-4,
                                       fixed={'c0': True, 'c1': True, 'c3': True})
            scale = models.Scale(factor=metric[imax])
            reparameterised_polynomial = shift | poly | scale

            # Initialise fitter
            fitter = fitting.LevMarLSQFitter()

            # Select data range for fitting. Tries to use 2 points either side of max, if in range.
            fitting_indices = (max(imax - 2, 0), min(imax + 2, n_positions - 1))

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
                self.logger.warning("Fitting failure: best focus {} below sweep limit {}",
                                    best_focus,
                                    min_focus)

                best_focus = focus_positions[1]

            if best_focus > max_focus:
                self.logger.warning("Fitting failure: best focus {} above sweep limit {}",
                                    best_focus,
                                    max_focus)

                best_focus = focus_positions[-2]

        else:
            # Coarse focus, just use max value.
            best_focus = focus_positions[imax]

        final_focus = self.move_to(best_focus)

        final_fn = "{}_{}_{}.{}".format(final_focus,
                                        focus_type,
                                        "final",
                                        self._camera.file_extension)
        file_path = os.path.join(file_path_root, final_fn)
        final_thumbnail = self._camera.get_thumbnail(
            seconds, file_path, thumbnail_size, keep_file=True)

        if make_plots:
            initial_thumbnail = focus_utils.mask_saturated(initial_thumbnail)
            final_thumbnail = focus_utils.mask_saturated(final_thumbnail)
            if dark_thumb is not None:
                initial_thumbnail = initial_thumbnail - dark_thumb
                final_thumbnail = final_thumbnail - dark_thumb

            fig = Figure()
            FigureCanvas(fig)
            fig.set_size_inches(9, 18)

            ax1 = fig.add_subplot(3, 1, 1)
            im1 = ax1.imshow(initial_thumbnail, interpolation='none',
                             cmap=get_palette(), norm=colours.LogNorm())
            fig.colorbar(im1)
            ax1.set_title('Initial focus position: {}'.format(initial_focus))

            ax2 = fig.add_subplot(3, 1, 2)
            ax2.plot(focus_positions, metric, 'bo', label='{}'.format(merit_function))
            if fitted:
                fs = np.arange(focus_positions[fitting_indices[0]],
                               focus_positions[fitting_indices[1]] + 1)
                ax2.plot(fs, fit(fs), 'b-', label='Polynomial fit')

            ax2.set_xlim(focus_positions[0] - focus_step / 2, focus_positions[-1] + focus_step / 2)
            u_limit = 1.10 * metric.max()
            l_limit = min(0.95 * metric.min(), 1.05 * metric.min())
            ax2.set_ylim(l_limit, u_limit)
            ax2.vlines(initial_focus, l_limit, u_limit, colors='k', linestyles=':',
                       label='Initial focus')
            ax2.vlines(best_focus, l_limit, u_limit, colors='k', linestyles='--',
                       label='Best focus')

            ax2.set_xlabel('Focus position')
            ax2.set_ylabel('Focus metric')

            ax2.set_title('{} {} focus at {}'.format(self._camera, focus_type, start_time))
            ax2.legend(loc='best')

            ax3 = fig.add_subplot(3, 1, 3)
            im3 = ax3.imshow(final_thumbnail, interpolation='none',
                             cmap=get_palette(), norm=colours.LogNorm())
            fig.colorbar(im3)
            ax3.set_title('Final focus position: {}'.format(final_focus))
            plot_path = os.path.join(file_path_root, '{}_focus.png'.format(focus_type))

            fig.tight_layout()
            fig.savefig(plot_path, transparent=False)

            # explicitly close and delete figure
            fig.clf()
            del fig

            self.logger.info('{} focus plot for camera {} written to {}'.format(
                focus_type.capitalize(), self._camera, plot_path))

        self.logger.debug(
            'Autofocus of {} complete - final focus position: {}', self._camera, final_focus)

        if focus_event:
            focus_event.set()

        return initial_focus, final_focus

    def _add_fits_keywords(self, header):
        header.set('FOC-NAME', self.name, 'Focuser name')
        header.set('FOC-MOD', self.model, 'Focuser model')
        header.set('FOC-ID', self.uid, 'Focuser serial number')
        header.set('FOC-POS', self.position, 'Focuser position')
        return header

    def __str__(self):
        return "{} ({}) on {}".format(self.name, self.uid, self.port)
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
                dynamic = self._camera.dynamic
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
