"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-22
Topic   : config_parser utils

"""


from distutils.command.config import config
from collections import UserDict
from ruamel import yaml
from ruamel.yaml.scanner import ScannerError

import os
import sys
import logging

log = logging.getLogger(__name__)

class Config(UserDict):
    """
    Arguments:
        config_path (str): Path to the configuration file.
        Default: ./properties/conf.yaml

    Public methods:
        load: Loads configuration from configuration YAML file.

    Attributes and properties:
        config_path (str): Path to the configuration file.
        data(dict): Program configuration.
    """

    def __init__(self, env_type, config_path = './properties/conf.yaml'):
        self.config_path = os.path.expanduser(config_path)
        self.load(env_type)

    def load(self, env_type):
        """
        loads config from yaml file
        """
        try:
            with open(os.path.expanduser(self.config_path), 'r') as f:
                try:
                    yaml_conn = yaml.YAML(typ='safe', pure=True)
                    cfg_data = yaml_conn.load(f)
                    self.data = cfg_data[env_type]
                except ScannerError as e:
                    log.error(
                        'Error parsing YAML config file '
                        '{}:{}'.format(
                            e.problem_mark,
                            e.problem
                        )
                    )
                    sys.exit(1)
        except FileNotFoundError:
            log.error(
                'YAML file not found in {}'.format(
                    self.config_path
                )
            )
            sys.exit(1)
