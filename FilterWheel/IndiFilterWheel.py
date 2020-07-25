# Basic stuff
import io
import json
import logging

# Indi stuff
from Base.Base import Base
from helper.IndiDevice import IndiDevice

class IndiFilterWheel(IndiDevice, Base):
    def __init__(self, config, connect_on_create=True):
        
        if config is None:
            config = dict(
                module="IndiFilterWheel",
                filterwheel_name="Filter Simulator",
                filter_list=dict(
                    Luminance=1,
                    Red=2,
                    Green=3,
                    Blue=4,
                    H_Alpha=5,
                    OIII=6,
                    SII=7,
                    LPR=8),
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"
                ))

        device_name = config['filterwheel_name']
        self.filterList = config['filter_list']

        logger.debug('Indi FilterWheel, filterwheel name is: {}'.format(
                     device_name))
      
        # device related intialization
        IndiDevice.__init__(self, logger=logger, device_name=device_name,
                            indi_client_config=config["indi_client"])
        if connect_on_create:
            self.connect()

        # Finished configuring
        self.logger.debug('configured successfully')

    def on_emergency(self):
        self.logger.debug('on emergency routine started...')
        set_filter_number(1)
        self.logger.debug('on emergency routine finished')

    def initFilterWheelConfiguration(self):
        for filterName, filterNumber in self.filterList.items():
            self.logger.debug('IndiFilterWheel: Initializing filter number {}'
                              ' to filter name {}'.format(filterNumber,
                              filterName))
            self.set_text('FILTER_NAME',{'FILTER_SLOT_NAME_{}'.format(
                                         filterNumber):filterName})

    def set_filter(self, name):
        self.logger.debug('setting filter {}'.format(name)) 
        self.set_filter_number(self.filters()[name])

    def set_filter_number(self, number):
        self.logger.debug('setting filter number {}'.format(
                          number)) 
        self.set_number('FILTER_SLOT', {'FILTER_SLOT_VALUE': number})

    def currentFilter(self):
        ctl = self.get_prop('FILTER_SLOT', 'number')
        number = int(ctl[0].value)
        return number, self.filterName(number)

    def filters(self):
        ctl = self.get_prop('FILTER_NAME', 'text')
        filters = [(x.text, IndiFilterWheel.__name2number(x.name)) for x in ctl]
        return dict(filters)

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
