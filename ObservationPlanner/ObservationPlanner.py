# Basic stuff
import datetime
import logging
import os.path
import pickle
import yaml


# Numerical stuff
import numpy as np

# Astropy stuff
from astropy.coordinates import get_moon
from astropy.coordinates import get_sun
from astropy import units as AU
from astropy.coordinates import AltAz
from astropy.coordinates import EarthLocation
from astropy.coordinates import SkyCoord
from astropy.time import Time as ATime

# Astroplan stuff
from astroplan import FixedTarget
from astroplan import moon_illumination
from astroplan import ObservingBlock
from astroplan.constraints import AtNightConstraint
from astroplan.constraints import AirmassConstraint
from astroplan.constraints import TimeConstraint
from astroplan.constraints import MoonSeparationConstraint
from astroplan.plots import plot_sky
from astroplan.scheduling import PriorityScheduler
from astroplan.scheduling import SequentialScheduler
from astroplan.scheduling import Schedule
from astroplan import TransitionBlock
from astroplan.scheduling import Transitioner

# Plotting stuff
import matplotlib
import matplotlib.pyplot as plt

# Local
from Base.Base import Base

# Locally defined constraints
from ObservationPlanner.LocalHorizonConstraint import LocalHorizonConstraint

class ObservationPlanner(Base):

    WheelToPltColors = {
        'Luminance' : 'orchid',
        'Red' : 'red',
        'Green' : 'green',
        'Blue' : 'blue',
        'H_Alpha' : 'lightcoral',
        'OIII' : 'mediumaquamarine',
        'SII' : 'lightskyblue',
        'LPR' : 'orchid' }
    # Max value for which a scheduling slot is programmed, otherwise
    # we split into smaller slots
    MaximumSlotDurationSec = 300

    def __init__(self, ntpServ, obs, configFileName=None, path='.',
                 logger=None):
        Base.__init__(self)
        self.ntpServ = ntpServ
        self.obs = obs
        
        if configFileName is None:
            self.configFileName = './conf_files/targets.yaml'
        else:
            self.configFileName = configFileName

        # Now configuring class
        self.logger.debug('Configuring ObservationPlanner with file {}'.format(
                          self.configFileName))

        # Get config from json
        with open(self.configFileName) as jsonFile:
            self.targetList = yaml.load(jsonFile, Loader=yaml.FullLoader)
            self.logger.debug('ObservationPlanner, targetList is: {}'.format(
                              self.targetList))
        self.schedule = None
        self.path = path
        self.tmh = 8

        # Axes/timeline/annotation
        self.air_ax = None
        self.air_timeline = None
        #self._annot = None
        self.alt_ax = None
        self.alt_timeline = None
        #self.alt_annot = None
        self.tmp_drawn = []

        # Finished configuring
        self.logger.debug('ObservationPlanner configured successfully')

      
    def getTargetList(self):
        return self.targetList

    def init_schedule(self, start_time=None, duration_hour=None):

        constr = self.gen_constraints()
        obs_blocks = self.gen_obs_blocks(constr)
        scheduler = self.gen_scheduler(constr)
        self.schedule = self.gen_schedule(obs_blocks, scheduler, start_time,
                                          duration_hour)
        # a bug, apparently: https://github.com/astropy/astroplan/issues/372
        #print(self.schedule.to_table())
        for i, el in enumerate(self.schedule.observing_blocks):
            print('Element {} in schedule: start at {}, target is {}, '
                  'filter is {}, count is {}, and duration is {}'.format(
                  i, el.start_time, el.target, el.configuration['filter'],
                  el.number_exposures, el.time_per_exposure))

    def gen_constraints(self):
        # create the list of constraints that all targets must satisfy
        #
        # At night constraint: seee http://astroplan.readthedocs.io/en/latest/api/astroplan.AtNightConstraint.html#astroplan.AtNightConstraint
        # Consider nighttime as time between astronomical twilights (-18 degrees).
        # 
        #
        return [AirmassConstraint(max=3, boolean_constraint=True),
                AtNightConstraint.twilight_astronomical(),
                MoonSeparationConstraint(min=45*AU.deg),
                LocalHorizonConstraint(horizon=self.obs.get_horizon(),
                                       boolean_constraint=True)]

    def gen_obs_blocks(self, constraint):

        #TODO TN readout time, get that info from camera
        camera_time = 1*AU.second
        # Create ObservingBlocks for each filter and target with our time
        # constraint, and durations determined by the exposures needed

        obs_blocks = []

        for target_name, config in self.targetList["targets"].items():
            target = FixedTarget.from_name(target_name)
            #target = FixedTarget(SkyCoord(239*AU.deg, 49*AU.deg))
            for filter_name, acq_config in config.items():
                # We split big observing blocks into smaller blocks for better
                # granularity
                (count, temperature, gain, exp_time_sec) = [acq_config[k] for k in ["count", "temperature", "gain", "exp_time_sec"]]
                while count > 0:
                    l_count = max(1, min(count,
                        self.MaximumSlotDurationSec//exp_time_sec))
                    exp_time = exp_time_sec*AU.second
                
                    #TODO TN retrieve priority from the file
                    priority = 0 if (filter_name=='Luminance') else 1
                    b = ObservingBlock.from_exposures(
                            target, priority, exp_time, l_count,
                            camera_time,
                            configuration={'filter': filter_name},
                            constraints=constraint)

                    obs_blocks.append(b)
                    count -= l_count
        return obs_blocks

    def gen_scheduler(self, constraint):
        # Initialize a transitioner object with the slew rate and/or the
        # duration of other transitions (e.g. filter changes)
        # TODO TN do that from mount or filterwheel info
        slew_rate = 1.5*AU.deg/AU.second
        transitions = Transitioner(slew_rate,
                                   {'filter':{'default': 10*AU.second}})

        # Initialize the priority scheduler with constraints and transitioner
        return PriorityScheduler(
            constraints=constraint,
            observer=self.obs.getAstroplanObserver(),
            transitioner=transitions)

    def gen_schedule(self, obs_blocks, scheduler, start_time=None,
                     duration_hour=None):
        """ start_time can either be a precise datetime or a datetime.date """
        if duration_hour is None:
            duration_hour = self.tmh * 2 * AU.hour
        else:
            duration_hour = duration_hour * AU.hour

        if start_time is None or (isinstance(start_time, datetime.date) and not
                                  isinstance(start_time, datetime.datetime)):
            if start_time is None:
                target_date = self.ntpServ.get_local_date()
            else:
                target_date = start_time
            midnight = self.ntpServ.get_next_local_midnight_in_utc(target_date)
            midnight = ATime(midnight)
            start_time = midnight - duration_hour / 2
        else:
            start_time = ATime(start_time)

        stop_time = start_time + duration_hour
        priority_schedule = Schedule(start_time, stop_time)
        # Call the schedule with the observing blocks and schedule to schedule
        # the blocks
        return scheduler(obs_blocks, priority_schedule)


    def showObservationPlan(self, start_time=None, duration_hour=None,
                            show_plot=False, write_plot=False,
                            show_airmass=True, afig=None, pfig=None):
        """ start_time can either be a precise datetime or a datetime.date """
        if duration_hour is None:
            duration_hour = self.tmh * 2 * AU.hour
        else:
            duration_hour = duration_hour * AU.hour

        if start_time is None or (isinstance(start_time, datetime.date) and not
                                  isinstance(start_time, datetime.datetime)):
            if start_time is None:
                target_date = self.ntpServ.get_local_date()
            else:
                target_date = start_time
            midnight = self.ntpServ.get_next_local_midnight_in_utc(target_date)
            d_h = float(duration_hour/AU.hour)
            start_time = midnight - datetime.timedelta(hours=d_h/2)
        else:
            target_date = start_time.date()

        #Time margin, in hour
        tmh_range = int(np.ceil(float(duration_hour/AU.hour)))
        #tmh_range = np.arange(tmh_range, dtype=float) - tmh_range//2
        date_font_size = 8
        resolution = 400

        #UTC range
        utc_tmh_range = [start_time+datetime.timedelta(hours=i) for i in
                         range(tmh_range)]
        #local time range
        local_tmh_range = [self.ntpServ.convert_to_local_time(i) for i in
                           utc_tmh_range]
        #Astropy ranges (everything in UTC)
        start_time = ATime(start_time)
        relative_time_frame = np.linspace(0, tmh_range,
                                          resolution) * AU.hour
        absolute_time_frame = start_time + relative_time_frame
        altaz_frame = AltAz(obstime=absolute_time_frame,
                            location=self.obs.getAstropyEarthLocation())
        #Matplotlib friendly versions
        m_absolute_time_frame = matplotlib.dates.date2num(
            absolute_time_frame.to_datetime())
        m_tmh_range = matplotlib.dates.date2num(utc_tmh_range)

        if afig is None:
            afig = plt.figure(figsize=(25,15))
        if show_airmass:
            # Configure airmass subplot
            self.air_ax = afig.add_subplot(2,1,1)
            # Configure altaz subplot
            self.alt_ax = afig.add_subplot(2,1,2)
        else:
            self.alt_ax = afig.add_subplot(111)

        #Configure altitude plot and plot sun/moon illumination
        sun_altazs = get_sun(absolute_time_frame).transform_to(altaz_frame)
        moon_altazs = get_moon(absolute_time_frame).transform_to(altaz_frame)
         
        # Plot Sun
        self.alt_ax.plot(m_absolute_time_frame, sun_altazs.alt,
                    color='gold', label='Sun')
        #Plot Moon
        moon_ill_perc = moon_illumination(start_time+duration_hour/2)*100.0
        moon_label = 'Moon {number:.{digits}f} %'.format(number = 
            moon_ill_perc, digits=0)
        self.alt_ax.plot(m_absolute_time_frame, moon_altazs.alt,
                    color='silver', label=moon_label)

        #grey sky when sun lower than -0 deg
        grey_sun_range = sun_altazs.alt < -0*AU.deg
        self.alt_ax.fill_between(matplotlib.dates.date2num(
                            absolute_time_frame.to_datetime()), 0, 90,
                            grey_sun_range, color='0.5', zorder=0)
        #Dark sky when sun is below -18 deg
        dark_sun_range = sun_altazs.alt < -18*AU.deg
        self.alt_ax.fill_between(matplotlib.dates.date2num(
                            absolute_time_frame.to_datetime()), 0, 90,
                            dark_sun_range, color='0', zorder=0)
        #grey sky when sun is low (<18deg) but moon has risen
        grey_moon_range = np.logical_and(moon_altazs.alt > -5*AU.deg,
                                         sun_altazs.alt < -18*AU.deg)
        grey_moon_intensity = 0.0025*moon_ill_perc #hence 0.25 for 100%
        self.alt_ax.fill_between(matplotlib.dates.date2num(
            absolute_time_frame.to_datetime()), 0, 90,
            grey_moon_range, color='{number:.{digits}f}'.format(
            number=grey_moon_intensity, digits=2), zorder=0)

        #Now setup the polar chart
        if pfig is None:
            pfig = plt.figure(figsize=(25,15))
        self.pol_ax = plt.gca(projection='polar')
        #self.pol_ax = pfig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)

        #First axis, azimut, MUST be in RAD (not deg)
        self.pol_ax.set_xlim(0, np.deg2rad(360))
        self.pol_ax.set_theta_direction(-1)
        degree_sign = u'\N{DEGREE SIGN}'
        theta_labels = []
        for chunk in range(0, 8):
            label_angle = chunk*45.0
            if label_angle == 0:
                theta_labels.append('N ' + '\n' + str(label_angle) +
                                    degree_sign + ' Azimuth [deg]')
            elif label_angle == 45:
                theta_labels.append('') #Let some space for r axis labels
            elif label_angle == 90:
                theta_labels.append('E' + '\n' + str(label_angle) +
                                    degree_sign)
            elif label_angle == 180:
                theta_labels.append('S' + '\n' + str(label_angle) +
                                    degree_sign)
            elif label_angle == 270:
                theta_labels.append('W' + '\n' + str(label_angle) +
                                    degree_sign)
            else:
                theta_labels.append(str(label_angle) + degree_sign)

        # Set ticks and labels for azimuth
        self.pol_ax.set_theta_zero_location('N')
        self.pol_ax.set_thetagrids(np.arange(0, 360, 45),
                              theta_labels)

        # Second axis (altitude) must be inverted
        # For positively-increasing range (e.g., range(1, 90, 15)),
        # labels go from middle to outside.
        r_labels = [str(angle)+degree_sign for angle in range(90,-1,-15)]
        r_labels[-1] += ' Altitude [deg]'

        # Set ticks and labels for altitude
        self.pol_ax.set_rlim(0, 90)
        self.pol_ax.set_rgrids(np.arange(0, 91, 15), r_labels, angle=45)

        # Now plot observatory horizon
        hor_az = np.sort(list(map(int,self.obs.get_horizon().keys())))
        hor_alt = np.array([int(self.obs.get_horizon()[i]) for i in
                            hor_az])
        # Now add virtual point to cover the circle
        hor_az = np.concatenate((hor_az,[360]))
        hor_alt = np.concatenate((hor_alt,[hor_alt[-1]]))
        self.pol_ax.fill_between(np.deg2rad(hor_az), np.ones_like(hor_alt)*90,
                            90-hor_alt, color='darkseagreen', alpha=0.5)

        # Now show sun and moon
        self.pol_ax.plot(np.deg2rad(np.array(sun_altazs.az)),
            90-np.array(sun_altazs.alt), color='gold', label='Sun')
        self.pol_ax.plot(np.deg2rad(np.array(sun_altazs.az)),
            90-np.array(moon_altazs.alt), color='silver', label=moon_label)

        #Setup various colors for the different targets
        nb_target = len(self.targetList)
        cm = plt.get_cmap('gist_rainbow')
        colors = [cm(1.*i/nb_target) for i in range(nb_target)]

        for (target_name, imaging_program), color in zip(
                self.targetList.items(), colors):
            #target_coord = SkyCoord.from_name(target_name)
            target_coord = SkyCoord(239*AU.deg, 49*AU.deg)

            # Compute altazs for target
            target_altazs = target_coord.transform_to(altaz_frame)

            if show_airmass:
                # First plot airmass
                self.air_ax.plot(m_absolute_time_frame, target_altazs.secz,
                            label=target_name, color=color, alpha=0.4)

            # Then plot altitude along with sun/moon
            self.alt_ax.plot(m_absolute_time_frame, target_altazs.alt,
                        label=target_name, color=color, alpha=0.4)

            # Then plot environment aware polar altaz map
            self.pol_ax.plot(np.deg2rad(np.array(target_altazs.az)),
                90-np.array(target_altazs.alt), color=color, label=target_name,
                alpha=0.4)

        if not (self.schedule is None):
            for bl in self.schedule.observing_blocks:
                # get target
                target_coord = bl.target.coord

                # compute slot absolute time frame
                start = bl.start_time
                # We add 1 because last time point is end of the last exposure
                l_resolution = bl.number_exposures+1
                l_rel_time_frame = (np.linspace(0, 1, l_resolution) *
                                    bl.duration)
                l_abs_time_frame = start + l_rel_time_frame
                l_altaz_frame = AltAz(obstime=l_abs_time_frame,
                    location=self.obs.getAstropyEarthLocation())
                # get matplotlib compatible absolute time frame
                l_m_abs_time_frame = matplotlib.dates.date2num(
                    l_abs_time_frame.to_datetime())
                # Compute altazs for target
                l_targ_altazs = target_coord.transform_to(l_altaz_frame)

                # Get color from filter
                l_color = 'orchid'
                if 'filter' in bl.configuration:
                    l_color = self.WheelToPltColors[bl.configuration['filter']]

                def scatter_altaz(ax, abstime, altaz, marker):
                    ax.scatter(abstime, altaz, color=l_color, marker=marker)
                if show_airmass:
                    # First plot airmass for acquisition start points
                    scatter_altaz(self.air_ax, l_m_abs_time_frame[:-1],
                                  l_targ_altazs.secz[:-1], marker='+')
                    # Then plot airmass for the last stop point
                    scatter_altaz(self.air_ax, l_m_abs_time_frame[-1],
                                  l_targ_altazs.secz[-1], marker='x')


                # Then plot altitude along with sun/moon: start points
                scatter_altaz(self.alt_ax, l_m_abs_time_frame[:-1],
                              l_targ_altazs.alt[:-1], marker='+')
                # Then plot altitude for the last stop point
                scatter_altaz(self.alt_ax, l_m_abs_time_frame[-1],
                              l_targ_altazs.alt[-1], marker='x')

                # Then plot environment aware polar altaz map: start points
                self.pol_ax.scatter(np.deg2rad(np.array(l_targ_altazs.az[:-1])),
                    90-np.array(l_targ_altazs.alt[:-1]),
                    color=l_color, marker='+')
                # Then plot environment aware polar altaz map: stop point
                self.pol_ax.scatter(np.deg2rad(np.array(l_targ_altazs.az[-1])),
                    90-np.array(l_targ_altazs.alt[-1]),
                    color=l_color, marker='x')

        if show_airmass:
            # Configure airmass plot, both utc and regular time
            self.air_ax.legend(loc='upper left')
            self.air_ax.set_xlim(m_absolute_time_frame[0],
                                 m_absolute_time_frame[-1])
            self.air_ax.set_xticks(m_tmh_range)
            self.air_ax.set_xticklabels(utc_tmh_range, rotation=15,
                                   fontsize=date_font_size)
            self.air_ax.set_xlabel('UTC Time')
            self.air_ax2 = self.air_ax.twiny()
            self.air_ax2.set_xlim(m_absolute_time_frame[0],
                                  m_absolute_time_frame[-1])
            self.air_ax2.set_xticks(m_tmh_range)
            self.air_ax2.set_xticklabels(local_tmh_range, rotation=15,
                                   fontsize=date_font_size)
            self.air_ax2.set_xlabel('Local time ({})'.format(
                self.ntpServ.timezone.zone))
            self.air_ax.set_ylim(0.9, 4)
            self.air_ax.set_ylabel('Airmass, [Sec(z)]')

        #Configure altitude plot, both utc and regular time
        self.alt_ax.legend(loc='upper left')
        self.alt_ax.set_xlim(m_absolute_time_frame[0],
                             m_absolute_time_frame[-1])
        self.alt_ax.set_xticks(m_tmh_range)
        self.alt_ax.set_xticklabels(utc_tmh_range, rotation=15,
                               fontsize=date_font_size)
        self.alt_ax.set_xlabel('UTC Time')
        self.alt_ax2 = self.alt_ax.twiny()
        self.alt_ax2.set_xlim(m_absolute_time_frame[0],
                              m_absolute_time_frame[-1])
        self.alt_ax2.set_xticks(m_tmh_range)
        self.alt_ax2.set_xticklabels(local_tmh_range, rotation=15,
                                fontsize=date_font_size)
        self.alt_ax2.set_xlabel('Local time ({})'.format(
                                self.ntpServ.timezone.zone))
        self.alt_ax.set_ylim(0, 90)
        self.alt_ax.set_ylabel('Altitude [deg]')

        # Configure airmass plot, both utc and regular time
        self.pol_ax.legend(loc='upper left')

        # Nice formating, no overlap between subplots
        afig.tight_layout()
        pfig.tight_layout()

        if show_plot:
            plt.show()

        if write_plot:
            # Now save everything to disk
            filepath = os.path.join(self.path, str(target_date) +
                                    '-observation-plan-altaz.png')
            afig.savefig(filepath)
            filepath = os.path.join(self.path, str(target_date) +
                                    '-observation-plan-polar.png')
            pfig.savefig(filepath)

        return afig, pfig

    def annotate_time_point(self, time_point=None, show_airmass=True):
        if time_point is None:
            time_point = self.ntpServ.get_local_time()
        tm = matplotlib.dates.date2num(time_point)
        color = 'mediumslateblue'
        axes = []
        lines = []
        if show_airmass and self.air_ax:
            axes.append(self.air_ax)
            if self.air_timeline is None:
                self.air_timeline, = self.air_ax.plot([],[], color=color)
            lines.append(self.air_timeline)
        if self.alt_ax:
            axes.append(self.alt_ax)
            if self.alt_timeline is None:
                self.alt_timeline, = self.alt_ax.plot([],[], color=color)
            lines.append(self.alt_timeline)
        # delete temporary elements
        for tmp in self.tmp_drawn:
            tmp.remove()
        self.tmp_drawn.clear()

        for ax,line in zip(axes,lines):
#        for ax in axes:
            ymin, ymax = ax.get_ylim()
            yrange = ymax-ymin
            ylabel = ymin+0.10*yrange
            #self.tmp_drawn.append(ax.plot([tm,tm],[0,90], color=color))
            line.set_xdata([tm,tm])
            line.set_ydata([0,90])
            self.tmp_drawn.append(
                ax.annotate("{:d}:{:02d}".format(time_point.hour,
                time_point.minute),(tm,ylabel), color=color))

