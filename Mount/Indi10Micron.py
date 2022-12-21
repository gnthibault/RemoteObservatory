# local
from Mount.IndiAbstractMount import IndiAbstractMount


class Indi10Micron(IndiAbstractMount):
    """
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
