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
    def __init__(self, connect_on_create=True, logger=None,
                 config=None):
        logger = logger or logging.getLogger(__name__)
        
        assert (config is not None) and (type(config)==dict), ("Please provide "
            "config as dictionary, with mount_name")
        device_name = config['mount_name']
        logger.debug('Indi Mount, mount name is: {}'.format(
            device_name))
        # device related intialization
        IndiDevice.__init__(self, logger=logger, device_name=device_name,
            indi_client_config=config["indi_client"])
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
        Subtleties here: coord should be given as Equatorial astrometric epoch
        of date coordinate (eod):  RA JNow RA, hours,  DEC JNow Dec, degrees +N

        As our software only manipulates J2000. we decided to convert to jnow
        for the generic case
        """
        fk5_now = FK5(equinox=Time.now())
        coord_jnow = coord.transform_to(fk5_now)
        rahour_decdeg = {'RA': coord_jnow.ra.hour,
                         'DEC': coord_jnow.dec.degree}
        if self.is_parked:
            self.logger.warning(f"Cannot set coord: {rahour_decdeg} because "
                                f"mount is parked")
        else:
            self.logger.info(f"Now setting JNow coord: {rahour_decdeg}")
            self.set_number('EQUATORIAL_EOD_COORD', rahour_decdeg, sync=True,
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

    def abort_motion(self):
        self.logger.debug('Abort Motion')
        self.set_switch('TELESCOPE_ABORT_MOTION', ['ABORT_MOTION'])

    def park(self):
        self.logger.debug('Slewing to Park')
        self.set_switch('TELESCOPE_PARK', ['PARK'])

    def unpark(self):
        self.logger.debug('unpark')
        self.set_switch('TELESCOPE_PARK', ['UNPARK'])

    def get_guide_rate(self):
        """
            GUIDE_RATE number should look like this:
            {'GUIDE_RATE_WE': {
                 'name': 'GUIDE_RATE_WE',
                 'label': 'W/E Rate', 'value': 0.5,
                 'min': 0.0,
                 'max': 1.0,
                 'step': 0.1,
                 'format': '%g'},
             'GUIDE_RATE_NS': {
                 'name': 'GUIDE_RATE_NS',
                 'label': 'N/S Rate',
                 'value': 0.5,
                 'min': 0.0,
                 'max': 1.0,
                 'step': 0.1,
                 'format': '%g'},
             'state': 'OK'}
        """
        guide_dict = self.get_number('GUIDE_RATE')
        self.logger.debug(f"Got mount guidinging rate: {guide_dict}")
        guide_rate = {}
        guide_rate['NS'] = guide_dict['GUIDE_RATE_NS']['value']
        guide_rate['WE'] = guide_dict['GUIDE_RATE_WE']['value']
        self.logger.debug(f"Got mount guiding rate: {guide_rate}")
        return guide_rate

    def set_guide_rate(self, guide_rate={'NS':0.5,'WE':0.5}):
        """
        """
        assert(all([v<=1 for k,v in guide_rate.items()]))
        guide_dict = {'GUIDE_RATE_NS': guide_rate['NS'],
                      'GUIDE_RATE_WE': guide_rate['WE']}
        self.set_number('GUIDE_RATE', guide_dict, sync=True)


    def get_slew_rate(self):
        """
            Slew rate switch looks like this:
            {'1x': {'name': '1x', 'label': 'Guide', 'value': False},
             '2x': {'name': '2x', 'label': 'Centering', 'value': False},
             '3x': {'name': '3x', 'label': 'Find', 'value': True},
             '4x': {'name': '4x', 'label': 'Max', 'value': False},
             'state': 'IDLE'}
        """
        slew_dict = self.get_switch('TELESCOPE_SLEW_RATE')
        self.logger.debug(f"Got mount slewing rate dict: {slew_dict}")
        slew_rate = [v for k,v in slew_dict.items() if
                         ('value' in v and v['value'])]
        self.logger.debug(f"Got mount slewing rate: {slew_rate}")
        if len(slew_rate) == 1:
            return slew_rate[0]
        else:
            return {'name': None, 'label': None, 'value': None}

    def set_slew_rate(self, slew_rate='3x'):
        """
        Should be one of (by order of speed):
            -1x (equiv to SLEW_GUIDE)
            -2x (equiv to SLEW_CENTERING)
            -3x (equiv to SLEW_FIND)
            -4x (equiv to SLEW_MAX)
        """
        slew_dict = self.get_switch('TELESCOPE_SLEW_RATE')
        self.logger.debug(f"Setting mount slewing rate: {slew_rate} while "
                          f"dictionary is {slew_dict}")
        if slew_rate in slew_dict:
            self.set_switch('TELESCOPE_SLEW_RATE', [slew_rate])
        else:
            msg = f"Trying to set mount slewing rate: {slew_rate} while "\
                  f"dictionary is {slew_dict}"
            raise RuntimeError(msg)

    def get_pier_side(self):
        ''' GEM Pier Side
            PIER_EAST Mount on the East side of pier (Pointing West).
            PIER_WEST Mount on the West side of pier (Pointing East).
            WARNING: does not work with simulator
        '''
        pier_side = self.get_switch('TELESCOPE_PIER_SIDE')
        self.logger.debug(f"Got mount pier side: {pier_side}")
        return ret

    def get_track_mode(self):
        ''' Track mode switch looks like this
         {'TRACK_SIDEREAL': 
              {'name': 'TRACK_SIDEREAL', 'label': 'Sidereal', 'value': False},
          'TRACK_CUSTOM':
              {'name': 'TRACK_CUSTOM', 'label': 'Custom', 'value': False},
          'state': 'OK'}
        '''
        track_dict = self.get_switch('TELESCOPE_TRACK_MODE')
        self.logger.debug(f"Got mount tracking rate dict: {track_dict}")
        track_mode = [v for k,v in track_dict.items() if
                         ('value' in v and v['value'])]
        self.logger.debug(f"Got mount tracking mode: {track_mode}")
        if len(track_mode) == 1:
            return track_mode[0]
        else:
            return {'name': None, 'label': None, 'value': None}


    # This does not work with simulator
    def set_track_mode(self, track_mode='TRACK_SIDEREAL'):
        ''' Available track mode
            TELESCOPE_TRACK_MODE Switch:
                TRACK_SIDEREAL: Track at sidereal rate.
                TRACK_SOLAR: Track at solar rate.
                TRACK_LUNAR: Track at lunar rate.
                TRACK_CUSTOM: custom
        '''
        track_dict = self.get_switch('TELESCOPE_TRACK_MODE')
        self.logger.debug(f"Setting mount tracking rate: {track_mode} while "
                          f"dictionary is {track_dict}")
        if track_mode in track_dict:
            self.set_switch('TELESCOPE_TRACK_MODE', [track_mode])
        else:
            msg = f"Trying to set mount tracking rate: {track_mode} while "\
                  f"dictionary is {track_dict}"
            raise RuntimeError(msg)

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
        self.logger.debug(f"Received current JNOW coordinates {rahour_decdeg}")
        ret = SkyCoord(ra=rahour_decdeg['RA']['value']*u.hourangle,
                       dec=rahour_decdeg['DEC']['value']*u.degree,
                       frame='cirs',
                       obstime=Time.now())
        self.logger.debug(f"Received coordinates in JNOw/CIRS from mount: "
                          f"{ret}")
        return ret

###############################################################################
# Monitoring related stuff
###############################################################################

    def __str__(self):
        return 'Mount: {}'.format(self.device_name)

    def __repr__(self):
        return self.__str__()
