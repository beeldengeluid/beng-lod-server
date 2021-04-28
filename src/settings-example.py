import os
from util import SettingsUtil


class Config(object):
    APP_HOST = '0.0.0.0'
    APP_PORT = 5309
    APP_VERSION = 'v1.2'

    DEBUG = True
    CACHE_TYPE = 'SimpleCache'

    base_path = SettingsUtil.getBasePath()

    OAI_BASE_URL = 'http://dummy.oai.com'

    XSLT_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'nisv-bg-oai2lod-v04.xsl'))
    SCHEMA_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'bengSchema.ttl'))
    SCHEMA_DOT_ORG = os.path.abspath(os.path.join(base_path, 'resource', 'schemaorg-current-https.ttl'))

    # use version below when using OAI
    # MAPPING_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'daan-mapping.ttl'))
    # use version below when using storage API
    MAPPING_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'daan-mapping-storage.ttl'))
    MAPPING_FILE_SDO = os.path.abspath(os.path.join(base_path, 'resource', 'daan-mapping-storage-sdo.ttl'))

    STORAGE_BASE_URL = 'http://acc-app-bng-01.beeldengeluid.nl:8101'
