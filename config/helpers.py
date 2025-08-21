from contextlib import suppress
from pathlib import Path
from typing import Dict, List, Union

from loguru import logger

from utils import error
from utils.serializers import from_yaml, to_yaml
from utils import listify


def load_config(config_files: Union[Path, List] = None, parse: bool = True,
                load_local: bool = True):
    """Load configuration information.

    .. note::

        This function is used by the config server and normal config usage should
        be via a running config server.

    This function supports loading of a number of different files. If no options
    are passed to ``config_files`` then the default ``$CONFIG_FILE``
    will be loaded.

    ``config_files`` is a list and loaded in order, so the second entry will overwrite
    any values specified by similarly named keys in the first entry.

    ``config_files`` should be specified by an absolute path, which can exist anywhere
    on the filesystem.

    Local versions of files can override built-in versions and are automatically loaded if
    they exist alongside the specified config path. Local files have a ``<>_local.yaml`` name, where
    ``<>`` is the built-in file.

    Given the following path:

    ::

        /path/to/dir
        |- my_conf.yaml
        |- my_conf_local.yaml

    You can do a ``load_config('/path/to/dir/my_conf.yaml')`` and both versions of the file will
    be loaded, with the values in the local file overriding the non-local. Typically the local
    file would also be ignored by ``git``, etc.

    For example, the ``config.server.config_server`` will always save values to
    a local version of the file so the default settings can always be recovered if necessary.

    Local files can be ignored (mostly for testing purposes or for recovering default values)
    with the ``load_local=False`` parameter.

    Args:
        config_files (list, optional): A list of files to load as config,
            see Notes for details of how to specify files.
        parse (bool, optional): If the config file should attempt to create
            objects such as dates, astropy units, etc.
        load_local (bool, optional): If local files should be used, see
            Notes for details.

    Returns:
        dict: A dictionary of config items.
    """
    config = dict()

    config_files = listify(config_files)
    logger.debug(f'Loading config files: config_files={config_files!r}')
    for config_file in config_files:
        config_file = Path(config_file)
        try:
            logger.debug(f'Adding config_file={config_file!r} to config dict')
            _add_to_conf(config, config_file, parse=parse)
        except Exception as e:  # pragma: no cover
            logger.warning(f"Problem with config_file={config_file!r}, skipping. {e!r}")

        # Load local version of config
        if load_local:
            local_version = config_file.parent / Path(config_file.stem + '_local.yaml')
            if local_version.exists():
                try:
                    _add_to_conf(config, local_version, parse=parse)
                except Exception as e:  # pragma: no cover
                    logger.warning(f"Problem with local_version={local_version!r}, skipping: {e!r}")

    # parse_config_directories currently only corrects directory names.
    if parse:
        logger.trace(f'Parsing config={config!r}')
        with suppress(KeyError):
            config['directories'] = parse_config_directories(config['directories'])
            logger.trace(f'Config directories parsed: config={config!r}')

    return config


def save_config(save_path: Path, config: dict, overwrite: bool = True):
    """Save config to local yaml file.

    Args:
        save_path (str): Path to save, can be relative or absolute. See Notes in
            ``load_config``.
        config (dict): Config to save.
        overwrite (bool, optional): True if file should be updated, False
            to generate a warning for existing config. Defaults to True
            for updates.

    Returns:
        bool: If the save was successful.

    Raises:
         FileExistsError: If the local path already exists and ``overwrite=False``.
    """
    # Make sure it's a path.
    save_path = Path(save_path)

    # Make sure ends with '_local.yaml'.     
    if save_path.stem.endswith('_local') is False:
        save_path = save_path.with_name(save_path.stem + '_local.yaml')

    if save_path.exists() and overwrite is False:
        raise FileExistsError(f"Path exists and overwrite=False: {save_path}")
    else:
        # Create directory if it does not exist.
        save_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f'Saving config to {save_path}')
        with save_path.open('w') as fn:
            to_yaml(config, stream=fn)
        logger.info(f'Config info saved to {save_path}')

    return True


def parse_config_directories(directories: Dict[str, str]):
    """Parse the config dictionary for common objects.

    Given a `base` entry that corresponds to the absolute path of a directory,
    prepend the `base` to all other relative directory entries.

    The `base` directory must exist or an exception is rasied.

    If the `base` entry is not given the current working directory is used.

    .. doctest::

        >>> dirs_config = dict(base='/tmp', foo='bar', baz='bam', app='/app')
        >>> parse_config_directories(dirs_config)
        {'base': '/tmp', 'foo': '/tmp/bar', 'baz': '/tmp/bam', 'app': '/app'}

        >>> # If base doesn't exist an exception is raised.
        >>> dirs_config = dict(base='/panoptes', foo='bar', baz='bam', app='/app')
        >>> parse_config_directories(dirs_config)
        Traceback (most recent call last):
        ...
        error.NotFound: NotFound: Base directory does not exist: /panoptes

    Args:
        directories (dict): The dictionary of directory information. Usually comes
            from the "directories" entry in the config.

    Returns:
        dict: The same directory but with relative directories resolved.

    Raises:
        error.NotFound: if the 'base' entry is given but does not exist.
    """
    resolved_dirs = directories.copy()

    # Try to get the base directory first.
    base_dir = Path(resolved_dirs.get('base', '.')).absolute()

    # Warn if base directory does not exist.
    if base_dir.is_dir() is False:
        raise error.NotFound(f'Base directory does not exist: {base_dir}')

    # Add back absolute path for base directory.
    resolved_dirs['base'] = str(base_dir)
    logger.trace(f'Using base_dir={base_dir!r} for setting config directories')

    # Add the base directory to any relative dir.
    for dir_name, dir_path in resolved_dirs.items():
        if dir_path.startswith('/') is False and dir_name != 'base':
            sub_dir = (base_dir / dir_path).absolute()

            if sub_dir.exists() is False:
                logger.warning(f'{sub_dir!r} does not exist.')

            logger.trace(f'Setting {dir_name} to {sub_dir}')
            resolved_dirs[dir_name] = str(sub_dir)

    return resolved_dirs


def _add_to_conf(config: dict, conf_fn: Path, parse: bool = False):
    with suppress(IOError, TypeError):
        with conf_fn.open('r') as fn:
            config.update(from_yaml(fn.read(), parse=parse))
