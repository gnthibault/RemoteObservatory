# Generic stuff
from threading import Event
from threading import Thread

# Numerical stuff
import numpy as np

# Astropy stuff
import astropy.units as u

# Local stuff
from Base.Base import Base
from utils import load_module

class SpectralCalibration(Base):
    def __init__(self,
                 camera=None,
                 config=None,
                 *args, **kwargs):
        super().__init__(self, args, kwargs)

        if config is None:
            config = dict(
                module="SpectralCalibration",
                controller=dict(
                    module='IndiSpectroController',
                    controller_name="spox")
            )

        # Get info from config
        self.spectral_calib_exp_sec = config["spectral_calib"]["sec"]*u.second
        self.spectral_calib_nb = config["spectral_calib"]["nb"]
        self.spectral_calib_gain = config["spectral_calib"]["gain"]
        self.spectral_calib_offset = config["spectral_calib"]["offset"]
        self.spectral_calib_temperature = config["spectral_calib"]["temperature"]
        self.flat_exp_sec = config["flat"]["sec"]*u.second
        self.flat_nb = config["flat"]["nb"]
        self.flat_gain = config["flat"]["gain"]
        self.flat_offset = config["flat"]["offset"]
        self.flat_temperature = config["flat"]["temperature"]
        self.dark_nb = config["dark"]["dark_nb"]
 
        # If controller is specified in the config, load
        try:
            cfg = config['controller']
            controller_name = cfg['module']
            controller = load_module('Spectro.'+controller_name)
            self.controller = getattr(controller, controller_name)(config=cfg)
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

        event_flat = self.take_flat(observed_list)
        event_spectral = self.take_spectral_calib(observed_list, event=event_flat)
        event_dark = self.take_dark(observed_list, event=event_spectral)
        return event_dark

    def take_flat(self, observed_list, event=None):
        if event:
            event.wait()
        self.controller.switch_on_flat_light()
        for i in range(self.flat_nb):
            event = self.camera.take_calibration(
                temperature=self.flat_temperature,
                gain=self.flat_gain,
                offset=self.flat_offset,
                exp_time=self.flat_exp_sec,
                calibration_name="flat",
                observations=observed_list.values())
            #yield event
            event.wait()
        self.controller.switch_off_flat_light()

    def take_spectral_calib(self, observed_list, event=None):
        if event:
            event.wait()
        self.controller.switch_on_spectro_light()
        for i in range(self.spectral_calib_nb):
            event = self.camera.take_calibration(
                temperature=self.spectral_calib_temperature,
                gain=self.spectral_calib_gain,
                offset=self.spectral_calib_offset,
                exp_time=self.spectral_calib_exp_sec,
                calibration_name="spectral_calib",
                observations=observed_list.values())
            # yield event
            event.wait()
        self.controller.switch_off_spectro_light()

    def take_dark(self, observed_list, event=None):
        """
        Temperature is the "most expensive" parameter to change, hence we will use this as our primary key
        :param observed_list:
        :return:
        """
        if event:
            event.wait()
        dark_config_dict = dict()
        for seq_time, observation in observed_list.items():
            temp_deg = observation.configuration['temperature']
            conf = (observation.time_per_exposure,
                    observation.configuration['gain'],
                    observation.configuration['offset'])
            if temp_deg in dark_config_dict:
                dark_config_dict[temp_deg].add(conf)
            else:
                dark_config_dict[temp_deg] = set((conf,))

        self.controller.close_optical_path_for_dark()
        for temp_deg, times_gains_offsets in dark_config_dict.items():
            if temp_deg:
                self.camera.set_temperature(temp_deg)
            for (exp_time, gain, offset) in times_gains_offsets:
                for i in range(self.dark_nb):
                    event = self.camera.take_calibration(
                        temperature=temp_deg,
                        gain=gain,
                        offset=offset,
                        exp_time=exp_time,
                        headers={},
                        calibration_name="dark",
                        observations=observed_list.values())
                    event.wait()
        self.controller.open_optical_path()
        return event