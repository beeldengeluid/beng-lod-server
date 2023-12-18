from apis.resource.DAANStorageLODHandler import DAANStorageLODHandler
from apis.resource.SDOStorageLODHandler import SDOStorageLODHandler
from util.base_util import relative_from_repo_root


class Config(object):
    APP_HOST = "0.0.0.0"
    APP_PORT = 5309
    APP_VERSION = "v1.2"

    DEBUG = True

    LOG_LEVEL = "DEBUG"  # Levels: DEBUG - INFO - WARNING - ERROR - CRITICAL

    STORAGE_BASE_URL = "http://flexstore.beng.example.com:1234"

    ENABLED_ENDPOINTS = [
        "resource",
        "dataset",
        "gtaa",
        "pong",
        "health",
    ]  # allow all by default

    # profiles determine which schema is used for the linked data
    PROFILES = [
        {
            "title": "NISV Catalogue schema",
            "uri": "http://data.rdlabs.beeldengeluid.nl/schema/",
            "prefix": "nisv",  # based on @prefix nisv: <http://data.rdlabs.beeldengeluid.nl/schema/> .
            "schema": relative_from_repo_root("resource/bengSchema.ttl"),
            "mapping": relative_from_repo_root("resource/daan-mapping-storage.ttl"),
            "storage_handler": DAANStorageLODHandler,
        },
        {
            "title": "NISV Catalogue using schema.org ontology",
            "uri": "https://schema.org/",
            "prefix": "sdo",  # based on @prefix sdo: <https://schema.org/> .
            "schema": relative_from_repo_root("resource/schema-dot-org.ttl"),
            "mapping": relative_from_repo_root("resource/daan-mapping-schema-org.ttl"),
            "storage_handler": SDOStorageLODHandler,
            "ob_links": relative_from_repo_root("resource/ob_link_matches.json"),
            "roles": relative_from_repo_root("resource/music_roles.csv"),
            "default": True,  # this profile is loaded in memory by default
        },
    ]

    DATA_CATALOG_GRAPH = "http://data.rdlabs.beeldengeluid.nl/datacatalog/"

    BENG_DATA_DOMAIN = "http://data.beeldengeluid.nl/"
    URI_NISV_ORGANISATION = "https://www.beeldengeluid.nl/"

    SPARQL_ENDPOINT = "https://cat.apis.beeldengeluid.nl/sparql"
    SPARQL_ENDPOINT_HEALTH_URL = "https://cat.apis.beeldengeluid.nl/sparql"

    SWAGGER_UI_PATH = "/swagger"

    AUTH_USER = "very_special"
    AUTH_PASSWORD = "nobody_knows"

    HEALTH_TIMEOUT_SEC = 5.0
