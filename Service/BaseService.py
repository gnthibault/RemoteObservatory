# Generic modules
import logging

# Local
from utils.config import load_config

# Global vars
_config = None

class BaseService():
    """
      Define common stuff for services. Is mainly used for providing helpers for
      class that are needed by the Base.Base class, such that we avoid circular
      dependency
    """
    def __init__(self, config = None, logger=None):
        global _config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        if _config is None:
            _config = load_config()
        self.config = _config


