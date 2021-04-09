import os
from util import SettingsUtil


class Config(object):
    APP_HOST = '0.0.0.0'
    APP_PORT = 5309
    APP_VERSION = 'v1.2'

    DEBUG = True
    CACHE_TYPE = 'SimpleCache'

    basePath = SettingsUtil.getBasePath()

    OAI_BASE_URL = 'http://dummy.oai.com'
    XSLT_FILE = basePath + os.sep + 'resource' + os.sep + 'nisv-bg-oai2lod-v04.xsl'
    SCHEMA_FILE = basePath + os.sep + 'resource' + os.sep + 'bengSchema.ttl'
    # use version below when using OAI
    # MAPPING_FILE = basePath + os.sep + 'resource' + os.sep + 'daan-mapping.ttl'
    # use version below when using storage API
    MAPPING_FILE = basePath + os.sep + 'resource' + os.sep + 'daan-mapping-storage.ttl'
    STORAGE_BASE_URL = 'http://acc-app-bng-01.beeldengeluid.nl:8101'
