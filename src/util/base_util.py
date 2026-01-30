import logging
import os.path
import validators
from pathlib import Path

logger = logging.getLogger(__name__)
LOG_FORMAT = "%(asctime)s|%(levelname)s|%(process)d|%(module)s|%(funcName)s|%(lineno)d|%(message)s"


# returns the root of this repo by running "cd ../.." from this __file__ on
def get_repo_root() -> str:
    return os.path.realpath(
        os.path.join(os.path.dirname(__file__), os.sep.join(["..", ".."]))
    )


# see https://stackoverflow.com/questions/52878999/adding-a-relative-path-to-an-absolute-path-in-python
def relative_from_repo_root(path: str) -> str:
    return os.path.normpath(
        os.path.join(
            get_repo_root(),
            path.replace("/", os.sep),  # POSIX path seperators also work on windows
        )
    )


def validate_config(config, validate_file_paths=True):
    file_paths_to_check = []
    try:
        assert __check_setting(config, "LOG_LEVEL", str), "LOG_LEVEL"
        assert __check_log_level(config["LOG_LEVEL"]), "LOG_LEVEL"

        assert __check_setting(config, "APP_HOST", str), "APP_HOST"  # check  host
        assert __check_setting(config, "APP_PORT", int), "APP_PORT"
        assert __check_setting(config, "APP_VERSION", str), "APP_VERSION"
        assert __check_setting(config, "DEBUG", bool), "DEBUG"

        assert __check_setting(config, "ENABLED_ENDPOINTS", list), "ENABLED_ENDPOINTS"
        for ep in config["ENABLED_ENDPOINTS"]:
            assert ep in [
                "dataset",
                "resource",
                "gtaa",
                "pong",
                "health",
                "link",
            ], "ENABLED_ENDPOINTS: invalid endpoint ID"

        assert __check_setting(config, "DATA_CATALOG_GRAPH", str), "DATA_CATALOG_GRAPH"
        assert validators.url(
            config["DATA_CATALOG_GRAPH"]
        ), "DATA_CATALOG_GRAPH invalid URL"

        assert __check_setting(config, "SPARQL_ENDPOINT", str), "SPARQL_ENDPOINT"
        assert validators.url(config["SPARQL_ENDPOINT"]), "SPARQL_ENDPOINT invalid URL"

        assert __check_setting(
            config, "SPARQL_ENDPOINT_HEALTH_URL", str
        ), "SPARQL_ENDPOINT_HEALTH_URL"
        assert validators.url(
            config["SPARQL_ENDPOINT_HEALTH_URL"]
        ), "SPARQL_ENDPOINT_HEALTH_URL invalid URL"

        assert __check_setting(config, "BENG_DATA_DOMAIN", str), "BENG_DATA_DOMAIN"
        assert validators.url(
            config["BENG_DATA_DOMAIN"]
        ), "BENG_DATA_DOMAIN invalid URL"

        assert __check_setting(
            config, "HEALTH_TIMEOUT_SEC", float
        ), "HEALTH_TIMEOUT_SEC"

        if validate_file_paths:
            assert __validate_file_paths(
                file_paths_to_check
            ), "invalid  paths in configuration"

    except AssertionError as e:
        return False, e
    return True, None


def __check_setting(config, key, t, optional=False):
    setting = config.get(key, None)
    return (isinstance(setting, t) and optional is False) or (
        optional and (setting is None or isinstance(setting, t))
    )


def __check_log_level(level: str) -> bool:
    return level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def __validate_file_paths(paths: list) -> bool:
    return all([os.path.exists(p) for p in paths])


def get_parent_dir(path: str) -> Path:
    return Path(path).parent
