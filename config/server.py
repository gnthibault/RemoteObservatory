import logging
import os
from sys import platform
from multiprocessing import Process

from flask import Flask
from flask import jsonify
from flask import request
from gevent.pywsgi import WSGIServer
from scalpl import Cut

from config.helpers import load_config
from config.helpers import save_config

# This seems to be needed. Should switch entire mechanism.
if platform == "darwin" or platform == "win32":
    import multiprocessing
    multiprocessing.set_start_method('fork')

# Turn off noisy logging for Flask wsgi server.
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('gevent').setLevel(logging.WARNING)
# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)


def config_server(config_file,
                  host=None,
                  port=None,
                  load_local=True,
                  save_local=False,
                  auto_start=True,
                  access_logs=None,
                  error_logs='logger',
                  ):
    """Start the config server in a separate process.

    A convenience function to start the config server.

    Args:
        config_file (str or None): The absolute path to the config file to load.
        host (str, optional): The config server host. First checks for CONFIG_HOST
            env var, defaults to 'localhost'.
        port (str or int, optional): The config server port. First checks for CONFIG_HOST
            env var, defaults to 6563.
        load_local (bool, optional): If local config files should be used when loading, default True.
        save_local (bool, optional): If setting new values should auto-save to local file, default False.
        auto_start (bool, optional): If server process should be started automatically, default True.
        access_logs ('default' or `logger` or `File`-like or None, optional): Controls access logs for
            the gevent WSGIServer. The `default` string will cause access logs to go to stderr. The
            string `logger` will use the logger. A File-like will write to file. The default
            `None` will turn off all access logs.
        error_logs ('default' or 'logger' or `File`-like or None, optional): Same as `access_logs` except we use
            our `logger` as the default.

    Returns:
        multiprocessing.Process: The process running the config server.
    """
    logger.info(f'Starting config-server with  config_file={config_file!r}')
    config = load_config(config_files=config_file, load_local=load_local, parse=False)
    logger.info(f'Config server Loaded {len(config)} top-level items')

    # Add an entry to control running of the server.
    config['config_server'] = dict(running=True)

    logger.info(f'{config!r}')
    cut_config = Cut(config)

    with app.app_context():
        app.config['config_file'] = config_file
        app.config['save_local'] = save_local
        app.config['load_local'] = load_local
        app.config['POCS'] = config
        app.config['POCS_cut'] = cut_config
        logger.info(f'Config items saved to flask config-server')

        # Set up access and error logs for server.
        access_logs = logger if access_logs == 'logger' else access_logs
        error_logs = logger if error_logs == 'logger' else error_logs

        def start_server(host='localhost', port=6563):
            try:
                logger.info(f'Starting config server with {host}:{port}')
                http_server = WSGIServer((host, int(port)), app, log=access_logs,
                                         error_log=error_logs)
                http_server.serve_forever()
            except OSError:
                logger.warning(
                    f'Problem starting config server, is another config server already running?')
                return None
            except Exception as e:
                logger.warning(f'Problem starting config server: {e!r}')
                return None

        host = host or os.getenv('CONFIG_HOST', 'localhost')
        port = port or os.getenv('CONFIG_PORT', 6563)
        cmd_kwargs = dict(host=host, port=port)
        logger.debug(f'Setting up config server process with  cmd_kwargs={cmd_kwargs!r}')
        server_process = Process(target=start_server,
                                 daemon=True,
                                 kwargs=cmd_kwargs)

        if auto_start:
            server_process.start()

        return server_process


@app.route('/heartbeat', methods=['GET', 'POST'])
def heartbeat():
    """A simple echo service to be used for a heartbeat.

    Defaults to looking for the 'config_server.running' bool value, although a
    different `key` can be specified in the POST.
    """
    params = dict()
    if request.method == 'GET':
        params = request.args
    elif request.method == 'POST':
        params = request.get_json()

    key = params.get('key', 'config_server.running')
    if key is None:
        key = 'config_server.running'
    is_running = app.config['POCS_cut'].get(key, False)

    return jsonify(is_running)


@app.route('/get-config', methods=['GET', 'POST'])
def get_config_entry():
    """Get config entries from server.

    Endpoint that responds to GET and POST requests and returns
    configuration item corresponding to provided key or entire
    configuration. The key entries should be specified in dot-notation,
    with the names corresponding to the entries stored in the configuration
    file. See the `scalpl <https://pypi.org/project/scalpl/>`_ documentation
    for details on the dot-notation.

    The endpoint should receive a JSON document with a single key named ``"key"``
    and a value that corresponds to the desired key within the configuration.

    For example, take the following configuration:

    .. code:: javascript

        {
            'location': {
                'elevation': 3400.0,
                'latitude': 19.55,
                'longitude': 155.12,
            }
        }

    To get the corresponding value for the elevation, pass a JSON document similar to:

    .. code:: javascript

        '{"key": "location.elevation"}'

    Returns:
        str: The json string for the requested object if object is found in config.
        Otherwise a json string with ``status`` and ``msg`` keys will be returned.
    """
    params = dict()
    if request.method == 'GET':
        params = request.args
    elif request.method == 'POST':
        params = request.get_json()

    verbose = params.get('verbose', True)
    log_level = 'DEBUG' if verbose else 'TRACE'

    # If requesting specific key
    logger.debug(f'Received  params={params!r}')

    if request.is_json:
        try:
            key = params['key']
            logger.debug(f'Request contains  key={key!r}')
        except KeyError:
            return jsonify({
                'success': False,
                'msg': "No valid key found. Need json request: {'key': <config_entry>}"
            })

        if key is None:
            # Return all
            logger.debug('No valid key given, returning entire config')
            show_config = app.config['POCS']
        else:
            try:
                logger.debug(f'Looking for  key={key!r} in config')
                show_config = app.config['POCS_cut'].get(key, None)
            except Exception as e:
                logger.error(f'Error while getting config item: {e!r}')
                show_config = None
    else:
        # Return entire config
        logger.debug('No valid key given, returning entire config')
        show_config = app.config['POCS']

    logger.debug(f'Returning  show_config={show_config!r}')
    logger.debug(f'Returning {show_config!r}')
    return jsonify(show_config)


@app.route('/set-config', methods=['GET', 'POST'])
def set_config_entry():
    """Sets an item in the config.

    Endpoint that responds to GET and POST requests and sets a
    configuration item corresponding to the provided key.

    The key entries should be specified in dot-notation, with the names
    corresponding to the entries stored in the configuration file. See
    the `scalpl <https://pypi.org/project/scalpl/>`_ documentation for details
    on the dot-notation.

    The endpoint should receive a JSON document with a single key named ``"key"``
    and a value that corresponds to the desired key within the configuration.

    For example, take the following configuration:

    .. code:: javascript

        {
            'location': {
                'elevation': 3400.0,
                'latitude': 19.55,
                'longitude': 155.12,
            }
        }

    To set the corresponding value for the elevation, pass a JSON document similar to:

    .. code:: javascript

        '{"location.elevation": "1000 m"}'


    Returns:
        str: If method is successful, returned json string will be a copy of the set values.
        On failure, a json string with ``status`` and ``msg`` keys will be returned.
    """
    params = dict()
    if request.method == 'GET':
        params = request.args
    elif request.method == 'POST':
        params = request.get_json()

    if params is None:
        return jsonify({
            'success': False,
            'msg': "Invalid. Need json request: {'key': <config_entry>, 'value': <new_values>}"
        })

    try:
        app.config['POCS_cut'].update(params)
    except KeyError:
        for k, v in params.items():
            app.config['POCS_cut'].setdefault(k, v)

    # Config has been modified so save to file.
    save_local = app.config['save_local']
    logger.info(f'Setting config  save_local={save_local!r}')
    if save_local and app.config['config_file'] is not None:
        save_config(app.config['config_file'], app.config['POCS_cut'].copy())

    return jsonify(params)


@app.route('/reset-config', methods=['POST'])
def reset_config():
    """Reset the configuration.

    An endpoint that accepts a POST method. The json request object
    must contain the key ``reset`` (with any value).

    The method will reset the configuration to the original configuration files that were
    used, skipping the local (and saved file).

    .. note::

        If the server was originally started with a local version of the file, those will
        be skipped upon reload. This is not ideal but hopefully this method is not used too
        much.

    Returns:
        str: A json string object containing the keys ``success`` and ``msg`` that indicate
        success or failure.
    """
    params = dict()
    if request.method == 'GET':
        params = request.args
    elif request.method == 'POST':
        params = request.get_json()

    logger.warning(f'Resetting config server')

    if params['reset']:
        # Reload the config
        config = load_config(config_files=app.config['config_file'],
                             load_local=app.config['load_local'],
                             parse=params.get('parse', False)
                             )
        # Add an entry to control running of the server.
        config['config_server'] = dict(running=True)
        app.config['POCS'] = config
        app.config['POCS_cut'] = Cut(config)
    else:
        return jsonify({
            'success': False,
            'msg': "Invalid. Need json request: {'reset': True}"
        })

    return jsonify({
        'success': True,
        'msg': f'Configuration reset'
    })