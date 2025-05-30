# Basic stuff
import datetime
import logging
import logging.config
import threading

# Local stuff : Service
from Service.NTPTimeService import NTPTimeService

# Local stuff : Observatory
from Observatory.Observatory import Observatory

# Local stuff : observation planner
from ObservationPlanner.ObservationPlanner import ObservationPlanner


if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    obs = Observatory()

    # ntp time server
    servTime = NTPTimeService()
    
    # ObservationPlanner
    obs_planner = ObservationPlanner(ntpServ=servTime, obs=obs)
    #configFileName='test.json')
    #print('Target list is {}'.format(obs_planner.getTargetList()))

    # Now schedule with astroplan
    obs_planner.init_schedule()
    # Plot nice stuff
    obs_planner.showObservationPlan(show_plot=True)

    # can also work for specific date
    obs_planner.init_schedule(start_time=servTime.get_utc().date())
    obs_planner.showObservationPlan(start_time=servTime.get_utc().date(),
                                    show_plot=True)

    # specific date + duration
    obs_planner.init_schedule(start_time=servTime.get_utc().date(),
                              duration_hour=6)
    obs_planner.showObservationPlan(start_time=servTime.get_utc().date(),
                              duration_hour=6, show_plot=True)

    # or even more specific precise time + duration
    obs_planner.init_schedule(start_time=servTime.get_utc(),
                              duration_hour=24)
    obs_planner.showObservationPlan(start_time=servTime.get_utc(),
                              duration_hour=24, show_plot=True)

