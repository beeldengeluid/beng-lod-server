import logging
import os
import validators
from pathlib import Path


def validate_config(config, validate_file_paths=True):
    file_paths_to_check = []
    try:
        assert __check_setting(config, "APP_HOST", str), "APP_HOST"  # check  host
        assert __check_setting(config, "APP_PORT", int), "APP_PORT"
        assert __check_setting(config, "APP_VERSION", str), "APP_VERSION"
        assert __check_setting(config, "DEBUG", bool), "DEBUG"

        # checking the list of profiles
        assert __check_setting(config, "PROFILES", list), "PROFILES"  # check contents

        for p in config["PROFILES"]:
            assert __check_setting(p, "title", str), "PROFILE.title"
            assert __check_setting(p, "uri", str), "PROFILE.uri"
            assert validators.url(p["uri"]), "PROFILE.contentUrl invalid URL"
            assert __check_setting(p, "prefix", str), "PROFILE.prefix"

            assert __check_setting(p, "schema", str), "PROFILE.schema"
            file_paths_to_check.append(p["schema"])
            assert __check_setting(p, "mapping", str), "PROFILE.mapping"
            file_paths_to_check.append(p["mapping"])

            assert __check_setting(
                p, "storage_handler", type
            ), "PROFILE.storage_handler"
            assert __check_setting(p, "ob_links", str, True), "PROFILE.ob_links"
            assert __check_setting(p, "default", bool, True), "PROFILE.default"

        assert __check_setting(config, "LOG_DIR", str), "LOG_DIR"  # check file path

        assert __check_setting(config, "LOG_NAME", str), "LOG_NAME"

        assert __check_setting(config, "LOG_LEVEL_CONSOLE", str), "LOG_LEVEL_CONSOLE"
        assert __check_log_level(config["LOG_LEVEL_CONSOLE"])

        assert __check_setting(config, "LOG_LEVEL_FILE", str), "LOG_LEVEL_FILE"
        assert __check_log_level(config["LOG_LEVEL_FILE"])

        assert __check_setting(config, "STORAGE_BASE_URL", str), "STORAGE_BASE_URL"
        assert validators.url(
            config["STORAGE_BASE_URL"]
        ), "STORAGE_BASE_URL invalid URL"

        assert __check_setting(config, "ENABLED_ENDPOINTS", list), "ENABLED_ENDPOINTS"
        for ep in config["ENABLED_ENDPOINTS"]:
            assert ep in [
                "dataset",
                "resource",
                "gtaa",
                "pong",
                "health",
            ], "ENABLED_ENDPOINTS: invalid endpoint ID"

        assert __check_setting(
            config, "DATA_CATALOG_FILE", str
        ), "DATA_CATALOG_FILE"  # check valid path
        file_paths_to_check.append(config["DATA_CATALOG_FILE"])

        assert __check_setting(config, "SPARQL_ENDPOINT", str), "SPARQL_ENDPOINT"
        assert validators.url(config["SPARQL_ENDPOINT"]), "SPARQL_ENDPOINT invalid URL"

        assert __check_setting(config, "SPARQL_ENDPOINT_HEALTH_URL", str), "SPARQL_ENDPOINT_HEALTH_URL"
        assert validators.url(config["SPARQL_ENDPOINT_HEALTH_URL"]), "SPARQL_ENDPOINT_HEALTH_URL invalid URL"

        assert __check_setting(config, "BENG_DATA_DOMAIN", str), "BENG_DATA_DOMAIN"
        assert validators.url(
            config["BENG_DATA_DOMAIN"]
        ), "BENG_DATA_DOMAIN invalid URL"

        assert __check_setting(config, "AUTH_USER", str), "AUTH_USER"
        assert __check_setting(config, "AUTH_PASSWORD", str), "AUTH_PASSWORD"

        assert __check_setting(config, "HEALTH_TIMEOUT_SEC", float), "HEALTH_TIMEOUT_SEC"

        if validate_file_paths:
            assert __validate_file_paths(
                file_paths_to_check
            ), "invalid  paths in configuration"
            assert __validate_parent_dir(
                config["LOG_DIR"]
            ), "LOG_DIR parent dir does not exist"

    except AssertionError as e:
        print(f"Configuration error: {str(e)}")
        return False
    return True


def __check_setting(config, key, t, optional=False):
    setting = config.get(key, None)
    return (type(setting) == t and optional is False) or (
        optional and (setting is None or type(setting) == t)
    )


def __check_log_level(level: str) -> bool:
    return level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def __validate_parent_dir(path: str) -> bool:
    return os.path.exists(Path(path).parent.absolute())


def __validate_file_paths(paths: list) -> bool:
    return all([os.path.exists(p) for p in paths])


def init_logger(app):
    logger = logging.getLogger(app.config["LOG_NAME"])
    level_file = logging.getLevelName(app.config["LOG_LEVEL_FILE"])
    level_console = logging.getLevelName(app.config["LOG_LEVEL_CONSOLE"])
    logger.setLevel(level_file)

    # create file handler which logs even debug messages
    if not os.path.exists(os.path.realpath(app.config["LOG_DIR"])):
        os.makedirs(os.path.realpath(app.config["LOG_DIR"]))

    fh = logging.FileHandler(
        os.path.join(os.path.realpath(app.config["LOG_DIR"]), app.config["LOG_NAME"])
    )
    fh.setLevel(level_file)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(level_console)

    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s|%(levelname)s|%(process)d|%(module)s|%(funcName)s|%(lineno)d|%(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info("Loaded logger")

    return logger
