# Basic stuff
import asyncio
import ctypes
import logging
import time

# Indi stuff
from helper.device import device, VectorHandler
from helper.IndiWebManagerClient import IndiWebManagerClient

#Local
from Base.Base import Base
from helper.IndiClient import IndiClient
from utils.error import IndiClientPredicateTimeoutError

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

def probe_device_driver_connection(self, indi_client_config, device_name):
    probe = IndiDevice(
        device_name=device_name,
        indi_client_config=indi_client_config)
    # setup indi client
    probe.connect(connect_device=False)
    try:
        probe.wait_for_any_property_vectors(timeout=1.5)
    except IndiClientPredicateTimeoutError as e:
        return False
    else:
        return True


class IndiDevice(Base, device):
    defaultTimeout = 30

    def __init__(self, device_name, indi_client_config, indi_driver_name=None, debug=False):
        Base.__init__(self)
        device.__init__(self, name=device_name)

        self.indi_client = None
        self.is_client_connected = False
        self.indi_client_config = indi_client_config
        self.timeout = IndiDevice.defaultTimeout
        self.indi_driver_name = indi_driver_name
        self.interfaces = None
        self.debug = debug

    async def xml_from_indiserver(self, data):
        """
        Called by parent class.
        """
        print(f"Async call from Indidevice: received {data}")

    @property
    def name(self):
        return self.device_name

    async def registering_runner(self, functor):
        self.indi_client.device_subscriptions[self.device_name] = functor
        await asyncio.sleep(0)

    async def unregistering_runner(self):
        try:
            assert self.indi_client is not None
            del self.indi_client.device_subscriptions[self.device_name]
        except KeyError as e:
            self.logger.warning(f"Device {self.device_name} cannot be unregistered from client, "
                                f"as it doesn't seems registered yet: {e}")
        await asyncio.sleep(0)

    async def registering_custom_vector_handler(self, handler_name, handler):
        self.register_custom_vector_handler(handler_name, handler)
        await asyncio.sleep(0)

    async def unregistering_custom_vector_handler(self, handler_name):
        self.unregister_custom_vector_handler(handler_name)
        await asyncio.sleep(0)

    def register_device_to_client(self):
        self.logger.debug(f"IndiDevice: asking indi_client to listen for device {self.device_name}")
        #self.indi_client.ioloop.call_soon_threadsafe(
        #    lambda x: self.indi_client.device_subscriptions.append(x),
        #    self.parse_xml_str)
        future = asyncio.run_coroutine_threadsafe(self.registering_runner(self.parse_xml_str), self.indi_client.ioloop)
        _ = future.result()  # This is just sync

    def unregister_device_to_client(self):
        self.logger.debug(f"IndiDevice: asking indi_client to stop listen for device {self.device_name}")
        future = asyncio.run_coroutine_threadsafe(self.unregistering_runner(), self.indi_client.ioloop)
        _ = future.result() # This is just sync

    def register_vector_handler_to_client(self, vector_name, handler_name, callback):
        vh = VectorHandler(devicename=self.device_name,
                           vectorname=vector_name,
                           callback=callback)
        future = asyncio.run_coroutine_threadsafe(
            self.registering_custom_vector_handler(handler_name, vh), self.indi_client.ioloop)
        _ = future.result()  # This is just sync

    def unregister_vector_handler_to_client(self, handler_name):
        future = asyncio.run_coroutine_threadsafe(
            self.unregistering_custom_vector_handler(handler_name), self.indi_client.ioloop)
        _ = future.result()  # This is just sync

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
            self.logger.debug(f"Setting up indi client")
            self.indi_client = IndiClient(config=self.indi_client_config)
        except Exception as e:
            msg = f"Problem setting up indi client for device {self.device_name}: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg)

    def connect_client(self):
        """
        connect client to indi server
        """
        self.indi_client.connect_to_server(sync=True, timeout=self.defaultTimeout)

    # def connect_driver(self):
    #     # Try first to ask server to give us the device handle, through client
    #     self._setup_device()

    def connect_device(self):
        """

        """
        # set the corresponding switch to on
        self.set_switch('CONNECTION', ['CONNECT'], sync=True, timeout=self.defaultTimeout)

    def disconnect_device(self):
        """
        Disable device connection
        """
        self.set_switch('CONNECTION', on_switches=['DISCONNECT'], sync=True, timeout=self.defaultTimeout)

    def connect(self, connect_device=True):
        # setup indi client
        self._setup_indi_client()
        # Connect indi client to server
        self.connect_client()
        # Ask client to parse and process any message related to this device
        self.register_device_to_client()
        # First thing to do is to force the server to re-send all informations
        # related to devices, so that we can populate the current device pv
        self.indi_client.trigger_get_properties()

        if connect_device:
            # now enable actual communication between driver and device
            self.connect_device()

    def disconnect(self):
        self.logger.debug(f"Disconnecting device {self.device_name}")
        if self.is_client_connected:
            # set the corresponding switch to off
            self.disconnect_device()
            self.unregister_device_to_client()
            self.is_client_connected = False
        self.logger.debug(f"Successfully disconnected device {self.device_name}")

    @property
    def is_connected(self):
        if self.is_client_connected:
            return False
        try:
            return self.get_switch("CONNECTION")["CONNECT"] == 'On'
        except Exception as e:
            return False

    def stop_indi_server(self):
        # We could simply do like that:
        # if self.indi_client is None:
        #     self._setup_indi_client()
        # self.indi_client.indi_webmanager_client.start_server()
        # But then in case of stopping, it could consume ressources for no reason
        if self.indi_client is not None:
            self.indi_client.indi_webmanager_client.stop_server()
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

    def get_switch(self, name):
        return self.get_vector_dict(name)

    def get_text(self, name):
        return self.get_vector_dict(name)

    def get_number(self, name):
        number_dict = self.get_vector_dict(name)
        number_dict.update({k: float(v) for k, v in number_dict.items()})
        return number_dict

    def get_light(self, name):
        return self.get_vector_dict(name)

    def set_switch(self, switch_name, on_switches=[], off_switches=[],
                   sync=True, timeout=None):
        if timeout is None:
            timeout = self.defaultTimeout
        self.set_and_send_switchvector_by_element_name(switch_name, on_switches=on_switches, off_switches=off_switches)
        if sync:
           self.wait_for_vector_light(switch_name, timeout=timeout)

    def set_number(self, number_name, value_vector, sync=True, timeout=None):
        if timeout is None:
            timeout = self.defaultTimeout
        self.set_and_send_float(vector_name=number_name, value_vector=value_vector)
        if sync:
            self.wait_for_vector_light(number_name, timeout=timeout)

    def set_text(self, text_name, value_vector, sync=True, timeout=None):
        if timeout is None:
            timeout = self.defaultTimeout
        self.set_and_send_text(vector_name=text_name, value_vector=value_vector)
        if sync:
            self.wait_for_vector_light(text_name, timeout=timeout)

    def wait_for_vector_light(self, vector_name, timeout=None):
        light_checker = lambda: self.check_vector_light(vector_name)
        self.indi_client.sync_with_predicate(light_checker, timeout=timeout)
        return

    def wait_for_incoming_blob_vector(self, blob_vector_name=None, timeout=None):
        blob_checker = lambda: self.check_blob_vector(blob_vector_name)
        self.indi_client.sync_with_predicate(blob_checker, timeout=timeout)
        return

    def wait_for_any_property_vectors(self, timeout=5):
        """
            Wait until property vector is non-empty
        :param timeout:
        :return:
        """
        light_checker = lambda: bool(self.property_vectors)
        self.indi_client.sync_with_predicate(light_checker, timeout=timeout)
        return