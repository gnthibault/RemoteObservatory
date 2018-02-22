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


    def slewToCoordAndTrack(self, coord):
        self.logger.info('Indi Mount slewing to coord RA: {}, DEC: {}'.format(
                          coord.ra.hour, coord.dec.degree)) 
        self.setNumber('EQUATORIAL_EOD_COORD', {'RA': coord.ra.hour, 
                                            'DEC': coord.dec.degree},
                       timeout=120)

    def getCurrentCoord(self):
        #ctl = self.getPropertyVector('FILTER_SLOT', 'number')
        #number = int(ctl[0].value)
        #return number, self.filterName(number)
        return 0

    def setTrackingMode(self, trackingMode='Sideral'):
        self.logger.debug('Indi Mount: Setting tracking mode: {}'.format(
                          trackingMode))
        pass

    def setTrackingOn(self):
        self.logger.debug('Indi Mount: Setting tracking on')
        pass

    def setTrackingOff(self):
        self.logger.debug('Indi Mount: Setting tracking off')
        pass

    def abortMotion(self):
        self.setSwitch('TELESCOPE_ABORT_MOTION', ['ABORT_MOTION'])

    def park(self):
        self.logger.debug('Indi Mount: Park')
        self.setSwitch('TELESCOPE_PARK', ['PARK'])

    def unPark(self):
        self.logger.debug('Indi Mount: unPark')
        self.setSwitch('TELESCOPE_PARK', ['UNPARK'])

    def isParked(self):
        return false

    def __str__(self):
        return 'Mount: {}, current position: {}'.format(
            self.name, self.getCurrentCoord())

    def __repr__(self):
        return self.__str__()
