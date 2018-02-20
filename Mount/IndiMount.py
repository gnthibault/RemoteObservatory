# Basic stuff
import io
import json
import logging

# Indi stuff
import PyIndi
from helper.IndiDevice import IndiDevice

class IndiMount(IndiDevice):
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


    def slewToCoordAndTrack(self, coord):
        self.logger.debug('Indi Mount slewing to coord {}'.format(
                          coord)) 
        #self.setNumber('FILTER_SLOT', {'FILTER_SLOT_VALUE': number})

    def getCurrentCoord(self):
        #ctl = self.getPropertyVector('FILTER_SLOT', 'number')
        #number = int(ctl[0].value)
        #return number, self.filterName(number)
        return 0

    def setTrackingMode(self, trackingMode='Sideral');
        self.logger.debug('Indi Mount: Setting tracking mode: {}'.format(
                          trackingMode))
        pass

    def setTrackingOn(self);
        self.logger.debug('Indi Mount: Setting tracking on')
        pass

    def setTrackingOff(self);
        self.logger.debug('Indi Mount: Setting tracking off')
        pass

    def park(self):
        self.logger.debug('Indi Mount: Park')
        pass

    def unPark(self):
        self.logger.debug('Indi Mount: unPark')
        pass

    def isParked(self):
        return false

    def onEmergency(self):
        self.logger.debug('Indi Mount: on emergency routine started...')
        self.park()
        self.logger.debug('Indi Mount: on emergency routine finished')

def __str__(self):
        return 'Mount: {}, current position: {}'.format(
            self.name, self.getCurrentCoord())

    def __repr__(self):
        return self.__str__()
