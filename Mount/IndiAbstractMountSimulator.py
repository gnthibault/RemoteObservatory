# Basic stuff

# Numerical stuff
import numpy as np

# Local stuff
from Mount.IndiAbstractMount import IndiAbstractMount

class IndiAbstractMountSimulator(IndiAbstractMount):
    def __init__(self, location, serv_time, config=None,
                 connect_on_create=True):

        # Parent initialization
        super().__init__(
            location=location,
            serv_time=serv_time,
            config=config,
            connect_on_create=connect_on_create)

    def initialize_simulation_setup(self):
        for switch, values in self.indi_mount_config["simulator_settings"]["switches"].items():
            self.set_switch(name=switch, on_switches=values)

    def connect_device(self):
        self.initialize_simulation_setup()
        IndiAbstractMount.connect_device(self, force_reconnect=True)
