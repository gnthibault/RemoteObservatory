# Generic stuff
from threading import Event
from threading import Thread

# Numerical stuff
import numpy as np

# Astropy stuff
import astropy.units as u

# Local stuff
from Base.Base import Base

class DummyController:
    def __init__(self):
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
        self.flat_offset = config["flat"]["offset"]
        self.flat_temperature = config["flat"]["temperature"]
        self.dark_nb = config["dark"]["dark_nb"]

        # Get devices
        self.camera = camera
        self.controller = kwargs.get("controller", DummyController())

        self.logger.debug(f"ImagingCalibration successfully created with camera"
                          f"{self.camera} and controller "
                          f"{self.controller}")

    def calibrate(self, observed_list):
        event_flat = self.take_flat(observed_list)
        event_dark = self.take_dark(observed_list, event=event_flat)
        return event_dark

    def take_flat(self, observed_list, event=None):
        if event:
            event.wait()
        flat_config = set()
        for seq_time, observation in observed_list.items():
            conf = observation.configuration.get("filter", "no-filter")
            flat_config.add(conf)
        self.controller.switch_on_flat_light()
        for filter_name in flat_config:
            if filter_name != "no-filter" and self.camera.filter_wheel is not None:
                self.camera.filter_wheel.set_filter(filter_name)
            for i in range(self.flat_nb):
                event = self.camera.take_calibration(
                    temperature=self.flat_temperature,
                    gain=self.flat_gain,
                    offset=self.flat_offset,
                    exp_time=self.flat_exp_sec,
                    headers={"filter": filter_name},
                    calibration_name="flat",
                    observations=observed_list.values())
                event.wait()
        self.controller.switch_off_flat_light()
        return event

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