#!/usr/bin/env python

import os
import logging
import yaml
import pkg_resources

from gmprocess.constants import CONFIG_FILE_TEST, CONFIG_FILE_PRODUCTION


def update_dict(target, source):
    """Merge values from source dictionary into target dictionary.

    Args:
        target (dict):
            Dictionary to be updated with values from source dictionary.

        source (dict):
            Dictionary with values to be transferred to target dictionary.
    """
    for key, value in source.items():
        if not isinstance(value, dict) or \
                not key in target.keys() or \
                not isinstance(target[key], dict):
            target[key] = value
        else:
            update_dict(target[key], value)
    return


def merge_dicts(dicts):
    """Merges a list of dictionaries into a new dictionary.

    The order of the dictionaries in the list provides precedence of the
    values, with values from subsequent dictionaries overriding earlier
    ones.

    Args:
        dicts (list of dictionaries):
            List of dictionaries to be merged.

    Returns:
        dictionary: Merged dictionary.
    """
    target = dicts[0].copy()
    for source in dicts[1:]:
        update_dict(target, source)
    return target


def get_config(section=None):
    """Gets the user defined config and validates it.

    Notes:
        If no config file is present, default parameters are used.

    Args:
        section (str):
            Name of section in the config to extract (i.e., 'fetchers',
            'processing', 'pickers', etc.) If None, whole config is returned.

    Returns:
        dictionary:
            Configuration parameters.
    Raises:
        IndexError:
            If input section name is not found.
    """

    if ('CALLED_FROM_PYTEST' in os.environ and
            os.environ['CALLED_FROM_PYTEST'] == 'True'):
        file_to_use = CONFIG_FILE_TEST
    else:
        file_to_use = CONFIG_FILE_PRODUCTION

    data_dir = os.path.abspath(
        pkg_resources.resource_filename('gmprocess', 'data'))
    config_file = os.path.join(data_dir, file_to_use)

    if not os.path.isfile(config_file):
        fmt = ('Missing config file %s, please run gmsetup to install '
               'default config file.')
        logging.info(fmt % config_file)
        config = None
    else:
        with open(config_file, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

    if section is not None:
        if section not in config:
            raise IndexError('Section %s not found in config file.' % section)
        else:
            config = config[section]

    return config
