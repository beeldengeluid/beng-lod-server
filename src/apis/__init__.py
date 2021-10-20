from flask_restx import Api
from .dataset.dataset_api import api as dataset_api
from .resource.resource_api import api as resource_api
from .concept.concept_api import api as concept_api
from config.settings import Config

apiVersion = 'v0.3'
base_path = '/'

api = Api(version=apiVersion)

try:
	enabled_endpoints = Config.ENABLED_ENDPOINTS
except AttributeError as e:
	print('Misconfiguration, please add ENABLED_ENDPOINTS, now disallowing all endpoints')
	enabled_endpoints = []

if 'dataset' in enabled_endpoints:
	api.add_namespace(dataset_api, path='%s' % base_path)

if 'resource' in enabled_endpoints:
	api.add_namespace(resource_api, path='%s' % base_path)

if 'concept' in enabled_endpoints:
	api.add_namespace(concept_api, path='%s' % base_path)