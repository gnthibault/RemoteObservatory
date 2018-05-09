# Basic stuff
import datetime
import json
import logging
import os.path

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
from astroplan.scheduling import Transitioner

# Plotting stuff
import matplotlib
import matplotlib.pyplot as plt

class ObservationPlanner:

    WheelToPltColors = {
        'Luminance' : 'orchid',
        'Red' : 'red',
        'Green' : 'green',
        'Blue' : 'blue',
        'H_Alpha' : 'lightcoral',
        'OIII' : 'mediumaquamarine',
        'SII' : 'lightskyblue',
        'LPR' : 'orchid' }


    def __init__(self, ntpServ, obs, configFileName=None, path='.',
                 logger=None):
        self.ntpServ = ntpServ
        self.obs = obs
        self.logger = logger or logging.getLogger(__name__)
        
        if configFileName is None:
            self.configFileName = 'TargetList.json'
        else:
            self.configFileName = configFileName

        # Now configuring class
        self.logger.debug('Configuring ObservationPlanner with file {}'.format(
                          self.configFileName))

        # Get config from json
        with open(self.configFileName) as jsonFile:
            self.targetList = json.load(jsonFile)
            self.logger.debug('ObservationPlanner, targetList is: {}'.format(
                              self.targetList))
        self.schedule = None
        self.path = path
        self.tmh = 8

        # Finished configuring
        self.logger.debug('ObservationPlanner configured successfully')

      
    def getTargetList(self):
        return self.targetList

    def gen_schedule(self, target_date=None):
        if target_date is None:
            target_date = self.ntpServ.getLocalDateFromNTP()

        # create the list of constraints that all targets must satisfy
        constr = [AirmassConstraint(max=2.5, boolean_constraint=False),
                  AtNightConstraint.twilight_astronomical(),
                  MoonSeparationConstraint(min=30*AU.deg)]

        # Initialize a transitioner object with the slew rate and/or the
        # duration of other transitions (e.g. filter changes)
        # TODO TN do that from mount or filterwheel info
        slew_rate = 1.5*AU.deg/AU.second
        trans = Transitioner(slew_rate,{'filter':{'default': 10*AU.second}})

        # Create ObservingBlocks for each filter and target with our time
        # constraint, and durations determined by the exposures needed
        obs_blocks = []

        for target_name, config in self.targetList.items():
            #target = FixedTarget.from_name(target_name)
            target = FixedTarget(SkyCoord(179*AU.deg, 49*AU.deg))
            for filter_name, (count, exp_time_sec) in config.items():
                #TODO TN get that info from camera
                camera_time = 1*AU.second
                exp_time = exp_time_sec*AU.second
                
                #TODO TN retrieve priority from the file
                priority = 0 if (filter_name=='Luminance') else 1
                b = ObservingBlock.from_exposures(
                        target, priority, 50*exp_time, 10*count, camera_time,
                        configuration = {'filter': filter_name}) #,
                        #constraints = constr)

                obs_blocks.append(b)

        # Initialize the priority scheduler with constraints and transitioner
        priority_scheduler = PriorityScheduler(
            constraints=constr,
            observer=self.obs.getAstroplanObserver(),
            transitioner=trans)

        # Initialize a Schedule object, to contain the new schedule
        midnight = self.ntpServ.getNextMidnightInUTC(target_date)
        midnight = ATime(midnight)
        start = midnight - self.tmh * AU.hour
        stop = midnight + self.tmh * AU.hour
        priority_schedule = Schedule(start, stop)
        # Call the schedule with the observing blocks and schedule to schedule
        # the blocks
        self.schedule = priority_scheduler(obs_blocks, priority_schedule)
        #print(self.schedule.to_table())
        convenient = [{'slot':sl,'block':bl} for (sl,bl) in zip(
            self.schedule.slots,
            self.schedule.observing_blocks)]
        for i, el in enumerate(convenient):
            print('Element {} in schedule: start at {}, target is {}, '
                  'filter is {}, count is {}, and duration is {}'.format(
                  i, el['slot'].start.to_datetime(), el['block'].target, 
                  el['block'].configuration['filter'],
                  el['block'].number_exposures, el['block'].time_per_exposure))


    def showObservationPlan(self, target_date=None):
        if target_date is None:
            target_date = self.ntpServ.getLocalDateFromNTP()
        #Time margin, in hour
        tmh_range = np.arange(self.tmh+1, dtype=float)*2 -self.tmh
        date_font_size = 8
        resolution = 400

        #time stuff
        midnight = self.ntpServ.getNextMidnightInUTC(target_date)

        #UTC range
        utc_tmh_range = [midnight+datetime.timedelta(hours=i) for i in
                         tmh_range]
        #local time range
        local_tmh_range = [self.ntpServ.convert_to_local_time(i) for i in
                           utc_tmh_range]
        #Astropy ranges (everything in UTC)
        midnight = ATime(midnight)
        relative_time_frame = np.linspace(-self.tmh, self.tmh,
                                          resolution) * AU.hour
        absolute_time_frame = midnight + relative_time_frame
        altaz_frame = AltAz(obstime=absolute_time_frame,
                            location=self.obs.getAstropyEarthLocation())
        #Matplotlib friendly versions
        m_absolute_time_frame = matplotlib.dates.date2num(
            absolute_time_frame.to_datetime())
        m_tmh_range = matplotlib.dates.date2num(utc_tmh_range)

        afig = plt.figure(0, figsize=(25,15))
        # Configure airmass subplot
        air_ax = afig.add_subplot(2,1,1)
        # Configure altaz subplot
        alt_ax = afig.add_subplot(2,1,2)

        #Configure altitude plot and plot sun/moon illumination
        sun_altazs = get_sun(absolute_time_frame).transform_to(altaz_frame)
        moon_altazs = get_moon(absolute_time_frame).transform_to(altaz_frame)
         
        # Plot Sun
        alt_ax.plot(m_absolute_time_frame, sun_altazs.alt,
                         color='gold', label='Sun')
        #Plot Moon
        moon_label = 'Moon {number:.{digits}f} %'.format(
            number=moon_illumination(midnight)*100.0, digits=0)
        alt_ax.plot(m_absolute_time_frame, moon_altazs.alt,
                         color='silver', label=moon_label)

        #grey sky when sun lower than -0 deg
        grey_sun_range = sun_altazs.alt < -0*AU.deg
        alt_ax.fill_between(matplotlib.dates.date2num(
                            absolute_time_frame.to_datetime()), 0, 90,
                            grey_sun_range, color='0.5', zorder=0)
        #Dark sky when sun is below -18 deg
        dark_sun_range = sun_altazs.alt < -18*AU.deg
        alt_ax.fill_between(matplotlib.dates.date2num(
                            absolute_time_frame.to_datetime()), 0, 90,
                            dark_sun_range, color='0', zorder=0)
        #grey sky when sun is low (<18deg) but moon has risen
        grey_moon_range = np.logical_and(moon_altazs.alt > -5*AU.deg,
                                         sun_altazs.alt < -18*AU.deg)
        grey_moon_intensity = 0.25*moon_illumination(midnight)
        alt_ax.fill_between(matplotlib.dates.date2num(
            absolute_time_frame.to_datetime()), 0, 90,
            grey_moon_range, color='{number:.{digits}f}'.format(
            number=grey_moon_intensity, digits=2), zorder=0)

        #Now setup the polar chart
        pfig = plt.figure(1, figsize=(25,15))
        pol_ax = plt.gca(projection='polar')
        #pol_ax = pfig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)

        #First axis, azimut, MUST be in RAD (not deg)
        pol_ax.set_xlim(0, np.deg2rad(360))
        pol_ax.set_theta_direction(-1)
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
        pol_ax.set_theta_zero_location('N')
        pol_ax.set_thetagrids(np.arange(0, 360, 45),
                              theta_labels)

        # Second axis (altitude) must be inverted
        # For positively-increasing range (e.g., range(1, 90, 15)),
        # labels go from middle to outside.
        r_labels = [str(angle)+degree_sign for angle in range(90,-1,-15)]
        r_labels[-1] += ' Altitude [deg]'

        # Set ticks and labels for altitude
        pol_ax.set_rlim(0, 90)
        pol_ax.set_rgrids(np.arange(0, 91, 15), r_labels, angle=45)

        # Now plot observatory horizon
        hor_az = np.sort(list(map(int,self.obs.get_horizon().keys())))
        hor_alt = np.array([int(self.obs.get_horizon()[str(i)]) for i in
                            hor_az])
        # Now add virtual point to cover the circle
        hor_az = np.concatenate((hor_az,[360]))
        hor_alt = np.concatenate((hor_alt,[hor_alt[-1]]))
        pol_ax.fill_between(np.deg2rad(hor_az), np.ones_like(hor_alt)*90,
                            90-hor_alt, color='darkseagreen', alpha=0.5)

        #Now show sun and moon
        pol_ax.plot(np.deg2rad(np.array(sun_altazs.az)),
            90-np.array(sun_altazs.alt), color='gold', label='Sun')
        pol_ax.plot(np.deg2rad(np.array(sun_altazs.az)),
            90-np.array(moon_altazs.alt), color='silver', label=moon_label)

        #Setup various colors for the different targets
        nb_target = len(self.targetList)
        cm = plt.get_cmap('gist_rainbow')
        colors = [cm(1.*i/nb_target) for i in range(nb_target)]

        for (target_name, imaging_program), color in zip(
                self.targetList.items(), colors):
            #target_coord = SkyCoord.from_name(target_name)
            target_coord = SkyCoord(179*AU.deg, 49*AU.deg)

            # Compute altazs for target
            target_altazs = target_coord.transform_to(altaz_frame)

            # First plot airmass
            air_ax.plot(m_absolute_time_frame, target_altazs.secz,
                        label=target_name, color=color, alpha=0.4)

            # Then plot altitude along with sun/moon
            alt_ax.plot(m_absolute_time_frame, target_altazs.alt,
                        label=target_name, color=color, alpha=0.4)

            # Then plot environment aware polar altaz map
            pol_ax.plot(np.deg2rad(np.array(target_altazs.az)),
                90-np.array(target_altazs.alt), color=color, label=target_name,
                alpha=0.4)

        if not (self.schedule is None):
            for sl, bl in zip(self.schedule.slots,
                              self.schedule.observing_blocks):
                # get target
                target_coord = bl.target.coord

                # compute slot absolute time frame
                start = sl.start
                l_resolution = bl.number_exposures
                l_rel_time_frame = (np.linspace(0, 1, l_resolution) *
                                    sl.duration)
                l_abs_time_frame = start + l_rel_time_frame
                l_altaz_frame = AltAz(obstime=l_abs_time_frame,
                    location=self.obs.getAstropyEarthLocation())
                # get matplotlib compatible absolute time frame
                l_m_abs_time_frame = matplotlib.dates.date2num(
                    l_abs_time_frame.to_datetime())
                # Compute altazs for target
                l_targ_altazs = target_coord.transform_to(l_altaz_frame)

                #Get color from filter
                l_color = 'lavenderblush'
                if 'filter' in bl.configuration:
                    l_color = self.WheelToPltColors[bl.configuration['filter']]

                # First plot airmass
                air_ax.scatter(l_m_abs_time_frame, l_targ_altazs.secz,
                               color=l_color, marker='+')

                # Then plot altitude along with sun/moon
                alt_ax.scatter(l_m_abs_time_frame, l_targ_altazs.alt,
                                color=l_color, marker='+')

                # Then plot environment aware polar altaz map
                pol_ax.scatter(np.deg2rad(np.array(l_targ_altazs.az)),
                    90-np.array(l_targ_altazs.alt), color=l_color, marker='+')

        # Configure airmass plot, both utc and regular time
        air_ax.legend(loc='upper left')
        air_ax.set_xlim(m_absolute_time_frame[0], m_absolute_time_frame[-1])
        air_ax.set_xticks(m_tmh_range)
        air_ax.set_xticklabels(utc_tmh_range, rotation=15,
                               fontsize=date_font_size)
        air_ax.set_xlabel('UTC Time')
        air_ax2 = air_ax.twiny()
        air_ax2.set_xlim(m_absolute_time_frame[0], m_absolute_time_frame[-1])
        air_ax2.set_xticks(m_tmh_range)
        air_ax2.set_xticklabels(local_tmh_range, rotation=15,
                               fontsize=date_font_size)
        air_ax2.set_xlabel('Local time ({})'.format(self.ntpServ.timezone.zone))
        air_ax.set_ylim(1, 4)
        air_ax.set_ylabel('Airmass, [Sec(z)]')

        #Configure altitude plot, both utc and regular time
        alt_ax.legend(loc='upper left')
        alt_ax.set_xlim(m_absolute_time_frame[0], m_absolute_time_frame[-1])
        alt_ax.set_xticks(m_tmh_range)
        alt_ax.set_xticklabels(utc_tmh_range, rotation=15,
                               fontsize=date_font_size)
        alt_ax.set_xlabel('UTC Time')
        alt_ax2 = alt_ax.twiny()
        alt_ax2.set_xlim(m_absolute_time_frame[0], m_absolute_time_frame[-1])
        alt_ax2.set_xticks(m_tmh_range)
        alt_ax2.set_xticklabels(local_tmh_range, rotation=15,
                                fontsize=date_font_size)
        alt_ax2.set_xlabel('Local time ({})'.format(self.ntpServ.timezone.zone))
        alt_ax.set_ylim(0, 90)
        alt_ax.set_ylabel('Altitude [deg]')

        afig.tight_layout()

        # Configure airmass plot, both utc and regular time
        pol_ax.legend(loc='upper left')

        plt.show()
        filepath = os.path.join(self.path, str(target_date) +
                                '-observation-plan-altaz.png')
        afig.savefig(filepath)
        filepath = os.path.join(self.path, str(target_date) +
                                '-observation-plan-polar.png')
        pfig.savefig(filepath)

