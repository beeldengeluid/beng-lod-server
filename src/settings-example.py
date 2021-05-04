class Config(object):
    APP_HOST = '0.0.0.0'
    APP_PORT = 5309
    APP_VERSION = 'v1.2'

    DEBUG = True
    CACHE_TYPE = 'SimpleCache'

    # OAI_BASE_URL = 'http://dummy.oai.com'
    # XSLT_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'nisv-bg-oai2lod-v04.xsl'))

    STORAGE_BASE_URL = 'http://...'

    PROFILES = [
        {
            'id' : 'http://data.rdlabs.beeldengeluid.nl/schema',
            'schema' : '../resource/bengSchema.ttl',
            'mapping' : '../resource/daan-mapping-storage.ttl',
            'default' : True #this profile is loaded in memory by default
        },
        {
            'id' : 'http://schema.org',
            'schema' : '../resource/schema-dot-org.ttl',
            'mapping' : '../resource/daan-mapping-schema-org.ttl'
        },
        {
            'id' : 'oai',
            'mapping' : '../resource/daan-mapping.ttl',
        }
    ]
