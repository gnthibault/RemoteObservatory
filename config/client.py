import os

import requests
from loguru import logger
from requests.exceptions import ConnectionError

from utils.error import InvalidConfig
from utils.serializers import from_json, to_json

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


def server_is_running(*args, **kwargs):  # pragma: no cover
    """Thin-wrapper to check server."""
    try:
        return get_config(endpoint='heartbeat', verbose=False, *args, **kwargs)
    except Exception as e:
        logger.warning(f'server_is_running error (ignore if just starting server): {e!r}')
        return False


def get_config(key=None,
               default=None,
               host=None,
               port=None,
               endpoint='get-config',
               parse=True,
               verbose=False
               ):
    """Get a config item from the config server.

    Return the config entry for the given ``key``. If ``key=None`` (default), return
    the entire config.

    Nested keys can be specified as a string, as per `scalpl <https://pypi.org/project/scalpl/>`_.

    Examples:

    .. doctest::

        >>> get_config(key='name')
        'Testing PANOPTES Unit'

        >>> get_config(key='location.horizon')
        <Quantity 30. deg>

        >>> # With no parsing, the raw string (including quotes) is returned.
        >>> get_config(key='location.horizon', parse=False)
        '"30 deg"'
        >>> get_config(key='cameras.devices[1].model')
        'canon_gphoto2'

        >>> # Returns `None` if key is not found.
        >>> foobar = get_config(key='foobar')
        >>> foobar is None
        True

        >>> # But you can supply a default.
        >>> get_config(key='foobar', default='baz')
        'baz'

        >>> # key and default are first two parameters.
        >>> get_config('foobar', 'baz')
        'baz'

        >>> # Can use Quantities as well.
        >>> from astropy import units as u
        >>> get_config('foobar', 42 * u.meter)
        <Quantity 42. m>


    Notes:
        By default all calls to this function will log at the `trace` level because
        there are some calls (e.g. during POCS operation) that will be quite noisy.

        Setting `verbose=True` changes those to `debug` log levels for an individual
        call.

    Args:
        key (str): The key to update, see Examples in :func:`get_config` for details.
        default (str, optional): The config server port, defaults to 6563.
        host (str, optional): The config server host. First checks for CONFIG_HOST
            env var, defaults to 'localhost'.
        port (str or int, optional): The config server port. First checks for CONFIG_HOST
            env var, defaults to 6563.
        endpoint (str, optional): The relative url endpoint to use for getting
            the config items, default 'get-config'. See `server_is_running()`
            for example of usage.
        parse (bool, optional): If response should be parsed by
            :func:`serializers.from_json`, default True.
        verbose (bool, optional): Determines the output log level, defaults to
            True (i.e. `debug` log level). See notes for details.
    Returns:
        dict: The corresponding config entry.

    Raises:
        Exception: Raised if the config server is not available.
    """
    log_level = 'DEBUG' if verbose else 'TRACE'

    host = host or os.getenv('CONFIG_HOST', 'localhost')
    port = port or os.getenv('CONFIG_PORT', 6563)

    url = f'http://{host}:{port}/{endpoint}'

    config_entry = default

    try:
        logger.debug(f'Calling get_config on url={url!r} with  key={key!r}')
        response = requests.post(url, json={'key': key, 'verbose': verbose})
        if not response.ok:  # pragma: no cover
            raise InvalidConfig(f'Config server returned invalid JSON: {response.content!r}')
    except ConnectionError:
        logger.debug('Bad connection to config-server. Check to make sure it is running.')
    except Exception as e:  # pragma: no cover
        logger.warning(f'Problem with get_config: {e!r}')
    else:
        response_text = response.text.strip()
        logger.debug(f'Decoded  response_text={response_text!r}')
        if response_text != 'null':
            logger.debug(f'Received config key={key!r}  response_text={response_text!r}')
            if parse:
                logger.debug(f'Parsing config results:  response_text={response_text!r}')
                config_entry = from_json(response_text)
            else:
                config_entry = response_text

    if config_entry is None:
        logger.debug(f'No config entry found, returning  default={default!r}')
        config_entry = default

    logger.debug(f'Config key={key!r}:  config_entry={config_entry!r}')
    return config_entry


def set_config(key, new_value, host=None, port=None, parse=True):
    """Set config item in config server.

    Given a `key` entry, update the config to match. The `key` is a dot accessible
    string, as given by `scalpl <https://pypi.org/project/scalpl/>`_. See Examples in
    :func:`get_config` for details.

    Examples:

    .. doctest::

        >>> from astropy import units as u

        >>> # Can use astropy units.
        >>> set_config('location.horizon', 35 * u.degree)
        {'location.horizon': <Quantity 35. deg>}

        >>> get_config(key='location.horizon')
        <Quantity 35. deg>

        >>> # String equivalent works for 'deg', 'm', 's'.
        >>> set_config('location.horizon', '30 deg')
        {'location.horizon': <Quantity 30. deg>}

    Args:
        key (str): The key to update, see Examples in :func:`get_config` for details.
        new_value (scalar|object): The new value for the key, can be any serializable object.
        host (str, optional): The config server host. First checks for CONFIG_HOST
            env var, defaults to 'localhost'.
        port (str or int, optional): The config server port. First checks for CONFIG_HOST
            env var, defaults to 6563.
        parse (bool, optional): If response should be parsed by
            :func:`serializers.from_json`, default True.

    Returns:
        dict: The updated config entry.

    Raises:
        Exception: Raised if the config server is not available.
    """
    host = host or os.getenv('CONFIG_HOST', 'localhost')
    port = port or os.getenv('CONFIG_PORT', 6563)
    url = f'http://{host}:{port}/set-config'

    json_str = to_json({key: new_value})

    config_entry = None
    try:
        # We use our own serializer so pass as `data` instead of `json`.
        logger.debug(f'Calling set_config on  url={url!r}')
        response = requests.post(url,
                                 data=json_str,
                                 headers={'Content-Type': 'application/json'}
                                 )
        if not response.ok:  # pragma: no cover
            raise Exception(f'Cannot access config server: {response.text}')
    except Exception as e:
        logger.warning(f'Problem with set_config: {e!r}')
    else:
        if parse:
            config_entry = from_json(response.content.decode('utf8'))
        else:
            config_entry = response.json()

    return config_entry
