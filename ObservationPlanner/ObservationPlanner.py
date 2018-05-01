# Basic stuff
import datetime
import json
import logging

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
from astroplan.plots import plot_sky
from astroplan import moon_illumination

# Plotting stuff
import matplotlib.pyplot as plt

class ObservationPlanner:

    def __init__(self, ntpServ, obs, configFileName=None, logger=None):
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

        # Finished configuring
        self.logger.debug('ObservationPlanner configured successfully')

      
    def getTargetList(self):
        return self.targetList

    def showObservationPlan(self):
        #Time margin, in hour
        tmh = 8
        tmh_range = np.arange(tmh+1, dtype=float)*2 -tmh
        date_font_size = 8
        resolution = 400

        #time stuff
        midnight = self.ntpServ.getNextMidnightInUTC()

        #UTC range
        utc_tmh_range = [midnight+datetime.timedelta(hours=i) for i in
                         tmh_range]
        #local time range
        local_tmh_range = [self.ntpServ.convert_to_local_time(i) for i in
                           utc_tmh_range]
        #Astropy ranges
        midnight = ATime(midnight)
        relative_time_frame = np.linspace(-tmh, tmh, resolution)*AU.hour
        absolute_time_frame = midnight + relative_time_frame
        altaz_frame = AltAz(obstime=absolute_time_frame,
                            location=self.obs.getAstropyEarthLocation())

        afig = plt.figure(0, figsize=(25,15))
        # Configure airmass subplot
        air_ax = afig.add_subplot(2,1,1)
        # Configure altaz subplot
        alt_ax = afig.add_subplot(2,1,2)

        #Configure altitude plot and plot sun/moon illumination
        sun_altazs = get_sun(absolute_time_frame).transform_to(altaz_frame)
        moon_altazs = get_moon(absolute_time_frame).transform_to(altaz_frame)
         
        # Plot Sun
        alt_ax.plot(relative_time_frame, sun_altazs.alt, color='gold',
                    label='Sun')
        #Plot Moon
        moon_label = 'Moon {number:.{digits}f} %'.format(
            number=moon_illumination(midnight)*100.0, digits=0)
        alt_ax.plot(relative_time_frame, moon_altazs.alt, color='silver',
                 label=moon_label)

        #grey sky when sun lower than -0 deg
        grey_sun_range = sun_altazs.alt < -0*AU.deg
        alt_ax.fill_between(relative_time_frame, 0, 90,
                            grey_sun_range, color='0.5', zorder=0)
        #Dark sky when sun is below -18 deg
        dark_sun_range = sun_altazs.alt < -18*AU.deg
        alt_ax.fill_between(relative_time_frame, 0, 90,
                            dark_sun_range, color='0', zorder=0)
        #grey sky when sun is low (<18deg) but moon has risen
        grey_moon_range = np.logical_and(moon_altazs.alt > -5*AU.deg,
                                         sun_altazs.alt < -18*AU.deg)
        grey_moon_intensity = 0.25*moon_illumination(midnight)
        alt_ax.fill_between(relative_time_frame, 0, 90,
            grey_moon_range, color='{number:.{digits}f}'.format(
            number=grey_moon_intensity, digits=2), zorder=0)


        nb_target = len(self.targetList)
        cm = plt.get_cmap('gist_rainbow')
        colors = [cm(1.*i/nb_target) for i in range(nb_target)]

        for (target_name, imaging_program), color in zip(
                self.targetList.items(),colors):
            target_coord = SkyCoord.from_name(target_name)

            # Compute altazs for target
            target_altazs = target_coord.transform_to(altaz_frame)

            # First plot airmass
            air_ax.plot(relative_time_frame, target_altazs.secz,
                        label=target_name,
                        color=color)

            # Then plot altitude along with sun/moon
            alt_ax.scatter(relative_time_frame, target_altazs.alt,
                        label=target_name, lw=0, s=8,
                        color=color)

            # Then plot environment aware polar altaz map
            #https://astroplan.readthedocs.io/en/latest/api/astroplan.Observer.html#astroplan.Observer.altaz
            #fig = plt.figure(figsize=(15,15))
            #ax = fig.add_subplot()
            #plot_sky(altair, observer, absolute_time_frame)

        # Configure airmass plot, both utc and regular time
        air_ax.legend(loc='upper left')
        air_ax.set_xlim(-tmh, tmh)
        air_ax.set_xticks(tmh_range)
        air_ax.set_xticklabels(utc_tmh_range, rotation=15,
                               fontsize=date_font_size)
        air_ax.set_xlabel('UTC Time')
        air_ax2 = air_ax.twiny()
        air_ax2.set_xlim(-tmh, tmh)
        air_ax2.set_xticks(tmh_range)
        air_ax2.set_xticklabels(local_tmh_range, rotation=15,
                               fontsize=date_font_size)
        air_ax2.set_xlabel('Local time ({})'.format(self.ntpServ.timezone.zone))
        air_ax.set_ylim(1, 4)
        air_ax.set_ylabel('Airmass, [Sec(z)]')

        #Configure altitude plot, both utc and regular time
        alt_ax.legend(loc='upper left')
        alt_ax.set_xlim(-tmh, tmh)
        alt_ax.set_xticks(tmh_range)
        alt_ax.set_xticklabels(utc_tmh_range, rotation=15,
                               fontsize=date_font_size)
        alt_ax.set_xlabel('UTC Time')
        alt_ax2 = alt_ax.twiny()
        alt_ax2.set_xlim(-tmh, tmh)
        alt_ax2.set_xticks(tmh_range)
        alt_ax2.set_xticklabels(local_tmh_range, rotation=15,
                                fontsize=date_font_size)
        alt_ax2.set_xlabel('Local time ({})'.format(self.ntpServ.timezone.zone))
        alt_ax.set_ylim(0, 90)
        alt_ax.set_ylabel('Altitude [deg]')

        afig.tight_layout()

        plt.show()  
