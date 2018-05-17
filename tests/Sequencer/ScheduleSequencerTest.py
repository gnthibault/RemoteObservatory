# Basic stuff
import datetime
import logging
import logging.config
import threading
import sys

sys.path.append('.')

# Miscellaneous
import io
from astropy.io import fits

# Local stuff : Service
from Service.NTPTimeService import NTPTimeService

# Local stuff : Observatory
from Observatory.ShedObservatory import ShedObservatory

# Local stuff : IndiClient
from helper.IndiClient import IndiClient

# Local stuff : Camera
from Camera.IndiCamera import IndiCamera

# Local stuff : FilterWheel
from FilterWheel.IndiFilterWheel import IndiFilterWheel

# Local stuff : Mount
from Mount.IndiMount import IndiMount

# Local stuff : Imaging tools
from Imaging.AsyncWriter import AsyncWriter
from Imaging.FitsWriter import FitsWriter

# Local stuff : observation planner
from ObservationPlanner.ObservationPlanner import ObservationPlanner

# Local stuff: ScheduleSequencer
from Sequencer.ScheduleSequencer import ScheduleSequencer

if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')
    logger = logging.getLogger('mainLogger')

    obs = ShedObservatory(logger=logger)

    # ntp time server
    servTime = NTPTimeService(logger=logger)
    
    # ObservationPlanner
    obs_planner = ObservationPlanner(logger=logger, ntpServ=servTime, obs=obs)
    #configFileName='test.json')

    # Precise time + duration
    start = servTime.getUTCFromNTP().date()
    duration = 6
    obs_planner.init_schedule(start_time=start, duration_hour=duration)
    obs_planner.showObservationPlan(start_time=start, duration_hour=duration,
                                    show_plot=True)

    # Instanciate indiclient and connect
    indi_client = IndiClient()

    # Instanciate all devices
    filter_wheel = IndiFilterWheel(indiClient=indi_client,
                                   configFileName=None,
                                   connectOnCreate=False)
    mount = IndiMount(indiClient=indi_client, configFileName=None,
                      connectOnCreate=False)
    camera = IndiCamera(indiClient=indi_client, configFileName=None,
                        connectOnCreate=False)

    # Instanciate the image writer stuff
    writer = FitsWriter(observatory=obs, filterWheel=filter_wheel)
    async_writer = AsyncWriter(writer)

    # Instanciate the ScheduleSequencer
    s = ScheduleSequencer(camera=camera, filter_wheel=filter_wheel,
                          observatory=obs, mount=mount,
                          async_writer=async_writer, use_auto_dark=True,
                          use_auto_flat=True)
    s.build_sequence(obs_planner.schedule)
    s.start_sequence()

