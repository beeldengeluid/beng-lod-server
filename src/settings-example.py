class Config(object):

    APP_HOST = '0.0.0.0'
    APP_PORT = 5309
    APP_VERSION = 'v1.2'

    DEBUG = True

    OAI_BASE_URL = 'http://dummy.oai.com'
    XSLT_FILE = '../resource/nisv-bg-oai2lod.xsl'
    SCHEMA_FILE = '../resource/bengSchema.ttl'
    MAPPING_FILE = '../resource/daan-mapping.ttl'

    ES_INDEX = "daan-aggregated-prod-2020"
    ES_HOST = "deves2001.beeldengeluid.nl"
    ES_PORT = 9200

    ODL_BASE_DOMAIN = "data.rdlabs.beeldengeluid.nl"
