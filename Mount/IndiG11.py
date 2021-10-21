#local
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
    """
    
    def __init__(self, indi_client, location, serv_time, config):

        if config is None:
            config = dict(mount_name="Losmandy Gemini")

        super().__init__(indi_client=indi_client,
                         location=location,
                         serv_time=serv_time,
                         config=config,
                         connect_on_create=False)

        self.set_startup_mode(mode='WARM_RESTART')
        self.connect()
        self.set_park_settings(mode='HOME')
        #TODO TN URGENT as a temporary fix. we decided to park at startup but
        # the proper behaviour for the mount should be parked status by default
        # at startup, see https://indilib.org/forum/general/5497-indi-losmandy-driver-impossible-to-get-proper-park-status.html#41664
        self.park()

    def set_startup_mode(self, mode='WARM_RESTART'):
        """
        STARTUP_MODE Ok
            COLD_START
            WARM_START
            WARM_RESTART
        """
        self.set_switch('STARTUP_MODE', [mode])

    def set_park_settings(self, mode='HOME'):
        """
            PARK_SETTINGS
                HOME
                STARTUP
                ZENITH
        """
        self.set_switch('PARK_SETTINGS', [mode])

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
#set_numberVector Losmandy Gemini GEOGRAPHIC_COORD Ok
#        LAT='51.466666666666668561'
#               LONG='5.7166666666666401397'
#                      ELEV='0'

#Dispatch command error(-1):
#<set_switchVector device="Losmandy Gemini" name="TELESCOPE_PARK" state="Ok" timeout="60" timestamp="2019-08-05T00:03:43">
#    <oneSwitch name="PARK">
#On
#    </oneSwitch>
#    <oneSwitch name="UNPARK">
#Off
#    </oneSwitch>
#</set_switchVector>
