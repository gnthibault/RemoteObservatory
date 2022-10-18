# General stuff
import json
import logging

# Astropy
from astropy import units as u
from astropy.time import Time

# GCP

# Local
from Service.NTPTimeService import HostTimeService
from Service.PanMessaging import PanMessaging

class PanMessagingPubSub(PanMessaging):

    """Messaging class for PANOPTES project. Creates a new pubsub
    context that can be shared across parent application.
    """
    logger = logging.getLogger('PanMessaging')

    def __init__(self, **kwargs):
        super().__init__(kwargs["config"])
