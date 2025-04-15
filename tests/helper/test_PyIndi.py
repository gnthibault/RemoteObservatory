# Generic


# PyIndi, for a better undesrtanding of client model, see https://docs.indilib.org/clients/
import PyIndi

# for logging
import sys
import time
import logging

# import the PyIndi module
import PyIndi

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# class IndiClient(PyIndi.BaseClient):
#     def __init__(self):
#         super(IndiClient, self).__init__()

# The IndiClient class which inherits from the module PyIndi.BaseClient class
# Note that all INDI constants are accessible from the module as PyIndi.CONSTANTNAME
class IndiClient(PyIndi.BaseClient):
    def __init__(self):
        super(IndiClient, self).__init__()
        logger.info('creating an instance of IndiClient')

    def newDevice(self, d):
        '''Emmited when a new device is created from INDI server.'''
        logger.info(f"new device {d.getDeviceName()}")

    def removeDevice(self, d):
        '''Emmited when a device is deleted from INDI server.'''
        logger.info(f"remove device {d.getDeviceName()}")

    def newProperty(self, p):
        '''Emmited when a new property is created for an INDI driver.'''
        logger.info(f"new property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}")

    def updateProperty(self, p):
        '''Emmited when a new property value arrives from INDI server.'''
        logger.info(f"update property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}")

    def removeProperty(self, p):
        '''Emmited when a property is deleted for an INDI driver.'''
        logger.info(f"remove property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}")

    def newMessage(self, d, m):
        '''Emmited when a new message arrives from INDI server.'''
        logger.info(f"new Message {d.messageQueue(m)}")

    def serverConnected(self):
        '''Emmited when the server is connected.'''
        logger.info(f"Server connected ({self.getHost()}:{self.getPort()})")

    def serverDisconnected(self, code):
        '''Emmited when the server gets disconnected.'''
        logger.info(f"Server disconnected (exit code = {code},{self.getHost()}:{self.getPort()})")

def test_PyIndiClientConnection():
    # Create an instance of the IndiClient class and initialize its host/port members
    indiclient = IndiClient()
    indiclient.setServer("localhost", 7624)
    assert indiclient.getHost() == "localhost"
    assert indiclient.getPort() == 7624
    res = indiclient.connectServer()
    assert res
    assert indiclient.isServerConnected()

def testPyIndiDeviceTraversal():
    indiclient = IndiClient()
    indiclient.setServer("localhost", 7624)
    assert indiclient.getHost() == "localhost"
    assert indiclient.getPort() == 7624
    res = indiclient.connectServer()
    assert res
    assert indiclient.isServerConnected()

    # This will fucking fail if you don't wait
    #time.sleep(1)
    #device_list = indiclient.getDevices()
    device_list = None
    while not device_list:
        device_list = indiclient.getDevices()
        time.sleep(0.1)
    assert len(device_list) > 0
    
    # Print all properties and their associated values.
    for device in device_list:
        genericPropertyList = device.getProperties()
        assert len(genericPropertyList) > 0
        for genericProperty in genericPropertyList:
            assert genericProperty.isValid()
            #print(f"   > {genericProperty.getName()} {genericProperty.getTypeAsString()}")
            if genericProperty.getType() == PyIndi.INDI_TEXT:
                for widget in PyIndi.PropertyText(genericProperty):
                    #print(f"       {widget.getName()}({widget.getLabel()}) = {widget.getText()}")
                    if isinstance(widget, PyIndi.WidgetViewText):
                        pass
                    else:
                        assert widget.isValid() #This is just here to validate proper cast
            if genericProperty.getType() == PyIndi.INDI_NUMBER:
                for widget in PyIndi.PropertyNumber(genericProperty):
                    #print(f"       {widget.getName()}({widget.getLabel()}) = {widget.getValue()}")
                    if isinstance(widget, PyIndi.WidgetViewNumber):
                        pass
                    else:
                        assert widget.isValid() #This is just here to validate proper cast
            if genericProperty.getType() == PyIndi.INDI_SWITCH:
                for widget in PyIndi.PropertySwitch(genericProperty):
                    #print(f"       {widget.getName()}({widget.getLabel()}) = {widget.getStateAsString()}")
                    if isinstance(widget, PyIndi.WidgetViewSwitch):
                        pass
                    else:
                        assert widget.isValid() #This is just here to validate proper cast
            if genericProperty.getType() == PyIndi.INDI_LIGHT:
                for widget in PyIndi.PropertyLight(genericProperty):
                    #print(f"       {widget.getLabel()}({widget.getLabel()}) = {widget.getStateAsString()}")
                    assert widget.isValid() #This is just here to validate proper cast
            if genericProperty.getType() == PyIndi.INDI_BLOB:
                for widget in PyIndi.PropertyBlob(genericProperty):
                    #print(f"       {widget.getName()}({widget.getLabel()}) = <blob {widget.getSize()} bytes>")
                    if isinstance(widget, PyIndi.WidgetViewBlob):
                        pass
                    else:
                        assert widget.isValid() #This is just here to validate proper cast

def test_PyIndiDeviceConnection():
    device_name = "CCD Simulator"

    # Create an instance of the IndiClient class and initialize its host/port members
    indiclient = IndiClient()
    indiclient.setServer("localhost", 7624)
    res = indiclient.connectServer()
    assert res
    assert indiclient.isServerConnected()

    # Basic device introspection
    camera = None
    while not camera:
        camera = indiclient.getDevice(deviceName=device_name)
        time.sleep(0.1)

    assert camera.isValid()
    indiclient.connectDevice(deviceName=device_name)
    assert camera.isConnected()
    assert camera.isValid()
    attribute_list = dir(camera)
    assert attribute_list
    attribute_dict = {k: getattr(camera, k) for k in camera.__dir__()}
    assert attribute_dict
    print(f"Here is the device object attributes/methods {dir(camera)}")

    # Basic device data
    assert camera.getDeviceName() == device_name
    assert camera.getDriverExec()
    assert camera.getDriverInterface()
    assert camera.getDriverName()
    assert camera.getDriverVersion()

    # Connection status - all are equivalent
    conn_status = camera.isConnected()
    cpv = camera.getSwitch("CONNECTION")
    cpv.isValid()
    assert cpv.getStateAsString() == "Ok"
    assert cpv.getState() == PyIndi.IPS_OK
    names = [s.getName() for s in cpv]
    assert 'CONNECT' in names
    assert 'DISCONNECT' in names
    assert [s for s in cpv if s.getName() == "CONNECT"][0].getState() == PyIndi.ISS_ON
    assert [s for s in cpv if s.getName() == "DISCONNECT"][0].getState() == PyIndi.ISS_OFF
    indiclient.connectDevice(deviceName=device_name)
    assert camera.isConnected()
    assert camera.isValid()
    # Please notice that there is no need to explicitly "receive" the switch, it is automatically updated
    # DisconnectDevice is equivalent to send CONNECTION switch DISCONNECT
    indiclient.disconnectDevice(deviceName=device_name)
    assert [s for s in cpv if s.getName() == "CONNECT"][0].getState() == PyIndi.ISS_OFF
    assert [s for s in cpv if s.getName() == "DISCONNECT"][0].getState() == PyIndi.ISS_ON
    assert not camera.isConnected()
    assert camera.isValid()
    # Check is setting a simple switch of the vector inside switch property vector does something
    [s for s in cpv if s.getName() == "CONNECT"][0].setState(PyIndi.ISS_ON)
    # Answer: no it doesnt, we have inconsistent state locally:
    assert cpv.isValid()
    assert [s for s in cpv if s.getName() == "CONNECT"][0].getState() == PyIndi.ISS_ON
    assert [s for s in cpv if s.getName() == "DISCONNECT"][0].getState() == PyIndi.ISS_ON
    # Does it triggers an error if we try to send ?
    indiclient.sendNewSwitch(cpv) # Apparently no... it just takes the connect
    assert cpv.isValid()
    while not camera.isConnected():
        time.sleep(0.1)
    assert camera.isConnected()
    assert [s for s in cpv if s.getName() == "CONNECT"][0].getState() == PyIndi.ISS_ON
    assert [s for s in cpv if s.getName() == "DISCONNECT"][0].getState() == PyIndi.ISS_OFF

# testPyIndi.IndiClient
# ['__class__',
#  '__delattr__',
#  '__dict__',
#  '__dir__',
#  '__disown__',
#  '__doc__',
#  '__eq__',
#  '__format__',
#  '__ge__',
#  '__getattribute__',
#  '__getstate__',
#  '__gt__',
#  '__hash__',
#  '__init__',
#  '__init_subclass__',
#  '__le__',
#  '__lt__',
#  '__module__',
#  '__ne__',
#  '__new__',
#  '__reduce__',
#  '__reduce_ex__',
#  '__repr__',
#  '__setattr__',
#  '__sizeof__',
#  '__str__',
#  '__subclasshook__',
#  '__swig_destroy__',
#  '__weakref__',
#  'connectDevice',
#  'connectServer',
#  'disconnectDevice',
#  'disconnectServer',
#  'enableDirectBlobAccess',
#  'finishBlob',
#  'getBLOBMode',
#  'getDevice',
#  'getDevices',
#  'getHost',
#  'getPort',
#  'isServerConnected',
#  'isVerbose',
#  'logger',
#  'newDevice',
#  'newMessage',
#  'newPingReply',
#  'newProperty',
#  'newUniversalMessage',
#  'removeDevice',
#  'removeProperty',
#  'sendNewNumber',
#  'sendNewProperty',
#  'sendNewSwitch',
#  'sendNewText',
#  'sendOneBlob',
#  'sendOneBlobFromBuffer',
#  'sendPingReply',
#  'sendPingRequest',
#  'serverConnected',
#  'serverDisconnected',
#  'setBLOBMode',
#  'setConnectionTimeout',
#  'setServer',
#  'setVerbose',
#  'startBlob',
#  'this',
#  'thisown',
#  'updateProperty',
#  'watchDevice',
#  'watchProperty']



# PyIndi.PyIndi.BaseDevice
# ['AO_INTERFACE',
#  'AUX_INTERFACE',
#  'CCD_INTERFACE',
#  'CORRELATOR_INTERFACE',
#  'DETECTOR_INTERFACE',
#  'DOME_INTERFACE',
#  'DUSTCAP_INTERFACE',
#  'FILTER_INTERFACE',
#  'FOCUSER_INTERFACE',
#  'GENERAL_INTERFACE',
#  'GPS_INTERFACE',
#  'GUIDER_INTERFACE',
#  'INDI_DEVICE_NOT_FOUND',
#  'INDI_DISABLED',
#  'INDI_DISPATCH_ERROR',
#  'INDI_ENABLED',
#  'INDI_PROPERTY_DUPLICATED',
#  'INDI_PROPERTY_INVALID',
#  'INPUT_INTERFACE',
#  'LIGHTBOX_INTERFACE',
#  'OUTPUT_INTERFACE',
#  'POWER_INTERFACE',
#  'ROTATOR_INTERFACE',
#  'SENSOR_INTERFACE',
#  'SPECTROGRAPH_INTERFACE',
#  'TELESCOPE_INTERFACE',
#  'WATCH_NEW',
#  'WATCH_NEW_OR_UPDATE',
#  'WATCH_UPDATE',
#  'WEATHER_INTERFACE',
#  '__bool__',
#  '__class__',
#  '__delattr__',
#  '__deref__',
#  '__dict__',
#  '__dir__',
#  '__doc__',
#  '__eq__',
#  '__format__',
#  '__ge__',
#  '__getattribute__',
#  '__getstate__',
#  '__gt__',
#  '__hash__',
#  '__init__',
#  '__init_subclass__',
#  '__le__',
#  '__lt__',
#  '__module__',
#  '__ne__',
#  '__new__',
#  '__nonzero__',
#  '__reduce__',
#  '__reduce_ex__',
#  '__repr__',
#  '__setattr__',
#  '__sizeof__',
#  '__str__',
#  '__subclasshook__',
#  '__swig_destroy__',
#  '__weakref__',
#  'addMessage',
#  'attach',
#  'buildProp',
#  'buildSkeleton',
#  'checkMessage',
#  'detach',
#  'doMessage',
#  'getBLOB',
#  'getDeviceName',
#  'getDriverExec',
#  'getDriverInterface',
#  'getDriverName',
#  'getDriverVersion',
#  'getLight',
#  'getMediator',
#  'getNumber',
#  'getProperties',
#  'getProperty',
#  'getPropertyPermission',
#  'getPropertyState',
#  'getRawProperty',
#  'getSharedFilePath',
#  'getSwitch',
#  'getText',
#  'isConnected',
#  'isDeviceNameMatch',
#  'isValid',
#  'lastMessage',
#  'messageQueue',
#  'registerProperty',
#  'removeProperty',
#  'setDeviceName',
#  'setMediator',
#  'setValue',
#  'this',
#  'thisown',
#  'watchProperty']