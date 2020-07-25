# Generic stuff
from threading import Event
from threading import Thread

# Numerical stuff
import numpy as np

# Astropy stuff
import astropy.units as u

# Local stuff
from Base.Base import Base

class SpectralCalibration(Base):
    def __init__(self,
                 camera=None,
                 config=None,
                 *args, **kwargs):
        super().__init__(self, args, kwargs)

        if config is None:
            config = dict(
                module = "SpectralCalibration",
                controller = dict(
                    module = 'IndiSpectroController',
                    controller_name = "spox")
            )

        # Get info from config
        self.spectral_calib_exp_sec = config["spectral_calib"]["sec"]*u.second
        self.spectral_calib_nb = config["spectral_calib"]["nb"]
        self.spectral_calib_gain = config["spectral_calib"]["gain"]
        self.spectral_calib_temperature = config["spectral_calib"]["temperature"]
        self.flat_exp_sec = config["flat"]["sec"]*u.second
        self.flat_nb = config["flat"]["nb"]
        self.flat_gain = config["flat"]["gain"]
        self.flat_temperature = config["flat"]["temperature"]
        self.dark_nb = config["dark_nb"]
 
        # If controller is specified in the config, load
        try:
            cfg = config['controller']
            controller_name = cfg['module']
            controller = load_module('Spectro.'+controller_name)
            self.controller = getattr(controller,
                                            controller_name)(cfg)
        except Exception as e:
            self.controller = None
            msg = f"Cannot instantiate controller properly: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg)

        self.camera = camera
        self.logger.debug(f"SpectralCalibration successfully created with camera"
                          f"{self.camera.device_name} and controller "
                          f"{self.controller.device_name}")

    def calibrate(self, observed_list):

        self.take_flat(observed_list)
        self.take_spectral_calib(observed_list)
        self.take_dark(observed_list)

    def take_flat(self, observed_list):
        self.controller.switch_on_flat_light()
        for i in range(self.flat_nb):
            event = self.camera.take_calibration(
                temperature=self.flat_temperature,
                gain=self.flat_gain,
                exp_time=self.flat_exp_sec,
                calibration_name="flat",
                observations=observed_list.values())
            #yield event
            event.wait()
        self.controller.switch_off_flat_light()

    def take_spectral_calib(self, observed_list):
        self.controller.switch_on_spectro_light()
        for i in range(self.spectral_calib_nb):
            event = self.camera.take_calibration(
                temperature=self.spectral_calib_temperature,
                gain=self.spectral_calib_gain,
                exp_time=self.spectral_calib_exp_sec,
                calibration_name="spectral_calib",
                observations=observed_list.values())
            # yield event
            event.wait()
        self.controller.switch_off_spectro_light()

    def take_dark(self, observed_list):
        dark_config_dict = {}
        for seq_time, observation in observed_list.items():
            conf = (
                observation.time_per_exposure
                observation.configuration['gain'],
                observation.configuration['temperature'])
            if conf in dark_config_dict:
                dark_config_dict[conf].append(seq_time)
            else:
                dark_config_dict[conf] = [seq_time]

        self.controller.close_optical_path_for_dark()
        for obsk, (exp_time_sec, gain, temperature) in dark_config_dict.items():
            for i in range(self.dark_nb):
                event = self.camera.take_calibration(
                    temperature=temperature,
                    gain=gain,
                    exp_time=exp_time_sec,
                    calibration_name="dark",
                    observations=[observed_list[i] for i in 
                                  dark_config_dict[obsk]]
                #yield event
                event.wait()
        self.controller.open_optical_path()

