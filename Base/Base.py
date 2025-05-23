# Generic
import logging
import sys
import threading

# Local stuff
#from pocs import hardware
from version import __version__
from utils.config import load_config
from utils.database import DB

# Global vars
_config = None

def reset_global_config():
    """Reset the global _config to None.

    Globals such as _config make tests non-hermetic. Enable conftest.py to
    clear _config in an explicit fashion.
    """
    global _config
    _config = None

class Base:
    """ Base class for other classes within the PANOPTES ecosystem

    Defines common properties for each class (e.g. logger, config).
    """

    def __init__(self, *args, **kwargs):
        # Load the default and local config files
        global _config
        if _config is None:
            ignore_local_config = kwargs.get('ignore_local_config', False)
            _config = load_config(ignore_local=ignore_local_config)

        self.__version__ = __version__

        # Update with run-time config
        if 'config' in kwargs:
            _config.update(kwargs['config'])

        self._check_config(_config)
        self.config = _config

        self.logger = kwargs.get('logger') or (
            logging.getLogger(self.__class__.__name__))

        # Get passed DB or set up new connection
        _db = kwargs.get('db', None)
        if _db is None:
            # If the user requests a db_type then update runtime config
            db_type = kwargs.get('db_type', None)
            db_name = kwargs.get('db_name', None)

            if db_type is not None:
                self.config['db']['type'] = db_type
            if db_name is not None:
                self.config['db']['name'] = db_name

            db_type = self.config['db']['type']
            db_name = self.config['db']['name']

            _db = DB(db_type=db_type, db_name=db_name, logger=self.logger)

        self.db = _db

    def _check_config(self, temp_config):
        """ Checks the config file for mandatory items """

        if 'directories' not in temp_config:
            raise RuntimeError("Base class: directories must be specified in config")

        if 'mount' not in temp_config:
            raise RuntimeError("Base class: Mount must be specified in config")

        if 'state_machine' not in temp_config:
            raise RuntimeError("Base class: State Table must be specified in config")

    def __getstate__(self):  # pragma: no cover
        """ Returns a copy of the internal dictionary without
            restricted acess ressources (logger and database object
        """
        d = dict(self.__dict__)

        if 'logger' in d:
            del d['logger']

        if 'db' in d:
            del d['db']

        return d
