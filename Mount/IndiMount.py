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
from astropy.coordinates import FK5
#c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs', equinox='J2000.0')

class IndiMount(IndiDevice):
    """
        We recall that, with indi, telescopes can be adressed using JNow/J2000
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

        There is also another important switch we need to use: pier side
        
        TELESCOPE_PIER_SIDE : GEM Pier Side
            PIER_EAST : Mount on the East side of pier (Pointing West).
            PIER_WEST : Mount on the West side of pier (Pointing East).
    """
    def __init__(self, indi_client, connect_on_create=True, logger=None,
                 config=None):
        logger = logger or logging.getLogger(__name__)
        
        assert (config is not None) and (type(config)==dict), ("Please provide "
            "config as dictionary, with mount_name")
        device_name = config['mount_name']
        logger.debug('Indi Mount, mount name is: {}'.format(
            device_name))
        # device related intialization
        IndiDevice.__init__(self, logger=logger, device_name=device_name,
            indi_client=indi_client)
        try:
            #try to get timezone from config file
            self.gps = dict(latitude = self.config['observatory']['latitude'],
                            longitude = self.config['observatory']['longitude'],
                            elevation = self.config['observatory']['elevation'])
        except:
            self.gps = None

        if connect_on_create:
            self.connect()

        # Finished configuring
        self.logger.debug('Indi Mount configured successfully')

    def on_emergency(self):
        self.logger.debug('on emergency routine started...')
        self.abort_motion()
        self.park()
        self.logger.debug('on emergency routine finished')

    def slew_to_coord_and_stop(self, coord):
        """
            Slew to a coordinate and stop upon receiving coordinates.
        """
        self.on_coord_set('SLEW')
        self.set_coord(coord)

    def slew_to_coord_and_track(self, coord):
        """
            Slew to a coordinate and track upon receiving coordinates.
        """
        self.on_coord_set('TRACK')
        self.set_coord(coord)

    def sync_to_coord(self, coord):
        """
           Accept current coordinate as correct upon receiving coordinates.
        """
        self.on_coord_set('SYNC')
        self.set_coord(coord)

    def set_coord(self, coord):
        """
        Subteletie here: coord should be given as Equatorial astrometric epoch
        of date coordinate (eod):  RA JNow RA, hours,  DEC JNow Dec, degrees +N

        As our software only manipulates J2000. we decided to convert to jnow
        for the generic case
        """
        fk5_now = FK5(equinox=Time.now())
        coord_jnow = coord.transform_to(fk5_now)
        rahour_decdeg = {'RA': coord_jnow.ra.hour,
                         'DEC': coord_jnow.dec.degree}
        if self.is_parked:
            self.logger.warning('Cannot set coord: {} because mount is parked'
                                ''.format(rahour_decdeg))
        else:
            self.logger.info('Now setting JNow coord: {}'.format(
                             rahour_decdeg)) 
            self.setNumber('EQUATORIAL_EOD_COORD', rahour_decdeg, sync=True,
                           timeout=180)

    def on_coord_set(self, what_to_do='TRACK'):
        """ What do to with the new set of given coordinates
            Can be either:
            SLEW: Slew to a coordinate and stop upon receiving coordinates.
            TRACK: Slew to a coordinate and track upon receiving coordinates.
            SYNC: Accept current coordinate as correct upon recving coordinates
        """
        self.logger.debug('Setting ON_COORD_SET behaviour: {}'.format(
                          what_to_do))
        self.set_switch('ON_COORD_SET', [what_to_do])

    # This does not work with simulator
    def setTrackRate(self, tracking_mode='TRACK_SIDEREAL'):
        self.logger.debug('Setting tracking mode: {}'.format(
                          tracking_mode))
        self.set_switch('TELESCOPE_TRACK_RATE', [tracking_mode])

    def abort_motion(self):
        self.logger.debug('Abort Motion')
        self.set_switch('TELESCOPE_ABORT_MOTION', ['ABORT_MOTION'])

    def park(self):
        self.logger.debug('Slewing to Park')
        self.set_switch('TELESCOPE_PARK', ['PARK'])

    def unpark(self):
        self.logger.debug('unpark')
        self.set_switch('TELESCOPE_PARK', ['UNPARK'])

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
        self.set_switch('TELESCOPE_SLEW_RATE', [slew_rate])

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
        try:
            ret = self.get_switch('TELESCOPE_TRACK_MODE')
            self.logger.debug('Got track rate: {}'.format(ret))
            # find actual name for which value is true
            v = [k for k,v in ret.items() if v['value']]
            assert len(v) == 1
            return v
        except Exception as e:
            self.logger.error("Cannot retrieve track rate: {}".format(e))
            return "NA"


    # This does not work with simulator
    def set_track_rate(self, track_rate='TRACK_SIDEREAL'):
        self.logger.debug('Setting track rate: {}'.format(
                          track_rate))
        self.set_switch('TELESCOPE_TRACK_MODE', [track_rate])

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
            self.device_name)) 
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
        return 'Mount: {}'.format(self.device_name)

    def __repr__(self):
        return self.__str__()
