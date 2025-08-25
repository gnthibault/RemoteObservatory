# Basic stuff
import json
import logging
import time

# Local
from Base.Base import Base
from helper.IndiDevice import IndiDevice
from Focuser.IndiFocuserMixin import IndiFocuserMixin


class IndiBaaderSteelDrive2Focuser(IndiDevice, IndiFocuserMixin):
    """
        Return of indi_getprop -h 192.168.0.194 -p 7624 "Baader SteelDriveII.*.*"
            Baader SteelDriveII.CONNECTION.CONNECT=On
            Baader SteelDriveII.CONNECTION.DISCONNECT=Off
            Baader SteelDriveII.DRIVER_INFO.DRIVER_NAME=Baader SteelDriveII
            Baader SteelDriveII.DRIVER_INFO.DRIVER_EXEC=indi_steeldrive2_focus
            Baader SteelDriveII.DRIVER_INFO.DRIVER_VERSION=1.0
            Baader SteelDriveII.DRIVER_INFO.DRIVER_INTERFACE=8
            Baader SteelDriveII.DEBUG.ENABLE=Off
            Baader SteelDriveII.DEBUG.DISABLE=On
            Baader SteelDriveII.POLLING_PERIOD.PERIOD_MS=500
            Baader SteelDriveII.SIMULATION.ENABLE=Off
            Baader SteelDriveII.SIMULATION.DISABLE=On
            Baader SteelDriveII.CONFIG_PROCESS.CONFIG_LOAD=Off
            Baader SteelDriveII.CONFIG_PROCESS.CONFIG_SAVE=Off
            Baader SteelDriveII.CONFIG_PROCESS.CONFIG_DEFAULT=Off
            Baader SteelDriveII.CONFIG_PROCESS.CONFIG_PURGE=Off
            Baader SteelDriveII.CONNECTION_MODE.CONNECTION_SERIAL=On
            Baader SteelDriveII.CONNECTION_MODE.CONNECTION_TCP=Off
            Baader SteelDriveII.DEVICE_PORT.PORT=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AB0KCL5O-if00-port0
            Baader SteelDriveII.DEVICE_BAUD_RATE.9600=Off
            Baader SteelDriveII.DEVICE_BAUD_RATE.19200=On
            Baader SteelDriveII.DEVICE_BAUD_RATE.38400=Off
            Baader SteelDriveII.DEVICE_BAUD_RATE.57600=Off
            Baader SteelDriveII.DEVICE_BAUD_RATE.115200=Off
            Baader SteelDriveII.DEVICE_BAUD_RATE.230400=Off
            Baader SteelDriveII.DEVICE_AUTO_SEARCH.INDI_ENABLED=Off
            Baader SteelDriveII.DEVICE_AUTO_SEARCH.INDI_DISABLED=On
            Baader SteelDriveII.DEVICE_PORT_SCAN.Scan Ports=On
            Baader SteelDriveII.SYSTEM_PORTS.Pegasus_Astro_UPBv2_revD_UPB25S4VWV=Off
            Baader SteelDriveII.SYSTEM_PORTS.FTDI_FT232R_USB_UART_AB0KCL5O=Off
            Baader SteelDriveII.FOCUS_MOTION.FOCUS_INWARD=On
            Baader SteelDriveII.FOCUS_MOTION.FOCUS_OUTWARD=Off
            Baader SteelDriveII.REL_FOCUS_POSITION.FOCUS_RELATIVE_POSITION=0
            Baader SteelDriveII.ABS_FOCUS_POSITION.FOCUS_ABSOLUTE_POSITION=2000
            Baader SteelDriveII.FOCUS_MAX.FOCUS_MAX_VALUE=65535
            Baader SteelDriveII.FOCUS_ABORT_MOTION.ABORT=Off
            Baader SteelDriveII.FOCUS_SYNC.FOCUS_SYNC_VALUE=0
            Baader SteelDriveII.FOCUS_REVERSE_MOTION.INDI_ENABLED=Off
            Baader SteelDriveII.FOCUS_REVERSE_MOTION.INDI_DISABLED=On
            Baader SteelDriveII.Presets.PRESET_1=0
            Baader SteelDriveII.Presets.PRESET_2=0
            Baader SteelDriveII.Presets.PRESET_3=0
            Baader SteelDriveII.Goto.Preset 1=Off
            Baader SteelDriveII.Goto.Preset 2=Off
            Baader SteelDriveII.Goto.Preset 3=Off
            Baader SteelDriveII.USEJOYSTICK.ENABLE=Off
            Baader SteelDriveII.USEJOYSTICK.DISABLE=On
            Baader SteelDriveII.SNOOP_JOYSTICK.SNOOP_JOYSTICK_DEVICE=Joystick
            Baader SteelDriveII.INFO.INFO_NAME=BP SteelDrive II
            Baader SteelDriveII.INFO.INFO_VERSION=1.130 (Mar  4 2021)
            Baader SteelDriveII.OPERATION.OPERATION_REBOOT=Off
            Baader SteelDriveII.OPERATION.OPERATION_RESET=Off
            Baader SteelDriveII.OPERATION.OPERATION_ZEROING=Off
            Baader SteelDriveII.TC_COMPENSATE.TC_ENABLED=Off
            Baader SteelDriveII.TC_COMPENSATE.TC_DISABLED=On
            Baader SteelDriveII.TC_State.TC_ACTIVE=On
            Baader SteelDriveII.TC_State.TC_PAUSED=Off
            Baader SteelDriveII.TC_SETTINGS.TC_FACTOR=0
            Baader SteelDriveII.TC_SETTINGS.TC_PERIOD=60000
            Baader SteelDriveII.TC_SETTINGS.TC_DELTA=0.5
            Baader SteelDriveII.TC_SENSOR.TEMP_0=-128
            Baader SteelDriveII.TC_SENSOR.TEMP_1=-128
            Baader SteelDriveII.TC_SENSOR.TEMP_AVG=-128
            Baader SteelDriveII.STEPPER_DRIVE.STEPPER_DRIVE_CURRENT_MOVE=25
            Baader SteelDriveII.STEPPER_DRIVE.STEPPER_DRIVE_CURRENT_HOLD=80
            Baader SteelDriveII.USEJOYSTICK.ENABLE=Off
            Baader SteelDriveII.USEJOYSTICK.DISABLE=On
            Baader SteelDriveII.SNOOP_JOYSTICK.SNOOP_JOYSTICK_DEVICE=Joystick
    """
    def __init__(self,
                 config=None,
                 connect_on_create=True):

        self.is_initialized = False

        if config is None:
            config = dict(
                device_name="Baader SteelDriveII",
                device_port="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AB0KCL5O-if00-port0",
                connection_type="CONNECTION_SERIAL",
                baud_rate=19200,
                polling_ms=1000,
                home_position=2000,
                default_focus=8450,
                focus_range={
                    "min": 8200,
                    "max": 8700},
                autofocus_step={
                    "coarse": 50,
                    "fine": 10},
                autofocus_range={
                    "coarse": 300,
                    "fine": 150},
                indi_client=dict(indi_host="localhost",
                                 indi_port=7624))

        # Communication config
        self.device_port = config["device_port"]
        self.connection_type = config["connection_type"]
        self.baud_rate = str(config["baud_rate"])
        self.polling_ms = float(config["polling_ms"])

        # Focus parameters
        self.home_position = config["home_position"]
        self.default_focus = config["default_focus"]
        self.focus_range = {k:float(v) for k,v in config['focus_range'].items()}
        self.autofocus_step = {k:float(v) for k,v in config['autofocus_step'].items()}
        self.autofocus_range = {k:float(v) for k,v in config['autofocus_range'].items()}


        # device related intialization
        IndiDevice.__init__(self,
                            device_name=config["device_name"],
                            indi_driver_name=config.get('indi_driver_name', None),
                            indi_client_config=config["indi_client"])

        if connect_on_create:
            self.default_connect()

        # Finished configuring
        self.logger.debug('configured successfully')

    def unpark(self):
        self.logger.debug("Unparking")
        self.start_indi_server()
        self.start_indi_driver()
        self.initialize()
        self.unpark_focuser()
        self.logger.debug("Successfully unparked")

    def unpark_focuser(self):
        self.logger.debug("About to unpark focuser")
        if self.is_connected:
            self.zero_home()
        # Move to default_focus
        IndiFocuserMixin.unpark_focuser(self)
        self.logger.debug("Focuser successfully unparked")

    def park(self):
        self.logger.debug("Parking")
        self.park_focuser()
        self.logger.debug("Successfully parked")

    def park_focuser(self):
        self.logger.debug("About to park focuser")
        if self.is_connected:
            self.reboot_device()
            self.zero_home()

    def zero_home(self):
        if self.get_position() == int(self.home_position):
            self.move_to(int(self.home_position)+500) # This is needed for the hall sensor to actually see the difference
        self.set_switch("OPERATION", on_switches=["OPERATION_ZEROING"])
        self.sync_position(position=self.home_position)

    def reboot_device(self):
        self.set_switch("OPERATION", on_switches=["OPERATION_REBOOT"])

    def factory_reset_device(self):
        self.set_switch("OPERATION", on_switches=["OPERATION_RESET"])

    def default_connect(self):
        """
        Connection is made in two phases:
          * connect client to server so that we can setup options, like port
          * connect server to actual physical device

        Then "initialize" all outputs such that the telescope is in a steady
        state, that can last a very long time (multiple days without operation)
        :return:
        """
        self.logger.debug("Initializing")
        self.connect(connect_device=False)
        self.set_device_communication_options()
        self.connect_device()
        self.reboot_device()

    def set_device_communication_options(self):
        self.set_text("DEVICE_PORT", {"PORT": self.device_port})
        self.set_switch("CONNECTION_MODE", on_switches=[self.connection_type])
        self.set_switch("DEVICE_BAUD_RATE", on_switches=[self.baud_rate])

    def initialize(self):
        """
        Connection is made in two phases:
          * connect client to server so that we can setup options, like port
          * connect server to actual physical device

        Then "initialize" all outputs such that the telescope is in a steady
        state, that can last a very long time (multiple days without operation)
        :return:
        """
        self.logger.debug("Initializing")
        self.default_connect()
        self.is_initialized = True
        self.logger.debug("Successfully Initialized")

    def park(self):
        self.logger.debug("Parking")
        self.deinitialize()
        self.disconnect()
        self.stop_indi_server()
        self.logger.debug("Successfully parked")

    def deinitialize(self):
        if not self.is_initialized:
            self.logger.debug("No need for deinitializing")
            return
        self.logger.debug("Deinitializing")
        # Then switch off all electronic devices
        self.is_initialized = False
        self.logger.debug("Successfully deinitialized")