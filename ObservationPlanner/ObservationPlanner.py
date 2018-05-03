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
                theta_labels.append('N ' + '\n' + str(label_angle) + degree_sign
                                    + ' Azimuth [deg]')
            elif label_angle == 45:
                theta_labels.append('') #Let some space for r axis labels
            elif label_angle == 90:
                theta_labels.append('E' + '\n' + str(label_angle) + degree_sign)
            elif label_angle == 180:
                theta_labels.append('S' + '\n' + str(label_angle) + degree_sign)
            elif label_angle == 270:
                theta_labels.append('W' + '\n' + str(label_angle) + degree_sign)
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
                self.targetList.items(),colors):
            target_coord = SkyCoord.from_name(target_name)
            #target_coord = SkyCoord(70.839125*AU.deg, 47.357167*AU.deg)

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
            pol_ax.plot(np.deg2rad(np.array(target_altazs.az)),
                90-np.array(target_altazs.alt), color=color, label=target_name)

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

        # Configure airmass plot, both utc and regular time
        pol_ax.legend(loc='upper left')

        plt.show()  