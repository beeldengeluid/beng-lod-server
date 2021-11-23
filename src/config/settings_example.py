from apis.resource.DAANStorageLODHandler import DAANStorageLODHandler
from apis.resource.SDOStorageLODHandler import SDOStorageLODHandler


class Config(object):
    APP_HOST = '0.0.0.0'
    APP_PORT = 5309
    APP_VERSION = 'v1.2'

    DEBUG = True

    LOG_DIR = "./resources/log/" #should always work, log dir will be automatically created in your src/resources dir
    LOG_NAME = "beng-lod-server.log"
    LOG_LEVEL_CONSOLE = "DEBUG" # Levels: NOTSET - DEBUG - INFO - WARNING - ERROR - CRITICAL
    LOG_LEVEL_FILE = "DEBUG" # Levels: NOTSET - DEBUG - INFO - WARNING - ERROR - CRITICAL

    STORAGE_BASE_URL = 'http://prd-app-bng-01.beeldengeluid.nl:8101/'

    ENABLED_ENDPOINTS = ['resource', 'dataset']  # allow all by default

    # profiles determine which schema is used for the linked data
    PROFILES = [
        {
            'title': 'NISV Catalogue schema',
            'uri': 'http://data.rdlabs.beeldengeluid.nl/schema/',
            'prefix': 'nisv',  # based on @prefix nisv: <http://data.rdlabs.beeldengeluid.nl/schema/> .
            'schema': '../resource/bengSchema.ttl',
            'mapping': '../resource/daan-mapping-storage.ttl',
            'storage_handler': DAANStorageLODHandler
        },
        {
            'title': 'NISV Catalogue using schema.org ontology',
            'uri': 'https://schema.org/',
            'prefix': 'sdo',  # based on @prefix sdo: <https://schema.org/> .
            'schema': '../resource/schema-dot-org.ttl',
            'mapping': '../resource/daan-mapping-schema-org.ttl',
            'storage_handler': SDOStorageLODHandler,
            'ob_links': '../resource/ob_link_matches.json',
            'default': True  # this profile is loaded in memory by default
        }
    ]

    SERVICE_ACCOUNT_FILE = 'datacatalogfromspreadsheet-a5ccabb0919f.json'
    SERVICE_ACCOUNT_ID = '112951440462998509903'
    ODL_SPREADSHEET_ID = '14KEFxuNfM9yezKssyUHrGuhL6sRC6ATvtPcrghKNh8s'

    DATA_CATALOG_FILE = '../resource/data_catalog.ttl'

    BENG_DATA_DOMAIN = 'http://data.beeldengeluid.nl/'

    SPARQL_EXAMPLES = "../resource/example_queries.json"
    SPARQL_ENDPOINT = "https://cat.apis.beeldengeluid.nl/sparql"

    AUTH_USER = 'very_special'
    AUTH_PASSWORD = 'nobody_knows'
