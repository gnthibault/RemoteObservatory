# Basic stuff
import ctypes
import logging
import time

# Indi stuff
from helper.device import device

#Local
from helper.IndiClient import IndiClient
from Base.Base import Base

class PyIndi():
    """
    Checkout indiapi.h and indibasetypes.h
    """
    # ISState
    ISS_OFF = 0
    ISS_ON = 0

    # IPState
    IPS_IDLE = 0
    IPS_OK = 1
    IPS_BUSY = 2
    IPS_ALERT = 3

    #ISRule
    ISR_1OFMANY = 0
    ISR_ATMOST1 = 1
    ISR_NOFMANY = 2

    #IPerm
    IP_RO = 0
    IP_WO = 1
    IP_RW = 2

    #INDI_PROPERTY_TYPE
    INDI_NUMBER = 0
    INDI_SWITCH = 1
    INDI_TEXT = 2
    INDI_LIGHT = 3
    INDI_BLOB = 4
    INDI_UNKNOWN = 5

class IndiDevice(Base, device):
    defaultTimeout = 30
    __prop_getter = {
        'blob': 'getBLOB',
        'light': 'getLight',
        'number': 'getNumber',
        'switch': 'getSwitch',
        'text': 'getText'
    }
    # Set of useful dictionaries (put as class att to override behaviour ?)
    __state_str = {
        PyIndi.IPS_IDLE: 'IDLE',
        PyIndi.IPS_OK: 'OK',
        PyIndi.IPS_BUSY: 'BUSY',
        PyIndi.IPS_ALERT: 'ALERT'}
    __switch_types = {
        PyIndi.ISR_1OFMANY: 'ONE_OF_MANY',
        PyIndi.ISR_ATMOST1: 'AT_MOST_ONE',
        PyIndi.ISR_NOFMANY: 'ANY'}
    __type_str = {
        PyIndi.INDI_NUMBER: 'number',
        PyIndi.INDI_SWITCH: 'switch',
        PyIndi.INDI_TEXT: 'text',
        PyIndi.INDI_LIGHT: 'light',
        PyIndi.INDI_BLOB: 'blob',
        PyIndi.INDI_UNKNOWN: 'unknown'}

    def __init__(self, device_name, indi_client_config, debug=False):
        Base.__init__(self)
        device.__init__(self, name=device_name)
    
        self.device_name = device_name
        self.indi_client_config = indi_client_config
        self.timeout = IndiDevice.defaultTimeout
        self.interfaces = None
        self.debug = debug

    def connect(self):
        """
        Enable device connection
        """
        vec = self.indi_client.set_and_send_switchvector_by_elementlabel(
            self.indi_client.driver, "CONNECTION", "Connect")
        if self.debug and vec is not None:
            vec.tell()
        self.process_events()
        return vec

    def disconnect(self):
        """
        Disable device connection
        """
        vec = self.indi_client.set_and_send_switchvector_by_elementlabel(
            self.indi_client.driver, "CONNECTION", "Disconnect")
        if self.debug:
            vec.tell()
        return vec

    async def xml_from_indiserver(self, data):
        """
        Called by parent class.
        """

        print(f"Async call from Indidevice: received {data}")

    @property
    def is_connected(self):
        return self.device.isConnected()

    @property
    def name(self):
        return self.device_name

    # def _setup_device(self):
    #     self.logger.debug(f"IndiDevice: asking indi_client to look for device "
    #                       f"{self.device_name}")
    #     if self.device is None:
    #         started = time.time()
    #         while not self.device:
    #             self.device = self.indi_client.getDevice(self.device_name)
    #             if 0 < self.timeout < time.time() - started:
    #                 self.logger.error(f"IndiDevice: Timeout while waiting for "
    #                                   f"device {self.device_name}")
    #                 raise RuntimeError(f"IndiDevice Timeout while waiting for "
    #                                    f"device {self.device_name}")
    #             time.sleep(0.01)
    #         self.logger.debug(f"Indi Device: indi_client has found device "
    #                           f"{self.device_name}")
    #     else:
    #         self.logger.warning(f"Device {self.device_name} already found")

    def _setup_interfaces(self):
        """
        Find out what interface the current device offers
        """
        interface = self.device.getDriverInterface()
        if type(interface) is int:
            device_interfaces = interface
        else:
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
        self.interfaces = (
            [interfaces[x] for x in interfaces if x & device_interfaces])
        self.logger.debug(f"device {self.device_name}, interfaces are: "
                          f"{self.interfaces}")

    def _setup_indi_client(self):
        """
            setup the indi client that will communicate with devices
        """
        try:
            self.logger.info(f"Setting up indi client")
            self.indi_client = IndiClient(config=self.indi_client_config)
        except Exception:
            raise RuntimeError('Problem setting up indi client')

    def connect_client(self):
        """
        connect to indi server
        TODO TN URGENT: check if we can setup a timeout or
        run_until_complete ?
        """
        self.mainloop.create_task(self.indi_client.connect())

    # def connect_driver(self):
    #     # Try first to ask server to give us the device handle, through client
    #     self._setup_device()

    def connect_device(self):
        """

        """
        # Now connect
        # if self.device.isConnected():
        #     self.logger.warning(f"already connected to device "
        #                         f"{self.device_name}")
        #     return
        # self.logger.info(f"Connecting to device {self.device_name}")
        # # setup available list of interfaces
        # self._setup_interfaces()
        self.start()
        # set the corresponding switch to on
        self.set_switch('CONNECTION', ['CONNECT'])

    def connect(self):
        # setup indi client
        self._setup_indi_client()
        # Connect indi client to server
        self.connect_client()
        # Ask server to give us the device handle, through client
        #self.connect_driver()
        # now enable actual communication between driver and device
        self.connect_device()

    def disconnect(self):
        if not self.device.isConnected():
            self.logger.warning(f"Not connected to device {self.device_name}")
            return
        self.logger.info(f"Disconnecting from device {self.device_name}")
        # set the corresponding switch to off
        self.set_switch('CONNECTION', on_switches=['DISCONNECT'])

    def get_values(self, ctl_name, ctl_type):
        return dict(map(lambda c: (c.name, c.value),
                        self.get_prop(ctl_name, ctl_type)))

    def get_switch(self, name, ctl=None):
        return self.indi_client.get_vector(self.device_name, name)

    def get_text(self, name, ctl=None):
        return self.get_prop_dict(name, 'text',
                                  lambda c: {"value": c.text},
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
                                             IndiDevice.__state_str[c.s]},
                                  ctl)

    def get_prop_dict(self, prop_name, prop_type, transform,
                      prop=None, timeout=None):
        def get_dict(element):
            dest = {'name': element.name, 'label': element.label}
            dest.update(transform(element))
            return dest

        prop = prop if prop else self.get_prop(prop_name, prop_type, timeout)
        d = dict((c.name, get_dict(c)) for c in prop)
        d["state"] = IndiDevice.__state_str[prop.s]
        return d

    def set_switch(self, name, on_switches=[], off_switches=[],
                   sync=True, timeout=None):
        pv = self.get_prop(name, 'switch')
        is_exclusive = pv.getRule() == PyIndi.ISR_ATMOST1 or pv.getRule() == PyIndi.ISR_1OFMANY
        if is_exclusive:
            on_switches = on_switches[0:1]
            off_switches = [s.name for s in pv if s.name not in on_switches]
        for index in range(0, len(pv)):
            current_state = pv[index].s
            new_state = current_state
            if pv[index].name in on_switches:
                new_state = PyIndi.ISS_ON
            elif is_exclusive or pv[index].name in off_switches:
                new_state = PyIndi.ISS_OFF
            pv[index].s = new_state
        self.indi_client.sendNewSwitch(pv)
        if sync:
            self.__wait_prop_status(pv, statuses=[PyIndi.IPS_IDLE,
                                                  PyIndi.IPS_OK],
                                    timeout=timeout)
        return pv
        
    def set_number(self, number_name, value_vector, sync=True, timeout=None):
        pv = self.get_prop(number_name, 'number', timeout)
        for property_name, index in self.__get_prop_vect_indices_having_values(
                                   pv, value_vector.keys()).items():
            pv[index].value = value_vector[property_name]
        self.indi_client.sendNewNumber(pv)
        if sync:
            ret = self.__wait_prop_status(pv, statuses=[PyIndi.IPS_ALERT,
                                                        PyIndi.IPS_OK],
                                          timeout=timeout)
            if ret == PyIndi.IPS_ALERT:
                raise RuntimeError(f"Indi alert upon set_number, {number_name} "
                                   f": {value_vector}")
        return pv

    def set_text(self, text_name, value_vector, sync=True, timeout=None):
        pv = self.get_prop(text_name, 'text')
        for property_name, index in self.__get_prop_vect_indices_having_values(
                                   pv, value_vector.keys()).items():
            pv[index].text = value_vector[property_name]
        self.indi_client.sendNewText(pv)
        if sync:
            ret = self.__wait_prop_status(pv, timeout=timeout)
            if ret == PyIndi.IPS_ALERT:
                raise RuntimeError(f"Indi alert upon set_text, {text_name} "
                                   f": {value_vector}")
        return pv

    def __wait_prop_status(self, prop, statuses=[PyIndi.IPS_OK,PyIndi.IPS_IDLE],
                           timeout=None):
        """Wait for the specified property to take one of the status in param"""

        started = time.time()
        if timeout is None:
            timeout = self.timeout
        while prop.s not in statuses:
            if 0 < timeout < time.time() - started:
                self.logger.debug(f"IndiDevice: Timeout while waiting for "
                                  f"property status {prop.name} for device "
                                  f"{self.device_name}")
                raise RuntimeError(f"Timeout error while changing property "
                                   f"{prop.name}")
            time.sleep(0.01)
        return prop.s

    def __get_prop_vect_indices_having_values(self, property_vector, values):
      """ return dict of name-index of prop that are in values"""
      result = {}
      for i, p in enumerate(property_vector):
        if p.name in values:
          result[p.name] = i
      return result

    def get_prop(self, propName, propType, timeout=None):
        """ Return the value corresponding to the given propName
            A prop often has the following attributes:
            prop.device   : 'OpenWeatherMap'
            prop.group    : 'Parameters', equiv to UI panel
            prop.label    : 'Parameters', equiv to UI subtable name
            prop.name     : 'WEATHER_PARAMETERS'
            prop.nnp      : 9
            prop.np       : Swig_stuff
            prop.p        : 0
            prop.s        : 1 , equiv to status: PyIndi.IPS_OK, PyIndi.IPS_ALERT
            prop.timeout  : 60.0
            prop.timestamp: ''
        """
        prop = None
        attr = IndiDevice.__prop_getter[propType]
        if timeout is None:
            timeout = self.timeout
        started = time.time()
        while not(prop):
            prop = getattr(self.device, attr)(propName)
            if not prop and 0 < timeout < time.time() - started:
                self.logger.debug(f"Timeout while waiting for property "
                                  f"{propName} of type {propType}  for device "
                                  f"{self.device_name}")
                raise RuntimeError(f"Timeout finding property {propName}")
            time.sleep(0.01)
        return prop

    def has_property(self, propName, propType):
        try:
            self.get_prop(propName, propType, timeout=1)
            return True
        except:
            return False
 
