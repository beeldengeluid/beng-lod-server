from flask_restx import Api
from .lod.dataset_api import api as dataset_api
from .lod.resource_api import api as resource_api
from .lod.concept_api import api as concept_api

apiVersion = 'v0.3'
base_path = '/'

api = Api(version=apiVersion)

#TODO figure out to add/remove namespace based on settings (current_app cannot be used here)
api.add_namespace(dataset_api, path='%s' % base_path)
api.add_namespace(resource_api, path='%s' % base_path)
api.add_namespace(concept_api, path='%s' % base_path)