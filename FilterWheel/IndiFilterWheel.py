# Basic stuff
import io
import json
import logging

# Indi stuff
import PyIndi
from helper.IndiDevice import IndiDevice

class IndiFilterWheel(IndiDevice):
    def __init__(self, indiClient, logger=None, configFileName=None,
                 connectOnCreate=True):
        logger = logger or logging.getLogger(__name__)
        
        if configFileName is None:
          self.configFileName = 'IndiSimulatorFilterWheel.json'
        else:
          self.configFileName = configFileName

        # Now configuring class
        logger.debug('Indi FilterWheel, configuring with file {}'.format(
          self.configFileName))
        # Get key from json
        with open(self.configFileName) as jsonFile:
          data = json.load(jsonFile)
          deviceName = data['FilterWheelName']
          self.filterList = data['FilterList']

        logger.debug('Indi FilterWheel, filterwheel name is: {}'.format(
          deviceName))
      
        # device related intialization
        IndiDevice.__init__(self, logger=logger, deviceName=deviceName,
          indiClient=indiClient)
        if connectOnCreate:
            self.connect()
            self.initFilterWheelConfiguration()

        # Finished configuring
        self.logger.debug('Indi FilterWheel configured successfully')

    def onEmergency(self):
        self.logger.debug('Indi FilterWheel: on emergency routine started...')
        pass
        self.logger.debug('Indi FilterWheel: on emergency routine finished')

    def initFilterWheelConfiguration(self):
        pass

    def setFilter(self, name):
        self.logger.debug('Indi FilterWheel setting filter {}'.format(name)) 
        self.setFilterNumber(self.filters()[name])

    def setFilterNumber(self, number):
        self.logger.debug('Indi FilterWheel setting filter number {}'.format(
                          number)) 
        self.setNumber('FILTER_SLOT', {'FILTER_SLOT_VALUE': number})

    def filters(self):
        ctl = self.getPropertyVector('FILTER_NAME', 'text')
        filters = [(x.text, IndiFilterWheel.__name2number(x.name)) for x in ctl]
        return dict(filters)

    def currentFilter(self):
        ctl = self.getPropertyVector('FILTER_SLOT', 'number')
        number = int(ctl[0].value)
        return number, self.filterName(number)

    def filterName(self, number):
        return [a for a, b in self.filters().items() if b == number][0]

    @staticmethod
    def __name2number(name):
        return int(name.replace('FILTER_SLOT_NAME_', ''))

    @staticmethod
    def __number2name(number):
        return 'FILTER_SLOT_NAME_{0}'.format(number)

    def __str__(self):
        filters = [(n, i) for n, i in self.filters().items()]
        filters.sort(key=lambda x: x[1])
        filters = ['{0} ({1})'.format(i[0], i[1]) for i in filters]
        return 'FilterWheel, current filter: {}, available: {}'.format(
            self.currentFilter(), ', '.join(filters))

    def __repr__(self):
        return self.__str__()
