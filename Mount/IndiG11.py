# Astropy
import time

import astropy.units as u

# local
from Mount.IndiMount import IndiMount
from Mount.IndiAbstractMount import IndiAbstractMount

class IndiG11(IndiAbstractMount):
    """
    Doc coming from
     https://gemini-2.com/hc/index.php
     https://www.indilib.org/devices/mounts/losmandy.html

    
     Startup mode:
     Cold: 
     A cold start wipes out all stored modeling. You need to have your mount
     positioned at want is called CWD.  This is with the counter weights down,
     and the Declination pointed towards Polaris in the Northern Hemisphere,
     and the South Celestial Pole in the Southern Hemisphere.
     The processor in the Gemini-2 uses this approximant position to start
     its calculations from.  It expects you to do an alignment, or
     synchronize on a bright star.  When you align or synchronize on the
     bright start, then the processor refines the known position in the sky
     and also repositions the limits correctly.  It also updates the All 
     modeling calculations will start from this point in space.
     Warm:
     This is basically the same as a cold start, but does not wipe out any
     models built. It also remembers all your setting. You still must start
     with the mount pointed to CWD position as in a cold start. If you have 
     models built, but have moved your Right Ascension axis or Declination
     axis, but not the location of the mount itself, then you can use this
     startup mode. Warm Start uses the CWD position as an approximant starting
     position, but expects you to do either an alignment, or synchronize on a
     bright star.  When you align or synchronize on the bright start, then the
     processors re-centers the model, and positions the limits correctly
     Restart:
     This mode also remembers your modeling and all setting. You can only use
     this mode if, and only if you have not moved both the Right Ascension
     axis or Declination axis and also have not moved the mount in position.
     All calculations will start from this point.  


     Startup settings
     The parking setting defaults to Home position but can be changed to
     Startup or Zenith as desired. Home defaults to CWD but can be changed by
     user through the handcontrol.
     Unpark wakes the mount up in the same position as parked.
     Home
     Startup
     Zenith

     Related to meridian flips:
     With respect to meridian flips, the mount performs a meridian flip on a
     GOTO-command when within 2.5 degrees of the safety limit. You can set a
     GoTo limit with the handcontroller, meaning that when past this limit, the
     mount performs a meridian flip. If set to 90 degrees, it flips on a GoTo
     command at any positive hour angle. However, to be safe, it is recommended
     to set a hour angle at for instance 0.2 hours to be safe. Refer to the
     Gemini manual pages 69-70 on setting the GoTo limit.

     About J2k / JNow coordinates:
     5.3.2.2 Accuracy and Epochs
     With the exception of the Solar System objects and the Alignment Bright
     Star list, all coordinates are stored rounded to 20 arcsec, giving 10
     arcsec accuracy for the standard epoch J2000.0. The coordinates are
     precessed to the equinox of the date when the object is selected; nutation
     is neglected. The apparent position of objects is calculated (for standard
     air pressure and temperature), taking refraction into account.
     For the Moon, topocentric coordinates are calculated. By default, Gemini
     assumes that any input coordinates are for the epoch of the current date.
     This default can be changed to Epoch J2000.0 by executing
     "Setup→Communication→Coordinate Epoch→Epoch J2000.0." If this change is
     made and Epoch J2000.0 coordinates are entered, Gemini will precess the
     entered coordinates to the epoch of the date so that GoTo slews will be
     accurate. The coordinates of the resident catalogs will not, however, be
     affected regardless of which epoch is selected.

     Related to meridian flip:
     https://indilib.org/forum/mounts/3550-losmandy-gemini-2-auto-meridian-flip-in-ekos.html
     https://www.indilib.org/forum/mounts/7946-losmandy-g-11-and-gemini-ii-and-merdian-flips.html

     Losmandy Gemini.CONNECTION.CONNECT=On
    Losmandy Gemini.CONNECTION.DISCONNECT=Off
    Losmandy Gemini.DRIVER_INFO.DRIVER_NAME=Losmandy Gemini
    Losmandy Gemini.DRIVER_INFO.DRIVER_EXEC=indi_lx200gemini
    Losmandy Gemini.DRIVER_INFO.DRIVER_VERSION=1.6
    Losmandy Gemini.DRIVER_INFO.DRIVER_INTERFACE=5
    Losmandy Gemini.POLLING_PERIOD.PERIOD_MS=1000
    Losmandy Gemini.DEBUG.ENABLE=Off
    Losmandy Gemini.DEBUG.DISABLE=On
    Losmandy Gemini.SIMULATION.ENABLE=Off
    Losmandy Gemini.SIMULATION.DISABLE=On
    Losmandy Gemini.CONFIG_PROCESS.CONFIG_LOAD=Off
    Losmandy Gemini.CONFIG_PROCESS.CONFIG_SAVE=Off
    Losmandy Gemini.CONFIG_PROCESS.CONFIG_DEFAULT=Off
    Losmandy Gemini.CONFIG_PROCESS.CONFIG_PURGE=Off
    Losmandy Gemini.CONNECTION_MODE.CONNECTION_SERIAL=Off
    Losmandy Gemini.CONNECTION_MODE.CONNECTION_TCP=On
    Losmandy Gemini.DEVICE_ADDRESS.ADDRESS=192.168.8.63
    Losmandy Gemini.DEVICE_ADDRESS.PORT=11110
    Losmandy Gemini.CONNECTION_TYPE.TCP=Off
    Losmandy Gemini.CONNECTION_TYPE.UDP=On
    Losmandy Gemini.DEVICE_LAN_SEARCH.INDI_ENABLED=Off
    Losmandy Gemini.DEVICE_LAN_SEARCH.INDI_DISABLED=On
    Losmandy Gemini.ACTIVE_DEVICES.ACTIVE_GPS=GPS Simulator
    Losmandy Gemini.ACTIVE_DEVICES.ACTIVE_DOME=Dome Simulator
    Losmandy Gemini.DOME_POLICY.DOME_IGNORED=On
    Losmandy Gemini.DOME_POLICY.DOME_LOCKS=Off
    Losmandy Gemini.TELESCOPE_INFO.TELESCOPE_APERTURE=200
    Losmandy Gemini.TELESCOPE_INFO.TELESCOPE_FOCAL_LENGTH=800
    Losmandy Gemini.TELESCOPE_INFO.GUIDER_APERTURE=200
    Losmandy Gemini.TELESCOPE_INFO.GUIDER_FOCAL_LENGTH=800
    Losmandy Gemini.SCOPE_CONFIG_NAME.SCOPE_CONFIG_NAME=
    Losmandy Gemini.STARTUP_MODE.COLD_START=On
    Losmandy Gemini.STARTUP_MODE.WARM_START=Off
    Losmandy Gemini.STARTUP_MODE.WARM_RESTART=Off
    Losmandy Gemini.ON_COORD_SET.TRACK=On
    Losmandy Gemini.ON_COORD_SET.SLEW=Off
    Losmandy Gemini.ON_COORD_SET.SYNC=Off
    Losmandy Gemini.ON_COORD_SET.FLIP=Off
    Losmandy Gemini.EQUATORIAL_EOD_COORD.RA=8.0608333333333348492
    Losmandy Gemini.EQUATORIAL_EOD_COORD.DEC=85.342777777777769188
    Losmandy Gemini.TELESCOPE_ABORT_MOTION.ABORT=Off
    Losmandy Gemini.TELESCOPE_TRACK_MODE.TRACK_SIDEREAL=On
    Losmandy Gemini.TELESCOPE_TRACK_MODE.TRACK_CUSTOM=Off
    Losmandy Gemini.TELESCOPE_TRACK_MODE.TRACK_LUNAR=Off
    Losmandy Gemini.TELESCOPE_TRACK_MODE.TRACK_SOLAR=Off
    Losmandy Gemini.TELESCOPE_TRACK_STATE.TRACK_ON=On
    Losmandy Gemini.TELESCOPE_TRACK_STATE.TRACK_OFF=Off
    Losmandy Gemini.TELESCOPE_MOTION_NS.MOTION_NORTH=Off
    Losmandy Gemini.TELESCOPE_MOTION_NS.MOTION_SOUTH=Off
    Losmandy Gemini.TELESCOPE_MOTION_WE.MOTION_WEST=Off
    Losmandy Gemini.TELESCOPE_MOTION_WE.MOTION_EAST=Off
    Losmandy Gemini.TELESCOPE_REVERSE_MOTION.REVERSE_NS=Off
    Losmandy Gemini.TELESCOPE_REVERSE_MOTION.REVERSE_WE=Off
    Losmandy Gemini.TELESCOPE_SLEW_RATE.1x=Off
    Losmandy Gemini.TELESCOPE_SLEW_RATE.2x=Off
    Losmandy Gemini.TELESCOPE_SLEW_RATE.3x=On
    Losmandy Gemini.TELESCOPE_SLEW_RATE.4x=Off
    Losmandy Gemini.TARGET_EOD_COORD.RA=8.0608333333333348492
    Losmandy Gemini.TARGET_EOD_COORD.DEC=87.213611111111120522
    Losmandy Gemini.TIME_UTC.UTC=2023-07-28T22:17:12
    Losmandy Gemini.TIME_UTC.OFFSET=2
    Losmandy Gemini.GEOGRAPHIC_COORD.LAT=46.233055555555559124
    Losmandy Gemini.GEOGRAPHIC_COORD.LONG=6.0666666666666664298
    Losmandy Gemini.GEOGRAPHIC_COORD.ELEV=418.04998799999998482
    Losmandy Gemini.TELESCOPE_PARK.PARK=Off
    Losmandy Gemini.TELESCOPE_PARK.UNPARK=On
    Losmandy Gemini.TELESCOPE_PIER_SIDE.PIER_WEST=Off
    Losmandy Gemini.TELESCOPE_PIER_SIDE.PIER_EAST=On
    Losmandy Gemini.PEC.PEC OFF=On
    Losmandy Gemini.PEC.PEC ON=Off
    Losmandy Gemini.APPLY_SCOPE_CONFIG.SCOPE_CONFIG1=On
    Losmandy Gemini.APPLY_SCOPE_CONFIG.SCOPE_CONFIG2=Off
    Losmandy Gemini.APPLY_SCOPE_CONFIG.SCOPE_CONFIG3=Off
    Losmandy Gemini.APPLY_SCOPE_CONFIG.SCOPE_CONFIG4=Off
    Losmandy Gemini.APPLY_SCOPE_CONFIG.SCOPE_CONFIG5=Off
    Losmandy Gemini.APPLY_SCOPE_CONFIG.SCOPE_CONFIG6=Off
    Losmandy Gemini.USEJOYSTICK.ENABLE=Off
    Losmandy Gemini.USEJOYSTICK.DISABLE=On
    Losmandy Gemini.SNOOP_JOYSTICK.SNOOP_JOYSTICK_DEVICE=Joystick
    Losmandy Gemini.Use Pulse Cmd.Off=Off
    Losmandy Gemini.Use Pulse Cmd.On=On
    Losmandy Gemini.Sites.Site 1=On
    Losmandy Gemini.Sites.Site 2=Off
    Losmandy Gemini.Sites.Site 3=Off
    Losmandy Gemini.Sites.Site 4=Off
    Losmandy Gemini.Site Name.Name=Hollywood
    Losmandy Gemini.TELESCOPE_TIMED_GUIDE_NS.TIMED_GUIDE_N=0
    Losmandy Gemini.TELESCOPE_TIMED_GUIDE_NS.TIMED_GUIDE_S=0
    Losmandy Gemini.TELESCOPE_TIMED_GUIDE_WE.TIMED_GUIDE_W=0
    Losmandy Gemini.TELESCOPE_TIMED_GUIDE_WE.TIMED_GUIDE_E=0
    Losmandy Gemini.Firmware Info.Build Date=Mar 12 2017
    Losmandy Gemini.Firmware Info.Build Time=08:22:00
    Losmandy Gemini.Firmware Info.Software Level=5.21
    Losmandy Gemini.Firmware Info.Product Name=Losmandy Gemini
    Losmandy Gemini.Firmware Info.=
    Losmandy Gemini.PARK_SETTINGS.HOME=On
    Losmandy Gemini.PARK_SETTINGS.STARTUP=Off
    Losmandy Gemini.PARK_SETTINGS.ZENITH=Off
    Losmandy Gemini.ENABLE_PEC_AT_BOOT.ENABLE_PEC_AT_BOOT=On
    Losmandy Gemini.PEC_GUIDING_SPEED.PEC_GUIDING_SPEED=0.5
    Losmandy Gemini.PEC_COMMANDS.PEC_START_TRAINING=Off
    Losmandy Gemini.PEC_COMMANDS.PEC_ABORT_TRAINING=Off
    Losmandy Gemini.PEC_COUNTER.PEC_COUNTER=318
    Losmandy Gemini.PEC_MAX_STEPS.PEC_MAX_STEPS=6400
    Losmandy Gemini.PEC_STATE.PEC_STATUS_ACTIVE=No
    Losmandy Gemini.PEC_STATE.PEC_STATUS_FRESH_TRAINED=No
    Losmandy Gemini.PEC_STATE.PEC_STATUS_TRAINING_IN_PROGRESS=No
    Losmandy Gemini.PEC_STATE.PEC_STATUS_TRAINING_COMPLETED=No
    Losmandy Gemini.PEC_STATE.PEC_STATUS_WILL_TRAIN=No
    Losmandy Gemini.PEC_STATE.PEC_STATUS_DATA_AVAILABLE=No
    Losmandy Gemini.SET_CURR_SAFETY.SET_SAFETY=Off
    Losmandy Gemini.SAFETY_LIMITS.EAST_SAFTEY=114
    Losmandy Gemini.SAFETY_LIMITS.WEST_SAFTEY=123
    Losmandy Gemini.SAFETY_LIMITS.WEST_GOTO=2.5
    Losmandy Gemini.MANUAL_SLEWING_SPEED.MANUAL_SLEWING_SPEED=800
    Losmandy Gemini.GOTO_SLEWING_SPEED.GOTO_SLEWING_SPEED=800
    Losmandy Gemini.MOVE_SLEWING_SPEED.MOVE_SPEED=500
    Losmandy Gemini.GUIDING_SLEWING_SPEED_BOTH.GUIDING_SPEED=0.5
    Losmandy Gemini.GUIDE_RATE.GUIDE_RATE_WE=0.5
    Losmandy Gemini.GUIDE_RATE.GUIDE_RATE_NS=0.5
    Losmandy Gemini.CENTERING_SLEWING_SPEED.CENTERING_SPEED=20
    Losmandy Gemini.ACTIVE_DEVICES.ACTIVE_GPS=GPS Simulator
    Losmandy Gemini.ACTIVE_DEVICES.ACTIVE_DOME=Dome Simulator
    Losmandy Gemini.DOME_POLICY.DOME_IGNORED=On
    Losmandy Gemini.DOME_POLICY.DOME_LOCKS=Off
    Losmandy Gemini.TELESCOPE_INFO.TELESCOPE_APERTURE=200
    Losmandy Gemini.TELESCOPE_INFO.TELESCOPE_FOCAL_LENGTH=800
    Losmandy Gemini.TELESCOPE_INFO.GUIDER_APERTURE=200
    Losmandy Gemini.TELESCOPE_INFO.GUIDER_FOCAL_LENGTH=800
    Losmandy Gemini.SCOPE_CONFIG_NAME.SCOPE_CONFIG_NAME=
    Losmandy Gemini.USEJOYSTICK.ENABLE=Off
    Losmandy Gemini.USEJOYSTICK.DISABLE=On
    Losmandy Gemini.SNOOP_JOYSTICK.SNOOP_JOYSTICK_DEVICE=Joystick
    Losmandy Gemini.STARTUP_MODE.COLD_START=On
    Losmandy Gemini.STARTUP_MODE.WARM_START=Off
    Losmandy Gemini.STARTUP_MODE.WARM_RESTART=Off
    """
    
    def __init__(self, location, serv_time, config, connect_on_create=False):

        if config is None:
            config = dict(
                module="IndiG11",
                mount_name="Losmandy Gemini",
                equatorial_eod="J2000",  # JNOW
                tcp_host="192.168.8.63",
                tcp_port="11110",
                max_east_safety_deg=95,
                max_west_safety_deg=95,
                max_west_post_meridian_deg=2.5,
                indi_client=dict(
                    indi_host="localhost",
                    indi_port=7625)
            )
        self.tcp_host = config["tcp_host"]
        self.tcp_port = config["tcp_port"]
        self.max_east_safety_deg = config["max_east_safety_deg"]
        self.max_west_safety_deg = config["max_west_safety_deg"]
        self.max_west_post_meridian_deg = config["max_west_post_meridian_deg"]

        super().__init__(location=location,
                         serv_time=serv_time,
                         config=config,
                         connect_on_create=connect_on_create)

    def initialize(self):
        self.logger.debug("Initializing from IndiG11")
        self.connect(connect_device=False)
        self.set_connectivity_config()
        self.connect_device()
        self.set_startup_mode(mode='WARM_RESTART') #COLD_START')
        self.set_park_settings(mode='HOME')
        self.set_geographic_config()
        self.set_time_config()
        self.set_limit_config()
        #TODO TN URGENT as a temporary fix. we decided to park at startup but
        # the proper behaviour for the mount should be parked status by default
        # at startup, see https://indilib.org/forum/general/5497-indi-losmandy-driver-impossible-to-get-proper-park-status.html#41664
        IndiMount.unpark(self)
        self.logger.debug("Successfully initialized from IndiG11")

    def set_time_config(self):
        """
            Losmandy Gemini.TIME_UTC.UTC=2023-8-8T21:43:12
            Losmandy Gemini.TIME_UTC.OFFSET=2
        :return:
        """
        utc_time_str = self.serv_time.get_astropy_time_from_utc().value.strftime("%Y-%m-%dT%H:%M:%S")
        utc_offset_value = self.serv_time.timezone.localize(self.serv_time.get_astropy_time_from_utc().value).utcoffset().total_seconds()/60/60
        self.set_text("TIME_UTC", {"UTC": utc_time_str}, sync=True)
        self.set_number('TIME_UTC', {'OFFSET': utc_offset_value}, sync=True)

    def set_limit_config(self):
        """
            Losmandy Gemini.SAFETY_LIMITS.EAST_SAFTEY=114
            Losmandy Gemini.SAFETY_LIMITS.WEST_SAFTEY=123
            Losmandy Gemini.SAFETY_LIMITS.WEST_GOTO=2.5
        :return:
        """
        self.set_number(
            'SAFETY_LIMITS',
            {   'EAST_SAFTEY': self.max_east_safety_deg,
                'WEST_SAFTEY': self.max_west_safety_deg,
                'WEST_GOTO': self.max_west_post_meridian_deg},
            sync=True)

    def set_geographic_config(self):
        self.set_number('GEOGRAPHIC_COORD', {
                'LAT': self.location.lat.to(u.deg).value,
                'LONG': self.location.lon.to(u.deg).value,
                'ELEV': self.location.height.to(u.meter).value},
            sync=True)

    def set_connectivity_config(self):
        """
        In fact it's not tcp but udp, but ok ...
        :return:
        """
        self.set_switch('CONNECTION_MODE', ["CONNECTION_TCP"], sync=True)
        self.set_switch('CONNECTION_TYPE', ["UDP"], sync=True)
        self.set_text("DEVICE_ADDRESS",
                      {"ADDRESS": self.tcp_host,
                       "PORT":    self.tcp_port}, sync=True)

    def set_startup_mode(self, mode='WARM_RESTART'):
        """
        STARTUP_MODE Ok
            COLD_START
            WARM_START
            WARM_RESTART
        """
        self.set_switch('STARTUP_MODE', [mode], sync=True, timeout=self.defaultTimeout)


    def set_park_settings(self, mode='HOME'):
        """
            PARK_SETTINGS
                HOME
                STARTUP
                ZENITH
        """
        self.set_switch('PARK_SETTINGS', [mode])

    def set_coord(self, coord):
        IndiMount.set_coord(self, coord)
        # Wait for the mount/tube to damper vibrations
        time.sleep(10)