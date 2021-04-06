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

    # # Cannot use these
    # # For head plugin: http://dev-es-bng-01.beeldengeluid.nl/head
    # ES_FLEX_HOST = "dev-es-bng-01.beeldengeluid.nl"
    # # ES_FLEX_PORT =
    #
    # # test cluster
    # ES_FLEX_PROGRAM_ALIAS = "flexdatastore-program"
    # ES_FLEX_PROGRAM_INDEX = "flexdatastore-program_1.0.3-snapshot"
    # ES_FLEX_SERIES_ALIAS = "flexdatastore-series"
    # ES_FLEX_SERIES_INDEX = "flexdatastore-series_1.0.3-snapshot"
    # ES_FLEX_SEASON_ALIAS = "flexdatastore-season"
    # ES_FLEX_SEASON_INDEX = "flexdatastore-season_1.0.3-snapshot"
    # ES_FLEX_ITEM_ALIAS = "flexdatastore-item"
    # ES_FLEX_ITEM_INDEX = "flexdatastore-item_1.0.3-snapshot"
    # ES_FLEX_LOGTRACKITEM_ALIAS = "flexdatastore-logtrackitem"
    # ES_FLEX_LOGTRACKITEM_INDEX = "flexdatastore-logtrackitem_1.0.3-snapshot"

    ODL_BASE_DOMAIN = "data.rdlabs.beeldengeluid.nl"
