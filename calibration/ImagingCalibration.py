# Generic stuff
from threading import Event
from threading import Thread

# Numerical stuff
import numpy as np

# Local stuff
from Base.Base import Base

class DummyController:
    def __init__()
        pass
    def switch_on_flat_light(self):
        pass
    def switch_off_flat_light(self):
        pass
    def close_optical_path_for_dark(self):
        pass
    def open_optical_path(self):
        pass

class ImagingCalibration(Base):
    def __init__(self,
                 camera=None,
                 config=None,
                 *args, **kwargs):
        super().__init__(self, args, kwargs)

        # Get info from config
        self.flat_exp_sec = config["flat"]["sec"]*u.second
        self.flat_nb = config["flat"]["nb"]
        self.flat_gain = config["flat"]["gain"]
        self.flat_temperature = config["flat"]["temperature"]
        self.dark_nb = config["dark_nb"]
 
        self.camera = camera
        self.controller = kwargs.get("controller", DummyController())

        self.logger.debug(f"ImagingCalibration successfully created with camera"
                          f"{self.camera.device_name} and controller "
                          f"{self.controller.device_name}")

    def calibrate(self, observed_list):

        self.take_flat(observed_list)
        self.take_dark(observed_list)

    def take_flat(self, observed_list):
        flat_config_dict = {}
        for seq_time, observation in observed_list.items():
            conf = (
                observation.configuration.get("filter", "no-filter"))
            if conf in flat_config_dict:
                flat_config_dict[conf].append(seq_time)
            else:
                flat_config_dict[conf] = [seq_time]

        self.controller.switch_on_flat_light()
        for obsk, (filter_name) in flat_config_dict.items():
            for i in range(self.flat_nb):
                #self.camera.filterwheel.set_filter(filter_name)
                event = self.camera.take_calibration(
                    temperature=self.flat_temperature,
                    gain=self.flat_gain,
                    exp_time=self.flat_exp_sec,
                    headers={"filter":filter_name}
                    calibration_name="flat",
                    observations=observed_list.values())
                #yield event
                event.wait()
        self.controller.switch_off_flat_light()

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

