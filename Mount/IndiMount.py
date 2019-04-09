# Basic stuff
import io
import json
import logging

# Indi stuff
import PyIndi
from helper.IndiDevice import IndiDevice

# Astropy stuff
from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord
from astropy.coordinates import ICRS
from astropy.coordinates import ITRS
from astropy.coordinates import EarthLocation
#c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs', equinox='J2000.0')

class IndiMount(IndiDevice):
    """
        We recall that, with indi, telescopes should be adressed using JNow
        coordinates, see:
        http://indilib.org/develop/developer-manual/101-standard-properties.html#h3-telescopes

        EQUATORIAL_EOD_COORD:
        Equatorial astrometric epoch of date coordinate
        RA JNow RA, hours
        DEC JNow Dec, degrees +N
        
        EQUATORIAL_COORD:
        Equatorial astrometric J2000 coordinate:
        RA  J2000 RA, hours
        DEC J2000 Dec, degrees +N
        
        HORIZONTAL_COORD:
        topocentric coordinate
        ALT Altitude, degrees above horizon
        AZ Azimuth, degrees E of N
    """
    def __init__(self, indiClient, connectOnCreate=True, logger=None,
                 config=None):
        logger = logger or logging.getLogger(__name__)
        
        if config is None:
            config = self.config
        deviceName = config['mount_name']
        logger.debug('Indi Mount, mount name is: {}'.format(
            deviceName))
        # device related intialization
        IndiDevice.__init__(self, logger=logger, deviceName=deviceName,
            indiClient=indiClient)
        try:
            #try to get timezone from config file
            self.gps = dict(latitude = self.config['observatory']['latitude'],
                            longitude = self.config['observatory']['longitude'],
                            elevation = self.config['observatory']['elevation'])
        except:
            self.gps = None

      

        if connectOnCreate:
            self.connect()

        # Finished configuring
        self.logger.debug('Indi Mount configured successfully')

    def onEmergency(self):
        self.logger.debug('on emergency routine started...')
        self.abortMotion()
        self.park()
        self.logger.debug('on emergency routine finished')

    def slew_to_coord_and_stop(self, coord):
        self.on_coord_set('SLEW')
        self.set_coord(coord)

    def slew_to_coord_and_track(self, coord):
        self.on_coord_set('TRACK')
        self.set_coord(coord)

    def sync_to_coord(self, coord):
        self.on_coord_set('SYNC')
        self.set_coord(coord)

    def set_coord(self, coord):
        """
        Big concern here: coord should be given as Equatorial astrometric epoch
        of date coordinate (eod):  RA JNow RA, hours,  DEC JNow Dec, degrees +N

        We found an interesting SO post explaining how to get that from astropy
        https://stackoverflow.com/questions/52900678/coordinates-transformation-in-astropy
        """
        #time = Time.now()
        #location = EarthLocation(lat=self.gps['latitude']*u.deg,
        #                         lon=self.gps['longitude']*u.deg,
        #                         height=self.gps['elevation']*u.m)
        #c_itrs = coord.transform_to(ITRS(obstime=time))
        # Calculate local apparent Hour Angle (HA), wrap at 0/24h
        #local_ha = location.lon - c_itrs.spherical.lon
        #local_ha.wrap_at(24*u.hourangle, inplace=True)
        # Calculate local apparent Declination
        #local_dec = c_itrs.spherical.lat
        #coord = SkyCoord(ra=local_ha, dec=local_dec)
        #coord = coord.transform_to(ICRS(equinox='J2000.0'))
        rahour_decdeg = {'RA': coord.ra.hour, 
                         'DEC': coord.dec.degree}
        if self.is_parked:
            self.logger.warning('Cannot set coord: {} because mount is parked'
                                ''.format(rahour_decdeg))
        else:
            self.logger.info('Now setting JNow coord: {}'.format(
                             rahour_decdeg)) 
            self.setNumber('EQUATORIAL_EOD_COORD', rahour_decdeg, sync=True,
                           timeout=180)

        #try:
        #    #Read Only property set once requested EQUATORIAL_EOD_COORD is
        #    #accepted by driver.
        #    res = self.get_number('TARGET_EOD_COORD')
        #    self.logger.debug('Indi Mount, coordinates accepted by driver, '
        #        'Mount driver TARGET_EOD_COORD are: {} and '
        #        'sent EQUATORIAL_EOD_COORD are: {}'.format(rahour_decdeg,res))
        #except Exception as e:
        #    self.logger.error('Indi Mount, coordinates not accepted by driver '
        #                      ': {}'.format(e))

    def on_coord_set(self, what_to_do='TRACK'):
        """ What do to with the new set of given coordinates
            Can be either:
            SLEW: Slew to a coordinate and stop upon receiving coordinates.
            TRACK: Slew to a coordinate and track upon receiving coordinates.
            SYNC: Accept current coordinate as correct upon recving coordinates
        """
        self.logger.debug('Setting ON_COORD_SET behaviour: {}'.format(
                          what_to_do))
        self.setSwitch('ON_COORD_SET', [what_to_do])

    # This does not work with simulator
    def setTrackRate(self, tracking_mode='TRACK_SIDEREAL'):
        self.logger.debug('Setting tracking mode: {}'.format(
                          tracking_mode))
        self.setSwitch('TELESCOPE_TRACK_RATE', [tracking_mode])

    def abortMotion(self):
        self.logger.debug('Abort Motion')
        self.setSwitch('TELESCOPE_ABORT_MOTION', ['ABORT_MOTION'])

    def park(self):
        self.logger.debug('Slewing to Park')
        self.setSwitch('TELESCOPE_PARK', ['PARK'])

    def unpark(self):
        self.logger.debug('unpark')
        self.setSwitch('TELESCOPE_PARK', ['UNPARK'])

    def set_slew_rate(self, slew_rate='SLEW_FIND'):
        """
        Should be one of (by order of speed):
            -SLEW_GUIDE
            -SLEW_CENTERING
            -SLEW_FIND
            -SLEW_MAX
        """
        self.logger.debug('Setting slewing rate: {}'.format(
                          slew_rate))
        self.setSwitch('TELESCOPE_SLEW_RATE', [slew_rate])

    def get_pier_side(self):
        ''' GEM Pier Side
            PIER_EAST Mount on the East side of pier (Pointing West).
            PIER_WEST Mount on the West side of pier (Pointing East).
            WARNING: does not work with simulator
        '''
        ret = self.get_switch('TELESCOPE_PIER_SIDE')
        self.logger.debug('Got pier side: {}'.format(ret))
        return ret

    def get_track_rate(self):
        ''' Available track rate
            TELESCOPE_TRACK_RATE Switch:
                TRACK_SIDEREAL: Track at sidereal rate.
                TRACK_SOLAR: Track at solar rate.
                TRACK_LUNAR: Track at lunar rate.
                TRACK_CUSTOM: custom
            WARNING: does not work with simulator
        '''
        ret = self.get_switch('TELESCOPE_TRACK_RATE')
        self.logger.debug('Got track rate: {}'.format(ret))
        return ret

    # This does not work with simulator
    def set_track_rate(self, track_rate='TRACK_SIDEREAL'):
        self.logger.debug('Setting track rate: {}'.format(
                          track_rate))
        self.setSwitch('TELESCOPE_TRACK_RATE', [track_rate])

    @property
    def is_parked(self):
        ret = None
        status = self.get_switch('TELESCOPE_PARK')
        self.logger.debug('Got TELESCOPE_PARK status: {}'.format(status))
        if status['PARK']['value']:
            ret = True
        else:
            ret = False
        return ret

    def get_current_coordinates(self):
        self.logger.debug('Asking mount {} for its current coordinates'.format(
            self.deviceName)) 
        rahour_decdeg = self.get_number('EQUATORIAL_EOD_COORD')
        self.logger.debug('Received current JNOW coordinates {}'.format(
                          rahour_decdeg))
        ret = SkyCoord(ra=rahour_decdeg['RA']['value']*u.hourangle,
                       dec=rahour_decdeg['DEC']['value']*u.degree,
                       frame='cirs',
                       obstime=Time.now())
        self.logger.debug('Received coordinates in JNOw/CIRS from mount: {}'
                          ''.format(ret))
        return ret

###############################################################################
# Monitoring related stuff
###############################################################################

    def __str__(self):
        return 'Mount: {}'.format(self.deviceName)

    def __repr__(self):
        return self.__str__()
