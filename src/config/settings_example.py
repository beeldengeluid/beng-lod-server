from apis.resource.DAANStorageLODHandler import DAANStorageLODHandler
from apis.resource.SDOStorageLODHandler import SDOStorageLODHandler


class Config(object):
    APP_HOST = '0.0.0.0'
    APP_PORT = 5309
    APP_VERSION = 'v1.2'

    DEBUG = True
    CACHE_TYPE = 'SimpleCache'

    STORAGE_BASE_URL = 'http://prd-app-bng-01.beeldengeluid.nl:8101/'

    ENABLED_ENDPOINTS = ['resource', 'concept', 'dataset'] # allow all by default

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
            'default': True  # this profile is loaded in memory by default
        },
        {
            'title': 'NISV Catalogue OAI schema',
            'uri': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
            # temporary: taken from https://dltj.org/article/oai-pmh-namespaces/
            'prefix': 'oai',
            'schema': None,
            'mapping': '../resource/daan-mapping.ttl',
        }
    ]

    SERVICE_ACCOUNT_FILE = 'datacatalogfromspreadsheet-a5ccabb0919f.json'
    SERVICE_ACCOUNT_ID = '112951440462998509903'
    ODL_SPREADSHEET_ID = '14KEFxuNfM9yezKssyUHrGuhL6sRC6ATvtPcrghKNh8s'

    DATA_CATALOG_FILE = '../resource/data_catalog.ttl'

    BENG_DATA_DOMAIN = 'http://data.beeldengeluid.nl/'

    SPARQL_EXAMPLES = "../resource/example_queries.json"
