import os
import sys
import logging
from typing import Dict
from pathlib import Path
from yaml import load, FullLoader
from yaml.scanner import ScannerError
from util.base_util import validate_config


logger = logging.getLogger(f"beng-lod-server.{__name__}")


# since the config is vital, it should be available
def load_config_or_die(cfg_file: str, load_as_env: bool = False):
    logger.info(f"Going to load the following config: {cfg_file}")
    try:
        with open(cfg_file, "r") as yamlfile:
            config = load(yamlfile, Loader=FullLoader)
            return config
    except (FileNotFoundError, ScannerError):
        logger.exception(f"Not a valid file path or config file {cfg_file}")
        sys.exit()


def load_env_vars():
    for k in VALID_ENV_VARS.keys():
        cfg[k] = os.environ[k]


def recursive_update(d1: dict, d2: dict) -> dict:
    """When updating config, only values that are overriden by config-local
    need to be updated. Especially, when a dict-type value is overridden, it should
    keep the values for keys that are not overridden. Therefor a recursive strategy
    is implemented. Further, when new keys appear in config-local, they should be
    added. Finally, a complete and overridden config structure is returned.
    """
    for k, v in d2.items():
        if isinstance(v, dict):
            d1[k] = recursive_update(d1.get(k, {}), v)
        elif isinstance(v, list):
            d1[k] = list(set(d1.get(k, []) + v))  # all unique list items
        else:
            d1[k] = d2[k]
    return d1


# TODO is there any way to detect the file path of the main function?
APPLICATION_MAIN_PATH = Path(
    __file__
).parent.parent  # your application must call from outside of dane_exporter

CONFIG_FILE = os.path.join(APPLICATION_MAIN_PATH, "config", "config.yml")
CONFIG_OVERRIDE = os.path.join(APPLICATION_MAIN_PATH, "config", "config-local.yml")
VALID_ENV_VARS: Dict[str, str] = {}

cfg = load_config_or_die(CONFIG_FILE)

# override with custom config
if os.path.exists(CONFIG_OVERRIDE):
    overrides = load_config_or_die(CONFIG_OVERRIDE)
    cfg = recursive_update(cfg, overrides)

# finally override with env vars
load_env_vars()

# Validate config before starting
config_valid, config_error = validate_config(cfg)
if config_valid is not True:
    logger.error(f"Config not valid: {config_error}\nQuitting..")
    quit()
