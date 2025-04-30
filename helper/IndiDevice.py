# Basic stuff
import asyncio
from collections import deque
import ctypes
import logging
import queue
import time

# Indi stuff
import PyIndi

#Local
from Base.Base import Base
from helper.IndiClient import defaultTimeout, IndiClient
from helper.IndiWebManagerClient import IndiWebManagerClient
from utils.error import BLOBError, IndiClientPredicateTimeoutError

logger = logging.getLogger(__name__)


# class PyIndi():
#     """
#     Checkout indiapi.h and indibasetypes.h
#     """
#     # ISState
#     ISS_OFF = 0
#     ISS_ON = 0
#
#     # IPState
#     IPS_IDLE = 0
#     IPS_OK = 1
#     IPS_BUSY = 2
#     IPS_ALERT = 3
#
#     #ISRule
#     ISR_1OFMANY = 0
#     ISR_ATMOST1 = 1
#     ISR_NOFMANY = 2
#
#     #IPerm
#     IP_RO = 0
#     IP_WO = 1
#     IP_RW = 2
#
#     #INDI_PROPERTY_TYPE
#     INDI_NUMBER = 0
#     INDI_SWITCH = 1
#     INDI_TEXT = 2
#     INDI_LIGHT = 3
#     INDI_BLOB = 4
#     INDI_UNKNOWN = 5
#
# def probe_device_driver_connection(self, indi_client_config, device_name):
#     probe = IndiDevice(
#         device_name=device_name,
#         indi_client_config=indi_client_config)
#     # setup indi client
#     probe.connect(connect_device=False)
#     try:
#         probe.wait_for_any_property_vectors(timeout=1.5)
#     except IndiClientPredicateTimeoutError as e:
#         return False
#     else:
#         return True


class IndiDevice(Base):
    __prop_getter = {
        'blob': 'getBLOB',
        'light': 'getLight',
        'number': 'getNumber',
        'switch': 'getSwitch',
        'text': 'getText'
    }
    __prop_caster = {
        'blob':   PyIndi.PropertyBlob,
        'light':  PyIndi.PropertyLight,
        'number': PyIndi.PropertyNumber,
        'switch': PyIndi.PropertySwitch,
        'text':   PyIndi.PropertyText
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

    def __init__(self, device_name, indi_client_config, indi_driver_name=None, debug=False):
#    def __init__(self, logger, device_name, indi_client_config):
        Base.__init__(self)

        self.device_name = device_name
        self.indi_client_config = indi_client_config
        self.timeout = defaultTimeout
        self.device = None
        self.interfaces = None
        self.blob_listener = None
        self.blob_queue = deque()

        self.indi_client = None
        # self.is_client_connected = False
        self.indi_driver_name = indi_driver_name
        # self.debug = debug

    @property
    def is_connected(self):
        return self.device.isConnected()
    # indi_client.isServerConnected()
    # indi_client.disconnectServer()

    @property
    def name(self):
        return self.device_name

    def _setup_indi_client(self):
        """
            setup the indi client that will communicate with devices
        """
        try:
            if self.indi_client is None:
                self.logger.info(f"Setting up indi client")
                self.indi_client = IndiClient(config=self.indi_client_config)
        except Exception:
            raise RuntimeError('Problem setting up indi client')

    def _setup_device(self):
        self.logger.debug(f"IndiDevice: asking indi_client to look for device {self.device_name}")
        if self.indi_client is None:
            logger.warning(f"Cannot setup device as indi client with config {self.indi_client_config} has not been initialized yet. About to setup it")
            self._setup_indi_client()
        if self.device is None or not self.device.isValid():
            self.device = None
            started = time.time()
            while not self.device:
                self.device = self.indi_client.getDevice(self.device_name)
                if 0 < self.timeout < time.time() - started:
                    msg = f"IndiDevice: Timeout while waiting for device {self.device_name}"
                    self.logger.error(msg)
                    raise RuntimeError(msg)
                time.sleep(0.01)
            self.logger.debug(f"Indi Device: indi_client has found device "
                              f"{self.device_name}")
        else:
            self.logger.warning(f"Device {self.device_name} already found")

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
        self.logger.debug(f"device {self.device_name}, interfaces are: {self.interfaces}")

    def connect_client(self):
        """
        connect client to indi server
        """
        self.indi_client.connect_to_server(sync=True, timeout=defaultTimeout)

    def connect_driver(self):
        # Try first to ask server to give us the device handle, through client
        self._setup_device()

    def connect_device(self, force_reconnect=False, timeout=None):
        """
        """
        # Now connect
        if self.device is None:
            logger.warning(f"Cannot connect device as device object named {self.device_name} has not been initialized yet. About to setup it")
            self._setup_device()
        if not self.device.isValid():
            self.device = None
            logger.warning(f"Cannot connect device as device object named {self.device_name} is invalid")
            self._setup_device()
        if self.device.isConnected():
            self.logger.warning(f"already connected to device {self.device_name}")
            if force_reconnect:
                self.disconnect()
            else:
                return
        self.logger.info(f"Connecting to device {self.device_name}")
        # setup available list of interfaces
        self._setup_interfaces()
        # set the corresponding switch to on
        self.set_switch('CONNECTION', ['CONNECT'])
        #     time.sleep(0.1)
        started = time.time()
        if timeout is None:
            timeout = self.timeout
        while not self.device.isConnected():
            self.logger.debug(f"Device {self.device_name} is valid ? {self.device.isValid()}")
            if 0 < timeout < time.time() - started:
                msg = f"IndiDevice: Timeout while waiting for connection to device {self.device_name} with timeout {timeout}"
                self.logger.debug(msg)
                raise RuntimeError(msg)
            time.sleep(0.01)


    def connect(self, connect_device=True):
        # setup indi client
        self._setup_indi_client()
        # Connect indi client to server
        self.connect_client()
        # Ask server to give us the device handle, through client
        self.connect_driver()
        if connect_device:
            # now enable actual communication between driver and device
            self.connect_device()

    def disconnect(self):
        self.logger.info(f"Disconnecting from device {self.device_name}")
        if self.indi_client is not None:
            self.indi_client.disconnectDevice(deviceName=self.device_name)
            self.disable_blob()
            self.unregister_vector_handler_to_client()

    def get_values(self, ctl_name, ctl_type):
        return dict(map(lambda c: (c.name, c.value),
                        self.get_prop(ctl_name, ctl_type)))
        # # set
        # anyProperty.setDeviceName("Some device")
        # anyProperty.setName("Some name")
        # anyProperty.setLabel("Some label")
        # anyProperty.setGroupName("Some group")
        # anyProperty.setState(PyIndi.IPS_IDLE)
        # anyProperty.setTimestamp("123")
        # anyProperty.setPermission(PyIndi.IP_RO) # no effect for Light Property
        # anyProperty.setTimeout(123)             # no effect for Light Property
        #
        # anyProperty[0].setName("Some name of widget")
        # anyProperty[0].setLabel("Some label of widget")
        #
        # # get
        # device    = anyProperty.getDeviceName()
        # name      = anyProperty.getName()
        # label     = anyProperty.getLabel()
        # group     = anyProperty.getGroupName()
        # state     = anyProperty.getState()
        # timestamp = anyProperty.getTimestamp()
        # perm      = anyProperty.getPermission() # returns IP_RO for Light Property
        # timeout   = anyProperty.getTimeout()    # returns 0 for Light Property
        #
        # name      = anyProperty[0].getName()
        # label     = anyProperty[0].getLabel()
        #
        # # auxiliary functions
        # if anyProperty.isNameMatch("Some name"):
        #     # anyProperty.getName() is equal to "Some name"
        #     pass
        #
        # if anyProperty.isLabelMatch("Some label"):
        #     # anyProperty.getLabel() is equal to "Some label"
        #     pass
        #
        # if not anyProperty.isValid():
        #     # e.g. PyIndi.Property() is not valid because type is unknown
        #     # PyIndi.PropertyText(somePropertySwitch) is also not valid because type
        #     # is mismatch (invalid cast)
        #     pass
        #
        # stringState  = anyProperty.getStateAsString()            # returns Idle/Ok/Busy/Alert
        # stringPerm   = anyProperty.getPermissionAsString()       # returns ro/wo/rw
        # someWidget   = anyProperty.findWidgetByName("Some name") # returns widget with `Some name` name

    def get_text(self, name, ctl=None):
        pv = self.get_prop(name, "text")
        return {p.getName():p.getText() for p in pv}
        # # set
        # textProperty[0].setText("Some text")
        #
        # # get
        # text  = textProperty[0].getText()

    def set_text(self, text_name, value_vector, sync=True, timeout=None):
        pv = self.get_prop(text_name, "text")
        for property_name, index in self.__get_prop_vect_indices_having_values(
                pv, value_vector.keys()).items():
            pv[index].text = value_vector[property_name]
        self.indi_client.sendNewText(pv)
        if sync:
            ret = self.__wait_prop_status(pv, statuses=[PyIndi.IPS_ALERT, PyIndi.IPS_OK, PyIndi.IPS_IDLE], timeout=timeout)
            if ret == PyIndi.IPS_ALERT:
                raise RuntimeError(f"Indi alert upon set_text, {text_name} : {value_vector}")
        return pv

    def get_number(self, name, ctl=None):
        pv = self.get_prop(name, "number")
        return {p.getName():p.getValue() for p in pv}
        # # set
        # numberProperty[0].setFormat("Some format")
        # numberProperty[0].setMin(0)
        # numberProperty[0].setMax(1000)
        # numberProperty[0].setMinMax(0, 1000) # simplification
        # numberProperty[0].setStep(1)
        # numberProperty[0].setValue(123)
        #
        # # get
        # format = numberProperty[0].getFormat()
        # min    = numberProperty[0].getMin()
        # max    = numberProperty[0].getMax()
        # step   = numberProperty[0].getStep()
        # value  = numberProperty[0].getValue()

    def set_number(self, number_name, value_vector, sync=True, timeout=None):
        pv = self.get_prop(number_name, "number")
        for property_name, index in self.__get_prop_vect_indices_having_values(
                pv, value_vector.keys()).items():
            pv[index].value = value_vector[property_name]
        self.indi_client.sendNewNumber(pv)
        if sync:
            ret = self.__wait_prop_status(pv, statuses=[PyIndi.IPS_ALERT, PyIndi.IPS_OK], timeout=timeout)
            if ret == PyIndi.IPS_ALERT:
                raise RuntimeError(f"Indi alert upon set_number {number_name}: {value_vector}")
        return pv

    def get_switch(self, name, ctl=None):
        pv = self.get_prop(name, "switch")
        return {p.getName():p.getState()==PyIndi.ISS_ON for p in pv}
        # # set
        # switchProperty.setRule(PyIndi.ISR_NOFMANY)
        # switchProperty[0].setState(PyIndi.ISS_ON)
        #
        # # get
        # rule  = switchProperty.getRule()
        # state = switchProperty[0].getState()
        #
        # # auxiliary functions
        # stringRule  = switchProperty.getRuleAsString()     # returns OneOfMany/AtMostOne/AnyOfMany
        # stringState = switchProperty[0].getStateAsString() # returns On/Off
        # switchProperty.reset()                             # reset all widget switches to Off
        # switchProperty.findOnSwitchIndex()                 # find index of Widget with On state
        # switchProperty.findOnSwitch()                      # returns widget with On state

    def set_switch(self, name, on_switches=[], off_switches=[], sync=True, timeout=None):
        pv = self.get_prop(name, "switch", timeout=timeout)
        is_exclusive = pv.getRule() == PyIndi.ISR_ATMOST1 or pv.getRule() == PyIndi.ISR_1OFMANY
        if is_exclusive:
            on_switches = on_switches[0:1]
            off_switches = [s.getName() for s in pv if s.getName() not in on_switches]
        for index in range(0, len(pv)):
            current_state = pv[index].getState()
            new_state = current_state
            if pv[index].getName() in on_switches:
                new_state = PyIndi.ISS_ON
            elif pv[index].getName() in off_switches:
                new_state = PyIndi.ISS_OFF
            pv[index].setState(new_state)
        self.indi_client.sendNewSwitch(pv)
        if sync:
            self.__wait_prop_status(pv, statuses=[PyIndi.IPS_IDLE, PyIndi.IPS_OK], timeout=timeout)
        return pv

    def get_light(self, name, ctl=None):
        pv = self.get_prop(name, "light")
        return {p.getName():p.getStateAsString() for p in pv} # p.getState()==PyIndi.IPS_OK
        # # set
        # switchProperty.setRule(PyIndi.ISR_NOFMANY)
        # switchProperty[0].setState(PyIndi.ISS_ON)
        #
        # # get
        # rule  = switchProperty.getRule()
        # state = switchProperty[0].getState()
        #
        # # auxiliary functions
        # stringRule  = switchProperty.getRuleAsString()     # returns OneOfMany/AtMostOne/AnyOfMany
        # stringState = switchProperty[0].getStateAsString() # returns On/Off
        # switchProperty.reset()                             # reset all widget switches to Off
        # switchProperty.findOnSwitchIndex()                 # find index of Widget with On state
        # switchProperty.findOnSwitch()                      # returns widget with On state

    def __wait_prop_status(self, prop, statuses=[PyIndi.IPS_OK, PyIndi.IPS_IDLE],
                           timeout=None):
        """Wait for the specified property to take one of the status in param"""
        started = time.time()
        if timeout is None:
            timeout = self.timeout
        while prop.getState() not in statuses:
            if 0 < timeout < time.time() - started:
                self.logger.debug(f"IndiDevice: Timeout while waiting for property status {prop.getName()} for device "
                                  f"{self.device_name} with timeout {timeout}")
                raise RuntimeError(f"Timeout error while changing property {prop.getName()}")
            time.sleep(0.01)
        return prop.getState()

    def __get_prop_vect_indices_having_values(self, property_vector, values):
        """ return dict of name-index of prop that are in values"""
        result = {}
        for i, p in enumerate(property_vector):
            if p.getName() in values:
                result[p.getName()] = i
        return result

    def get_prop(self, prop_name, prop_type, timeout=None):
        """ Return the value corresponding to the given propName
            EDIT: the Python API completely changed after V2 see: https://github.com/indilib/pyindi-client
        """
        if timeout is None:
            timeout = self.timeout
        prop = self.device.getProperty(prop_name)
        started = time.time()
        while not prop.isValid():
            prop = self.device.getProperty(prop_name)
            if not prop.isValid() and 0 < timeout < time.time() - started:
                msg = f"Timeout while waiting for property {prop_name} of type {prop_type}  for device {self.device_name}"
                logger.error(msg)
                raise RuntimeError(msg)
            time.sleep(0.01)
        # logger.debug(f"Property {prop_name} of expected type {prop_type} but detected type {prop.getTypeAsString()} has status {prop.isValid()}")
        prop = IndiDevice.__prop_caster[prop_type](prop)
        return prop
        # prop = None
        # attr = IndiDevice.__prop_getter[propType]
        # if timeout is None:
        #     timeout = self.timeout
        # started = time.time()
        # while not (prop):
        #     prop = getattr(self.device, attr)(propName)
        #     if not prop and 0 < timeout < time.time() - started:
        #         self.logger.debug(f"Timeout while waiting for property "
        #                           f"{propName} of type {propType}  for device "
        #                           f"{self.device_name}")
        #         raise RuntimeError(f"Timeout finding property {propName}")
        #     time.sleep(0.01)
        # return prop

    def has_property(self, prop_name, prop_type):
        prop = self.device.getProperty(prop_name)
        return prop.isValid()

    def enable_blob(self):
        self.logger.debug(f"About to enable blob, and allocate associated control structures")
        self.blob_queue.clear()
        self.blob_listener = self.indi_client.reset_blob_listener(
            device_name=self.device_name,
            queue_size=1
        )
        self.indi_client.enable_blob(
            blob_mode=PyIndi.B_ALSO,
            device_name=self.device_name,
            property_name=None)

    def disable_blob(self):
        self.logger.debug(f"About to disable blob, and clean associated control structures")
        self.indi_client.remove_blob_listener(
            device_name=self.device_name
        )
        self.blob_listener = None
        self.blob_queue.clear()
        self.indi_client.enable_blob(
            blob_mode=PyIndi.B_NEVER,
            device_name=self.device_name,
            property_name=None)


# class IndiDevice(Base, device):
#     defaultTimeout = 30
#
#     def __init__(self, device_name, indi_client_config, indi_driver_name=None, debug=False):
#         Base.__init__(self)
#         device.__init__(self, name=device_name)
#
#         self.indi_client = None
#         self.is_client_connected = False
#         self.indi_client_config = indi_client_config
#         self.timeout = defaultTimeout
#         self.indi_driver_name = indi_driver_name
#         self.interfaces = None
#         self.debug = debug
#
#     async def xml_from_indiserver(self, data):
#         """
#         Called by parent class.
#         """
#         print(f"Async call from Indidevice: received {data}")
#
#     @property
#     def name(self):
#         return self.device_name
#
#     async def registering_runner(self, functor):
#         self.indi_client.device_subscriptions[self.device_name] = functor
#         await asyncio.sleep(0)
#
#     async def unregistering_runner(self):
#         try:
#             assert self.indi_client is not None
#             del self.indi_client.device_subscriptions[self.device_name]
#         except KeyError as e:
#             self.logger.warning(f"Device {self.device_name} cannot be unregistered from client, "
#                                 f"as it doesn't seems registered yet: {e}")
#         await asyncio.sleep(0)
#
#     async def registering_custom_vector_handler(self, handler_name, handler):
#         self.register_custom_vector_handler(handler_name, handler)
#         await asyncio.sleep(0)
#
#     async def unregistering_custom_vector_handler(self, handler_name):
#         self.unregister_custom_vector_handler(handler_name)
#         await asyncio.sleep(0)
#
#     def register_device_to_client(self):
#         self.logger.debug(f"IndiDevice: asking indi_client to listen for device {self.device_name}")
#         #self.indi_client.ioloop.call_soon_threadsafe(
#         #    lambda x: self.indi_client.device_subscriptions.append(x),
#         #    self.parse_xml_str)
#         future = asyncio.run_coroutine_threadsafe(self.registering_runner(self.parse_xml_str), self.indi_client.ioloop)
#         _ = future.result()  # This is just sync
#
#     def unregister_device_to_client(self):
#         self.logger.debug(f"IndiDevice: asking indi_client to stop listen for device {self.device_name}")
#         future = asyncio.run_coroutine_threadsafe(self.unregistering_runner(), self.indi_client.ioloop)
#         _ = future.result() # This is just sync
#
#     def register_vector_handler_to_client(self, vector_name, handler_name, callback):
#         vh = VectorHandler(devicename=self.device_name,
#                            vectorname=vector_name,
#                            callback=callback)
#         future = asyncio.run_coroutine_threadsafe(
#             self.registering_custom_vector_handler(handler_name, vh), self.indi_client.ioloop)
#         _ = future.result()  # This is just sync
    def register_vector_handler_to_client(self, vector_name, handler_name, callback):
        self.indi_client.add_pv_handler(
            device_name=self.device_name,
            pv_name=vector_name,
            handler_name=handler_name,
            pv_handler=callback)
    #
#     def unregister_vector_handler_to_client(self, handler_name):
#         future = asyncio.run_coroutine_threadsafe(
#             self.unregistering_custom_vector_handler(handler_name), self.indi_client.ioloop)
#         _ = future.result()  # This is just sync
    def unregister_vector_handler_to_client(self, vector_name=None, handler_name=None):
        self.indi_client.remove_pv_handler(
            device_name=self.device_name,
            pv_name=vector_name,
            handler_name=handler_name

            )
    #
#     def _setup_interfaces(self):
#         """
#         Find out what interface the current device offers
#         """
#         interface = self.device.getDriverInterface()
#         if type(interface) is int:
#             device_interfaces = interface
#         else:
#             interface.acquire()
#             device_interfaces = int(ctypes.cast(interface.__int__(),
#                 ctypes.POINTER(ctypes.c_uint16)).contents.value)
#             interface.disown()
#         interfaces = {
#             PyIndi.BaseDevice.GENERAL_INTERFACE: 'general',
#             PyIndi.BaseDevice.TELESCOPE_INTERFACE: 'telescope',
#             PyIndi.BaseDevice.CCD_INTERFACE: 'ccd',
#             PyIndi.BaseDevice.GUIDER_INTERFACE: 'guider',
#             PyIndi.BaseDevice.FOCUSER_INTERFACE: 'focuser',
#             PyIndi.BaseDevice.FILTER_INTERFACE: 'filter',
#             PyIndi.BaseDevice.DOME_INTERFACE: 'dome',
#             PyIndi.BaseDevice.GPS_INTERFACE: 'gps',
#             PyIndi.BaseDevice.WEATHER_INTERFACE: 'weather',
#             PyIndi.BaseDevice.AO_INTERFACE: 'ao',
#             PyIndi.BaseDevice.DUSTCAP_INTERFACE: 'dustcap',
#             PyIndi.BaseDevice.LIGHTBOX_INTERFACE: 'lightbox',
#             PyIndi.BaseDevice.DETECTOR_INTERFACE: 'detector',
#             PyIndi.BaseDevice.ROTATOR_INTERFACE: 'rotator',
#             PyIndi.BaseDevice.AUX_INTERFACE: 'aux'
#         }
#         self.interfaces = (
#             [interfaces[x] for x in interfaces if x & device_interfaces])
#         self.logger.debug(f"device {self.device_name}, interfaces are: "
#                           f"{self.interfaces}")
#
#     def _setup_indi_client(self):
#         """
#             setup the indi client that will communicate with devices
#         """
#         try:
#             self.logger.debug(f"Setting up indi client")
#             self.indi_client = IndiClient(config=self.indi_client_config)
#         except Exception as e:
#             msg = f"Problem setting up indi client for device {self.device_name}: {e}"
#             self.logger.error(msg)
#             raise RuntimeError(msg)
#

#     def connect_device(self):
#         """
#         """
#         # set the corresponding switch to on
#         self.set_switch('CONNECTION', ['CONNECT'], sync=True, timeout=defaultTimeout)
#
#     def disconnect_device(self):
#         """
#         Disable device connection
#         """
#         self.set_switch('CONNECTION', on_switches=['DISCONNECT'], sync=True, timeout=defaultTimeout)
#
#     def connect(self, connect_device=True):
#         # setup indi client
#         self._setup_indi_client()
#         # Connect indi client to server
#         self.connect_client()
#         # Ask client to parse and process any message related to this device
#         self.register_device_to_client()
#         # First thing to do is to force the server to re-send all informations
#         # related to devices, so that we can populate the current device pv
#         self.indi_client.trigger_get_properties()
#
#         if connect_device:
#             # now enable actual communication between driver and device
#             self.connect_device()
#
    # def disconnect(self):
    #     self.logger.debug(f"Disconnecting device {self.device_name}")
    #     if self.is_client_connected:
    #         # set the corresponding switch to off
    #         self.disconnect_device()
    #         self.unregister_device_to_client()
    #         self.is_client_connected = False
    #     self.logger.debug(f"Successfully disconnected device {self.device_name}")
#
#     @property
#     def is_connected(self):
#         if self.is_client_connected:
#             return False
#         try:
#             return self.get_switch("CONNECTION")["CONNECT"] == 'On'
#         except Exception as e:
#             return False
#
    def stop_indi_server(self):
        # We could simply do like that:
        # if self.indi_client is None:
        #     self._setup_indi_client()
        # self.indi_client.indi_webmanager_client.start_server()
        # But then in case of stopping, it could consume ressources for no reason
        if not (self.indi_client is None):
            self.indi_client.indi_webmanager_client.stop_server(device_name=self.device_name)
        else:
            # Setup temporary webmanager client
            if "indi_webmanager" in self.indi_client_config:
                iwmc = IndiWebManagerClient(config=self.indi_client_config["indi_webmanager"],
                                            indi_config=self.indi_client_config)
                iwmc.stop_server(device_name=self.device_name)

    def start_indi_server(self):
        if self.indi_client is None:
            self._setup_indi_client()
        self.indi_client.indi_webmanager_client.start_server(device_name=self.device_name)

    def start_indi_driver(self):
        self.indi_client.indi_webmanager_client.start_driver(
            driver_name=self.indi_driver_name,
            check_started=True)
#
#     def get_switch(self, name):
#         return self.get_vector_dict(name)
#
#     def get_text(self, name):
#         return self.get_vector_dict(name)
#
#     def get_number(self, name):
#         number_dict = self.get_vector_dict(name)
#         number_dict.update({k: float(v) for k, v in number_dict.items()})
#         return number_dict
#
#     def get_light(self, name):
#         return self.get_vector_dict(name)
#
#     def set_switch(self, switch_name, on_switches=[], off_switches=[],
#                    sync=True, timeout=None):
#         if timeout is None:
#             timeout = defaultTimeout
#         self.set_and_send_switchvector_by_element_name(switch_name, on_switches=on_switches, off_switches=off_switches)
#         if sync:
#            self.wait_for_vector_light(switch_name, timeout=timeout)
#
#     def set_number(self, number_name, value_vector, sync=True, timeout=None):
#         if timeout is None:
#             timeout = defaultTimeout
#         self.set_and_send_float(vector_name=number_name, value_vector=value_vector)
#         if sync:
#             self.wait_for_vector_light(number_name, timeout=timeout)
#
#     def set_text(self, text_name, value_vector, sync=True, timeout=None):
#         if timeout is None:
#             timeout = defaultTimeout
#         self.set_and_send_text(vector_name=text_name, value_vector=valufe_vector)
#         if sync:
#             self.wait_for_vector_light(text_name, timeout=timeout)
#
#     def wait_for_vector_light(self, vector_name, timeout=None):
#         light_checker = lambda: self.check_vector_light(vector_name)
#         self.indi_client.sync_with_predicate(light_checker, timeout=timeout)
#         return

    def wait_for_incoming_blob_vector(self, blob_vector_name=None, timeout=None):
        #blob_checker = lambda: self.check_blob_vector(blob_vector_name)
        #self.indi_client.sync_with_predicate(blob_checker, timeout=timeout)
        #return
        try:
            logger.debug(f"BLOBListener[{self.device_name}]: waiting for blob, timeout={timeout}")
            blob = self.blob_listener.queue.get(block=True, timeout=timeout)
            logger.debug(f"BLOBListener[{self.device_name}]: blob received name={blob.name}, label={blob.label}, "
                f"size={blob.size}, queue size: {self.blob_listener.queue.qsize()} (isEmpty: {self.blob_listener.queue.empty()})")
            self.blob_queue.append(blob)
        except queue.Empty:
            raise BLOBError(f"Timeout while waiting for BLOB on {self.device.name}")

    def get_last_incoming_blob_vector(self):
        blob = self.blob_queue.pop() # deque Append + pop = LIFO
        #blob = self.blob_queue.popleft() # deque Append + popleft = FIFO
        return blob

#     def wait_for_any_property_vectors(self, timeout=5):
#         """
#             Wait until property vector is non-empty
#         :param timeout:
#         :return:
#         """
#         light_checker = lambda: bool(self.property_vectors)
#         self.indi_client.sync_with_predicate(light_checker, timeout=timeout)
#         return