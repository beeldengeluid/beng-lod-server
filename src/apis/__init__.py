from flask_restplus import Api
from .lod.lod_api import api as lodAPI

apiVersion = 'v0.1'
basePath = '/api'
api = Api(version=apiVersion)

api.add_namespace(lodAPI, path='%s' % basePath)