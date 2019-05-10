class Config(object):

	APP_HOST = '0.0.0.0'
	APP_PORT = 5309
	APP_VERSION = 'v1.1'

	DEBUG = True

	OAI_BASE_URL = 'http://oaipmh.beeldengeluid.nl'
	XSLT_FILE = '../resource/nisv-bg-oai2lod-v03.xsl'
	SCHEMA_FILE = '../resource/bengSchema.ttl'