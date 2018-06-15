# Basic stuff
import io
import json
import logging

# Indi stuff
import PyIndi
from helper.IndiDevice import IndiDevice

# Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord
#c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')

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
    def __init__(self, indiClient, logger=None, configFileName=None,
                 connectOnCreate=True):
        logger = logger or logging.getLogger(__name__)
        
        if configFileName is None:
            self.configFileName = 'IndiSimulatorMount.json'
        else:
            self.configFileName = configFileName

        # Now configuring class
        logger.debug('Indi Mount, configuring with file {}'.format(
            self.configFileName))
        # Get key from json
        with open(self.configFileName) as jsonFile:
            data = json.load(jsonFile)
            deviceName = data['MountName']

        logger.debug('Indi Mount, mount name is: {}'.format(
            deviceName))
      
        # device related intialization
        IndiDevice.__init__(self, logger=logger, deviceName=deviceName,
            indiClient=indiClient)
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
        rahour_decdeg = {'RA': coord.ra.hour, 
                         'DEC': coord.dec.degree}
        if self.isParked():
            self.logger.warning('Cannot set coord: {} because mount is parked'
                                ''.format(rahour_decdeg))
        else:
            self.logger.info('Now setting coord: {}'.format(rahour_decdeg)) 
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
    #def setTrackingMode(self, tracking_mode='TRACK_SIDEREAL'):
    #    self.logger.debug('Setting tracking mode: {}'.format(
    #                      tracking_mode))
    #    self.setSwitch('TELESCOPE_TRACK_RATE', [tracking_mode])

    def abortMotion(self):
        self.logger.debug('Abort Motion')
        self.setSwitch('TELESCOPE_ABORT_MOTION', ['ABORT_MOTION'])

    def park(self):
        self.logger.debug('Park')
        self.setSwitch('TELESCOPE_PARK', ['PARK'])

    def unPark(self):
        self.logger.debug('unPark')
        self.setSwitch('TELESCOPE_PARK', ['UNPARK'])

    def set_slew_rate(self, slew_rate='SLEW_FIND'):
        self.logger.debug('Setting slewing rate: {}'.format(
                          slew_rate))
        self.setSwitch('TELESCOPE_SLEW_RATE', [slew_rate])

    def get_pier_side(self):
        ''' GEM Pier Side
            PIER_EAST Mount on the East side of pier (Pointing West).
            PIER_WEST Mount on the West side of pier (Pointing East).
        '''
        ret = self.get_switch('TELESCOPE_PIER_SIDE')
        self.logger.debug('Got pier side: {}'.format(ret))
        return ret

    def isParked(self):
        status = self.get_switch('TELESCOPE_PARK')
        self.logger.debug('Got TELESCOPE_PARK status: {}'.format(status))
        if status['PARK']['value']:
            return True
        else:
            return False

    def __str__(self):
        return 'Mount: {}'.format(self.name)

    def __repr__(self):
        return self.__str__()
