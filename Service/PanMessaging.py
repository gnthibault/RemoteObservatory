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
        print(f"Messaging placeholder, sending msg {message} on channel {channel}")
        #return NotImplementedError()

    def register_callback(self, callback, cmd_type):
        return
        #return NotImplementedError()
