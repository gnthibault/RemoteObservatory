#local
from Mount.IndiAbstractMount import IndiAbstractMount


class IndiG11(IndiAbstractMount):
    def __init__(self, indiClient, location, serv_time, config):

        if config is None:
            config = dict(mount_name="G11")

        super().__init__()(indiClient=indiClient,
                           location=location,
                           serv_time=serv_time,
                           config=config)


