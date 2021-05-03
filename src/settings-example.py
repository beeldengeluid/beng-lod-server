import os
from util import SettingsUtil


class Config(object):
    APP_HOST = '0.0.0.0'
    APP_PORT = 5309
    APP_VERSION = 'v1.2'

    DEBUG = True
    CACHE_TYPE = 'SimpleCache'

    base_path = SettingsUtil.get_base_path()

    OAI_BASE_URL = 'http://dummy.oai.com'

    XSLT_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'nisv-bg-oai2lod-v04.xsl'))
    SCHEMA_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'bengSchema.ttl'))

    # use version below when using storage API
    MAPPING_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'daan-mapping-storage.ttl'))
    STORAGE_BASE_URL = 'http://acc-app-bng-01.beeldengeluid.nl:8101'


# use version below when using OAI
class OAIConfig(Config):
    base_path = SettingsUtil.get_base_path()
    MAPPING_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'daan-mapping.ttl'))


class SDOConfig(Config):
    base_path = SettingsUtil.get_base_path()
    # SCHEMA_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'schemaorg-current-https.ttl'))
    MAPPING_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'daan-mapping-storage-sdo.ttl'))


class NISVConfig(Config):
    base_path = SettingsUtil.get_base_path()
    # SCHEMA_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'bengSchema.ttl'))
    MAPPING_FILE = os.path.abspath(os.path.join(base_path, 'resource', 'daan-mapping-storage.ttl'))
