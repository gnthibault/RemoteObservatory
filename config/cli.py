import time

import click
from loguru import logger

from config import (server)
from config.client import get_config
from config.client import server_is_running
from config.client import set_config

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose/--no-verbose',
              envvar='DEBUG',
              help='Turn on logger for utils, default False')
@click.option('--host',
              default=None,
              envvar='CONFIG_HOST',
              help='The config server IP address or host name. First'
                   'checks cli argument, then CONFIG_HOST, then localhost.')
@click.option('--port',
              default=None,
              envvar='CONFIG_PORT',
              help='The config server port. First checks cli argument, '
                   'then CONFIG_PORT, then 6563')
@click.pass_context
def config_server_cli(context, host='localhost', port=6563, verbose=False):
    context.ensure_object(dict)
    context.obj['host'] = host
    context.obj['port'] = port

    # if verbose:
    #     logger.enable('')


@click.command('run')
@click.option('--config-file',
              default=None,
              envvar='CONFIG_FILE',
              help='The yaml config file to load.'
              )
@click.option('--load-local/--no-load-local',
              default=True,
              help='Use the local config files when loading, default True.')
@click.option('--save-local/--no-save-local',
              default=True,
              help='If the set values should be saved to the local file, default True.')
@click.option('--heartbeat',
              default=2,
              help='Heartbeat interval, default 2 seconds.')
@click.pass_context
def run(context, config_file=None, save_local=True, load_local=False, heartbeat=2):
    """Runs the config server with command line options.

    This function is installed as an entry_point for the module, accessible
     at `config-server`.
    """
    host = context.obj.get('host')
    port = context.obj.get('port')
    logger.debug("About to run config server")
    server_process = server.config_server(
        config_file,
        host=host,
        port=port,
        load_local=load_local,
        save_local=save_local,
        auto_start=False
    )

    try:
        print(f'Starting config server. Ctrl-c to stop')
        server_process.start()
        print(f'Config server started on  server_process.pid={server_process.pid!r}. '
              f'Set "config_server.running=False" or Ctrl-c to stop')

        # Loop until config told to stop.
        while server_is_running(host=host, port=port):
            time.sleep(heartbeat)

        server_process.terminate()
        server_process.join(30)
    except KeyboardInterrupt:
        logger.info(f'Config server interrupted, shutting down {server_process.pid}')
        server_process.terminate()
    except Exception as e:  # pragma: no cover
        logger.error(f'Unable to start config server {e!r}')


@click.command('stop')
@click.pass_context
def stop(context):
    """Stops the config server by setting a flag in the server itself."""
    host = context.obj.get('host')
    port = context.obj.get('port')
    logger.info(f'Shutting down config server on {host}:{port}')
    set_config('config_server.running', False, host=host, port=port)


@click.command('get')
@click.argument('key', nargs=-1)
@click.option('--default', help='The default to return if not key is found, default None')
@click.option('--parse/--no-parse',
              default=True,
              help='If results should be parsed into object, default True.')
@click.pass_context
def config_getter(context, key, parse=True, default=None):
    """Get an item from the config server by key name, using dotted notation (e.g. 'location.elevation')

    If no key is given, returns the entire config.
    """
    host = context.obj.get('host')
    port = context.obj.get('port')
    try:
        # The nargs=-1 makes this a tuple so we get first entry.
        key = key[0]
    except IndexError:
        key = None
    logger.debug(f'Getting config  key={key!r}')
    try:
        config_entry = get_config(key=key, host=host, port=port, parse=parse, default=default)
    except Exception as e:
        logger.error(f'Error while trying to get config: {e!r}')
        click.secho(f'Error while trying to get config: {e!r}', fg='red')
    else:
        logger.debug(f'Config server response:  config_entry={config_entry!r}')
        click.echo(config_entry)


@click.command('set')
@click.argument('key')
@click.argument('new_value')
@click.option('--parse/--no-parse',
              default=True,
              help='If results should be parsed into object.')
@click.pass_context
def config_setter(context, key, new_value, parse=True):
    """Set an item in the config server. """
    host = context.obj.get('host')
    port = context.obj.get('port')

    logger.debug(f'Setting config key={key!r}  new_value={new_value!r} on {host}:{port}')
    config_entry = set_config(key, new_value, host=host, port=port, parse=parse)
    click.echo(config_entry)


config_server_cli.add_command(run)
config_server_cli.add_command(stop)
config_server_cli.add_command(config_setter)
config_server_cli.add_command(config_getter)

if __name__ == '__main__':
    config_server_cli()  # This is where click takes control
