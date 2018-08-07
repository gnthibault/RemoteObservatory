# Basic stuff
import ctypes
import time

# Indi stuff
import PyIndi
from helper.IndiClient import IndiClient

class IndiDevice:
    defaultTimeout = 30
    propTypeToGetterMap = {
        'blob': 'getBLOB',
        'light': 'getLight',
        'number': 'getNumber',
        'switch': 'getSwitch',
        'text': 'getText'
    }
    def __init__(self, logger, deviceName, indiClient):
        self.logger = logger or logging.getLogger(__name__)
    
        self.deviceName = deviceName
        self.indiClient = indiClient
        self.timeout = IndiDevice.defaultTimeout
        self.device = None
        self.interfaces = None

        # Set of useful dictionaries that can be overriden to change behaviour
        self.__state_to_str = { PyIndi.IPS_IDLE: 'IDLE',
                                PyIndi.IPS_OK: 'OK',
                                PyIndi.IPS_BUSY: 'BUSY',
                                PyIndi.IPS_ALERT: 'ALERT' }
        self.__switch_types = { PyIndi.ISR_1OFMANY: 'ONE_OF_MANY',
                                PyIndi.ISR_ATMOST1: 'AT_MOST_ONE',
                                PyIndi.ISR_NOFMANY: 'ANY'}
        self.__type_to_str = { PyIndi.INDI_NUMBER: 'number',
                               PyIndi.INDI_SWITCH: 'switch',
                               PyIndi.INDI_TEXT: 'text',
                               PyIndi.INDI_LIGHT: 'light',
                               PyIndi.INDI_BLOB: 'blob',
                               PyIndi.INDI_UNKNOWN: 'unknown' }

    @property
    def is_connected(self):
        return self.device.isConnected()

    @property
    def name(self):
        return self.deviceName

    def __findDevice(self):
        self.logger.debug('IndiDevice: asking indiClient to look for device {}'
                          ''.format(self.deviceName))
        if self.device is None:
            started = time.time()
            while not self.device:
                self.device = self.indiClient.getDevice(self.deviceName)
                if 0 < self.timeout < time.time() - started:
                    self.logger.error('IndiDevice: Timeout while waiting for '
                                      ' device {}'.format(self.deviceName))
                    raise RuntimeError('IndiDevice Timeout while waiting for '
                                       'device {}'.format(self.deviceName))
                time.sleep(0.01)
            self.logger.debug('Indi Device: indiClient has found device {}'
                              ''.format(self.deviceName))
        else:
            self.logger.warning('Device {} already found'.format(
                                self.deviceName))
    def find_interfaces(self, device):
        interface = device.getDriverInterface()
        interface.acquire()
        device_interfaces = int(ctypes.cast(interface.__int__(),
                                ctypes.POINTER(ctypes.c_uint16)).contents.value)
        interface.disown()
        interfaces = {
            PyIndi.BaseDevice.GENERAL_INTERFACE: 'general', 
            PyIndi.BaseDevice.TELESCOPE_INTERFACE: 'telescope',
            PyIndi.BaseDevice.CCD_INTERFACE: 'ccd',
            PyIndi.BaseDevice.GUIDER_INTERFACE: 'guider',
            PyIndi.BaseDevice.FOCUSER_INTERFACE: 'focuser',
            PyIndi.BaseDevice.FILTER_INTERFACE: 'filter',
            PyIndi.BaseDevice.DOME_INTERFACE: 'dome',
            PyIndi.BaseDevice.GPS_INTERFACE: 'gps',
            PyIndi.BaseDevice.WEATHER_INTERFACE: 'weather',
            PyIndi.BaseDevice.AO_INTERFACE: 'ao',
            PyIndi.BaseDevice.DUSTCAP_INTERFACE: 'dustcap',
            PyIndi.BaseDevice.LIGHTBOX_INTERFACE: 'lightbox',
            PyIndi.BaseDevice.DETECTOR_INTERFACE: 'detector',
            PyIndi.BaseDevice.ROTATOR_INTERFACE: 'rotator',
            PyIndi.BaseDevice.AUX_INTERFACE: 'aux'
        }
        interfaces = (
            [interfaces[x] for x in interfaces if x & device_interfaces])
        self.logger.debug('device {}, interfaces are: {}'.format(
            self.deviceName, interfaces))
        return interfaces

    def connect(self):
        # Try first to ask server to give us the device handle, through client
        self.__findDevice()

        # Now connect
        if self.device.isConnected():
            self.logger.warn('IndiDevice: already connected to device {}'
                             ''.format(self.deviceName))
            return
        self.logger.info('IndiDevice: connecting to device {}'.format(
                         self.deviceName))
        # get interfaces
        self.interfaces = self.find_interfaces(self.device)
        # set the corresponding switch to on
        self.setSwitch('CONNECTION', ['CONNECT'])

    def get_values(self, ctl_name, ctl_type):
        return dict(map(lambda c: (c.name, c.value),
                        self.get_prop(ctl_name, ctl_type)))

    def get_switch(self, name, ctl=None):
        return self.get_prop_dict(name, 'switch',
                                  lambda c: {'value': c.s == PyIndi.ISS_ON},
                                  ctl)

    def get_text(self, name, ctl=None):
        return self.get_prop_dict(name, 'text',
                                  lambda c: {'value': c.text},
                                  ctl)

    def get_number(self, name, ctl=None):
        return self.get_prop_dict(name, 'number',
                                  lambda c: {'value': c.value, 'min': c.min,
                                             'max': c.max, 'step': c.step,
                                             'format': c.format},
                                  ctl)

    def get_light(self, name, ctl=None):
        return self.get_prop_dict(name, 'light',
                                  lambda c: {'value':
                                             self.__state_to_str[c.s]},
                                  ctl)

    def get_prop_dict(self, prop_name, prop_type, transform,
                      prop=None, timeout=None):
        def get_dict(element):
            dest = {'name': element.name, 'label': element.label}
            dest.update(transform(element))
            return dest

        prop = prop if prop else self.get_prop(prop_name, prop_type, timeout)
        return dict((c.name, get_dict(c)) for c in prop)

    def setSwitch(self, name, onSwitches = [], offSwitches = [],
                  sync=True, timeout=None):
        pv = self.get_prop(name, 'switch')
        if pv.r == PyIndi.ISR_ATMOST1 or pv.r == PyIndi.ISR_1OFMANY:
            onSwitches = onSwitches[0:1]
            offSwitches = [s.name for s in pv if s.name not in onSwitches]
        for index in range(0, len(pv)):
            pv[index].s = (PyIndi.ISS_ON if pv[index].name in onSwitches
                else PyIndi.ISS_OFF)
        self.indiClient.sendNewSwitch(pv)
        if sync:
            self.__waitPropStatus(pv, statuses=[PyIndi.IPS_IDLE,
                                                PyIndi.IPS_OK],
                                  timeout=timeout)
        return pv
        
    def setNumber(self, name, valueVector, sync=True, timeout=None):
        pv = self.get_prop(name, 'number', timeout)
        for propertyName, index in self.__getPropVectIndicesHavingValues(
                                   pv, valueVector.keys()).items():
            pv[index].value = valueVector[propertyName]
        self.indiClient.sendNewNumber(pv)
        if sync:
            self.__waitPropStatus(pv, statuses=[PyIndi.IPS_ALERT,
                                                PyIndi.IPS_OK],
                                  timeout=timeout)
        return pv

    def setText(self, propertyName, valueVector, sync=True, timeout=None):
        pv = self.get_prop(propertyName, 'text')
        for propertyName, index in self.__getPropVectIndicesHavingValues(
                                   pv, valueVector.keys()).items():
            pv[index].text = valueVector[propertyName]
        self.indiClient.sendNewText(pv)
        if sync:
            self.__waitPropStatus(pv, timeout=timeout)
        return pv

    def __waitPropStatus(self, prop,\
        statuses=[PyIndi.IPS_OK, PyIndi.IPS_IDLE], timeout=None):
        """Wait for the specified property to take one of the status in param"""

        started = time.time()
        if timeout is None:
            timeout = self.timeout
        while prop.s not in statuses:
            if 0 < timeout < time.time() - started:
                self.logger.debug('IndiDevice: Timeout while waiting for '
                                  'property status {} for device {}'.format(
                                  prop.name, self.deviceName))
                raise RuntimeError('Timeout error while changing property '
                  '{}'.format(prop.name))
            time.sleep(0.01)

    def __getPropVectIndicesHavingValues(self, propertyVector, values):
      """ return dict of name-index of prop that are in values"""
      result = {}
      for i, p in enumerate(propertyVector):
        if p.name in values:
          result[p.name] = i
      return result

    def get_prop(self, propName, propType, timeout=None):
        """ Return the value corresponding to the given propName"""
        prop = None
        attr = IndiDevice.propTypeToGetterMap[propType]
        if timeout is None:
            timeout = self.timeout
        started = time.time()
        while not(prop):
            prop = getattr(self.device, attr)(propName)
            if not prop and 0 < timeout < time.time() - started:
                self.logger.debug('Timeout while waiting for '
                                  'property {} of type {}  for device {}'
                                  ''.format(propName,propType,self.deviceName))
                raise RuntimeError('Timeout finding property {}'.format(
                                   propName))
            time.sleep(0.01)
        return prop

    def hasProperty(self, propName, propType):
        try:
            self.get_prop(propName, propType, timeout=1)
            return True
        except:
            return False
 
