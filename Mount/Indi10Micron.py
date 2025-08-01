# local
from Mount.IndiAbstractMount import IndiAbstractMount


class Indi10Micron(IndiAbstractMount):
    """
        Return of indi_getprop -h 192.168.8.202 -p 7624 "LX200 10micron.*.*"
            LX200 10micron.CONNECTION.CONNECT=On
            LX200 10micron.CONNECTION.DISCONNECT=Off
            LX200 10micron.DRIVER_INFO.DRIVER_NAME=10micron
            LX200 10micron.DRIVER_INFO.DRIVER_EXEC=indi_lx200_10micron
            LX200 10micron.DRIVER_INFO.DRIVER_VERSION=1.3
            LX200 10micron.DRIVER_INFO.DRIVER_INTERFACE=5
            LX200 10micron.POLLING_PERIOD.PERIOD_MS=1000
            LX200 10micron.DEBUG.ENABLE=Off
            LX200 10micron.DEBUG.DISABLE=On
            LX200 10micron.SIMULATION.ENABLE=Off
            LX200 10micron.SIMULATION.DISABLE=On
            LX200 10micron.CONFIG_PROCESS.CONFIG_LOAD=Off
            LX200 10micron.CONFIG_PROCESS.CONFIG_SAVE=Off
            LX200 10micron.CONFIG_PROCESS.CONFIG_DEFAULT=Off
            LX200 10micron.CONFIG_PROCESS.CONFIG_PURGE=Off
            LX200 10micron.CONNECTION_MODE.CONNECTION_SERIAL=Off
            LX200 10micron.CONNECTION_MODE.CONNECTION_TCP=On
            LX200 10micron.DEVICE_ADDRESS.ADDRESS=192.168.8.181
            LX200 10micron.DEVICE_ADDRESS.PORT=3490
            LX200 10micron.CONNECTION_TYPE.TCP=On
            LX200 10micron.CONNECTION_TYPE.UDP=Off
            LX200 10micron.DEVICE_LAN_SEARCH.INDI_ENABLED=Off
            LX200 10micron.DEVICE_LAN_SEARCH.INDI_DISABLED=On
            LX200 10micron.ACTIVE_DEVICES.ACTIVE_GPS=
            LX200 10micron.ACTIVE_DEVICES.ACTIVE_DOME=Dome Simulator
            LX200 10micron.DOME_POLICY.DOME_IGNORED=On
            LX200 10micron.DOME_POLICY.DOME_LOCKS=Off
            LX200 10micron.ON_COORD_SET.TRACK=On
            LX200 10micron.ON_COORD_SET.SLEW=Off
            LX200 10micron.ON_COORD_SET.SYNC=Off
            LX200 10micron.ON_COORD_SET.FLIP=Off
            LX200 10micron.EQUATORIAL_EOD_COORD.RA=11.052448272705078125
            LX200 10micron.EQUATORIAL_EOD_COORD.DEC=89.98590850830078125
            LX200 10micron.TELESCOPE_ABORT_MOTION.ABORT=Off
            LX200 10micron.TELESCOPE_TRACK_MODE.TRACK_SIDEREAL=On
            LX200 10micron.TELESCOPE_TRACK_MODE.TRACK_SOLAR=Off
            LX200 10micron.TELESCOPE_TRACK_MODE.TRACK_LUNAR=Off
            LX200 10micron.TELESCOPE_TRACK_MODE.TRACK_CUSTOM=Off
            LX200 10micron.TELESCOPE_TRACK_STATE.TRACK_ON=On
            LX200 10micron.TELESCOPE_TRACK_STATE.TRACK_OFF=Off
            LX200 10micron.TELESCOPE_TRACK_RATE.TRACK_RATE_RA=15.04106717867020393
            LX200 10micron.TELESCOPE_TRACK_RATE.TRACK_RATE_DE=0
            LX200 10micron.TELESCOPE_MOTION_NS.MOTION_NORTH=Off
            LX200 10micron.TELESCOPE_MOTION_NS.MOTION_SOUTH=Off
            LX200 10micron.TELESCOPE_MOTION_WE.MOTION_WEST=Off
            LX200 10micron.TELESCOPE_MOTION_WE.MOTION_EAST=Off
            LX200 10micron.TELESCOPE_REVERSE_MOTION.REVERSE_NS=Off
            LX200 10micron.TELESCOPE_REVERSE_MOTION.REVERSE_WE=Off
            LX200 10micron.TELESCOPE_SLEW_RATE.1x=Off
            LX200 10micron.TELESCOPE_SLEW_RATE.2x=Off
            LX200 10micron.TELESCOPE_SLEW_RATE.3x=Off
            LX200 10micron.TELESCOPE_SLEW_RATE.4x=On
            LX200 10micron.TARGET_EOD_COORD.RA=0
            LX200 10micron.TARGET_EOD_COORD.DEC=0
            LX200 10micron.TIME_UTC.UTC=2025-08-01T01:56:10
            LX200 10micron.TIME_UTC.OFFSET=2
            LX200 10micron.GEOGRAPHIC_COORD.LAT=46.233055555555559124
            LX200 10micron.GEOGRAPHIC_COORD.LONG=6.0666666666666664298
            LX200 10micron.GEOGRAPHIC_COORD.ELEV=418.04998799999998482
            LX200 10micron.TELESCOPE_PARK.PARK=Off
            LX200 10micron.TELESCOPE_PARK.UNPARK=On
            LX200 10micron.TELESCOPE_PIER_SIDE.PIER_WEST=On
            LX200 10micron.TELESCOPE_PIER_SIDE.PIER_EAST=Off
            LX200 10micron.SAT_TLE_TEXT.TLE=
            LX200 10micron.SAT_PASS_WINDOW.SAT_PASS_WINDOW_START=2025-07-31T23:27:36
            LX200 10micron.SAT_PASS_WINDOW.SAT_PASS_WINDOW_END=2025-07-31T23:27:36
            LX200 10micron.SAT_TRACKING_STAT.SAT_TRACK=Off
            LX200 10micron.SAT_TRACKING_STAT.SAT_HALT=On
            LX200 10micron.USEJOYSTICK.ENABLE=Off
            LX200 10micron.USEJOYSTICK.DISABLE=On
            LX200 10micron.SNOOP_JOYSTICK.SNOOP_JOYSTICK_DEVICE=Joystick
            LX200 10micron.Tracking Frequency.trackFreq=60.200000762939453125
            LX200 10micron.Use Pulse Cmd.Off=Off
            LX200 10micron.Use Pulse Cmd.On=On
            LX200 10micron.TELESCOPE_TIMED_GUIDE_NS.TIMED_GUIDE_N=0
            LX200 10micron.TELESCOPE_TIMED_GUIDE_NS.TIMED_GUIDE_S=0
            LX200 10micron.TELESCOPE_TIMED_GUIDE_WE.TIMED_GUIDE_W=0
            LX200 10micron.TELESCOPE_TIMED_GUIDE_WE.TIMED_GUIDE_E=0
            LX200 10micron.PRODUCT_INFO.NAME=10micron GM2000HPS
            LX200 10micron.PRODUCT_INFO.CONTROL_BOX=Q-TYPE2016
            LX200 10micron.PRODUCT_INFO.FIRMWARE_VERSION=3.1.10
            LX200 10micron.PRODUCT_INFO.FIRMWARE_DATE=2022-10-12T16:47:16
            LX200 10micron.UNATTENDED_FLIP.Disabled=On
            LX200 10micron.UNATTENDED_FLIP.Enabled=Off
            LX200 10micron.REFRACTION_MODEL_TEMPERATURE.TEMPERATURE=16.700000762939453125
            LX200 10micron.REFRACTION_MODEL_PRESSURE.PRESSURE=942.5999755859375
            LX200 10micron.MODEL_COUNT.COUNT=1
            LX200 10micron.ALIGNMENT_POINTS.COUNT=0
            LX200 10micron.Alignment.Idle=On
            LX200 10micron.Alignment.Start=Off
            LX200 10micron.Alignment.End=Off
            LX200 10micron.Alignment.Del=Off
            LX200 10micron.MINIMAL_NEW_ALIGNMENT_POINT_RO.MRA=11.052448272705078125
            LX200 10micron.MINIMAL_NEW_ALIGNMENT_POINT_RO.MDEC=89.98590850830078125
            LX200 10micron.MINIMAL_NEW_ALIGNMENT_POINT_RO.MSIDE=1
            LX200 10micron.MINIMAL_NEW_ALIGNMENT_POINT_RO.SIDTIME=23.077147222222222922
            LX200 10micron.MINIMAL_NEW_ALIGNMENT_POINT.PRA=0
            LX200 10micron.MINIMAL_NEW_ALIGNMENT_POINT.PDEC=0
            LX200 10micron.NEW_ALIGNMENT_POINT.MRA=0
            LX200 10micron.NEW_ALIGNMENT_POINT.MDEC=0
            LX200 10micron.NEW_ALIGNMENT_POINT.MSIDE=0
            LX200 10micron.NEW_ALIGNMENT_POINT.SIDTIME=0
            LX200 10micron.NEW_ALIGNMENT_POINT.PRA=0
            LX200 10micron.NEW_ALIGNMENT_POINT.PDEC=0
            LX200 10micron.NEW_ALIGNMENT_POINTS.COUNT=0
            LX200 10micron.NEW_MODEL_NAME.NAME=newmodel
            LX200 10micron.TLE_NUMBER.NUMBER=1
            LX200 10micron.ACTIVE_DEVICES.ACTIVE_GPS=
            LX200 10micron.ACTIVE_DEVICES.ACTIVE_DOME=Dome Simulator
            LX200 10micron.DOME_POLICY.DOME_IGNORED=On
            LX200 10micron.DOME_POLICY.DOME_LOCKS=Off
            LX200 10micron.USEJOYSTICK.ENABLE=Off
            LX200 10micron.USEJOYSTICK.DISABLE=On
            LX200 10micron.SNOOP_JOYSTICK.SNOOP_JOYSTICK_DEVICE=Joystick
    """

    def __init__(self, location, serv_time,
                 config=None, connect_on_create=True):
        if config is None:
            config = dict(mount_name="10micron")

        super().__init__(location=location,
                         serv_time=serv_time,
                         config=config,
                         connect_on_create=connect_on_create)

    def get_guide_rate(self):
        """
            GUIDE_RATE number should look like this:
            {'GUIDE_RATE_WE': {
                 'name': 'GUIDE_RATE_WE',
                 'label': 'W/E Rate', 'value': 0.5,
                 'min': 0.0,
                 'max': 1.0,
                 'step': 0.1,
                 'format': '%g'},
             'GUIDE_RATE_NS': {
                 'name': 'GUIDE_RATE_NS',
                 'label': 'N/S Rate',
                 'value': 0.5,
                 'min': 0.0,
                 'max': 1.0,
                 'step': 0.1,
                 'format': '%g'},
             'state': 'OK'}
        """
        guide_rate = {}
        guide_rate['NS'] = {
                 'name': 'GUIDE_RATE_NS',
                 'label': 'N/S Rate',
                 'value': 0.5,
                 'min': 0.0,
                 'max': 1.0,
                 'step': 0.1,
                 'format': '%g'}
        guide_rate['WE'] = {
                 'name': 'GUIDE_RATE_WE',
                 'label': 'W/E Rate', 'value': 0.5,
                 'min': 0.0,
                 'max': 1.0,
                 'step': 0.1,
                 'format': '%g'},
        self.logger.warning(f"Device {self.device_name} driver does not implement guide rate getter")
        return guide_rate

    def set_guide_rate(self, guide_rate={'NS':0.5,'WE':0.5}):
        """
        """
        self.logger.warning(f"Device {self.device_name} driver does not implement guide rate setup")

    # def set_coord(self, coord):
    #     """
    #     Subtleties here: coord should be given as Equatorial astrometric epoch
    #     of date coordinate (eod):  RA JNow RA, hours,  DEC JNow Dec, degrees +N
    #
    #     As our software only manipulates J2000. we decided to convert to jnow
    #     for the generic case
    #     """
    #     fk5_j2k = FK5(equinox=Time('J2000'))
    #     coord_j2k = coord.transform_to(fk5_j2k)
    #     rahour_decdeg = {'RA': coord_j2k.ra.hour,
    #                      'DEC': coord_j2k.dec.degree}
    #     if self.is_parked:
    #         self.logger.warning(f"Cannot set coord: {rahour_decdeg} because "
    #                             f"mount is parked")
    #     else:
    #         self.logger.info(f"Now setting J2k coord: {rahour_decdeg}")
    #         self.set_number('EQUATORIAL_EOD_COORD', rahour_decdeg, sync=True,
    #                        timeout=180)
