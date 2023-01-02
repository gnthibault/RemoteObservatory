# General stuff
from bson import ObjectId
import datetime
import json
import logging
import random
import yaml

# Astropy
from astropy import units as u
from astropy.time import Time

# Local
from Service.NTPTimeService import HostTimeService

class PanMessaging:
    """
    """
    logger = logging.getLogger('PanMessaging')

    def __init__(self, **kwargs):
        self.serv_time = HostTimeService()

    def send_message(self, channel, message):
        """ Responsible for actually sending message across a channel
        Args:
            channel(str):   Name of channel to send on.
            message(str):   Message to be sent.
        """
        raise NotImplementedError()

    def register_callback(self, callback, cmd_type=None):
        raise NotImplementedError()

    def scrub_message(self, message):
        for k, v in message.items():
            if isinstance(v, dict):
                v = self.scrub_message(v)
            if isinstance(v, u.Quantity):
                v = v.value
            if isinstance(v, datetime.datetime):
                v = v.isoformat()
            if isinstance(v, ObjectId):
                v = str(v)
            if isinstance(v, Time):
                v = str(v.isot).split('.')[0].replace('T', ' ')
            # Hmmmm
            if k.endswith('_time'):
                v = str(v).split(' ')[-1]
            if isinstance(v, float):
                v = round(v, 3)
            message[k] = v
        return message

