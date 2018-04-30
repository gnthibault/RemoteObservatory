# Basic stuff
import json
import logging

# Numerical stuff
import numpy as np

# Astropy stuff
from astropy.coordinates import get_sun
from astropy import units as AU
from astropy.coordinates import AltAz
from astropy.coordinates import EarthLocation
from astropy.coordinates import SkyCoord
from astropy.time import Time as ATime

# Astroplan stuff
from astroplan.plots import plot_sky

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


    def getAstropyTimeFromUTC(self):
        return ATime(self.ntpServ.getUTCFromNTP())
      
      

    def getTargetList(self):
        return self.targetList

    def showObservationComparison(self):
        #location = self.getAstropyEarthLocation() TODO TN
        from astropy import units as u
        location = EarthLocation(lat=41.3*u.deg, lon=-74*u.deg, height=390*u.m)
        

        utcoffset = -4*AU.hour # Eastern Daylight Time TODO

        #Time margin, in hour
        tmh = 8

        #TODO TN get sun rise and sunset from server
        midnight = ATime('2012-7-13 00:00:00') - utcoffset
        relative_time_frame = np.linspace(-tmh, tmh, 100)*AU.hour
        absolute_time_frame = midnight + relative_time_frame
        altaz_frame = AltAz(obstime=absolute_time_frame, location=location)

        # Compute altazs for sun
        sun_altazs = get_sun(absolute_time_frame).transform_to(altaz_frame)

        # Configure airmass plot
        afig = plt.figure(0, figsize=(25,15))
        air_ax = afig.add_subplot(2,1,1)

        #Configure altitude plot and plot sun/moon stuff (todo moon)
        alt_ax = afig.add_subplot(2,1,2)
        alt_ax.plot(relative_time_frame, sun_altazs.alt, color='y',
                 label='Sun')
        alt_ax.fill_between(relative_time_frame, 0, 90,
                         sun_altazs.alt < -0*AU.deg, color='0.5', zorder=0)
        alt_ax.fill_between(relative_time_frame, 0, 90,
                         sun_altazs.alt < -18*AU.deg, color='k', zorder=0)


        for target_name, imaging_program in self.targetList.items():
            target_coord = SkyCoord.from_name(target_name)

            # Compute altazs for target
            target_altazs = target_coord.transform_to(altaz_frame)

            # First plot airmass
            air_ax.plot(relative_time_frame, target_altazs.secz,
                        label=target_name)

            # Then plot altitude along with sun/moon
            alt_ax.scatter(relative_time_frame, target_altazs.alt,
                        c=target_altazs.az, label=target_name, lw=0, s=8)

            # Then plot environment aware polar altaz map
            #https://astroplan.readthedocs.io/en/latest/api/astroplan.Observer.html#astroplan.Observer.altaz
            fig = plt.figure(figsize=(15,15))
            ax = fig.add_subplot()
            #plot_sky(altair, observer, absolute_time_frame)

        # Configure airmass plot
        air_ax.legend(loc='upper left')
        air_ax.set_xlim(-tmh, tmh)
        air_ax.set_ylim(1, 4)
        air_ax.set_xlabel('Hours from EDT Midnight')
        air_ax.set_ylabel('Airmass, secant fo zenith angle [Sec(z)]')

        #Configure altitude plot
        #alt_ax.set_colorbar().set_label('Azimuth [deg]') TODO TN
        alt_ax.legend(loc='upper left')
        alt_ax.set_xlim(-tmh, tmh)
        alt_ax.set_xticks(np.arange(tmh+1)*2 -tmh) #TODO TN proper xticks
        alt_ax.set_ylim(0, 90)
        alt_ax.set_xlabel('Hours from EDT Midnight')
        alt_ax.set_ylabel('Altitude [deg]')

        plt.show()  
