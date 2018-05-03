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
        self.logger.debug('Indi Mount: on emergency routine started...')
        self.abortMotion()
        self.park()
        self.logger.debug('Indi Mount: on emergency routine finished')


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
        self.logger.info('Indi Mount setting coord: {}'.format(rahour_decdeg)) 
        self.setNumber('EQUATORIAL_EOD_COORD', rahour_decdeg)

        try:
            #Read Only property set once requested EQUATORIAL_EOD_COORD is
            #accepted by driver.
            res = self.getNumber('TARGET_EOD_COORD')
            self.logger.info('Indi Mount, coordinates accepted by driver, '
                'Mount driver TARGET_EOD_COORD are: {} and '
                'sent EQUATORIAL_EOD_COORD are: {}'.format(rahour_decdeg,res))
        except Exception as e:
            self.logger.error('Indi Mount, coordinates not accepted by driver '
                              ': {}'.format(e))

    def on_coord_set(self, what_to_do='TRACK'):
        """ What do to with the new set of given coordinates
            Can be either:
            SLEW: Slew to a coordinate and stop upon receiving coordinates.
            TRACK: Slew to a coordinate and track upon receiving coordinates.
            SYNC: Accept current coordinate as correct upon recving coordinates
        """
        self.setSwitch('ON_COORD_SET', [what_to_do])

    # This does not work with simulator
    #def setTrackingMode(self, tracking_mode='TRACK_SIDEREAL'):
    #    self.logger.debug('Indi Mount: Setting tracking mode: {}'.format(
    #                      tracking_mode))
    #    self.setSwitch('TELESCOPE_TRACK_RATE', [tracking_mode])

    def abortMotion(self):
        self.logger.debug('Indi Mount: Abort Motion')
        self.setSwitch('TELESCOPE_ABORT_MOTION', ['ABORT_MOTION'])

    def park(self):
        self.logger.debug('Indi Mount: Park')
        self.setSwitch('TELESCOPE_PARK', ['PARK'])

    def unPark(self):
        self.logger.debug('Indi Mount: unPark')
        self.setSwitch('TELESCOPE_PARK', ['UNPARK'])

    def set_slew_rate(self, slew_rate='SLEW_FIND'):
        self.logger.debug('Indi Mount: Setting slewing rate: {}'.format(
                          slew_rate))
        self.setSwitch('TELESCOPE_SLEW_RATE', [slew_rate])

    def isParked(self):
        status = self.getOnSwitchValueVector('TELESCOPE_PARK') 
        if status['PARK']:
            return true
        else:
            return false

    def __str__(self):
        return 'Mount: {}, current position: {}'.format(
            self.name, self.getCurrentCoord())

    def __repr__(self):
        return self.__str__()