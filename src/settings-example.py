class Config(object):
    APP_HOST = '0.0.0.0'
    APP_PORT = 5309
    APP_VERSION = 'v1.2'

    DEBUG = True
    CACHE_TYPE = 'SimpleCache'

    ONTOSPY_OUTPUT_DIR = 'static/ontospy'

    STORAGE_BASE_URL = 'http://...'

    PROFILES = [
        {
            'title' : 'NISV Catalogue schema',
            'uri' : 'http://data.rdlabs.beeldengeluid.nl/schema/',
            'prefix' : 'nisv', # based on @prefix nisv: <http://data.rdlabs.beeldengeluid.nl/schema/> .
            'schema' : '../resource/bengSchema.ttl',
            'mapping' : '../resource/daan-mapping-storage.ttl'
        },
        {
            'title' : 'NISV Catalogue schema.org schema',
            'uri' : 'https://schema.org/',
            'prefix' : 'sdo', # based on @prefix sdo: <https://schema.org/> .
            'schema' : '../resource/schema-dot-org.ttl',
            'mapping' : '../resource/daan-mapping-schema-org.ttl',
            'default' : True #this profile is loaded in memory by default
        },
        {
            'title' : 'NISV Catalogue OAI schema',
            'uri' : 'http://www.openarchives.org/OAI/2.0/oai_dc/', #temporary: taken from https://dltj.org/article/oai-pmh-namespaces/
            'prefix' : 'oai',
            'schema' : None, # no ontospy dir is created if there is no schema
            'mapping' : '../resource/daan-mapping.ttl',
        }
    ]
