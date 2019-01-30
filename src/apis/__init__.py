from flask_restplus import Api
from .lod.lod_api import api as lodAPI
from .lod.lod_api import api2 as lodSchema


apiVersion = 'v0.1'
basePath = '/'
api = Api(version=apiVersion)

api.add_namespace(lodAPI, path='%s' % basePath)
api.add_namespace(lodSchema, path='%s//schema' % basePath)
